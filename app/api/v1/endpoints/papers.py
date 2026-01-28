
from typing import List
from math import ceil
from typing import Optional
from app.models.papers import Paper
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.schemas.papers import Category, DOIPaperCreate, ManualPaperCreate, PaperResponse, PaperUpdate, PubmedPaperCreate, ReorderPaperRequest
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.db.database import get_db
from app.services.auth import get_current_active_user
from app.models.user import User
from app.services.reorder import reorder_item

from app.services.papers import doi_fetch, e_fetch

router = APIRouter()

@router.post("/add/doi")
async def add_paper_by_doi(
    paper: DOIPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    
    try:
        res = doi_fetch(paper.doi)
        if res[2]=="None Information":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No information found for given DOI."
            )
        if res[2] == 'DOI Service Error 404':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOI. Please try again with a valid DOI."
            )
        if res[2]!="OK":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res[2]
            )
        comma_separated_authors = res[0]['authors'].replace(';', ',')
        publish_date2 = res[0]['pub_date']
        if paper.order < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be greater than 0"
            )
        # Create new paper entry
        db_paper = Paper(
            doi=paper.doi,
            nct_number = paper.nct_number,
            title = res[0]['title'],
            abstract = res[0]['abstract'],
            publish_date = publish_date2,
            authers = comma_separated_authors,
            journal = res[0]['journal'],
            category = [cat.value for cat in paper.category] if paper.category else [],
            is_presentation = paper.is_presentation,
            order = paper.order,
            is_open=paper.is_open

        )

        db.add(db_paper)
        db.commit()

        return {"message": "The paper has been successfully added to the system."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )

@router.post("/add/pubmed")
async def add_paper_by_pubmed_id(
    paper: PubmedPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    
    try:
        result = e_fetch([paper.pm_id])
        if result == None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No information found for given PubMED ID."
            )
        publish_date2 = result['result'][result['result']['uids'][0]]['date_pub']
        authers2 = ", ".join(author['name'] for author in result['result'][result['result']['uids'][0]]['authors'])
        if paper.order < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be greater than 0"
            )
        # Create new paper entry
        db_paper = Paper(
            pubmed_id=paper.pm_id,
            nct_number = paper.nct_number,
            title = result['result'][result['result']['uids'][0]]['title'],
            abstract = result['result'][result['result']['uids'][0]]['abstract'],
            publish_date = publish_date2,
            authers = authers2,
            category = [cat.value for cat in paper.category] if paper.category else [],
            is_presentation = paper.is_presentation,
            order = paper.order,
            is_open=paper.is_open
        )

        db.add(db_paper)
        db.commit()

        return {"message": "The paper has been successfully added to the system."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/add/manual")
async def add_paper_manual(
    paper_data: ManualPaperCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a new paper manually (Authenticated users only)
    """

    if not paper_data.doi and not paper_data.pubmed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DOI or PubMED ID is required"
        )
    if paper_data.order < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must be greater than 0"
        )
    try:
        db_paper = Paper(
            title=paper_data.title,
            abstract=paper_data.abstract,
            authers=paper_data.authers,
            journal=paper_data.journal,
            publish_date=paper_data.publish_date,
            pubmed_id=paper_data.pubmed_id,
            nct_number=paper_data.nct_number,
            doi=paper_data.doi,
            category=[cat.value for cat in paper_data.category] if paper_data.category else [],
            is_presentation=paper_data.is_presentation,
            order=paper_data.order,
            is_open=paper_data.is_open
        )

        db.add(db_paper)
        db.commit()
        db.refresh(db_paper)

        return {
            "message": "The paper has been successfully added to the system.",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add paper: {str(e)}"
        )

@router.put("/update/paper/{paper_id}")
async def update_paper(
    paper_id: int,
    paper_data: PaperUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Paper not found"
                )
        
        # Check if order is being updated and needs reordering
        order_changed = False
        new_order = None
        
        if paper_data.order is not None and paper_data.order < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must be greater than 0"
            )
        
        if paper_data.order is not None and paper_data.order != paper.order:
            order_changed = True
            new_order = paper_data.order
        
        if paper_data.title is not None:
            paper.title = paper_data.title
        if paper_data.abstract is not None:
            paper.abstract = paper_data.abstract
        if paper_data.authers is not None:
            paper.authers = paper_data.authers
        if paper_data.journal is not None:
            paper.journal = paper_data.journal
        if paper_data.publish_date is not None:
            paper.publish_date = paper_data.publish_date
        if paper_data.pubmed_id is not None:
            paper.pubmed_id = paper_data.pubmed_id
        if paper_data.nct_number is not None:
            paper.nct_number = paper_data.nct_number
        if paper_data.doi is not None:
            paper.doi = paper_data.doi
        if paper_data.category is not None:
            paper.category = [cat.value for cat in paper_data.category] 
        if paper_data.is_presentation is not None:
            paper.is_presentation = paper_data.is_presentation
        if paper_data.is_open is not None:
            paper.is_open = paper_data.is_open
        # Note: order is handled by reorder_item service below

        # If order changed, perform reordering
        if order_changed:
            try:
                reorder_item(db, Paper, paper_id, new_order)
            except HTTPException:
                raise
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to reorder: {str(e)}"
                )
        
        db.commit()
        return {"message": "The paper has been successfully updated."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to update paper: {str(e)}")


@router.get("/list_all_papers", response_model=PaginatedResponse[PaperResponse])
async def list_all_papers(
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Max number of items to return"),
    category: Optional[Category] = Query(None, description="Search by category"),
    search: Optional[str] = Query(None, description="Search by title or abstract"),
    db: Session = Depends(get_db),
):
    """
    Get all papers with pagination
    """
    try:
        # Build query with soft delete filter
        query = db.query(Paper).filter(Paper.is_deleted == False)
        
        # Apply search filter if provided
        if search:
            query = query.filter(
                or_(
                    Paper.title.ilike(f"%{search}%"),
                    Paper.abstract.ilike(f"%{search}%")
                )
            )

        if category:
            query = query.filter(
                func.JSON_CONTAINS(Paper.category, f'"{category.value}"')
            )
        

        # Order by order field
        query = query.order_by(Paper.order)
        
        # Get total count
        total_items = query.count()
        
        # Calculate total pages
        total_pages = ceil(total_items / size)
        
        # Apply pagination
        papers = query.offset((page - 1) * size).limit(size).all()
        
        # Convert to response models
        items = [PaperResponse.model_validate(paper) for paper in papers]
        
        # Create page info
        page_info = PageInfo(
            total=total_items,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return PaginatedResponse[PaperResponse](
            items=items,
            page_info=page_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch papers: {str(e)}"
        )
         
@router.delete("/delete/paper/{paper_id}")
async def delete_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
        paper.is_deleted = True
        db.commit()
        return {"message": "The paper has been successfully deleted from the system."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

