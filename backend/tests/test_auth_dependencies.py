"""
Comprehensive tests for authentication dependencies.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status, WebSocket, WebSocketException
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
    require_admin,
    get_current_active_user,
    get_current_admin_user,
    get_current_user_websocket,
    oauth2_scheme
)
from app.db.models import User, UserRole
from tests.conftest import TestingSessionLocal, override_get_db


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    def test_get_current_user_success(self):
        """Test successful user retrieval with valid token."""
        # Mock token and database session
        mock_token = "valid_token"
        mock_db = MagicMock(spec=Session)

        # Mock user object
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.role = UserRole.USER

        # Mock database query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            result = get_current_user(token=mock_token, db=mock_db)

            assert result == mock_user
            mock_decode.assert_called_once_with(mock_token)
            mock_db.query.assert_called_once_with(User)

    def test_get_current_user_invalid_token_type(self):
        """Test user retrieval with invalid token type."""
        mock_token = "invalid_token"
        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "refresh"}  # Wrong type

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token=mock_token, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_no_user_id(self):
        """Test user retrieval when token has no user ID."""
        mock_token = "token_without_user_id"
        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"type": "access"}  # No 'sub' field

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token=mock_token, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_decode_exception(self):
        """Test user retrieval when token decoding fails."""
        mock_token = "malformed_token"
        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Token decode error")

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token=mock_token, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_not_found(self):
        """Test user retrieval when user doesn't exist in database."""
        mock_token = "valid_token"
        mock_db = MagicMock(spec=Session)

        # Mock database query returning None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 999, "type": "access"}

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token=mock_token, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_inactive(self):
        """Test user retrieval when user is inactive."""
        mock_token = "valid_token"
        mock_db = MagicMock(spec=Session)

        # Mock inactive user
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = False

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(token=mock_token, db=mock_db)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Inactive user" in exc_info.value.detail


class TestRequireAdmin:
    """Test require_admin dependency."""

    def test_require_admin_success(self):
        """Test successful admin requirement check."""
        mock_user = MagicMock(spec=User)
        mock_user.role = UserRole.ADMIN

        result = require_admin(current_user=mock_user)
        assert result == mock_user

    def test_require_admin_not_admin(self):
        """Test admin requirement check with non-admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.role = UserRole.USER

        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""

    def test_get_current_active_user_success(self):
        """Test successful active user retrieval."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = True

        result = get_current_active_user(current_user=mock_user)
        assert result == mock_user

    def test_get_current_active_user_inactive(self):
        """Test active user retrieval with inactive user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in exc_info.value.detail


class TestGetCurrentAdminUser:
    """Test get_current_admin_user dependency."""

    def test_get_current_admin_user_success(self):
        """Test successful admin user retrieval."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = True
        mock_user.role = UserRole.ADMIN

        result = get_current_admin_user(current_user=mock_user)
        assert result == mock_user

    def test_get_current_admin_user_inactive(self):
        """Test admin user retrieval with inactive user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = False
        mock_user.role = UserRole.ADMIN

        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in exc_info.value.detail

    def test_get_current_admin_user_not_admin(self):
        """Test admin user retrieval with non-admin user."""
        mock_user = MagicMock(spec=User)
        mock_user.is_active = True
        mock_user.role = UserRole.USER

        with pytest.raises(HTTPException) as exc_info:
            get_current_admin_user(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail


class TestGetCurrentUserWebSocket:
    """Test get_current_user_websocket dependency."""

    @pytest.mark.asyncio
    async def test_websocket_auth_success_query_param(self):
        """Test successful WebSocket authentication with query parameter token."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "valid_token"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            result = await get_current_user_websocket(
                websocket=mock_websocket,
                token=None,
                db=mock_db
            )

            assert result == mock_user
            mock_decode.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_websocket_auth_success_header(self):
        """Test successful WebSocket authentication with header token."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = None
        mock_websocket.headers.get.return_value = "Bearer valid_token"

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            result = await get_current_user_websocket(
                websocket=mock_websocket,
                token=None,
                db=mock_db
            )

            assert result == mock_user
            mock_decode.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_websocket_auth_success_direct_token(self):
        """Test successful WebSocket authentication with direct token parameter."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            result = await get_current_user_websocket(
                websocket=mock_websocket,
                token="direct_token",
                db=mock_db
            )

            assert result == mock_user
            mock_decode.assert_called_once_with("direct_token")

    @pytest.mark.asyncio
    async def test_websocket_auth_no_token(self):
        """Test WebSocket authentication failure when no token provided."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = None
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)

        with pytest.raises(WebSocketException) as exc_info:
            await get_current_user_websocket(
                websocket=mock_websocket,
                token=None,
                db=mock_db
            )

        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
        assert "Missing authentication token" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_invalid_token_type(self):
        """Test WebSocket authentication failure with invalid token type."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "invalid_token"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "refresh"}  # Wrong type

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_websocket(
                    websocket=mock_websocket,
                    token=None,
                    db=mock_db
                )

            assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
            assert "Invalid token type" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_no_user_id(self):
        """Test WebSocket authentication failure when token has no user ID."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "token_without_user_id"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"type": "access"}  # No 'sub' field

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_websocket(
                    websocket=mock_websocket,
                    token=None,
                    db=mock_db
                )

            assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
            assert "Invalid token payload" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_user_not_found(self):
        """Test WebSocket authentication failure when user not found."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "valid_token"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)

        # Mock database query returning None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 999, "type": "access"}

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_websocket(
                    websocket=mock_websocket,
                    token=None,
                    db=mock_db
                )

            assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
            assert "User not found" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_inactive_user(self):
        """Test WebSocket authentication failure with inactive user."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "valid_token"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = False

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_websocket(
                    websocket=mock_websocket,
                    token=None,
                    db=mock_db
                )

            assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
            assert "Inactive user" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_decode_exception(self):
        """Test WebSocket authentication failure when token decoding fails."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = "malformed_token"
        mock_websocket.headers.get.return_value = None

        mock_db = MagicMock(spec=Session)

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Token decode error")

            with pytest.raises(WebSocketException) as exc_info:
                await get_current_user_websocket(
                    websocket=mock_websocket,
                    token=None,
                    db=mock_db
                )

            assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
            assert "Authentication failed" in exc_info.value.reason

    @pytest.mark.asyncio
    async def test_websocket_auth_malformed_header(self):
        """Test WebSocket authentication with malformed authorization header."""
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.query_params.get.return_value = None
        mock_websocket.headers.get.return_value = "InvalidHeader"  # Not "Bearer ..."

        mock_db = MagicMock(spec=Session)

        with pytest.raises(WebSocketException) as exc_info:
            await get_current_user_websocket(
                websocket=mock_websocket,
                token=None,
                db=mock_db
            )

        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
        assert "Missing authentication token" in exc_info.value.reason


class TestOAuth2Scheme:
    """Test OAuth2 scheme configuration."""

    def test_oauth2_scheme_configuration(self):
        """Test OAuth2 scheme is properly configured."""
        assert oauth2_scheme is not None
        # Check the correct path for FastAPI OAuth2PasswordBearer
        assert hasattr(oauth2_scheme, 'model')
        assert hasattr(oauth2_scheme.model, 'flows')
        assert hasattr(oauth2_scheme.model.flows, 'password')
        assert oauth2_scheme.model.flows.password.tokenUrl == "/auth/login"


class TestIntegrationScenarios:
    """Test integration scenarios with multiple dependencies."""

    def test_admin_endpoint_flow(self):
        """Test complete admin endpoint authentication flow."""
        # Mock token and database session
        mock_token = "admin_token"
        mock_db = MagicMock(spec=Session)

        # Mock admin user
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.role = UserRole.ADMIN

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 1, "type": "access"}

            # Test the complete flow: get_current_user -> require_admin
            current_user = get_current_user(token=mock_token, db=mock_db)
            admin_user = require_admin(current_user=current_user)

            assert admin_user == mock_user
            assert admin_user.role == UserRole.ADMIN

    def test_user_endpoint_flow(self):
        """Test complete user endpoint authentication flow."""
        # Mock token and database session
        mock_token = "user_token"
        mock_db = MagicMock(spec=Session)

        # Mock regular user
        mock_user = MagicMock(spec=User)
        mock_user.id = 2
        mock_user.is_active = True
        mock_user.role = UserRole.USER

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        with patch('app.auth.dependencies.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": 2, "type": "access"}

            # Test the complete flow: get_current_user -> get_current_active_user
            current_user = get_current_user(token=mock_token, db=mock_db)
            active_user = get_current_active_user(current_user=current_user)

            assert active_user == mock_user
            assert active_user.is_active is True

    def test_admin_access_denied_for_regular_user(self):
        """Test admin access is denied for regular users."""
        # Mock regular user
        mock_user = MagicMock(spec=User)
        mock_user.id = 2
        mock_user.is_active = True
        mock_user.role = UserRole.USER

        # Should raise exception when trying to access admin endpoint
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=mock_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail
