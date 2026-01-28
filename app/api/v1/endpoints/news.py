from datetime import datetime, timezone
from typing import Optional
from math import ceil
from app.models.news import News
from app.schemas.news import NewsResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from app.db.database import get_db  
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.services.reorder import reorder_item


router = APIRouter()

@router.post("/create_news")
async def create_news(
    title: str = Form(...),
    content: str = Form(...),
    hyperlink: str | None = Form(None),
    publish_date: datetime = Form(...),
    image_url: Optional[str] = Form(None),
    order: int = Form(1),
    is_open: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Create a new news item with optional image upload
    """
    if order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0"
        )
    news = News(
        title=title,
        content=content,
        hyperlink=hyperlink,
        publish_date=publish_date,
        image_url=image_url if image_url else None,
        order=order,
        is_open=is_open
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
    image_url: Optional[str] = Form(None),
    is_open: Optional[bool] = Form(None),
    order: Optional[int] = Form(None),
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
    if order is not None and order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0"
        )

    # Check if order is being updated and needs reordering
    order_changed = False
    new_order = None
    
    if order is not None and order != news.order:
        order_changed = True
        new_order = order

    # Update fields if provided
    if title is not None:
        news.title = title
    if content is not None:
        news.content = content
    if hyperlink is not None:
        news.hyperlink = hyperlink
    if publish_date is not None:
        news.publish_date = publish_date
    if image_url is not None:
        news.image_url = image_url
    if is_open is not None:
        news.is_open = is_open

    # If order changed, perform reordering
    if order_changed:
        try:
            reorder_item(db, News, news_id, new_order)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to reorder: {str(e)}"
            )
    
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
    search: Optional[str] = Query(None, description="Search by title or content"),
    db: Session = Depends(get_db)
):
    """
    List all news items (public endpoint).
    Returns only news with is_deleted=False.
    """
    query = db.query(News).filter(News.is_deleted == False)
    if search:
        query = query.filter(News.title.ilike(f"%{search}%") | News.content.ilike(f"%{search}%"))
    
    # Get total count
    total_items = query.count()
    total_pages = ceil(total_items / size)
    
    # Apply pagination
    items = query.order_by(News.order).offset((page - 1) * size).limit(size).all()
    
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

