from datetime import datetime, timezone
from typing import Optional
from math import ceil
from pathlib import Path
import os
from app.services.image_upload import upload_image
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File,Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.models.feature_publication import FeaturePublication
from app.schemas.feature_publication import (
    DOIFeaturePublicationCreate,
    ManualFeaturePublicationCreate,
    FeaturePublicationUpdate,
    FeaturePublicationResponse,
    PubmedFeaturePublicationCreate
)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_active_user
from app.models.user import User
from app.services.papers import doi_fetch, e_fetch
from app.services.reorder import reorder_item
from app.core.config import settings

router = APIRouter()


@router.post("/add/manual")
async def add_feature_publication_manual(
    publication_data: ManualFeaturePublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a new feature publication manually (Authenticated users only)
    """
    if not publication_data.doi and not publication_data.pubmed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DOI or PubMED ID is required"
        )

    try:
        feature_publication = FeaturePublication(
            title=publication_data.title,
            abstract=publication_data.abstract,
            authers=publication_data.authers,
            journal=publication_data.journal,
            publish_date=publication_data.publish_date,
            pubmed_id=publication_data.pubmed_id,
            nct_number=publication_data.nct_number,
            doi=publication_data.doi,
            is_presentation=publication_data.is_presentation,
            order=publication_data.order,
            is_open=publication_data.is_open,
            image_url=publication_data.image_url if publication_data.image_url else None,
        )

        db.add(feature_publication)
        db.commit()
        db.refresh(feature_publication)

        return {
            "message": "Feature publication added successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add feature publication: {str(e)}"
        )


@router.post("/add/doi")
async def add_feature_publication_by_doi(
    paper: DOIFeaturePublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a feature publication by DOI (Auto upload - Authenticated users only)
    """
    try:
        res = doi_fetch(paper.doi)
        if res[2] == "None Information":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No information found for given DOI."
            )
        if res[2] == 'DOI Service Error 404':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOI. Please try again with a valid DOI."
            )
        if res[2] != "OK":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res[2]
            )
        
        comma_separated_authors = res[0]['authors'].replace(';', ',')
        publish_date2 = res[0]['pub_date']
        
        # Create new feature publication entry
        db_publication = FeaturePublication(
            nct_number=paper.nct_number,
            title=res[0]['title'],
            abstract=res[0]['abstract'],
            publish_date=publish_date2,
            authers=comma_separated_authors,
            journal=res[0]['journal'],
            doi=paper.doi,
            is_presentation=paper.is_presentation,
            order=paper.order,
            is_open=paper.is_open,
            image_url=paper.image_url if paper.image_url else None,
        )

        db.add(db_publication)
        db.commit()
        db.refresh(db_publication)

        return {
            "message": "Feature publication has been successfully added to the system.",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/add/pubmed")
async def add_feature_publication_by_pubmed_id(
    paper: PubmedFeaturePublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a feature publication by PubMed ID (Auto upload - Authenticated users only)
    """
    try:
        result = e_fetch([paper.pm_id])
        if result == None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No information found for given PubMED ID."
            )
        
        paper_data = result['result'][result['result']['uids'][0]]
        publish_date2 = paper_data['date_pub']
        authers2 = ", ".join(author['name'] for author in paper_data['authors'])
        
        # Create new feature publication entry
        db_publication = FeaturePublication(
            nct_number=paper.nct_number,
            title=paper_data['title'],
            abstract=paper_data['abstract'],
            publish_date=publish_date2,
            authers=authers2,
            pubmed_id=paper.pm_id,
            is_presentation=paper.is_presentation,
            order=paper.order,
            is_open=paper.is_open,
            image_url=paper.image_url if paper.image_url else None,
        )

        db.add(db_publication)
        db.commit()
        db.refresh(db_publication)

        return {
            "message": "Feature publication has been successfully added to the system.",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/list", response_model=PaginatedResponse[FeaturePublicationResponse])
async def list_feature_publications(
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Max number of items to return"),
    search: Optional[str] = Query(None, description="Search by title"),
    db: Session = Depends(get_db)
):
    """
    List all feature publications with pagination (Public endpoint)
    """
    try:
        # Build query with soft delete filter
        query = db.query(FeaturePublication).filter(
            FeaturePublication.is_deleted == False
        )
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                FeaturePublication.title.ilike(f"%{search}%")
            )
        
        # Order by order field
        query = query.order_by(FeaturePublication.order)
        
        # Get total count
        total_items = query.count()
        
        # Calculate total pages
        total_pages = ceil(total_items / size) if total_items > 0 else 0
        
        # Apply pagination
        publications = query.offset((page - 1) * size).limit(size).all()
        
        # Create page info
        page_info = PageInfo(
            total=total_items,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return PaginatedResponse(
            items=publications,
            page_info=page_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feature publications: {str(e)}"
        )


@router.get("/{publication_id}/get", response_model=FeaturePublicationResponse)
async def get_feature_publication(
    publication_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a feature publication by ID (Public endpoint)
    """
    publication = db.query(FeaturePublication).filter(
        FeaturePublication.id == publication_id,
        FeaturePublication.is_deleted == False
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature publication not found"
        )
    
    return publication


@router.put("/{publication_id}/update")
async def update_feature_publication(
    publication_id: int,
    publication_data: FeaturePublicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a feature publication by ID (Authenticated users only)
    """
    publication = db.query(FeaturePublication).filter(
        FeaturePublication.id == publication_id,
        FeaturePublication.is_deleted == False
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature publication not found"
        )

    # Check if order is being updated and needs reordering
    order_changed = False
    new_order = None
    
    if publication_data.order is not None and publication_data.order != publication.order:
        order_changed = True
        new_order = publication_data.order

    # Update fields if provided
    if publication_data.title is not None:
        publication.title = publication_data.title
    if publication_data.abstract is not None:
        publication.abstract = publication_data.abstract
    if publication_data.authers is not None:
        publication.authers = publication_data.authers
    if publication_data.journal is not None:
        publication.journal = publication_data.journal
    if publication_data.publish_date is not None:
        publication.publish_date = publication_data.publish_date
    if publication_data.pubmed_id is not None:
        publication.pubmed_id = publication_data.pubmed_id
    if publication_data.nct_number is not None:
        publication.nct_number = publication_data.nct_number
    if publication_data.is_presentation is not None:
        publication.is_presentation = publication_data.is_presentation
    if publication_data.doi is not None:
        publication.doi = publication_data.doi
    if publication_data.is_open is not None:
        publication.is_open = publication_data.is_open
    if publication_data.image_url is not None:
        publication.image_url = publication_data.image_url
    # Note: order is handled by reorder_item service below

    # If order changed, perform reordering
    if order_changed:
        try:
            reorder_item(db, FeaturePublication, publication_id, new_order)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to reorder: {str(e)}"
            )
    
    publication.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(publication)
    
    return {
        "message": "Feature publication updated successfully"
    }


@router.delete("/{publication_id}/delete")
async def delete_feature_publication(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a feature publication by ID (Soft delete - Authenticated users only)
    """
    publication = db.query(FeaturePublication).filter(
        FeaturePublication.id == publication_id,
        FeaturePublication.is_deleted == False
    ).first()
    
    if not publication:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature publication not found"
        )
    
    publication.is_deleted = True
    publication.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(publication)
    
    return {
        "message": "Feature publication deleted successfully"
    }


@router.delete("/{publication_id}/delete_image")
async def delete_image(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an image from a feature publication (Authenticated users only)
    """
    publication = db.query(FeaturePublication).filter(
        and_(
            FeaturePublication.id == publication_id,
            FeaturePublication.is_deleted == False
        )
    ).first()
    
    if not publication:
        raise HTTPException(status_code=404, detail="Feature publication not found")
    
    if not publication.image_url:
        raise HTTPException(
            status_code=404,
            detail="No image found for this feature publication"
        )
    
    try:
        image_path = publication.image_url
        file_to_delete = Path(image_path)
        
        if file_to_delete.exists():
            try:
                file_to_delete.unlink()
            except Exception as e:
                print(f"Warning: unable to delete file {image_path}: {e}")
        
        # Clear image_url in database
        publication.image_url = ""
        publication.updated_at = datetime.now(timezone.utc)
        db.add(publication)
        db.commit()
        db.refresh(publication)
        
        return {"message": "Image deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
