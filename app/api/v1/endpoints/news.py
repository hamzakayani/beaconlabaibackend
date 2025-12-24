from datetime import datetime, timezone
from typing import Optional
from math import ceil
from pathlib import Path
import os
from app.models.news import News
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from sqlalchemy import and_
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.core.config import settings


router = APIRouter()

@router.post("/create_news")
async def create_news(
    title: str = Form(...),
    content: str = Form(...),
    hyperlink: str | None = Form(None),
    publish_date: datetime = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Create a new news item with optional image upload
    """
    image_url = ""
    file_path = None
    
    # Handle image upload if provided
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only images are allowed"
            )
        
        # Create news first to get the ID for filename
        news = News(
            title=title,
            content=content,
            hyperlink=hyperlink,
            publish_date=publish_date,
            image_url="",  # Will be updated after file upload
        )
        
        db.add(news)
        db.commit()
        db.refresh(news)
        
        # Now create filename with news_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_{news.id}_{timestamp}{file_ext}"
        file_path = settings.IMAGES_UPLOAD_DIR / filename
        
        try:
            contents = await file.read()
            
            if len(contents) > settings.IMAGE_MAX_FILE_SIZE:
                db.delete(news)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File is too large to upload."
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Update news with image_url
            image_url = str(file_path)
            news.image_url = image_url
            news.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(news)
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up: delete news if file upload fails
            if news:
                db.delete(news)
                db.commit()
            if file_path and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image: {str(e)}"
            )
    else:
        # No image provided, create news without image
        news = News(
            title=title,
            content=content,
            hyperlink=hyperlink,
            publish_date=publish_date,
            image_url="",
        )
        
        db.add(news)
        db.commit()
        db.refresh(news)

    return {"message": "News created successfully"}

@router.put("/update_news/{news_id}")
async def update_news(
    news_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    hyperlink: Optional[str] = Form(None),
    publish_date: Optional[datetime] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a news item by ID with optional image upload
    """
    news = db.query(News).filter(
        News.id == news_id,
        News.is_deleted == False
    ).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="News not found"
        )

    old_image_path = None
    file_path = None
    
    # Handle image upload if provided
    # If no file is provided, skip image handling and preserve existing image_url
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only images are allowed"
            )
        
        # Store old image path for deletion
        if news.image_url:
            old_image_path = Path(news.image_url)
        
        # Create filename with news_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_{news.id}_{timestamp}{file_ext}"
        file_path = settings.IMAGES_UPLOAD_DIR / filename
        
        try:
            contents = await file.read()
            
            if len(contents) > settings.IMAGE_MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File is too large to upload."
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Update news with new image_url
            news.image_url = str(file_path)
            
            # Delete old image if it exists
            if old_image_path and old_image_path.exists():
                try:
                    old_image_path.unlink()
                except Exception as e:
                    # Log but don't fail if old image deletion fails
                    pass
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up: delete new file if update fails
            if file_path and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image: {str(e)}"
            )

    # Update fields if provided
    if title is not None:
        news.title = title
    if content is not None:
        news.content = content
    if hyperlink is not None:
        news.hyperlink = hyperlink
    if publish_date is not None:
        news.publish_date = publish_date
    
    news.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(news)
    
    return {"message": "News updated successfully"}

@router.delete("/delete_news/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    news = db.query(News).filter(
        News.id == news_id,
        News.is_deleted == False
    ).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="News not found"
        )
    news.is_deleted = True
    news.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(news)
    return {"message": "News deleted successfully"}

@router.get("/get_news/{news_id}")
async def get_news(
    news_id: int,
    db: Session = Depends(get_db)
):
    news = db.query(News).filter(
        News.id == news_id,
        News.is_deleted == False
    ).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="News not found"
        )
    return news

@router.get("/get_all_news",response_model=PaginatedResponse[NewsResponse])
async def get_all_news(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """
    List all news items (public endpoint).
    Returns only news with is_deleted=False.
    """
    query = db.query(News).filter(News.is_deleted == False)
    
    # Get total count
    total_items = query.count()
    total_pages = ceil(total_items / size)
    
    # Apply pagination
    items = query.order_by(News.publish_date.desc()).offset((page - 1) * size).limit(size).all()
    
    page_info = PageInfo(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return PaginatedResponse(
        items=items, 
        page_info=page_info
        )

