
from math import ceil
from app.models.papers import Paper
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.schemas.papers import DOIPaperCreate, PaperResponse, PubmedPaperCreate
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.auth import get_current_active_user
from app.models.user import User

from app.services.papers import doi_fetch, e_fetch

router = APIRouter()

@router.post("/add/doi/{project_id}")
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
        # Create new paper entry
        db_paper = Paper(
            paper_id=paper.doi,
            nct_number = paper.nct_number,
            title = res[0]['title'],
            abstract = res[0]['abstract'],
            publish_date = publish_date2,
            authers = comma_separated_authors,
            journal = res[0]['journal']
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

@router.post("/add/pubmed/{project_id}")
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
        # Create new paper entry
        db_paper = Paper(
            paper_id=paper.pm_id,
            nct_number = paper.nct_number,
            title = result['result'][result['result']['uids'][0]]['title'],
            abstract = result['result'][result['result']['uids'][0]]['abstract'],
            publish_date = publish_date2,
            authers = authers2
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

@router.get("/list_all_papers", response_model=PaginatedResponse[PaperResponse])
async def list_all_papers(
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Max number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all papers with pagination
    """
    try:
        # Build query with soft delete filter
        query = db.query(Paper).filter(Paper.is_deleted == False)
        
        # Order by created_at descending
        query = query.order_by(Paper.created_at.desc())
        
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
