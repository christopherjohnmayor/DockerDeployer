"""
FastAPI router for Template Marketplace endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.db.database import get_db
from app.db.models import User
from app.marketplace.models import (
    Category,
    MarketplaceStats,
    Review,
    ReviewCreate,
    Template,
    TemplateApproval,
    TemplateCreate,
    TemplateList,
    TemplateSearch,
    TemplateUpdate,
)
from app.marketplace.service import MarketplaceService
from app.middleware.rate_limiting import rate_limit_admin, rate_limit_api, rate_limit_metrics

router = APIRouter()


def get_marketplace_service(db: Session = Depends(get_db)) -> MarketplaceService:
    """Get marketplace service instance."""
    return MarketplaceService(db)


@router.post("/templates", response_model=Template, status_code=status.HTTP_201_CREATED)
@rate_limit_api("10/minute")
async def create_template(
    request: Request,
    response: Response,
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Create a new marketplace template.
    
    Requires authentication. Template will be in 'pending' status awaiting admin approval.
    Rate limited to 10 requests per minute per user.
    """
    try:
        template = service.create_template(template_data, current_user.id)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.get("/templates", response_model=TemplateList)
@rate_limit_api("100/minute")
async def search_templates(
    request: Request,
    response: Response,
    query: str = Query(None, max_length=100, description="Search query"),
    category_id: int = Query(None, description="Filter by category"),
    min_rating: float = Query(None, ge=0, le=5, description="Minimum rating"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Search and browse marketplace templates.
    
    Returns only approved templates. Supports filtering, sorting, and pagination.
    Rate limited to 100 requests per minute.
    """
    search_params = TemplateSearch(
        query=query,
        category_id=category_id,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    
    try:
        templates_db, total = service.search_templates(search_params)
        pages = (total + per_page - 1) // per_page

        # Convert database models to dict format for Pydantic validation
        templates = []
        for template in templates_db:
            template_dict = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category_id": template.category_id,
                "docker_compose_yaml": template.docker_compose_yaml,
                "tags": template.tags or [],
                "author_id": template.author_id,
                "version": template.version,
                "status": template.status,
                "downloads": template.downloads,
                "rating_avg": template.rating_avg,
                "rating_count": template.rating_count,
                "approved_by": template.approved_by,
                "approved_at": template.approved_at,
                "rejection_reason": template.rejection_reason,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "author_username": template.author.username if template.author else None,
                "category_name": template.category.name if template.category else None,
            }
            templates.append(template_dict)

        return TemplateList(
            templates=templates,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=Template)
@rate_limit_api("100/minute")
async def get_template(
    request: Request,
    response: Response,
    template_id: int,
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Get a specific template by ID.
    
    Returns template details including author and category information.
    Rate limited to 100 requests per minute.
    """
    template = service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.put("/templates/{template_id}", response_model=Template)
@rate_limit_api("20/minute")
async def update_template(
    request: Request,
    response: Response,
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Update a template.
    
    Only the template author can update their templates.
    Rate limited to 20 requests per minute per user.
    """
    template = service.update_template(template_id, template_data, current_user.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )
    
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit_api("5/minute")
async def delete_template(
    request: Request,
    response: Response,
    template_id: int,
    current_user: User = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Delete a template.
    
    Only the template author can delete their templates.
    Rate limited to 5 requests per minute per user.
    """
    success = service.delete_template(template_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )


@router.post("/templates/{template_id}/reviews", response_model=Review, status_code=status.HTTP_201_CREATED)
@rate_limit_api("30/minute")
async def create_review(
    request: Request,
    response: Response,
    template_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Create or update a review for a template.
    
    Users can only review approved templates and can update their existing reviews.
    Rate limited to 30 requests per minute per user.
    """
    review = service.create_review(template_id, review_data, current_user.id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or not approved"
        )
    
    return review


@router.get("/categories", response_model=List[Category])
@rate_limit_api("200/minute")
async def get_categories(
    request: Request,
    response: Response,
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Get all active template categories.
    
    Returns categories sorted by sort_order and name.
    Rate limited to 200 requests per minute.
    """
    categories = service.get_categories()
    return categories


# Admin endpoints
@router.get("/admin/pending", response_model=List[Template])
@rate_limit_admin("200/minute")
async def get_pending_templates(
    request: Request,
    response: Response,
    admin_user: User = Depends(require_admin),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Get all pending templates for admin approval.

    Admin only endpoint. Rate limited to 200 requests per minute.
    """
    templates = service.get_pending_templates()
    return templates


@router.post("/admin/templates/{template_id}/approve", response_model=Template)
@rate_limit_admin("50/minute")
async def approve_template(
    request: Request,
    response: Response,
    template_id: int,
    approval_data: TemplateApproval,
    admin_user: User = Depends(require_admin),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Approve or reject a template.
    
    Admin only endpoint. Rate limited to 50 requests per minute.
    """
    template = service.approve_template(template_id, approval_data, admin_user.id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.get("/admin/stats", response_model=MarketplaceStats)
@rate_limit_admin("100/minute")
async def get_marketplace_stats(
    request: Request,
    response: Response,
    admin_user: User = Depends(require_admin),
    service: MarketplaceService = Depends(get_marketplace_service),
):
    """
    Get marketplace statistics and analytics.
    
    Admin only endpoint. Rate limited to 100 requests per minute.
    """
    stats = service.get_marketplace_stats()
    return MarketplaceStats(**stats)
