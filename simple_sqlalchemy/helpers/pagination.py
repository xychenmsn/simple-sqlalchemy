"""
Pagination helper for simple-sqlalchemy
"""

import math
from typing import Dict, Any, List, TypeVar, Optional
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class PaginationInfo:
    """Information about pagination state"""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    prev_page: Optional[int]
    next_page: Optional[int]


class PaginationHelper:
    """
    Helper class for pagination utilities.
    
    Provides utilities for calculating pagination information,
    building pagination responses, and handling edge cases.
    """
    
    @staticmethod
    def calculate_pagination_info(
        page: int,
        per_page: int,
        total: int
    ) -> PaginationInfo:
        """
        Calculate pagination information.
        
        Args:
            page: Current page number (1-based)
            per_page: Number of items per page
            total: Total number of items
            
        Returns:
            PaginationInfo object with calculated values
        """
        # Ensure valid values
        page = max(1, page)
        per_page = max(1, per_page)
        total = max(0, total)
        
        # Calculate total pages
        total_pages = math.ceil(total / per_page) if per_page > 0 else 1
        
        # Ensure page doesn't exceed total pages
        page = min(page, total_pages) if total_pages > 0 else 1
        
        # Calculate navigation info
        has_prev = page > 1
        has_next = page < total_pages
        prev_page = page - 1 if has_prev else None
        next_page = page + 1 if has_next else None
        
        return PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_prev=has_prev,
            has_next=has_next,
            prev_page=prev_page,
            next_page=next_page
        )
    
    @staticmethod
    def build_pagination_response(
        items: List[T],
        page: int,
        per_page: int,
        total: int,
        include_pagination_info: bool = True
    ) -> Dict[str, Any]:
        """
        Build a standardized pagination response.
        
        Args:
            items: List of items for current page
            page: Current page number
            per_page: Number of items per page
            total: Total number of items
            include_pagination_info: Whether to include detailed pagination info
            
        Returns:
            Dictionary with items and pagination information
        """
        pagination_info = PaginationHelper.calculate_pagination_info(page, per_page, total)
        
        response = {
            "items": items,
            "total": total,
            "page": pagination_info.page,
            "per_page": pagination_info.per_page,
            "total_pages": pagination_info.total_pages
        }
        
        if include_pagination_info:
            response.update({
                "has_prev": pagination_info.has_prev,
                "has_next": pagination_info.has_next,
                "prev_page": pagination_info.prev_page,
                "next_page": pagination_info.next_page
            })
        
        return response
    
    @staticmethod
    def calculate_offset(page: int, per_page: int) -> int:
        """
        Calculate the offset for SQL queries.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            Offset value for SQL queries
        """
        page = max(1, page)
        per_page = max(1, per_page)
        return (page - 1) * per_page
    
    @staticmethod
    def validate_pagination_params(
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        max_per_page: int = 1000,
        default_per_page: int = 20
    ) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            max_per_page: Maximum allowed items per page
            default_per_page: Default items per page
            
        Returns:
            Tuple of (validated_page, validated_per_page)
        """
        # Validate page
        if page is None or page < 1:
            page = 1
        
        # Validate per_page
        if per_page is None or per_page < 1:
            per_page = default_per_page
        elif per_page > max_per_page:
            per_page = max_per_page
        
        return page, per_page
    
    @staticmethod
    def get_page_range(
        current_page: int,
        total_pages: int,
        max_pages: int = 10
    ) -> List[int]:
        """
        Get a range of page numbers for pagination UI.
        
        Args:
            current_page: Current page number
            total_pages: Total number of pages
            max_pages: Maximum number of page links to show
            
        Returns:
            List of page numbers to display
        """
        if total_pages <= max_pages:
            return list(range(1, total_pages + 1))
        
        # Calculate start and end of page range
        half_max = max_pages // 2
        
        if current_page <= half_max:
            # Near the beginning
            return list(range(1, max_pages + 1))
        elif current_page >= total_pages - half_max:
            # Near the end
            return list(range(total_pages - max_pages + 1, total_pages + 1))
        else:
            # In the middle
            start = current_page - half_max
            end = current_page + half_max
            return list(range(start, end + 1))
    
    @staticmethod
    def get_pagination_summary(
        page: int,
        per_page: int,
        total: int
    ) -> str:
        """
        Get a human-readable pagination summary.
        
        Args:
            page: Current page number
            per_page: Number of items per page
            total: Total number of items
            
        Returns:
            String like "Showing 21-40 of 100 items"
        """
        if total == 0:
            return "No items found"
        
        pagination_info = PaginationHelper.calculate_pagination_info(page, per_page, total)
        
        start = (pagination_info.page - 1) * pagination_info.per_page + 1
        end = min(start + pagination_info.per_page - 1, total)
        
        if start == end:
            return f"Showing item {start} of {total}"
        else:
            return f"Showing {start}-{end} of {total} items"
    
    @staticmethod
    def is_valid_page(page: int, total: int, per_page: int) -> bool:
        """
        Check if a page number is valid for the given total and per_page.
        
        Args:
            page: Page number to check
            total: Total number of items
            per_page: Number of items per page
            
        Returns:
            True if page is valid, False otherwise
        """
        if page < 1:
            return False
        
        if total == 0:
            return page == 1
        
        total_pages = math.ceil(total / per_page) if per_page > 0 else 1
        return page <= total_pages
