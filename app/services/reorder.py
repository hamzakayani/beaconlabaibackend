from sqlalchemy.orm import Session
from typing import Type, TypeVar
from fastapi import HTTPException, status

# Generic type for models with order field
ModelType = TypeVar('ModelType')

def reorder_item(
    db: Session,
    model_class: Type[ModelType],
    item_id: int,
    new_order: int
) -> None:
    """
    Generic service to reorder items in a collection.
    
    Works with any SQLAlchemy model that has:
    - id field
    - order field (Integer)
    - is_deleted field (Boolean, for soft delete filtering)
    
    Args:
        db: Database session
        model_class: The SQLAlchemy model class
        item_id: ID of the item to reorder
        new_order: The new order position (1-indexed)
    
    Raises:
        HTTPException: If item not found or order is invalid
    """
    # Get the item to reorder
    item = db.query(model_class).filter(
        model_class.id == item_id,
        model_class.is_deleted == False
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model_class.__name__} not found"
        )
    
    # Get all siblings (all non-deleted items except the current one)
    siblings = db.query(model_class).filter(
        model_class.is_deleted == False,
        model_class.id != item_id
    ).order_by(model_class.order).all()
    
    max_order = len(siblings) + 1
    
    # Validate order range
    if new_order <= 0 or new_order > max_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be between 1 and {max_order}"
        )
    
    # If order hasn't changed, no need to do anything
    if new_order == item.order:
        return
    
    # Perform reordering
    if new_order > item.order:
        # Moving forward - decrease order of items between old and new position
        affected_items = db.query(model_class).filter(
            model_class.is_deleted == False,
            model_class.id != item_id,
            model_class.order > item.order,
            model_class.order <= new_order
        ).order_by(model_class.order).all()
        
        for affected_item in affected_items:
            affected_item.order -= 1
    else:
        # Moving backward - increase order of items between new and old position
        affected_items = db.query(model_class).filter(
            model_class.is_deleted == False,
            model_class.id != item_id,
            model_class.order >= new_order,
            model_class.order < item.order
        ).order_by(model_class.order).all()
        
        for affected_item in affected_items:
            affected_item.order += 1
    
    # Update the item's order
    item.order = new_order

