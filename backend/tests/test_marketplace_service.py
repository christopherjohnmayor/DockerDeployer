"""
Tests for marketplace service layer.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.db.models import (
    MarketplaceTemplate,
    TemplateCategory,
    TemplateReview,
    TemplateStatus,
    User,
    UserRole,
)
from app.marketplace.models import (
    ReviewCreate,
    TemplateApproval,
    TemplateCreate,
    TemplateSearch,
    TemplateUpdate,
)
from app.marketplace.service import MarketplaceService
from tests.conftest import TestingSessionLocal


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """Create an admin user."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"admin_{unique_id}",
        email=f"admin_{unique_id}@example.com",
        hashed_password="hashed_password",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_category(db_session: Session):
    """Create a test category."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    category = TemplateCategory(
        name=f"Test Category {unique_id}",
        description="A test category",
        icon="test",
        sort_order=1,
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def marketplace_service(db_session: Session):
    """Create a marketplace service instance."""
    return MarketplaceService(db_session)


def get_valid_docker_compose_yaml():
    """Get a valid Docker Compose YAML for testing."""
    return """version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - '80:80'
    environment:
      - ENV=production
    volumes:
      - ./html:/usr/share/nginx/html"""


class TestMarketplaceService:
    """Test MarketplaceService functionality."""

    def test_create_template(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test creating a new template."""
        template_data = TemplateCreate(
            name="Test Template",
            description="A test template for testing purposes",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            tags=["test", "nginx"],
            version="1.0.0",
        )

        template = marketplace_service.create_template(template_data, test_user.id)

        assert template is not None
        assert template.name == "Test Template"
        assert template.description == "A test template for testing purposes"
        assert template.author_id == test_user.id
        assert template.category_id == test_category.id
        assert template.status == TemplateStatus.PENDING
        assert template.tags == ["test", "nginx"]

    def test_create_template_with_dangerous_yaml(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test creating a template with dangerous YAML configuration."""
        template_data = TemplateCreate(
            name="Dangerous Template",
            description="A template with dangerous configuration",
            category_id=test_category.id,
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx\n    privileged: true",
            tags=["dangerous"],
            version="1.0.0",
        )

        with pytest.raises(ValueError, match="Security violation"):
            marketplace_service.create_template(template_data, test_user.id)

    def test_get_template(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test getting a template by ID."""
        # Create a template first
        template_data = TemplateCreate(
            name="Get Test Template",
            description="A template for get testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            tags=["get", "test"],
        )
        created_template = marketplace_service.create_template(template_data, test_user.id)

        # Get the template
        retrieved_template = marketplace_service.get_template(created_template.id)

        assert retrieved_template is not None
        assert retrieved_template.id == created_template.id
        assert retrieved_template.name == "Get Test Template"

    def test_get_nonexistent_template(self, marketplace_service: MarketplaceService):
        """Test getting a non-existent template."""
        template = marketplace_service.get_template(99999)
        assert template is None

    def test_update_template(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test updating a template."""
        # Create a template first
        template_data = TemplateCreate(
            name="Update Test Template",
            description="A template for update testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        created_template = marketplace_service.create_template(template_data, test_user.id)

        # Update the template
        update_data = TemplateUpdate(
            name="Updated Template Name",
            description="Updated description",
            tags=["updated", "test"],
        )
        updated_template = marketplace_service.update_template(created_template.id, update_data, test_user.id)

        assert updated_template is not None
        assert updated_template.name == "Updated Template Name"
        assert updated_template.description == "Updated description"
        assert updated_template.tags == ["updated", "test"]

    def test_update_template_unauthorized(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test updating a template by unauthorized user."""
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER,
            is_active=True,
        )
        marketplace_service.db.add(other_user)
        marketplace_service.db.commit()
        marketplace_service.db.refresh(other_user)

        # Create a template
        template_data = TemplateCreate(
            name="Unauthorized Update Test",
            description="A template for unauthorized update testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        created_template = marketplace_service.create_template(template_data, test_user.id)

        # Try to update with different user
        update_data = TemplateUpdate(name="Should Not Update")
        updated_template = marketplace_service.update_template(created_template.id, update_data, other_user.id)

        assert updated_template is None

    def test_delete_template(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test deleting a template."""
        # Create a template first
        template_data = TemplateCreate(
            name="Delete Test Template",
            description="A template for delete testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        created_template = marketplace_service.create_template(template_data, test_user.id)

        # Delete the template
        success = marketplace_service.delete_template(created_template.id, test_user.id)
        assert success is True

        # Verify it's deleted
        deleted_template = marketplace_service.get_template(created_template.id)
        assert deleted_template is None

    def test_search_templates(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test searching templates."""
        # Create some approved templates with unique search term
        for i in range(3):
            template_data = TemplateCreate(
                name=f"UniqueSearchable Template {i}",
                description=f"A template for uniquesearchable testing {i}",
                category_id=test_category.id,
                docker_compose_yaml=get_valid_docker_compose_yaml(),
                tags=[f"search{i}", "uniquesearchable"],
            )
            template = marketplace_service.create_template(template_data, test_user.id)
            # Manually approve for testing
            template.status = TemplateStatus.APPROVED
            marketplace_service.db.commit()

        # Search templates with unique term
        search_params = TemplateSearch(
            query="UniqueSearchable",
            page=1,
            per_page=10,
        )
        templates, total = marketplace_service.search_templates(search_params)

        assert total == 3
        assert len(templates) == 3
        assert all("UniqueSearchable" in template.name for template in templates)

    def test_create_review(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test creating a review for a template."""
        # Create and approve a template
        template_data = TemplateCreate(
            name="Review Test Template",
            description="A template for review testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        template = marketplace_service.create_template(template_data, test_user.id)
        template.status = TemplateStatus.APPROVED
        marketplace_service.db.commit()

        # Create a review
        review_data = ReviewCreate(
            rating=5,
            comment="Excellent template!",
        )
        review = marketplace_service.create_review(template.id, review_data, test_user.id)

        assert review is not None
        assert review.rating == 5
        assert review.comment == "Excellent template!"
        assert review.template_id == template.id
        assert review.user_id == test_user.id

    def test_approve_template(self, marketplace_service: MarketplaceService, test_user: User, admin_user: User, test_category: TemplateCategory):
        """Test approving a template."""
        # Create a pending template
        template_data = TemplateCreate(
            name="Approval Test Template",
            description="A template for approval testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        template = marketplace_service.create_template(template_data, test_user.id)

        # Approve the template
        approval_data = TemplateApproval(action="approve")
        approved_template = marketplace_service.approve_template(template.id, approval_data, admin_user.id)

        assert approved_template is not None
        assert approved_template.status == TemplateStatus.APPROVED
        assert approved_template.approved_by == admin_user.id
        assert approved_template.approved_at is not None

    def test_reject_template(self, marketplace_service: MarketplaceService, test_user: User, admin_user: User, test_category: TemplateCategory):
        """Test rejecting a template."""
        # Create a pending template
        template_data = TemplateCreate(
            name="Rejection Test Template",
            description="A template for rejection testing",
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
        )
        template = marketplace_service.create_template(template_data, test_user.id)

        # Reject the template
        approval_data = TemplateApproval(action="reject", reason="Does not meet quality standards")
        rejected_template = marketplace_service.approve_template(template.id, approval_data, admin_user.id)

        assert rejected_template is not None
        assert rejected_template.status == TemplateStatus.REJECTED
        assert rejected_template.rejection_reason == "Does not meet quality standards"

    def test_get_categories(self, marketplace_service: MarketplaceService, test_category: TemplateCategory):
        """Test getting template categories."""
        categories = marketplace_service.get_categories()

        assert len(categories) >= 1
        assert any(cat.name.startswith("Test Category") for cat in categories)

    def test_get_marketplace_stats(self, marketplace_service: MarketplaceService, test_user: User, test_category: TemplateCategory):
        """Test getting marketplace statistics."""
        # Create some templates with different statuses
        for status in [TemplateStatus.PENDING, TemplateStatus.APPROVED, TemplateStatus.REJECTED]:
            template_data = TemplateCreate(
                name=f"Stats Test Template {status}",
                description=f"A template for stats testing with status {status}",
                category_id=test_category.id,
                docker_compose_yaml=get_valid_docker_compose_yaml(),
            )
            template = marketplace_service.create_template(template_data, test_user.id)
            template.status = status
            marketplace_service.db.commit()

        stats = marketplace_service.get_marketplace_stats()

        assert "total_templates" in stats
        assert "approved_templates" in stats
        assert "pending_templates" in stats
        assert "rejected_templates" in stats
        assert "total_downloads" in stats
        assert "total_reviews" in stats
        assert "average_rating" in stats
        assert stats["total_templates"] >= 3
