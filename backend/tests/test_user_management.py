"""
Tests for User Management admin operations.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.user_management import (
    activate_user,
    deactivate_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)
from app.auth.models import UserUpdateAdmin
from app.db.models import User as UserModel, UserRole


class TestUserManagement:
    """Test suite for User Management admin operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def admin_user(self):
        """Create a mock admin user."""
        user = MagicMock(spec=UserModel)
        user.id = 1
        user.username = "admin"
        user.email = "admin@example.com"
        user.role = UserRole.ADMIN
        user.is_active = True
        return user

    @pytest.fixture
    def regular_user(self):
        """Create a mock regular user."""
        user = MagicMock(spec=UserModel)
        user.id = 2
        user.username = "user"
        user.email = "user@example.com"
        user.role = UserRole.USER
        user.is_active = True
        return user

    def test_list_users_success(self, mock_db, admin_user, regular_user):
        """Test successful user listing."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            admin_user,
            regular_user,
        ]
        mock_db.query.return_value = mock_query

        # Test
        result = list_users(skip=0, limit=100, current_user=admin_user, db=mock_db)

        # Assertions
        assert len(result) == 2
        assert result[0] == admin_user
        assert result[1] == regular_user
        mock_db.query.assert_called_once_with(UserModel)
        mock_query.offset.assert_called_once_with(0)
        mock_query.offset.return_value.limit.assert_called_once_with(100)

    def test_list_users_with_pagination(self, mock_db, admin_user):
        """Test user listing with pagination."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [admin_user]
        mock_db.query.return_value = mock_query

        # Test
        result = list_users(skip=10, limit=5, current_user=admin_user, db=mock_db)

        # Assertions
        assert len(result) == 1
        mock_query.offset.assert_called_once_with(10)
        mock_query.offset.return_value.limit.assert_called_once_with(5)

    def test_get_user_success(self, mock_db, admin_user, regular_user):
        """Test successful user retrieval."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        # Test
        result = get_user(user_id=2, current_user=admin_user, db=mock_db)

        # Assertions
        assert result == regular_user
        mock_db.query.assert_called_once_with(UserModel)

    def test_get_user_not_found(self, mock_db, admin_user):
        """Test user retrieval when user not found."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            get_user(user_id=999, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    @patch("app.auth.user_management.get_password_hash")
    def test_update_user_success(self, mock_hash, mock_db, admin_user, regular_user):
        """Test successful user update."""
        # Setup mock
        mock_hash.return_value = "hashed_new_password"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        # Mock email check query
        mock_email_query = MagicMock()
        mock_email_query.filter.return_value.first.return_value = None
        mock_db.query.side_effect = [mock_query, mock_email_query]

        user_update = UserUpdateAdmin(
            email="newemail@example.com",
            full_name="New Name",
            password="NewPassword123!",
            role=UserRole.USER,
            is_active=True,
        )

        # Test
        result = update_user(
            user_id=2, user_update=user_update, current_user=admin_user, db=mock_db
        )

        # Assertions
        assert result == regular_user
        mock_hash.assert_called_once_with("NewPassword123!")
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(regular_user)

    def test_update_user_not_found(self, mock_db, admin_user):
        """Test user update when user not found."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        user_update = UserUpdateAdmin(email="newemail@example.com")

        # Test
        with pytest.raises(HTTPException) as exc_info:
            update_user(
                user_id=999, user_update=user_update, current_user=admin_user, db=mock_db
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    def test_update_user_cannot_deactivate_self(self, mock_db, admin_user):
        """Test admin cannot deactivate their own account."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = admin_user
        mock_db.query.return_value = mock_query

        user_update = UserUpdateAdmin(is_active=False)

        # Test
        with pytest.raises(HTTPException) as exc_info:
            update_user(
                user_id=1, user_update=user_update, current_user=admin_user, db=mock_db
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot deactivate your own account"

    def test_update_user_cannot_change_own_role(self, mock_db, admin_user):
        """Test admin cannot change their own role."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = admin_user
        mock_db.query.return_value = mock_query

        user_update = UserUpdateAdmin(role=UserRole.USER)

        # Test
        with pytest.raises(HTTPException) as exc_info:
            update_user(
                user_id=1, user_update=user_update, current_user=admin_user, db=mock_db
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot change your own role"

    def test_update_user_invalid_role(self, mock_db, admin_user, regular_user):
        """Test user update with invalid role."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        user_update = UserUpdateAdmin(role="invalid_role")

        # Test
        with pytest.raises(HTTPException) as exc_info:
            update_user(
                user_id=2, user_update=user_update, current_user=admin_user, db=mock_db
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid role. Must be 'admin' or 'user'"

    def test_update_user_email_already_exists(self, mock_db, admin_user, regular_user):
        """Test user update with email that already exists."""
        # Setup mock for user lookup
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        
        # Setup mock for email check - return existing user
        existing_user = MagicMock(spec=UserModel)
        existing_user.id = 3
        mock_email_query = MagicMock()
        mock_email_query.filter.return_value.first.return_value = existing_user
        
        mock_db.query.side_effect = [mock_query, mock_email_query]

        user_update = UserUpdateAdmin(email="existing@example.com")

        # Test
        with pytest.raises(HTTPException) as exc_info:
            update_user(
                user_id=2, user_update=user_update, current_user=admin_user, db=mock_db
            )

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Email already registered"

    def test_delete_user_success(self, mock_db, admin_user, regular_user):
        """Test successful user deletion."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        # Test
        result = delete_user(user_id=2, current_user=admin_user, db=mock_db)

        # Assertions
        assert result == {"message": "User deleted successfully"}
        mock_db.delete.assert_called_once_with(regular_user)
        mock_db.commit.assert_called_once()

    def test_delete_user_not_found(self, mock_db, admin_user):
        """Test user deletion when user not found."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            delete_user(user_id=999, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    def test_delete_user_cannot_delete_self(self, mock_db, admin_user):
        """Test admin cannot delete their own account."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = admin_user
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            delete_user(user_id=1, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot delete your own account"

    def test_activate_user_success(self, mock_db, admin_user, regular_user):
        """Test successful user activation."""
        # Setup mock
        regular_user.is_active = False
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        # Test
        result = activate_user(user_id=2, current_user=admin_user, db=mock_db)

        # Assertions
        assert result == {"message": "User activated successfully"}
        assert regular_user.is_active is True
        mock_db.commit.assert_called_once()

    def test_activate_user_not_found(self, mock_db, admin_user):
        """Test user activation when user not found."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            activate_user(user_id=999, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    def test_deactivate_user_success(self, mock_db, admin_user, regular_user):
        """Test successful user deactivation."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = regular_user
        mock_db.query.return_value = mock_query

        # Test
        result = deactivate_user(user_id=2, current_user=admin_user, db=mock_db)

        # Assertions
        assert result == {"message": "User deactivated successfully"}
        assert regular_user.is_active is False
        mock_db.commit.assert_called_once()

    def test_deactivate_user_not_found(self, mock_db, admin_user):
        """Test user deactivation when user not found."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            deactivate_user(user_id=999, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    def test_deactivate_user_cannot_deactivate_self(self, mock_db, admin_user):
        """Test admin cannot deactivate their own account."""
        # Setup mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = admin_user
        mock_db.query.return_value = mock_query

        # Test
        with pytest.raises(HTTPException) as exc_info:
            deactivate_user(user_id=1, current_user=admin_user, db=mock_db)

        # Assertions
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot deactivate your own account"
