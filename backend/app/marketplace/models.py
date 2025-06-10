"""
Pydantic models for the Template Marketplace API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class TemplateBase(BaseModel):
    """Base template model with common fields."""

    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    description: str = Field(..., min_length=10, max_length=1000, description="Template description")
    category_id: int = Field(..., description="Template category ID")
    docker_compose_yaml: str = Field(..., min_length=50, description="Docker Compose YAML content")
    tags: Optional[List[str]] = Field(default=[], description="Template tags")

    @validator("name")
    def validate_name(cls, v):
        """Validate template name."""
        if not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip()

    @validator("description")
    def validate_description(cls, v):
        """Validate template description."""
        if not v.strip():
            raise ValueError("Template description cannot be empty")
        return v.strip()

    @validator("tags")
    def validate_tags(cls, v):
        """Validate template tags."""
        if v is None:
            return []
        # Limit to 10 tags, each max 30 characters
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if len(tag) > 30:
                raise ValueError("Tag length cannot exceed 30 characters")
        return [tag.strip().lower() for tag in v if tag.strip()]


class TemplateCreate(TemplateBase):
    """Model for creating a new template."""

    version: str = Field(default="1.0.0", description="Template version")

    @validator("version")
    def validate_version(cls, v):
        """Validate semantic version format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v


class TemplateUpdate(BaseModel):
    """Model for updating an existing template."""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    category_id: Optional[int] = None
    docker_compose_yaml: Optional[str] = Field(None, min_length=50)
    tags: Optional[List[str]] = None

    @validator("name")
    def validate_name(cls, v):
        """Validate template name."""
        if v is not None and not v.strip():
            raise ValueError("Template name cannot be empty")
        return v.strip() if v else v

    @validator("description")
    def validate_description(cls, v):
        """Validate template description."""
        if v is not None and not v.strip():
            raise ValueError("Template description cannot be empty")
        return v.strip() if v else v

    @validator("tags")
    def validate_tags(cls, v):
        """Validate template tags."""
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if len(tag) > 30:
                raise ValueError("Tag length cannot exceed 30 characters")
        return [tag.strip().lower() for tag in v if tag.strip()]


class Template(TemplateBase):
    """Model for template responses."""

    id: int
    author_id: int
    version: str
    status: str
    downloads: int
    rating_avg: float
    rating_count: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Related data
    author_username: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        """Pydantic config."""
        orm_mode = True


class TemplateList(BaseModel):
    """Model for paginated template list responses."""

    templates: List[Template]
    total: int
    page: int
    per_page: int
    pages: int


class TemplateSearch(BaseModel):
    """Model for template search parameters."""

    query: Optional[str] = Field(None, max_length=100, description="Search query")
    category_id: Optional[int] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(default=[], description="Filter by tags")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field."""
        allowed_fields = ["created_at", "updated_at", "name", "downloads", "rating_avg"]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class CategoryBase(BaseModel):
    """Base category model."""

    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    pass


class Category(CategoryBase):
    """Model for category responses."""

    id: int
    created_at: datetime
    updated_at: datetime
    template_count: Optional[int] = 0

    class Config:
        """Pydantic config."""
        orm_mode = True


class ReviewBase(BaseModel):
    """Base review model."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=500, description="Review comment")

    @validator("comment")
    def validate_comment(cls, v):
        """Validate review comment."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else v


class ReviewCreate(ReviewBase):
    """Model for creating a new review."""
    pass


class Review(ReviewBase):
    """Model for review responses."""

    id: int
    template_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # Related data
    username: Optional[str] = None

    class Config:
        """Pydantic config."""
        orm_mode = True


class TemplateApproval(BaseModel):
    """Model for template approval/rejection."""

    action: str = Field(..., description="Action: 'approve' or 'reject'")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")

    @validator("action")
    def validate_action(cls, v):
        """Validate approval action."""
        if v not in ["approve", "reject"]:
            raise ValueError("Action must be 'approve' or 'reject'")
        return v

    @validator("reason")
    def validate_reason(cls, v, values):
        """Validate rejection reason."""
        if values.get("action") == "reject" and not v:
            raise ValueError("Reason is required for rejection")
        return v.strip() if v else v


class TemplateVersion(BaseModel):
    """Model for template version responses."""

    id: int
    template_id: int
    version_number: str
    changelog: Optional[str] = None
    created_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class TemplateVersionCreate(BaseModel):
    """Model for creating a new template version."""

    version_number: str = Field(..., description="Version number")
    docker_compose_yaml: str = Field(..., min_length=50, description="Docker Compose YAML content")
    changelog: Optional[str] = Field(None, max_length=1000, description="Version changelog")

    @validator("version_number")
    def validate_version_number(cls, v):
        """Validate semantic version format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        return v


class MarketplaceStats(BaseModel):
    """Model for marketplace statistics."""

    total_templates: int
    approved_templates: int
    pending_templates: int
    rejected_templates: int
    total_downloads: int
    total_reviews: int
    average_rating: float
    top_categories: List[dict]
    recent_templates: List[Template]
