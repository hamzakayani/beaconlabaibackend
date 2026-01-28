

from datetime import datetime
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from app.core.config import settings


async def upload_image(
    file: UploadFile,
    stage: str,
    old_image_path: Optional[str] = None
):

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only images are allowed"
        )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{stage}_{timestamp}{file_ext}"
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

        print(file_path)
        
        return file_path
    
    except HTTPException:
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


def delete_image(image_path: str) -> None:
    """
    Delete an image file. The path must be under IMAGES_UPLOAD_DIR.
    Accepts the path as returned by list_all_images (relative or absolute).
    """
    path = Path(image_path).resolve()
    upload_dir = settings.IMAGES_UPLOAD_DIR.resolve()

    try:
        path.relative_to(upload_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image path must be within the upload directory",
        )

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a file",
        )

    try:
        path.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}",
        )