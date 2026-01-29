from math import ceil
from app.services.image_upload import upload_image, delete_image
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.pagination import PageInfo, PaginatedResponse
from app.services.auth import get_current_active_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

@router.post("/upload_image")
async def upload_images(
    file: UploadFile = File(...),
    stage: str = Form(...),
    old_image_path: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload an image for a feature publication (Authenticated users only)
    """
    valid_stages = ["feature_publication", "teams", "news"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stage. Must be one of: {valid_stages}"
        )
    file_path = await upload_image(file, stage, old_image_path=old_image_path) 
    
    return {
        "message": "Image uploaded successfully",
        "image_url": f"/{file_path}",
        "stage": stage
    }

@router.get("/list_all_images")
async def list_all_images(
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Max number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all images from the images directory (Authenticated users only)
    Returns all images regardless of stage (feature_publication, teams, news)
    """
    try:
        images_dir = settings.IMAGES_UPLOAD_DIR
        

        if not images_dir.exists():
            total_items = 0
            total_pages = 0
            image_list = []
        else:

            all_images = []
            for ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                all_images.extend(list(images_dir.glob(f"*{ext}")))
                all_images.extend(list(images_dir.glob(f"*{ext.upper()}")))
            
            # Sort by modification time (newest first)
            all_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            

            total_items = len(all_images)
            total_pages = ceil(total_items / size) if total_items > 0 else 0
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_images = all_images[start_idx:end_idx]
            
            image_list = [f"/{str(image_path)}" for image_path in paginated_images]
        
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
            items=image_list,
            page_info=page_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch images: {str(e)}"
        )


@router.delete("/delete_image")
def delete_image_endpoint(
    image_path: str = Query(..., description="Path to the image (as returned by list_all_images)"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete an image (authenticated users only).
    Pass the image path as returned by the list_all_images endpoint.
    """
    delete_image(image_path)
    return {"message": "Image deleted successfully", "image_path": image_path}
