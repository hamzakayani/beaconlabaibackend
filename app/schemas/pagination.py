from typing import Generic, TypeVar, List
from pydantic import BaseModel
from app.core.config import settings

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    size: int = settings.PAGINATION_SIZE

class PageInfo(BaseModel):
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page_info: PageInfo

