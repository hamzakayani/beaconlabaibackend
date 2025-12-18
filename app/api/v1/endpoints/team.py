from datetime import datetime, timezone
from typing import Optional
from math import ceil
from pathlib import Path
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.models.team import TeamMember
from app.schemas.team import (
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,

)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.core.config import settings

router = APIRouter()



@router.post("/add_team_member")
async def add_team_member(
    team_member_data: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)

):
    """
    Add a new team member
    """
    team_member = TeamMember(
        name=team_member_data.name,
        category=team_member_data.category.value,
        role=team_member_data.role,
        designation=team_member_data.designation,
        description=team_member_data.description,
        image_url=team_member_data.image_url,
        hyperlink=team_member_data.hyperlink
    )   

    db.add(team_member)
    db.commit()
    db.refresh(team_member)

    return {
        "message": "Team member added successfully"
    }

@router.put("/{team_member_id}/update")
async def update_team_member(
    team_member_id: int,
    team_member_data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a team member by ID
    """

    team_member = db.query(TeamMember).filter(
        TeamMember.id == team_member_id,
        TeamMember.is_deleted == False
        ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="Team member not found"
        )

    if team_member.name != team_member_data.name:
        team_member.name = team_member_data.name
    if team_member.category != team_member_data.category:
        team_member.category = team_member_data.category
    if team_member.role != team_member_data.role:
        team_member.role = team_member_data.role
    if team_member.designation != team_member_data.designation:
        team_member.designation = team_member_data.designation
    if team_member.description != team_member_data.description:
        team_member.description = team_member_data.description
    if team_member.image_url != team_member_data.image_url:
        team_member.image_url = team_member_data.image_url
    if team_member.hyperlink != team_member_data.hyperlink:
        team_member.hyperlink = team_member_data.hyperlink
    team_member.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(team_member)
    return team_member

@router.get("/{team_member_id}/get", response_model=TeamMemberResponse)
async def get_team_member(
    team_member_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a team member by ID
    """
    team_member = db.query(TeamMember).filter(
        TeamMember.id == team_member_id,
        TeamMember.is_deleted == False
        ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="Team member not found"
        )
    return team_member

@router.get("/list_team_members", response_model=PaginatedResponse[TeamMemberResponse])
async def list_team_members(
    page: int = Query(1, description="Number of items to skip"),
    size: int = Query(10, description="Max number of items to return"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    List all team members with pagination
    """
    query = db.query(TeamMember).filter(
        TeamMember.is_deleted == False
        )
    
    if search:
        query = query.filter(
            TeamMember.name.ilike(f"%{search}%")
        )
    
    # Order by created_at descending
    query = query.order_by(TeamMember.created_at.desc())
    
    # Get total count before pagination
    total_items = query.count()
    total_pages = ceil(total_items / size)
    
    # Apply pagination
    items = query.offset((page - 1) * size).limit(size).all()

    page_info = PageInfo(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    return PaginatedResponse(items=items, page_info=page_info)

@router.delete("/{team_member_id}/delete")
async def delete_team_member(
    team_member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Delete a team member by ID
    """
    team_member = db.query(TeamMember).filter(
        TeamMember.id == team_member_id,
        TeamMember.is_deleted == False
        ).first()
    if not team_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="Team member not found"
        )
    team_member.is_deleted = True
    team_member.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(team_member)
    return {
        "message": "Team member deleted successfully"
    }


@router.post("/{team_member_id}/upload_image")
async def upload_image(
    team_member_id: int,
    file: UploadFile = File(...),
    old_image_path: str | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Upload an image for a team member (Admin only)
    """
    team_member = db.query(TeamMember).filter(
        and_(
            TeamMember.id == team_member_id,
            TeamMember.is_deleted == False
        )
    ).first()
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only images are allowed"
        )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"team_member_{team_member_id}_{timestamp}{file_ext}"
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
        
        # Delete old image if provided
        if old_image_path:
            old_file = Path(old_image_path)
            if old_file.exists():
                try:
                    old_file.unlink()
                except Exception:
                    pass
        
        # Update team member image_url
        team_member.image_url = str(file_path)
        team_member.updated_at = datetime.now(timezone.utc)
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        
        return {
            "message": "Image uploaded successfully",
            "image_url": str(file_path)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{team_member_id}/delete_image")
async def delete_image(
    team_member_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Delete an image from a team member (Admin only)
    """
    team_member = db.query(TeamMember).filter(
        and_(
            TeamMember.id == team_member_id,
            TeamMember.is_deleted == False
        )
    ).first()
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    if not team_member.image_url:
        raise HTTPException(
            status_code=404,
            detail="No image found for this team member"
        )
    
    try:
        image_path = team_member.image_url
        file_to_delete = Path(image_path)
        
        if file_to_delete.exists():
            try:
                file_to_delete.unlink()
            except Exception as e:
                print(f"Warning: unable to delete file {image_path}: {e}")
        
        # Clear image_url in database
        team_member.image_url = ""
        team_member.updated_at = datetime.now(timezone.utc)
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        
        return {"message": "Image deleted successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

