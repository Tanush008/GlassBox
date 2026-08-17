"""Small helpers shared by more than one router."""
import uuid
from typing import List, Tuple, TypeVar

T = TypeVar("T")


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def paginate(items: List[T], page: int = 1, page_size: int = 20) -> Tuple[List[T], int]:
    """Return (page_of_items, total_count)."""
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], len(items)
