"""
Comprehensive tests for JWT authentication module.
"""

import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException, status

from app.auth.jwt import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_password_hash_and_verify_success(self):
        """Test successful password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_password_verify_failure(self):
        """Test password verification with wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_password_hash_different_each_time(self):
        """Test that password hashing produces different hashes each time."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_hash_empty_string(self):
        """Test password hashing with empty string."""
        password = ""
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True


class TestCreateAccessToken:
    """Test access token creation."""

    def test_create_access_token_success(self):
        """Test successful access token creation."""
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_access_token_with_custom_expiry(self):
        """Test access token creation with custom expiry."""
        data = {"sub": "123", "username": "testuser"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta

        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_time).total_seconds()) < 5

    def test_create_access_token_unique_jti(self):
        """Test that each access token has a unique JTI."""
        data = {"sub": "123", "username": "testuser"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        
        payload1 = jwt.decode(token1, SECRET_KEY, algorithms=[ALGORITHM])
        payload2 = jwt.decode(token2, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload1["jti"] != payload2["jti"]

    def test_create_access_token_data_copy(self):
        """Test that original data is not modified."""
        data = {"sub": "123", "username": "testuser"}
        original_data = data.copy()
        
        create_access_token(data)
        
        assert data == original_data


class TestCreateRefreshToken:
    """Test refresh token creation."""

    def test_create_refresh_token_success(self):
        """Test successful refresh token creation."""
        data = {"sub": "123", "username": "testuser"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_refresh_token_with_custom_expiry(self):
        """Test refresh token creation with custom expiry."""
        data = {"sub": "123", "username": "testuser"}
        expires_delta = timedelta(days=14)
        token = create_refresh_token(data, expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta

        # Allow 5 second tolerance for test execution time
        assert abs((exp_time - expected_time).total_seconds()) < 5

    def test_create_refresh_token_unique_jti(self):
        """Test that each refresh token has a unique JTI."""
        data = {"sub": "123", "username": "testuser"}
        token1 = create_refresh_token(data)
        token2 = create_refresh_token(data)
        
        payload1 = jwt.decode(token1, SECRET_KEY, algorithms=[ALGORITHM])
        payload2 = jwt.decode(token2, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload1["jti"] != payload2["jti"]

    def test_create_refresh_token_longer_expiry(self):
        """Test that refresh tokens have longer expiry than access tokens."""
        data = {"sub": "123", "username": "testuser"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        access_payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert refresh_payload["exp"] > access_payload["exp"]


class TestDecodeToken:
    """Test token decoding and validation."""

    def test_decode_token_success(self):
        """Test successful token decoding."""
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_token(token)

        # decode_token converts string sub to int
        assert payload["sub"] == 123
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_decode_token_expired(self):
        """Test decoding expired token."""
        data = {"sub": "123", "username": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has expired" in exc_info.value.detail

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in exc_info.value.detail

    def test_decode_token_malformed(self):
        """Test decoding malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(malformed_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in exc_info.value.detail

    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret."""
        data = {"sub": "123", "username": "testuser"}
        # Create token with different secret
        wrong_token = jwt.encode(data, "wrong_secret", algorithm=ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(wrong_token)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in exc_info.value.detail

    def test_decode_token_sub_string_to_int_conversion(self):
        """Test conversion of string sub to int."""
        # Create token with string sub
        data = {"sub": "123", "username": "testuser", "type": "access"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        payload = decode_token(token)
        
        assert payload["sub"] == 123
        assert isinstance(payload["sub"], int)

    def test_decode_token_sub_string_conversion_failure(self):
        """Test handling of non-numeric string sub (covers lines 130-131)."""
        # Create token with non-numeric string sub
        data = {"sub": "non_numeric_id", "username": "testuser", "type": "access"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        payload = decode_token(token)
        
        # Should keep as string when conversion fails
        assert payload["sub"] == "non_numeric_id"
        assert isinstance(payload["sub"], str)

    def test_decode_token_sub_already_int(self):
        """Test that integer sub remains unchanged."""
        # JWT library requires sub to be string, so we pass string and verify conversion
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload["sub"] == 123
        assert isinstance(payload["sub"], int)

    def test_decode_token_no_sub_field(self):
        """Test decoding token without sub field."""
        data = {"username": "testuser", "type": "access"}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        payload = decode_token(token)
        
        assert "sub" not in payload
        assert payload["username"] == "testuser"


class TestJWTConfiguration:
    """Test JWT configuration and constants."""

    def test_jwt_constants(self):
        """Test JWT configuration constants."""
        assert SECRET_KEY is not None
        assert ALGORITHM == "HS256"
        assert isinstance(SECRET_KEY, str)

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "test_secret"}):
            # Re-import to get updated environment variable
            from importlib import reload
            from app.auth import jwt as jwt_module
            reload(jwt_module)
            
            assert jwt_module.SECRET_KEY == "test_secret"


class TestIntegrationScenarios:
    """Test integration scenarios with multiple JWT operations."""

    def test_full_token_lifecycle(self):
        """Test complete token creation and validation lifecycle."""
        # Create user data
        user_data = {"sub": "123", "username": "testuser", "role": "user"}
        
        # Create access and refresh tokens
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        
        # Decode and verify both tokens
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        # Verify access token (decode_token converts string sub to int)
        assert access_payload["sub"] == 123
        assert access_payload["username"] == "testuser"
        assert access_payload["role"] == "user"
        assert access_payload["type"] == "access"

        # Verify refresh token (decode_token converts string sub to int)
        assert refresh_payload["sub"] == 123
        assert refresh_payload["username"] == "testuser"
        assert refresh_payload["role"] == "user"
        assert refresh_payload["type"] == "refresh"
        
        # Verify different expiry times
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_token_uniqueness_across_users(self):
        """Test that tokens are unique across different users."""
        user1_data = {"sub": "123", "username": "user1"}
        user2_data = {"sub": "456", "username": "user2"}
        
        token1 = create_access_token(user1_data)
        token2 = create_access_token(user2_data)
        
        assert token1 != token2
        
        payload1 = decode_token(token1)
        payload2 = decode_token(token2)
        
        assert payload1["sub"] != payload2["sub"]
        assert payload1["username"] != payload2["username"]
        assert payload1["jti"] != payload2["jti"]

    def test_password_and_token_integration(self):
        """Test integration between password hashing and token creation."""
        password = "securepassword123"
        hashed_password = get_password_hash(password)
        
        # Simulate successful login
        if verify_password(password, hashed_password):
            user_data = {"sub": "123", "username": "testuser"}
            token = create_access_token(user_data)
            payload = decode_token(token)
            
            # decode_token converts string sub to int
            assert payload["sub"] == 123
            assert payload["username"] == "testuser"
