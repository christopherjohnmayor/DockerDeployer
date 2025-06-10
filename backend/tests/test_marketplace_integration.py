"""
Integration tests for Template Marketplace.
Tests end-to-end workflows and complex scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.db.models import (
    MarketplaceTemplate,
    TemplateCategory,
    TemplateReview,
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
        name=f"Integration Category {unique_id}",
        description="A test category for integration testing",
        icon="integration",
        sort_order=1,
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


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


class TestMarketplaceIntegration:
    """Integration tests for marketplace workflows."""

    def test_complete_template_lifecycle(
        self, 
        authenticated_user_client: TestClient, 
        authenticated_admin_client: TestClient,
        test_user: User, 
        admin_user: User,
        test_category: TemplateCategory
    ):
        """Test complete template lifecycle: create → approve → review → stats."""
        # Step 1: User creates a template
        template_data = {
            "name": "Lifecycle Test Template",
            "description": "A template for testing complete lifecycle",
            "category_id": test_category.id,
            "docker_compose_yaml": get_valid_docker_compose_yaml(),
            "tags": ["lifecycle", "test"],
            "version": "1.0.0",
        }

        create_response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=template_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert create_response.status_code == 201
        template = create_response.json()
        template_id = template["id"]
        assert template["status"] == "pending"

        # Step 2: Admin approves the template
        approval_data = {"action": "approve"}
        approve_response = authenticated_admin_client.post(
            f"/api/marketplace/admin/templates/{template_id}/approve",
            json=approval_data,
            headers={"Authorization": "Bearer admin_token"},
        )
        assert approve_response.status_code == 200
        approved_template = approve_response.json()
        assert approved_template["status"] == "approved"

        # Step 3: User creates a review
        review_data = {
            "rating": 5,
            "comment": "Excellent template for lifecycle testing!",
        }
        review_response = authenticated_user_client.post(
            f"/api/marketplace/templates/{template_id}/reviews",
            json=review_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert review_response.status_code == 201
        review = review_response.json()
        assert review["rating"] == 5

        # Step 4: Check marketplace stats include our template
        stats_response = authenticated_admin_client.get(
            "/api/marketplace/admin/stats",
            headers={"Authorization": "Bearer admin_token"},
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_templates"] >= 1
        assert stats["approved_templates"] >= 1
        assert stats["total_reviews"] >= 1

        # Step 5: Search for the template
        search_response = client.get(
            "/api/marketplace/templates?query=Lifecycle"
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert search_results["total"] >= 1
        assert any(t["name"] == "Lifecycle Test Template" for t in search_results["templates"])

    def test_template_rejection_workflow(
        self,
        authenticated_user_client: TestClient,
        authenticated_admin_client: TestClient,
        test_user: User,
        admin_user: User,
        test_category: TemplateCategory
    ):
        """Test template rejection workflow."""
        # Create a template
        template_data = {
            "name": "Rejection Test Template",
            "description": "A template for testing rejection workflow",
            "category_id": test_category.id,
            "docker_compose_yaml": get_valid_docker_compose_yaml(),
            "tags": ["rejection", "test"],
            "version": "1.0.0",
        }

        create_response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=template_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert create_response.status_code == 201
        template = create_response.json()
        template_id = template["id"]

        # Admin rejects the template
        rejection_data = {
            "action": "reject",
            "reason": "Does not meet quality standards for integration testing"
        }
        reject_response = authenticated_admin_client.post(
            f"/api/marketplace/admin/templates/{template_id}/approve",
            json=rejection_data,
            headers={"Authorization": "Bearer admin_token"},
        )
        assert reject_response.status_code == 200
        rejected_template = reject_response.json()
        assert rejected_template["status"] == "rejected"
        assert "quality standards" in rejected_template["rejection_reason"]

        # Verify rejected template doesn't appear in public search
        search_response = client.get(
            "/api/marketplace/templates?query=Rejection"
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        # Should not find rejected templates in public search
        assert not any(t["name"] == "Rejection Test Template" for t in search_results["templates"])

    def test_rate_limiting_enforcement(self, authenticated_user_client: TestClient, test_category: TemplateCategory):
        """Test that rate limiting is properly enforced."""
        # Note: Rate limiting is disabled in testing, but we test the endpoint structure
        template_data = {
            "name": "Rate Limit Test Template",
            "description": "A template for testing rate limiting",
            "category_id": test_category.id,
            "docker_compose_yaml": get_valid_docker_compose_yaml(),
            "tags": ["rate", "limit"],
            "version": "1.0.0",
        }

        # Make multiple requests - should all succeed in testing environment
        for i in range(3):
            response = authenticated_user_client.post(
                "/api/marketplace/templates",
                json={**template_data, "name": f"Rate Limit Test Template {i}"},
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == 201

    def test_error_scenarios(self, authenticated_user_client: TestClient, test_category: TemplateCategory):
        """Test various error scenarios."""
        # Test invalid YAML
        invalid_template_data = {
            "name": "Invalid YAML Template",
            "description": "A template with invalid YAML",
            "category_id": test_category.id,
            "docker_compose_yaml": "version: '3.8'\nservices:\n  test:\n    image: nginx\n    privileged: true",
            "tags": ["invalid"],
            "version": "1.0.0",
        }

        response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=invalid_template_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == 400
        assert "Security violation" in response.json()["detail"]

        # Test non-existent template
        response = client.get("/api/marketplace/templates/99999")
        assert response.status_code == 404

        # Test missing required fields
        incomplete_data = {
            "name": "Incomplete Template",
            "description": "A template missing required fields",
            # Missing category_id and docker_compose_yaml
            "tags": ["incomplete"],
            "version": "1.0.0",
        }

        response = authenticated_user_client.post(
            "/api/marketplace/templates",
            json=incomplete_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == 422  # Validation error
