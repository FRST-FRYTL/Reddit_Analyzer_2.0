"""Phase 4 Authentication Tests."""

import pytest
import jwt
from unittest.mock import patch
from sqlalchemy.orm import Session

from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.utils.auth import AuthTokenManager, AuthService, get_auth_service
from reddit_analyzer.middleware.auth import extract_token_from_header


class TestUserModel:
    """Test User model authentication features."""

    def test_user_password_hashing(self, db_session: Session):
        """Test password hashing and verification."""
        user = User(username="testuser", email="test@example.com")
        password = "SecurePassword123"

        user.set_password(password)
        assert user.password_hash is not None
        assert user.password_hash != password
        assert user.verify_password(password) is True
        assert user.verify_password("wrongpassword") is False

    def test_user_roles(self, db_session: Session):
        """Test user role functionality."""
        user = User(username="testuser", role=UserRole.ADMIN)

        assert user.has_role(UserRole.ADMIN) is True
        assert user.has_role(UserRole.USER) is False
        assert user.is_admin() is True

        user.role = UserRole.USER
        assert user.is_admin() is False
        assert user.has_role(UserRole.USER) is True

    def test_user_model_defaults(self, db_session: Session):
        """Test user model default values."""
        user = User(username="testuser")

        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.comment_karma == 0
        assert user.link_karma == 0
        assert user.is_verified is False

    def test_user_repr(self, db_session: Session):
        """Test user string representation."""
        user = User(username="testuser", role=UserRole.ADMIN)
        user.id = 1

        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "admin" in repr_str
        assert "id=1" in repr_str


class TestAuthTokenManager:
    """Test JWT token management."""

    @pytest.fixture
    def token_manager(self):
        return AuthTokenManager(secret_key="test-secret")

    @pytest.fixture
    def test_user(self, db_session: Session):
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.id = 1
        return user

    def test_create_access_token(self, token_manager, test_user):
        """Test access token creation."""
        token = token_manager.create_access_token(test_user)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_create_refresh_token(self, token_manager, test_user):
        """Test refresh token creation."""
        token = token_manager.create_refresh_token(test_user)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"
        assert "username" not in payload
        assert "role" not in payload

    def test_verify_access_token(self, token_manager, test_user):
        """Test access token verification."""
        token = token_manager.create_access_token(test_user)
        payload = token_manager.verify_access_token(token)

        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"

    def test_verify_refresh_token(self, token_manager, test_user):
        """Test refresh token verification."""
        token = token_manager.create_refresh_token(test_user)
        payload = token_manager.verify_refresh_token(token)

        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_expired_token(self, token_manager, test_user):
        """Test expired token handling."""
        # Create token with very short expiry
        token_manager.access_token_expire_minutes = -1
        token = token_manager.create_access_token(test_user)

        with pytest.raises(ValueError, match="Token has expired"):
            token_manager.verify_access_token(token)

    def test_invalid_token(self, token_manager):
        """Test invalid token handling."""
        with pytest.raises(ValueError, match="Invalid token"):
            token_manager.verify_access_token("invalid.token.here")

    def test_wrong_token_type(self, token_manager, test_user):
        """Test wrong token type verification."""
        access_token = token_manager.create_access_token(test_user)
        refresh_token = token_manager.create_refresh_token(test_user)

        with pytest.raises(ValueError, match="Invalid token type"):
            token_manager.verify_refresh_token(access_token)

        with pytest.raises(ValueError, match="Invalid token type"):
            token_manager.verify_access_token(refresh_token)


class TestAuthService:
    """Test authentication service."""

    @pytest.fixture
    def auth_service(self):
        token_manager = AuthTokenManager(secret_key="test-secret")
        return AuthService(token_manager)

    @pytest.fixture
    def test_user(self, db_session: Session):
        user = User(
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password("SecurePassword123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_authenticate_user_success(self, auth_service, test_user, db_session):
        """Test successful user authentication."""
        user = auth_service.authenticate_user(
            "testuser", "SecurePassword123", db_session
        )

        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_wrong_password(
        self, auth_service, test_user, db_session
    ):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user("testuser", "wrongpassword", db_session)

        assert user is None

    def test_authenticate_user_not_found(self, auth_service, db_session):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user("nonexistent", "password", db_session)

        assert user is None

    def test_authenticate_inactive_user(self, auth_service, test_user, db_session):
        """Test authentication with inactive user."""
        test_user.is_active = False
        db_session.commit()

        user = auth_service.authenticate_user(
            "testuser", "SecurePassword123", db_session
        )

        assert user is None

    def test_create_tokens(self, auth_service, test_user):
        """Test token creation."""
        tokens = auth_service.create_tokens(test_user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"

    def test_refresh_access_token(self, auth_service, test_user, db_session):
        """Test access token refresh."""
        tokens = auth_service.create_tokens(test_user)
        refresh_token = tokens["refresh_token"]

        new_tokens = auth_service.refresh_access_token(refresh_token, db_session)

        assert "access_token" in new_tokens
        assert "token_type" in new_tokens
        assert new_tokens["token_type"] == "bearer"

    def test_get_current_user(self, auth_service, test_user, db_session):
        """Test getting current user from token."""
        tokens = auth_service.create_tokens(test_user)
        access_token = tokens["access_token"]

        user = auth_service.get_current_user(access_token, db_session)

        assert user is not None
        assert user.username == "testuser"

    def test_require_role(self, auth_service):
        """Test role requirement checking."""
        admin_user = User(username="admin", role=UserRole.ADMIN)
        mod_user = User(username="mod", role=UserRole.MODERATOR)
        regular_user = User(username="user", role=UserRole.USER)

        # Admin can access everything
        assert auth_service.require_role(admin_user, UserRole.USER) is True
        assert auth_service.require_role(admin_user, UserRole.MODERATOR) is True
        assert auth_service.require_role(admin_user, UserRole.ADMIN) is True

        # Moderator can access user and moderator
        assert auth_service.require_role(mod_user, UserRole.USER) is True
        assert auth_service.require_role(mod_user, UserRole.MODERATOR) is True
        assert auth_service.require_role(mod_user, UserRole.ADMIN) is False

        # User can only access user level
        assert auth_service.require_role(regular_user, UserRole.USER) is True
        assert auth_service.require_role(regular_user, UserRole.MODERATOR) is False
        assert auth_service.require_role(regular_user, UserRole.ADMIN) is False


class TestAuthMiddleware:
    """Test authentication middleware."""

    def test_extract_token_from_header(self):
        """Test token extraction from Authorization header."""
        with patch("app.middleware.auth.request") as mock_request:
            # Valid bearer token
            mock_request.headers.get.return_value = "Bearer abc123token"
            token = extract_token_from_header()
            assert token == "abc123token"

            # No authorization header
            mock_request.headers.get.return_value = None
            token = extract_token_from_header()
            assert token is None

            # Invalid format
            mock_request.headers.get.return_value = "InvalidFormat"
            token = extract_token_from_header()
            assert token is None

            # Wrong scheme
            mock_request.headers.get.return_value = "Basic abc123token"
            token = extract_token_from_header()
            assert token is None


class TestAuthIntegration:
    """Integration tests for authentication system."""

    @pytest.fixture
    def auth_service(self):
        return get_auth_service("test-secret")

    @pytest.fixture
    def test_user(self, db_session: Session):
        user = User(
            username="integrationuser",
            email="integration@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password("IntegrationTest123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_full_auth_flow(self, auth_service, test_user, db_session):
        """Test complete authentication flow."""
        # 1. Authenticate user
        user = auth_service.authenticate_user(
            "integrationuser", "IntegrationTest123", db_session
        )
        assert user is not None

        # 2. Create tokens
        tokens = auth_service.create_tokens(user)
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # 3. Verify access token
        current_user = auth_service.get_current_user(tokens["access_token"], db_session)
        assert current_user.username == "integrationuser"

        # 4. Refresh token
        new_tokens = auth_service.refresh_access_token(
            tokens["refresh_token"], db_session
        )
        assert "access_token" in new_tokens

        # 5. Verify new access token
        user_from_new_token = auth_service.get_current_user(
            new_tokens["access_token"], db_session
        )
        assert user_from_new_token.username == "integrationuser"

    def test_security_scenarios(self, auth_service, test_user, db_session):
        """Test security edge cases."""
        # Test with deactivated user
        test_user.is_active = False
        db_session.commit()

        user = auth_service.authenticate_user(
            "integrationuser", "IntegrationTest123", db_session
        )
        assert user is None

        # Reactivate for token tests
        test_user.is_active = True
        db_session.commit()

        tokens = auth_service.create_tokens(test_user)

        # Deactivate user after token creation
        test_user.is_active = False
        db_session.commit()

        # Token should not work for inactive user
        current_user = auth_service.get_current_user(tokens["access_token"], db_session)
        assert current_user is None


@pytest.mark.performance
class TestAuthPerformance:
    """Performance tests for authentication system."""

    def test_password_hashing_performance(self, db_session: Session):
        """Test password hashing performance."""
        user = User(username="perfuser")

        import time

        start_time = time.time()
        user.set_password("TestPassword123")
        hash_time = time.time() - start_time

        # Hashing should take reasonable time (< 1 second)
        assert hash_time < 1.0

    def test_token_operations_performance(self):
        """Test token creation and verification performance."""
        token_manager = AuthTokenManager()
        user = User(username="perfuser", role=UserRole.USER)
        user.id = 1

        import time

        # Test token creation
        start_time = time.time()
        for _ in range(100):
            token_manager.create_access_token(user)
        creation_time = time.time() - start_time

        # Should create 100 tokens quickly
        assert creation_time < 1.0

        # Test token verification
        token = token_manager.create_access_token(user)
        start_time = time.time()
        for _ in range(100):
            token_manager.verify_access_token(token)
        verification_time = time.time() - start_time

        # Should verify 100 tokens quickly
        assert verification_time < 1.0
