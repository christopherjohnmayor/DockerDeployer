"""
Tests for marketplace API router.
"""

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.db.models import (
    MarketplaceTemplate,
    TemplateCategory,
    TemplateStatus,
    User,
    UserRole,
)
from app.main import app
from tests.conftest import TestingSessionLocal, override_get_db

# Override the get_db dependency
from app.db.database import get_db
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


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
def auth_headers():
    """Create authentication headers for testing."""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def authenticated_user_client(test_user: User):
    """Create a test client with authenticated user."""
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    # Clean up
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def authenticated_admin_client(admin_user: User):
    """Create a test client with authenticated admin user."""
    def override_get_current_user():
        return admin_user

    def override_require_admin():
        return admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_admin] = override_require_admin
    yield TestClient(app)
    # Clean up
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if require_admin in app.dependency_overrides:
        del app.dependency_overrides[require_admin]


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


class TestMarketplaceRouter:
    """Test marketplace API endpoints."""

    def test_create_template(self, authenticated_user_client: TestClient, test_user: User, test_category: TemplateCategory):
        """Test creating a new template."""
        template_data = {
            "name": "Test Template",
            "description": "A test template for API testing",
            "category_id": test_category.id,
            "docker_compose_yaml": get_valid_docker_compose_yaml(),
            "tags": ["test", "api"],
            "version": "1.0.0",
        }

        response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=template_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Template"
        assert data["status"] == "pending"
        assert data["author_id"] == test_user.id

    def test_create_template_invalid_yaml(self, authenticated_user_client: TestClient, test_user: User, test_category: TemplateCategory):
        """Test creating a template with invalid YAML."""
        template_data = {
            "name": "Invalid Template",
            "description": "A template with invalid YAML",
            "category_id": test_category.id,
            "docker_compose_yaml": "version: '3.8'\nservices:\n  test:\n    image: nginx\n    privileged: true\n    ports:\n      - '80:80'",
            "tags": ["invalid"],
            "version": "1.0.0",
        }

        response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=template_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        assert "Security violation" in response.json()["detail"]

    def test_create_template_unauthorized(self, test_category: TemplateCategory):
        """Test creating a template without authentication."""
        template_data = {
            "name": "Unauthorized Template",
            "description": "A template without auth",
            "category_id": test_category.id,
            "docker_compose_yaml": get_valid_docker_compose_yaml(),
        }

        response = client.post("/api/marketplace/templates", json=template_data)

        assert response.status_code == 401

    def test_search_templates(self, test_category: TemplateCategory, test_user: User, db_session: Session):
        """Test searching templates."""
        # Create some approved templates
        for i in range(3):
            template = MarketplaceTemplate(
                name=f"Search Template {i}",
                description=f"Template for search testing {i}",
                author_id=test_user.id,
                category_id=test_category.id,
                docker_compose_yaml=get_valid_docker_compose_yaml(),
                status=TemplateStatus.APPROVED,
                tags=[f"search{i}", "test"],
            )
            db_session.add(template)
        db_session.commit()

        response = client.get("/api/marketplace/templates?query=Search")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_search_templates_with_filters(self, test_category: TemplateCategory):
        """Test searching templates with filters."""
        response = client.get(
            f"/api/marketplace/templates?category_id={test_category.id}&min_rating=4.0&sort_by=rating_avg&sort_order=desc"
        )

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total" in data

    def test_get_template(self, test_user: User, test_category: TemplateCategory, db_session: Session):
        """Test getting a specific template."""
        # Create a template
        template = MarketplaceTemplate(
            name="Get Template Test",
            description="Template for get testing",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.APPROVED,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.get(f"/api/marketplace/templates/{template.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == "Get Template Test"

    def test_get_nonexistent_template(self):
        """Test getting a non-existent template."""
        response = client.get("/api/marketplace/templates/99999")

        assert response.status_code == 404

    def test_update_template(self, authenticated_user_client: TestClient, test_user: User, test_category: TemplateCategory, db_session: Session):
        """Test updating a template."""
        # Create a template
        template = MarketplaceTemplate(
            name="Update Template Test",
            description="Template for update testing",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.PENDING,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description",
        }

        response = authenticated_user_client.put(
            f"/api/marketplace/templates/{template.id}",
            json=update_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"

    def test_delete_template(self, authenticated_user_client: TestClient, test_user: User, test_category: TemplateCategory, db_session: Session):
        """Test deleting a template."""
        # Create a template
        template = MarketplaceTemplate(
            name="Delete Template Test",
            description="Template for delete testing",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.PENDING,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = authenticated_user_client.delete(
            f"/api/marketplace/templates/{template.id}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 204

    def test_create_review(self, authenticated_user_client: TestClient, test_user: User, test_category: TemplateCategory, db_session: Session):
        """Test creating a review for a template."""
        # Create an approved template
        template = MarketplaceTemplate(
            name="Review Template Test",
            description="Template for review testing",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.APPROVED,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        review_data = {
            "rating": 5,
            "comment": "Excellent template!",
        }

        response = authenticated_user_client.post(
            f"/api/marketplace/templates/{template.id}/reviews",
            json=review_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent template!"

    def test_get_categories(self, test_category: TemplateCategory):
        """Test getting template categories."""
        response = client.get("/api/marketplace/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Check that our test category is in the response
        category_names = [cat["name"] for cat in data]
        assert test_category.name in category_names

    def test_get_pending_templates_admin(self, authenticated_admin_client: TestClient, test_category: TemplateCategory, test_user: User, db_session: Session):
        """Test getting pending templates (admin only)."""
        # Create a pending template
        template = MarketplaceTemplate(
            name="Pending Template",
            description="Template pending approval",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.PENDING,
        )
        db_session.add(template)
        db_session.commit()

        response = authenticated_admin_client.get(
            "/api/marketplace/admin/pending"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_approve_template_admin(self, authenticated_admin_client: TestClient, test_category: TemplateCategory, test_user: User, db_session: Session):
        """Test approving a template (admin only)."""
        # Create a pending template
        template = MarketplaceTemplate(
            name="Approval Template",
            description="Template for approval testing",
            author_id=test_user.id,
            category_id=test_category.id,
            docker_compose_yaml=get_valid_docker_compose_yaml(),
            status=TemplateStatus.PENDING,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        approval_data = {"action": "approve"}

        response = authenticated_admin_client.post(
            f"/api/marketplace/admin/templates/{template.id}/approve",
            json=approval_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_get_marketplace_stats_admin(self, authenticated_admin_client: TestClient):
        """Test getting marketplace statistics (admin only)."""
        response = authenticated_admin_client.get(
            "/api/marketplace/admin/stats"
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_templates" in data
        assert "approved_templates" in data
        assert "pending_templates" in data
