from datetime import datetime, timezone
from typing import Optional
from math import ceil
from pathlib import Path
import os
from app.services.file_upload import save_image
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.models.team import TeamMember
from app.schemas.team import (
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamCategory,
)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.core.config import settings

router = APIRouter()


@router.post("/add_team_member")
async def add_team_member(
    name: str = Form(..., min_length=1, max_length=50),
    category: str = Form(...),
    role: str = Form(..., min_length=1, max_length=50),
    designation: str = Form(..., min_length=1, max_length=50),
    description: Optional[str] = Form(None, min_length=1),
    hyperlink: Optional[str] = Form(None, max_length=255),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Add a new team member with optional image upload
    """
    # Validate category
    try:
        team_category = TeamCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {[c.value for c in TeamCategory]}"
        )
    
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
        
        # Create team member first to get the ID for filename
        team_member = TeamMember(
            name=name,
            category=team_category.value,
            role=role,
            designation=designation,
            description=description or "",
            image_url="",  # Will be updated after file upload
            hyperlink=hyperlink or ""
        )
        
        db.add(team_member)
        db.commit()
        db.refresh(team_member)
        
        # Now create filename with team_member_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"team_member_{team_member.id}_{timestamp}{file_ext}"
        file_path = settings.IMAGES_UPLOAD_DIR / filename
        
        try:
            contents = await file.read()
            
            if len(contents) > settings.IMAGE_MAX_FILE_SIZE:
                db.delete(team_member)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File is too large to upload."
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Update team member with image_url
            image_url = f"/images/{filename}"
            team_member.image_url = image_url
            team_member.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(team_member)
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up: delete team member if file upload fails
            if team_member:
                db.delete(team_member)
                db.commit()
            if file_path and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image: {str(e)}"
            )
    else:
        # No image provided, create team member without image
        team_member = TeamMember(
            name=name,
            category=team_category.value,
            role=role,
            designation=designation,
            description=description or "",
            image_url="",
            hyperlink=hyperlink or ""
        )
        
        db.add(team_member)
        db.commit()
        db.refresh(team_member)

    return {
        "message": "Team member added successfully",
    }

@router.put("/{team_member_id}/update")
async def update_team_member(
    team_member_id: int,
    name: Optional[str] = Form(None, max_length=50),
    category: Optional[str] = Form(None),
    role: Optional[str] = Form(None, max_length=50),
    designation: Optional[str] = Form(None, max_length=50),
    description: Optional[str] = Form(None),
    hyperlink: Optional[str] = Form(None, max_length=255),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Update a team member by ID with optional image upload.
    To remove a field, send an empty string for that field.
    Note: Team category cannot be set to None or empty - it must be a valid category value.
    """
    team_member = db.query(TeamMember).filter(
        TeamMember.id == team_member_id,
        TeamMember.is_deleted == False
    ).first()
    if not team_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found"
        )
    
    # if name is not None and name == "":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Team name is required"
    #     )

    # if role is not None and role == "":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Team role is required"
    #     )

    # if designation is not None and designation == "":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Team designation is required"
    #     )

    # if category is not None and category == "":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Team category is required"
    #     )


    team_category = None
    if category is not None:
        try:
            team_category = TeamCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {[c.value for c in TeamCategory]}"
            )

    if file:
        old_image_path = None
        if team_member.image_url:
            filename = team_member.image_url.replace("/images/", "")
            old_image_path = settings.IMAGES_UPLOAD_DIR / filename
        image_url = await save_image(path_prefix="team_member", file=file, old_image_path=old_image_path)
        team_member.image_url = image_url

    if name is not None:
        team_member.name = name
    elif not name:
        team_member.name = ""

    if category is not None:
        team_member.category = team_category.value
    elif not category:
        team_member.category = ""

    if role is not None:
        team_member.role = role
    elif not role:
        team_member.role = ""

    if designation is not None:
        team_member.designation = designation
    elif not designation:
        team_member.designation = ""

    if description is not None:
        team_member.description = description
    elif not description:
        team_member.description = ""
    
    if hyperlink is not None:
        team_member.hyperlink = hyperlink
    elif not hyperlink:
        team_member.hyperlink = ""
    
    team_member.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(team_member)
    
    return {
        "message": "Team member updated successfully",
    }

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

