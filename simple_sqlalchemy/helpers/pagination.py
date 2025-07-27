"""
Pagination helper for simple-sqlalchemy
"""

import math
from typing import Dict, Any, List, TypeVar, Optional

T = TypeVar('T')


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

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate page
    if page is not None and page < 1:
        raise ValueError(f"Page must be >= 1, got {page}")
    page = page or 1

    # Validate per_page
    if per_page is not None and per_page < 1:
        raise ValueError(f"Per page must be >= 1, got {per_page}")
    if per_page is not None and per_page > max_per_page:
        raise ValueError(f"Per page must be <= {max_per_page}, got {per_page}")
    per_page = per_page or default_per_page

    return page, per_page


def calculate_pagination(page: int, per_page: int, total: int) -> Dict[str, Any]:
    """
    Calculate all pagination information in one pass - O(1) operation.

    Args:
        page: Current page number (1-based)
        per_page: Number of items per page
        total: Total number of items

    Returns:
        Dict with all calculated pagination values:
        - page: Current page number
        - per_page: Items per page
        - total: Total number of items
        - total_pages: Total number of pages
        - offset: SQL offset for queries
        - has_prev: Whether there's a previous page
        - has_next: Whether there's a next page
        - prev_page: Previous page number (or None)
        - next_page: Next page number (or None)
        - start_item: First item number on current page
        - end_item: Last item number on current page

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    if page < 1:
        raise ValueError(f"Page must be >= 1, got {page}")
    if per_page < 1:
        raise ValueError(f"Per page must be >= 1, got {per_page}")
    if total < 0:
        raise ValueError(f"Total must be >= 0, got {total}")

    # Calculate everything in one pass - all O(1) operations
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    # Clamp page to valid range
    page = min(page, total_pages)

    # Calculate offset for SQL queries
    offset = (page - 1) * per_page

    # Navigation info
    has_prev = page > 1
    has_next = page < total_pages
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None

    # Item range for current page
    start_item = offset + 1 if total > 0 else 0
    end_item = min(offset + per_page, total)

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "offset": offset,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": prev_page,
        "next_page": next_page,
        "start_item": start_item,
        "end_item": end_item
    }


def build_pagination_response(
    items: List[T],
    page: int,
    per_page: int,
    total: int,
    include_navigation: bool = True
) -> Dict[str, Any]:
    """
    Build a standardized pagination response.

    Args:
        items: List of items for current page
        page: Current page number
        per_page: Number of items per page
        total: Total number of items
        include_navigation: Whether to include navigation info (prev/next)

    Returns:
        Dictionary with items and pagination information
    """
    info = calculate_pagination(page, per_page, total)

    response = {
        "items": items,
        "total": info["total"],
        "page": info["page"],
        "per_page": info["per_page"],
        "total_pages": info["total_pages"]
    }

    if include_navigation:
        response.update({
            "has_prev": info["has_prev"],
            "has_next": info["has_next"],
            "prev_page": info["prev_page"],
            "next_page": info["next_page"]
        })

    return response


def get_pagination_summary(page: int, per_page: int, total: int) -> str:
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

    info = calculate_pagination(page, per_page, total)

    if info["start_item"] == info["end_item"]:
        return f"Showing item {info['start_item']} of {total}"
    else:
        return f"Showing {info['start_item']}-{info['end_item']} of {total} items"


def get_page_range(current_page: int, total_pages: int, max_pages: int = 10) -> List[int]:
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


# Backward compatibility - deprecated class
class PaginationHelper:
    """
    Deprecated: Use the module-level functions instead.
    This class is kept for backward compatibility only.
    """

    @staticmethod
    def calculate_pagination_info(page: int, per_page: int, total: int):
        """Deprecated: Use calculate_pagination() instead"""
        import warnings
        warnings.warn("PaginationHelper.calculate_pagination_info is deprecated. Use calculate_pagination() instead.",
                     DeprecationWarning, stacklevel=2)
        return calculate_pagination(page, per_page, total)

    @staticmethod
    def build_pagination_response(items: List[T], page: int, per_page: int, total: int, include_pagination_info: bool = True):
        """Deprecated: Use build_pagination_response() instead"""
        import warnings
        warnings.warn("PaginationHelper.build_pagination_response is deprecated. Use build_pagination_response() instead.",
                     DeprecationWarning, stacklevel=2)
        return build_pagination_response(items, page, per_page, total, include_pagination_info)

    @staticmethod
    def calculate_offset(page: int, per_page: int) -> int:
        """Deprecated: Use calculate_pagination()['offset'] instead"""
        import warnings
        warnings.warn("PaginationHelper.calculate_offset is deprecated. Use calculate_pagination()['offset'] instead.",
                     DeprecationWarning, stacklevel=2)
        return calculate_pagination(page, per_page, 0)["offset"]

    @staticmethod
    def validate_pagination_params(page=None, per_page=None, max_per_page=1000, default_per_page=20):
        """Deprecated: Use validate_pagination_params() instead"""
        import warnings
        warnings.warn("PaginationHelper.validate_pagination_params is deprecated. Use validate_pagination_params() instead.",
                     DeprecationWarning, stacklevel=2)
        return validate_pagination_params(page, per_page, max_per_page, default_per_page)

    @staticmethod
    def get_pagination_summary(page: int, per_page: int, total: int) -> str:
        """Deprecated: Use get_pagination_summary() instead"""
        import warnings
        warnings.warn("PaginationHelper.get_pagination_summary is deprecated. Use get_pagination_summary() instead.",
                     DeprecationWarning, stacklevel=2)
        return get_pagination_summary(page, per_page, total)

    @staticmethod
    def get_page_range(current_page: int, total_pages: int, max_pages: int = 10):
        """Deprecated: Use get_page_range() instead"""
        import warnings
        warnings.warn("PaginationHelper.get_page_range is deprecated. Use get_page_range() instead.",
                     DeprecationWarning, stacklevel=2)
        return get_page_range(current_page, total_pages, max_pages)

    @staticmethod
    def is_valid_page(page: int, total: int, per_page: int) -> bool:
        """Deprecated: Use is_valid_page() instead"""
        import warnings
        warnings.warn("PaginationHelper.is_valid_page is deprecated. Use is_valid_page() instead.",
                     DeprecationWarning, stacklevel=2)
        return is_valid_page(page, total, per_page)
