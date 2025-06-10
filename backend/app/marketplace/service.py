"""
Service layer for Template Marketplace functionality.
"""

import html
import re
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    MarketplaceTemplate,
    TemplateCategory,
    TemplateReview,
    TemplateStatus,
    TemplateVersion,
    User,
)
from app.marketplace.models import (
    CategoryCreate,
    ReviewCreate,
    TemplateApproval,
    TemplateCreate,
    TemplateSearch,
    TemplateUpdate,
    TemplateVersionCreate,
)


class MarketplaceService:
    """Service class for marketplace operations."""

    def __init__(self, db: Session):
        """Initialize the service with database session."""
        self.db = db

    def create_template(self, template_data: TemplateCreate, author_id: int) -> MarketplaceTemplate:
        """Create a new marketplace template."""
        # Sanitize input data
        sanitized_data = self._sanitize_template_data(template_data.model_dump())
        
        # Validate Docker Compose YAML
        self._validate_docker_compose(sanitized_data["docker_compose_yaml"])
        
        # Create template
        template = MarketplaceTemplate(
            name=sanitized_data["name"],
            description=sanitized_data["description"],
            author_id=author_id,
            category_id=sanitized_data["category_id"],
            version=sanitized_data["version"],
            docker_compose_yaml=sanitized_data["docker_compose_yaml"],
            tags=sanitized_data.get("tags", []),
            status=TemplateStatus.PENDING,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        # Create initial version
        self._create_template_version(template.id, template.version, template.docker_compose_yaml)
        
        return template

    def get_template(self, template_id: int) -> Optional[MarketplaceTemplate]:
        """Get a template by ID with related data."""
        return (
            self.db.query(MarketplaceTemplate)
            .options(
                joinedload(MarketplaceTemplate.author),
                joinedload(MarketplaceTemplate.category),
                joinedload(MarketplaceTemplate.reviews),
            )
            .filter(MarketplaceTemplate.id == template_id)
            .first()
        )

    def update_template(
        self, template_id: int, template_data: TemplateUpdate, user_id: int
    ) -> Optional[MarketplaceTemplate]:
        """Update a template (only by author or admin)."""
        template = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.id == template_id
        ).first()
        
        if not template:
            return None
            
        # Check ownership (will be enforced at router level)
        if template.author_id != user_id:
            return None
        
        # Sanitize and update fields
        update_data = template_data.model_dump(exclude_unset=True)
        if update_data:
            sanitized_data = self._sanitize_template_data(update_data)
            
            for field, value in sanitized_data.items():
                if hasattr(template, field):
                    setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(template)
        
        return template

    def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template (only by author or admin)."""
        template = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.id == template_id
        ).first()
        
        if not template or template.author_id != user_id:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True

    def search_templates(self, search_params: TemplateSearch) -> Tuple[List[MarketplaceTemplate], int]:
        """Search templates with filters and pagination."""
        query = self.db.query(MarketplaceTemplate).options(
            joinedload(MarketplaceTemplate.author),
            joinedload(MarketplaceTemplate.category),
        )
        
        # Filter by status (only show approved templates to regular users)
        query = query.filter(MarketplaceTemplate.status == TemplateStatus.APPROVED)
        
        # Apply search filters
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    MarketplaceTemplate.name.ilike(search_term),
                    MarketplaceTemplate.description.ilike(search_term),
                )
            )
        
        if search_params.category_id:
            query = query.filter(MarketplaceTemplate.category_id == search_params.category_id)
        
        if search_params.tags:
            # Filter by tags (JSON contains)
            for tag in search_params.tags:
                query = query.filter(MarketplaceTemplate.tags.contains([tag]))
        
        if search_params.min_rating:
            query = query.filter(MarketplaceTemplate.rating_avg >= search_params.min_rating)
        
        # Apply sorting
        sort_field = getattr(MarketplaceTemplate, search_params.sort_by)
        if search_params.sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (search_params.page - 1) * search_params.per_page
        templates = query.offset(offset).limit(search_params.per_page).all()
        
        return templates, total

    def create_review(self, template_id: int, review_data: ReviewCreate, user_id: int) -> Optional[TemplateReview]:
        """Create a review for a template."""
        # Check if template exists and is approved
        template = self.db.query(MarketplaceTemplate).filter(
            and_(
                MarketplaceTemplate.id == template_id,
                MarketplaceTemplate.status == TemplateStatus.APPROVED,
            )
        ).first()
        
        if not template:
            return None
        
        # Check if user already reviewed this template
        existing_review = self.db.query(TemplateReview).filter(
            and_(
                TemplateReview.template_id == template_id,
                TemplateReview.user_id == user_id,
            )
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = review_data.rating
            existing_review.comment = html.escape(review_data.comment) if review_data.comment else None
            existing_review.updated_at = datetime.utcnow()
            review = existing_review
        else:
            # Create new review
            review = TemplateReview(
                template_id=template_id,
                user_id=user_id,
                rating=review_data.rating,
                comment=html.escape(review_data.comment) if review_data.comment else None,
            )
            self.db.add(review)
        
        self.db.commit()
        
        # Update template rating
        self._update_template_rating(template_id)
        
        return review

    def approve_template(self, template_id: int, approval_data: TemplateApproval, admin_id: int) -> Optional[MarketplaceTemplate]:
        """Approve or reject a template (admin only)."""
        template = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        if approval_data.action == "approve":
            template.status = TemplateStatus.APPROVED
            template.approved_by = admin_id
            template.approved_at = datetime.utcnow()
            template.rejection_reason = None
        else:  # reject
            template.status = TemplateStatus.REJECTED
            template.approved_by = None
            template.approved_at = None
            template.rejection_reason = html.escape(approval_data.reason) if approval_data.reason else None
        
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        
        return template

    def get_categories(self, active_only: bool = True) -> List[TemplateCategory]:
        """Get all template categories."""
        query = self.db.query(TemplateCategory)
        
        if active_only:
            query = query.filter(TemplateCategory.is_active == True)
        
        return query.order_by(TemplateCategory.sort_order, TemplateCategory.name).all()

    def create_category(self, category_data: CategoryCreate) -> TemplateCategory:
        """Create a new template category (admin only)."""
        category = TemplateCategory(
            name=html.escape(category_data.name),
            description=html.escape(category_data.description) if category_data.description else None,
            icon=category_data.icon,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active,
        )
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category

    def get_pending_templates(self) -> List[MarketplaceTemplate]:
        """Get all pending templates for admin approval."""
        return (
            self.db.query(MarketplaceTemplate)
            .options(
                joinedload(MarketplaceTemplate.author),
                joinedload(MarketplaceTemplate.category),
            )
            .filter(MarketplaceTemplate.status == TemplateStatus.PENDING)
            .order_by(MarketplaceTemplate.created_at)
            .all()
        )

    def get_marketplace_stats(self) -> dict:
        """Get marketplace statistics (admin only)."""
        stats = {}

        # Template counts by status
        stats["total_templates"] = self.db.query(MarketplaceTemplate).count()
        stats["approved_templates"] = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.status == TemplateStatus.APPROVED
        ).count()
        stats["pending_templates"] = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.status == TemplateStatus.PENDING
        ).count()
        stats["rejected_templates"] = self.db.query(MarketplaceTemplate).filter(
            MarketplaceTemplate.status == TemplateStatus.REJECTED
        ).count()

        # Download and review stats
        stats["total_downloads"] = self.db.query(func.sum(MarketplaceTemplate.downloads)).scalar() or 0
        stats["total_reviews"] = self.db.query(TemplateReview).count()

        # Average rating
        avg_rating = self.db.query(func.avg(MarketplaceTemplate.rating_avg)).filter(
            MarketplaceTemplate.rating_count > 0
        ).scalar()
        stats["average_rating"] = round(float(avg_rating), 2) if avg_rating else 0.0

        # Top categories
        top_categories = (
            self.db.query(
                TemplateCategory.name,
                func.count(MarketplaceTemplate.id).label("count")
            )
            .join(MarketplaceTemplate)
            .filter(MarketplaceTemplate.status == TemplateStatus.APPROVED)
            .group_by(TemplateCategory.id, TemplateCategory.name)
            .order_by(desc(func.count(MarketplaceTemplate.id)))
            .limit(5)
            .all()
        )
        stats["top_categories"] = [{"name": cat.name, "count": cat.count} for cat in top_categories]

        # Recent templates - convert to dict format for Pydantic
        recent_templates_db = (
            self.db.query(MarketplaceTemplate)
            .options(
                joinedload(MarketplaceTemplate.author),
                joinedload(MarketplaceTemplate.category),
            )
            .filter(MarketplaceTemplate.status == TemplateStatus.APPROVED)
            .order_by(desc(MarketplaceTemplate.created_at))
            .limit(5)
            .all()
        )

        # Convert database models to dict format for Pydantic validation
        recent_templates = []
        for template in recent_templates_db:
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
            recent_templates.append(template_dict)

        stats["recent_templates"] = recent_templates

        return stats

    def _sanitize_template_data(self, data: dict) -> dict:
        """Sanitize template data to prevent XSS."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = html.escape(value.strip())
            elif isinstance(value, list) and key == "tags":
                sanitized[key] = [html.escape(tag.strip()) for tag in value if tag.strip()]
            else:
                sanitized[key] = value
        
        return sanitized

    def _validate_docker_compose(self, yaml_content: str) -> None:
        """Validate Docker Compose YAML content."""
        # Basic validation - check for required fields
        if "version" not in yaml_content and "services" not in yaml_content:
            raise ValueError("Invalid Docker Compose format: missing 'services' section")
        
        # Security validation - check for dangerous configurations
        dangerous_patterns = [
            r"privileged:\s*true",
            r"network_mode:\s*host",
            r"pid:\s*host",
            r"--privileged",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, yaml_content, re.IGNORECASE):
                raise ValueError(f"Security violation: dangerous configuration detected")

    def _create_template_version(self, template_id: int, version: str, yaml_content: str, changelog: str = None) -> TemplateVersion:
        """Create a new template version."""
        version_obj = TemplateVersion(
            template_id=template_id,
            version_number=version,
            docker_compose_yaml=yaml_content,
            changelog=changelog,
        )
        
        self.db.add(version_obj)
        self.db.commit()
        
        return version_obj

    def _update_template_rating(self, template_id: int) -> None:
        """Update template rating based on reviews."""
        reviews = self.db.query(TemplateReview).filter(
            TemplateReview.template_id == template_id
        ).all()
        
        if reviews:
            avg_rating = sum(review.rating for review in reviews) / len(reviews)
            
            template = self.db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.id == template_id
            ).first()
            
            if template:
                template.rating_avg = round(avg_rating, 2)
                template.rating_count = len(reviews)
                self.db.commit()
