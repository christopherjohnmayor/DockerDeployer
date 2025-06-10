"""
Template Marketplace module for DockerDeployer.

This module provides functionality for community-contributed Docker templates
including submission, approval workflow, reviews, and marketplace browsing.
"""

from .models import (
    Category,
    CategoryCreate,
    MarketplaceStats,
    Review,
    ReviewCreate,
    Template,
    TemplateApproval,
    TemplateCreate,
    TemplateList,
    TemplateSearch,
    TemplateUpdate,
    TemplateVersion,
    TemplateVersionCreate,
)
from .router import router
from .service import MarketplaceService

__all__ = [
    "MarketplaceService",
    "router",
    "Template",
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateList",
    "TemplateSearch",
    "Category",
    "CategoryCreate",
    "Review",
    "ReviewCreate",
    "TemplateApproval",
    "TemplateVersion",
    "TemplateVersionCreate",
    "MarketplaceStats",
]
