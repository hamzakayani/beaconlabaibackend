from datetime import datetime, timezone
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.models.contact import ContactInquiry
from app.models.contact_enums import ContactSubjectEnum
from app.schemas.contact import (
    ContactFormCreate,
    ContactInquiryResponse,
    ContactInquiryUpdate,
    ContactInquiryListResponse,
    ContactInfoResponse,
)
from app.schemas.pagination import PaginationParams, PageInfo
from app.services.auth import get_current_admin
from app.services.email import send_contact_inquiry_notification
from app.core.config import settings
from app.core.logging_config import setup_logging

logger = setup_logging()
router = APIRouter()

@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    contact_data: ContactFormCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a new contact inquiry (Public endpoint)
    Sends email notification to admin if ADMIN_NOTIFICATION_EMAIL is configured.
    """
    try:
        # Create new contact inquiry
        contact_inquiry = ContactInquiry(
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            email=contact_data.email,
            phone_number=contact_data.phone_number,
            subject=contact_data.subject,
            message=contact_data.message
        )
        
        db.add(contact_inquiry)
        db.commit()
        db.refresh(contact_inquiry)
        
        # Send email notification to admin in background (non-blocking)
        # Convert None values to placeholder strings to avoid "None" in email
        background_tasks.add_task(
            send_contact_inquiry_notification,
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            email=contact_data.email or "Not provided",
            phone_number=contact_data.phone_number or "Not provided",
            subject=contact_data.subject.value,
            message=contact_data.message or "No message provided"
        )
        
        return {
            "message": "Your inquiry has been submitted successfully. We will get back to you soon.",
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting contact form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit inquiry. Please try again later."
        )

@router.get("/info", response_model=ContactInfoResponse)
async def get_contact_info():
    """
    Get contact information (Public endpoint)
    """
    return ContactInfoResponse(
        email=settings.CONTACT_EMAIL,
        address=settings.CONTACT_ADDRESS
    )

@router.get("/inquiries", response_model=ContactInquiryListResponse)
async def get_all_inquiries(
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Max number of items to return"),
    subject: Optional[ContactSubjectEnum] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Get all contact inquiries with pagination (Admin only)
    """
    try:
        # Build query with soft delete filter
        query = db.query(ContactInquiry).filter(ContactInquiry.is_deleted == False)
        
        # Apply subject filter if provided
        if subject:
            query = query.filter(ContactInquiry.subject == subject)
        
        # Order by created_at descending
        query = query.order_by(ContactInquiry.created_at.desc())
        
        # Get total count
        total_items = query.count()
        
        # Calculate total pages
        total_pages = ceil(total_items / size)
        
        # Apply pagination
        inquiries = query.offset((page - 1) * size).limit(size).all()
        
        # Convert to response models
        items = [ContactInquiryResponse.model_validate(inquiry) for inquiry in inquiries]
        
        # Create page info
        page_info = PageInfo(
            total=total_items,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return ContactInquiryListResponse(
            items=items,
            page_info=page_info
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error fetching inquiries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch inquiries"
        )

@router.get("/inquiries/{inquiry_id}", response_model=ContactInquiryResponse)
async def get_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Get a single contact inquiry by ID (Admin only)
    """
    inquiry = db.query(ContactInquiry).filter(
        and_(
            ContactInquiry.id == inquiry_id,
            ContactInquiry.is_deleted == False
        )
    ).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    return ContactInquiryResponse.model_validate(inquiry)

@router.put("/inquiries/{inquiry_id}")
async def update_inquiry(
    inquiry_id: int,
    inquiry_data: ContactInquiryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a contact inquiry (Admin only)
    """
    inquiry = db.query(ContactInquiry).filter(
            ContactInquiry.id == inquiry_id,
            ContactInquiry.is_deleted == False
            ).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    try:
        # Update only provided fields
        update_data = inquiry_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inquiry, field, value)
        
        inquiry.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(inquiry)
        
        return {
            "message": "The inquiry has been successfully updated."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating inquiry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update inquiry"
        )

@router.delete("/inquiries/{inquiry_id}")
async def delete_inquiry(
    inquiry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Soft delete a contact inquiry (Admin only)
    """
    inquiry = db.query(ContactInquiry).filter(
            ContactInquiry.id == inquiry_id,
            ContactInquiry.is_deleted == False
    ).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    try:
        # Soft delete
        inquiry.is_deleted = True
        inquiry.deleted_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "message": "The inquiry has been successfully deleted."
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting inquiry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete inquiry"
        )

