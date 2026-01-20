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
    TeamMemberResponse,
    TeamCategory,
    ReorderTeamMemberRequest,
)
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_admin
from app.services.reorder import reorder_item
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
    order: int = Form(1),
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
            hyperlink=hyperlink or "",
            order=order
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
            hyperlink=hyperlink or "",
            order=order
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
    order: Optional[int] = Form(None),
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

    # Check if order is being updated and needs reordering
    order_changed = False
    new_order = None
    
    if order is not None and order != team_member.order:
        order_changed = True
        new_order = order

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
    # Note: order is handled by reorder_item service below

    # If order changed, perform reordering
    if order_changed:
        try:
            reorder_item(db, TeamMember, team_member_id, new_order)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to reorder: {str(e)}"
            )
    
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
    
    # Order by order field
    query = query.order_by(TeamMember.order)
    
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


# @router.put("/reorder/{team_member_id}")
# async def reorder_team_member(
#     team_member_id: int,
#     request: ReorderTeamMemberRequest,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_admin)
# ):
#     """
#     Reorder a team member (admin only)
#     """
#     team_member = db.query(TeamMember).filter(
#         TeamMember.id == team_member_id,
#         TeamMember.is_deleted == False
#     ).first()
    
#     if not team_member:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Team member not found"
#         )
    
#     # Get all siblings (all non-deleted team members)
#     siblings = db.query(TeamMember).filter(
#         TeamMember.is_deleted == False,
#         TeamMember.id != team_member_id
#     ).order_by(TeamMember.order).all()
    
#     max_order = len(siblings) + 1
    
#     if request.order <= 0 or request.order > max_order:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Order must be between 1 and {max_order}"
#         )
    
#     if request.order == team_member.order:
#         return {"message": "Team member is already at the desired order"}
    
#     try:
#         if request.order > team_member.order:
#             # Moving forward - decrease order of items between old and new position
#             affected_items = db.query(TeamMember).filter(
#                 TeamMember.is_deleted == False,
#                 TeamMember.id != team_member_id,
#                 TeamMember.order > team_member.order,
#                 TeamMember.order <= request.order
#             ).order_by(TeamMember.order).all()
            
#             for item in affected_items:
#                 item.order -= 1
#         else:
#             # Moving backward - increase order of items between new and old position
#             affected_items = db.query(TeamMember).filter(
#                 TeamMember.is_deleted == False,
#                 TeamMember.id != team_member_id,
#                 TeamMember.order >= request.order,
#                 TeamMember.order < team_member.order
#             ).order_by(TeamMember.order).all()
            
#             for item in affected_items:
#                 item.order += 1
        
#         team_member.order = request.order
        
#         db.commit()
#         return {"message": "Team member reordered successfully"}
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )

