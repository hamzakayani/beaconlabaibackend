from datetime import datetime, timezone
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from email_validator import validate_email, EmailNotValidError

from app.db.database import get_db
from app.models.jobs import Job
from app.models.job_applicants import JobApplicant
from app.schemas.jobs import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobApplicationCreate,
    JobApplicationResponse,
    JobStatusEnum
)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.services.file_upload import save_cv_file

router = APIRouter()


@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    status_filter: Optional[JobStatusEnum] = Query(None, description="Filter by job status"),
    db: Session = Depends(get_db)
):
    """
    List all open jobs (public endpoint).
    Returns only jobs with status='open' and is_deleted=False.
    """
    query = db.query(Job).filter(
        and_(
            Job.is_deleted == False,
            Job.status == JobStatusEnum.open
        )
    )
    
    # Apply status filter if provided (for admin use, but keeping it flexible)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    
    # Get total count
    total_items = query.count()
    total_pages = ceil(total_items / size) if total_items > 0 else 0
    
    # Apply pagination
    items = query.order_by(Job.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    page_info = PageInfo(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return PaginatedResponse(items=items, page_info=page_info)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single job by ID (public endpoint).
    """
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.is_deleted == False
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Create a new job posting (admin only).
    """
    job = Job(
        title=job_data.title,
        job_type=job_data.job_type,
        location=job_data.location,
        description=job_data.description,
        status=job_data.status
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a job posting (admin only).
    """
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.is_deleted == False
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Update only provided fields
    if job.title is not None:
        job.title = job_data.title
    if job.job_type is not None:
        job.job_type = job_data.job_type
    if job.location is not None:
        job.location = job_data.location
    if job.description is not None:
        job.description = job_data.description
    if job.status is not None:
        job.status = job_data.status
    db.refresh(job)
    job.updated_at = datetime.now(timezone.utc)
    db.commit()

    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Soft delete a job posting (admin only).
    """
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.is_deleted == False
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job.is_deleted = True
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return None


@router.post("/{job_id}/apply", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    job_id: int,
    full_name: str = Form(..., min_length=1, max_length=255),
    email: str = Form(...),
    phone: Optional[str] = Form(None, max_length=50),
    cover_letter: Optional[str] = Form(None),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Apply to a job with CV upload (public endpoint).
    Accepts multipart/form-data with CV file and application details.
    """
    # Validate email format
    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email address: {str(e)}"
        )
    
    # Verify job exists and is open
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.is_deleted == False,
            Job.status == JobStatusEnum.open
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not accepting applications"
        )
    
    # Save CV file
    try:
        cv_file_path = await save_cv_file(cv, job_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV file: {str(e)}"
        )
    
    # Create job application
    try:
        application = JobApplicant(
            job_id=job_id,
            full_name=full_name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            cv_file_path=cv_file_path
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        return application
    
    except Exception as e:
        # Rollback and clean up file if database operation fails
        db.rollback()
        from app.services.file_upload import delete_cv_file
        delete_cv_file(cv_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )


@router.get("/{job_id}/applications", response_model=PaginatedResponse[JobApplicationResponse])
async def list_job_applications(
    job_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    List all applications for a specific job (admin only).
    """
    # Verify job exists
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.is_deleted == False
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    query = db.query(JobApplicant).filter(JobApplicant.job_id == job_id)
    
    # Get total count
    total_items = query.count()
    total_pages = ceil(total_items / size) if total_items > 0 else 0
    
    # Apply pagination
    items = query.order_by(JobApplicant.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    page_info = PageInfo(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return PaginatedResponse(items=items, page_info=page_info)

