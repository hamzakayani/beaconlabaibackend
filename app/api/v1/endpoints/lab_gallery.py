from datetime import datetime, timezone
from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.lab_gallery import LabGallery
from app.schemas.lab_gallery import LabGalleryCreate, LabGalleryUpdate, LabGalleryResponse
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin


router = APIRouter()


@router.post("/add")
async def add_lab_gallery(
    lab_gallery_data: LabGalleryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """
    Add a new lab gallery item (admin only).
    """
    if lab_gallery_data.order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0",
        )

    lab_gallery = LabGallery(
        title=lab_gallery_data.title,
        content=lab_gallery_data.content,
        image_url=lab_gallery_data.image_url if lab_gallery_data.image_url else None,
        order=lab_gallery_data.order,
    )

    db.add(lab_gallery)
    db.commit()
    db.refresh(lab_gallery)

    return {"message": "Lab gallery added successfully"}


@router.put("/{lab_gallery_id}/update")
async def update_lab_gallery(
    lab_gallery_id: int,
    lab_gallery_data: LabGalleryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """
    Update a lab gallery item by ID (admin only).
    """
    lab_gallery = db.query(LabGallery).filter(
        LabGallery.id == lab_gallery_id,
        LabGallery.is_deleted == False,
    ).first()

    if not lab_gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab gallery not found",
        )

    if lab_gallery_data.order is not None and lab_gallery_data.order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0",
        )

    if lab_gallery_data.title is not None:
        lab_gallery.title = lab_gallery_data.title
    if lab_gallery_data.content is not None:
        lab_gallery.content = lab_gallery_data.content
    if lab_gallery_data.image_url is not None:
        lab_gallery.image_url = lab_gallery_data.image_url
    if lab_gallery_data.order is not None:
        lab_gallery.order = lab_gallery_data.order

    lab_gallery.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lab_gallery)

    return {"message": "Lab gallery updated successfully"}


@router.get("/list", response_model=PaginatedResponse[LabGalleryResponse])
async def list_lab_gallery(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search by title or content"),
    db: Session = Depends(get_db),
):
    """
    List all lab gallery items with pagination (public endpoint).
    Returns only items with is_deleted=False.
    """
    query = db.query(LabGallery).filter(LabGallery.is_deleted == False)

    if search:
        query = query.filter(
            LabGallery.title.ilike(f"%{search}%") | LabGallery.content.ilike(f"%{search}%")
        )

    total_items = query.count()
    total_pages = ceil(total_items / size) if total_items > 0 else 0

    items = (
        query.order_by(LabGallery.order.asc(), LabGallery.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    page_info = PageInfo(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    return PaginatedResponse(items=items, page_info=page_info)


@router.delete("/{lab_gallery_id}/delete")
async def delete_lab_gallery(
    lab_gallery_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """
    Soft delete a lab gallery item by ID (admin only).
    """
    lab_gallery = db.query(LabGallery).filter(
        LabGallery.id == lab_gallery_id,
        LabGallery.is_deleted == False,
    ).first()

    if not lab_gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab gallery not found",
        )

    lab_gallery.is_deleted = True
    lab_gallery.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lab_gallery)

    return {"message": "Lab gallery deleted successfully"}

