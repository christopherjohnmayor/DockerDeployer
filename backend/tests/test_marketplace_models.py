"""
Tests for marketplace database models.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    MarketplaceTemplate,
    TemplateCategory,
    TemplateReview,
    TemplateStatus,
    TemplateVersion,
    User,
    UserRole,
)
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
def test_template(db_session: Session, test_user: User, test_category: TemplateCategory):
    """Create a test template."""
    template = MarketplaceTemplate(
        name="Test Template",
        description="A test template for testing purposes",
        author_id=test_user.id,
        category_id=test_category.id,
        version="1.0.0",
        docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx",
        status=TemplateStatus.PENDING,
        tags=["test", "nginx"],
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


class TestTemplateCategory:
    """Test TemplateCategory model."""

    def test_create_category(self, db_session: Session):
        """Test creating a template category."""
        category = TemplateCategory(
            name="Web Servers",
            description="Web server stacks",
            icon="web",
            sort_order=1,
            is_active=True,
        )
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.name == "Web Servers"
        assert category.description == "Web server stacks"
        assert category.icon == "web"
        assert category.sort_order == 1
        assert category.is_active is True
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_category_name_unique(self, db_session: Session):
        """Test that category names must be unique."""
        category1 = TemplateCategory(name="Unique Name", sort_order=1)
        category2 = TemplateCategory(name="Unique Name", sort_order=2)
        
        db_session.add(category1)
        db_session.commit()
        
        db_session.add(category2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestMarketplaceTemplate:
    """Test MarketplaceTemplate model."""

    def test_create_template(self, test_template: MarketplaceTemplate):
        """Test creating a marketplace template."""
        assert test_template.id is not None
        assert test_template.name == "Test Template"
        assert test_template.description == "A test template for testing purposes"
        assert test_template.version == "1.0.0"
        assert test_template.status == TemplateStatus.PENDING
        assert test_template.downloads == 0
        assert test_template.rating_avg == 0.0
        assert test_template.rating_count == 0
        assert test_template.tags == ["test", "nginx"]
        assert test_template.created_at is not None
        assert test_template.updated_at is not None

    def test_template_relationships(self, test_template: MarketplaceTemplate):
        """Test template relationships."""
        assert test_template.author is not None
        assert test_template.author.username.startswith("testuser_")
        assert test_template.category is not None
        assert test_template.category.name.startswith("Test Category")

    def test_template_status_enum(self, db_session: Session, test_user: User, test_category: TemplateCategory):
        """Test template status enum values."""
        # Test pending status
        template_pending = MarketplaceTemplate(
            name="Pending Template",
            description="A pending template",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx",
            status=TemplateStatus.PENDING,
        )
        db_session.add(template_pending)
        
        # Test approved status
        template_approved = MarketplaceTemplate(
            name="Approved Template",
            description="An approved template",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx",
            status=TemplateStatus.APPROVED,
        )
        db_session.add(template_approved)
        
        # Test rejected status
        template_rejected = MarketplaceTemplate(
            name="Rejected Template",
            description="A rejected template",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx",
            status=TemplateStatus.REJECTED,
        )
        db_session.add(template_rejected)
        
        db_session.commit()
        
        assert template_pending.status == TemplateStatus.PENDING
        assert template_approved.status == TemplateStatus.APPROVED
        assert template_rejected.status == TemplateStatus.REJECTED


class TestTemplateReview:
    """Test TemplateReview model."""

    def test_create_review(self, db_session: Session, test_template: MarketplaceTemplate, test_user: User):
        """Test creating a template review."""
        review = TemplateReview(
            template_id=test_template.id,
            user_id=test_user.id,
            rating=5,
            comment="Great template!",
        )
        db_session.add(review)
        db_session.commit()

        assert review.id is not None
        assert review.template_id == test_template.id
        assert review.user_id == test_user.id
        assert review.rating == 5
        assert review.comment == "Great template!"
        assert review.created_at is not None
        assert review.updated_at is not None

    def test_review_relationships(self, db_session: Session, test_template: MarketplaceTemplate, test_user: User):
        """Test review relationships."""
        review = TemplateReview(
            template_id=test_template.id,
            user_id=test_user.id,
            rating=4,
            comment="Good template",
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.template is not None
        assert review.template.name == "Test Template"
        assert review.user is not None
        assert review.user.username.startswith("testuser_")

    def test_review_rating_constraints(self, db_session: Session, test_template: MarketplaceTemplate, test_user: User):
        """Test review rating constraints."""
        # Valid ratings (1-5)
        for rating in [1, 2, 3, 4, 5]:
            review = TemplateReview(
                template_id=test_template.id,
                user_id=test_user.id,
                rating=rating,
            )
            db_session.add(review)
            db_session.commit()
            db_session.delete(review)  # Clean up for next iteration


class TestTemplateVersion:
    """Test TemplateVersion model."""

    def test_create_version(self, db_session: Session, test_template: MarketplaceTemplate):
        """Test creating a template version."""
        version = TemplateVersion(
            template_id=test_template.id,
            version_number="1.1.0",
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx:latest",
            changelog="Updated to latest nginx",
        )
        db_session.add(version)
        db_session.commit()

        assert version.id is not None
        assert version.template_id == test_template.id
        assert version.version_number == "1.1.0"
        assert version.changelog == "Updated to latest nginx"
        assert version.created_at is not None

    def test_version_relationship(self, db_session: Session, test_template: MarketplaceTemplate):
        """Test version relationship with template."""
        version = TemplateVersion(
            template_id=test_template.id,
            version_number="2.0.0",
            docker_compose_yaml="version: '3'\nservices:\n  test:\n    image: nginx:alpine",
        )
        db_session.add(version)
        db_session.commit()
        db_session.refresh(version)

        assert version.template is not None
        assert version.template.name == "Test Template"


class TestUserRelationships:
    """Test user relationships with marketplace models."""

    def test_user_authored_templates(self, test_template: MarketplaceTemplate, test_user: User):
        """Test user's authored templates relationship."""
        assert len(test_user.authored_templates) == 1
        assert test_user.authored_templates[0].name == "Test Template"

    def test_user_template_reviews(self, db_session: Session, test_template: MarketplaceTemplate, test_user: User):
        """Test user's template reviews relationship."""
        review = TemplateReview(
            template_id=test_template.id,
            user_id=test_user.id,
            rating=5,
            comment="Excellent!",
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(test_user)

        assert len(test_user.template_reviews) == 1
        assert test_user.template_reviews[0].rating == 5
