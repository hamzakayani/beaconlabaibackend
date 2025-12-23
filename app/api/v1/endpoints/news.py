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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    # Create news first
    news = News(
        title=title,
        content=content,
        hyperlink=hyperlink,
        publish_date=publish_date,
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    
    # Upload image
    news_id = news.id
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only images are allowed"
        )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"news_{news_id}_{timestamp}{file_ext}"
    file_path = settings.IMAGES_UPLOAD_DIR / filename
    
    try:
        contents = await file.read()
        
        if len(contents) > settings.IMAGE_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File is too large to upload."
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Update news image_url
        news.image_url = str(file_path)
        news.updated_at = datetime.now(timezone.utc)
        db.add(news)
        db.commit()
        db.refresh(news)
        
        return {"message": "News created successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/update_news/{news_id}")
async def update_news(
    news_id: int,
    news_data: NewsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="News not found"
            )
    
    if news_data.title:
        news.title = news_data.title
    if news_data.content:
        news.content = news_data.content
    if news_data.hyperlink:
        news.hyperlink = news_data.hyperlink
    if news_data.publish_date:
        news.publish_date = news_data.publish_date
    db.commit()
    db.refresh(news)
    return {"message": "News updated successfully"}

@router.delete("/delete_news/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="News not found"
            )
    if news.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="News already deleted"
            )
    news.is_deleted = True
    db.commit()
    db.refresh(news)
    return {"message": "News deleted successfully"}

@router.get("/get_news/{news_id}")
async def get_news(
    news_id: int,
    db: Session = Depends(get_db)
):
    news = db.query(News).filter(News.id == news_id).first()
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

