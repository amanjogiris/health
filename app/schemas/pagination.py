"""Generic paginated response wrapper."""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope returned by every list endpoint.

    Attributes
    ----------
    items  : the page items
    total  : total number of matching records in the database
    skip   : offset that was applied
    limit  : page size that was requested
    """

    items: List[T]
    total: int
    skip: int
    limit: int
