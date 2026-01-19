from datetime import datetime
import os
from typing import Optional
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


async def save_cv_file(
    file: UploadFile,
    job_id: int
) -> str:
    """
    Save CV file to disk with UUID-based filename.
    Validates file type and size before saving.
    
    Args:
        file: UploadFile object from FastAPI
        job_id: ID of the job application is for
        
    Returns:
        str: Relative file path to the saved CV
        
    Raises:
        HTTPException: If file validation fails
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_CV_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_CV_EXTENSIONS)}"
        )
    
    # Read file content to check size
    contents = await file.read()
    
    # Validate file size
    if len(contents) > settings.CV_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.CV_MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
        )
    
    # Generate UUID-based filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create job-specific directory
    job_dir = settings.CV_UPLOAD_DIR / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = job_dir / unique_filename
    
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return relative path for database storage
        # This makes it easier to migrate to S3 later
        return str(file_path)
    
    except Exception as e:
        # Clean up if file was partially written
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


def delete_cv_file(file_path: str) -> bool:
    """
    Delete a CV file from disk.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        bool: True if file was deleted, False if it didn't exist
    """
    try:
        file = Path(file_path)
        if file.exists():
            file.unlink()
            return True
        return False
    except Exception:
        return False

async def save_image(
    file: UploadFile,
    path_prefix: str,
    old_image_path: Optional[Path] = None
) -> str:
    """
    Save an image to disk with UUID-based filename.
    Validates file type and size before saving."""

    file_path = None
    
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only images are allowed"
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{path_prefix}_{timestamp}{file_ext}"
        file_path = settings.IMAGES_UPLOAD_DIR / filename
        
        try:
            contents = await file.read()
            
            if len(contents) > settings.IMAGE_MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File is too large to upload."
                )
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            new_url = f"/images/{filename}"
            
            if old_image_path and old_image_path.exists():
                try:
                    old_image_path.unlink()
                except Exception as e:
                    pass
            
            return new_url
        
        except HTTPException:
            raise
        except Exception as e:
            if file_path and file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image: {str(e)}"
            )