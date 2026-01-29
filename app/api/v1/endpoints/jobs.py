from datetime import datetime, timezone
import os
from typing import Optional
from math import ceil
import uuid
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, BackgroundTasks
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
    JobApplicationResponse,
    JobStatusEnum,
    ReorderJobRequest
)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.services.file_upload import save_cv_file
from app.services.reorder import reorder_item
from app.services.email import send_job_application_notification

router = APIRouter()

@router.post("/create_job")
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Create a new job posting (admin only).
    """
    if job_data.order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0"
        )
    job = Job(
        title=job_data.title,
        job_type=job_data.job_type,
        location=job_data.location,
        description=job_data.description,
        status=job_data.status,
        funded_by=job_data.funded_by,
        visa_type=job_data.visa_type,
        job_tenure=job_data.job_tenure,
        required_qualifications=job_data.required_qualifications,
        preferred_qualifications=job_data.preferred_qualifications,
        order=job_data.order
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {"message": "Job created successfully"}

@router.get("", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    is_public: bool = Query(True, description="Whether to return all (open,closed,draft) jobs or only open and closed jobs"),
    status_filter: Optional[JobStatusEnum] = Query(None, description="Filter by job status"),
    db: Session = Depends(get_db)
):
    """
    List all open jobs (public endpoint).
    Returns only jobs with status='open' and is_deleted=False.
    """
    query = db.query(Job).filter(
        Job.is_deleted == False
    )
    
    if is_public:
        query = query.filter(Job.status.in_([JobStatusEnum.open, JobStatusEnum.closed]))
    else:
        query = query.filter(Job.status.in_([JobStatusEnum.open, JobStatusEnum.closed, JobStatusEnum.draft]))


    if status_filter:
        query = query.filter(Job.status == status_filter)

    total_items = query.count()
    total_pages = ceil(total_items / size) if total_items > 0 else 0

    items = query.order_by(Job.order).offset((page - 1) * size).limit(size).all()
    
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
        Job.id == job_id,
        Job.is_deleted == False
        ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job





@router.put("/{job_id}")
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
        Job.id == job_id,
        Job.is_deleted == False
        ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if order is being updated and needs reordering
    order_changed = False
    new_order = None
    
    if job_data.order is not None and job_data.order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0"
        )
    
    if job_data.order is not None and job_data.order != job.order:
        order_changed = True
        new_order = job_data.order
    
    if job_data.title is not None:
        job.title = job_data.title
    if job_data.job_type is not None:
        job.job_type = job_data.job_type
    if job_data.location is not None:
        job.location = job_data.location
    if job_data.description is not None:
        job.description = job_data.description
    if job_data.status is not None:
        job.status = job_data.status
    if job_data.funded_by is not None:
        job.funded_by = job_data.funded_by
    if job_data.visa_type is not None:
        job.visa_type = job_data.visa_type
    if job_data.job_tenure is not None:
        job.job_tenure = job_data.job_tenure
    if job_data.required_qualifications is not None:
        job.required_qualifications = job_data.required_qualifications
    if job_data.preferred_qualifications is not None:
        job.preferred_qualifications = job_data.preferred_qualifications
    # Note: order is handled by reorder_item service below

    # If order changed, perform reordering
    if order_changed:
        try:
            reorder_item(db, Job, job_id, new_order)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to reorder: {str(e)}"
            )
    
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    
    return {"message": "Job updated successfully"}

@router.delete("/{job_id}")
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
    
    return {"message": "Job deleted successfully"}


@router.post("/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    full_name: str = Form(..., min_length=1, max_length=255),
    email: str = Form(...),
    phone: Optional[str] = Form(None, max_length=50),
    cover_letter: Optional[str] = Form(None),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Apply to a job with CV upload (public endpoint).
    """

    try:
        validate_email(email)
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email address: {str(e)}"
        )

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

    file_ext = os.path.splitext(cv.filename)[1].lower()

    if file_ext not in settings.ALLOWED_CV_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF or Word documents are allowed"
        )

    contents = await cv.read()

    if len(contents) > settings.CV_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CV file is too large"
        )

    job_dir = settings.CV_UPLOAD_DIR / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = job_dir / filename

    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save CV file: {str(e)}"
        )

    cv_public_url = f"/cv_uploads/{job_id}/{filename}"

    try:
        application = JobApplicant(
            job_id=job_id,
            full_name=full_name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            cv_file_path=cv_public_url
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        # Notify admins in background (same list as contact inquiry)
        background_tasks.add_task(
            send_job_application_notification,
            job_id=job_id,
            job_title=job.title,
            full_name=full_name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            cv_filename=filename,
        )

        return application

    except Exception as e:

        if file_path.exists():
            file_path.unlink()

        db.rollback()
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


# @router.put("/reorder/{job_id}")
# async def reorder_job(
#     job_id: int,
#     request: ReorderJobRequest,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_admin)
# ):
#     """
#     Reorder a job (admin only)
#     """
#     job = db.query(Job).filter(
#         Job.id == job_id,
#         Job.is_deleted == False
#     ).first()
    
#     if not job:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Job not found"
#         )
    
#     # Get all siblings (all non-deleted jobs)
#     siblings = db.query(Job).filter(
#         Job.is_deleted == False,
#         Job.id != job_id
#     ).order_by(Job.order).all()
    
#     max_order = len(siblings) + 1
    
#     if request.order <= 0 or request.order > max_order:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Order must be between 1 and {max_order}"
#         )
    
#     if request.order == job.order:
#         return {"message": "Job is already at the desired order"}
    
#     try:
#         if request.order > job.order:
#             # Moving forward - decrease order of items between old and new position
#             affected_items = db.query(Job).filter(
#                 Job.is_deleted == False,
#                 Job.id != job_id,
#                 Job.order > job.order,
#                 Job.order <= request.order
#             ).order_by(Job.order).all()
            
#             for item in affected_items:
#                 item.order -= 1
#         else:
#             # Moving backward - increase order of items between new and old position
#             affected_items = db.query(Job).filter(
#                 Job.is_deleted == False,
#                 Job.id != job_id,
#                 Job.order >= request.order,
#                 Job.order < job.order
#             ).order_by(Job.order).all()
            
#             for item in affected_items:
#                 item.order += 1
        
#         job.order = request.order
        
#         db.commit()
#         return {"message": "Job reordered successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

