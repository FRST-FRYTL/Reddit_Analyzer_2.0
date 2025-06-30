"""Phase 4 Authentication API Tests."""

import pytest
import json
from unittest.mock import patch
from flask import Flask
from sqlalchemy.orm import Session

from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.api.auth import auth_bp
from reddit_analyzer.api.admin import admin_bp
from reddit_analyzer.utils.auth import get_auth_service, AuthTokenManager


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create test user."""
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

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user."""
        user = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
        )
        user.set_password("AdminPassword123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_user_registration_success(self, client, db_session):
        """Test successful user registration."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            response = client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "NewPassword123",
                },
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["username"] == "newuser"

    def test_user_registration_validation_error(self, client, db_session):
        """Test registration with validation errors."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            # Missing password
            response = client.post(
                "/api/auth/register",
                json={"username": "newuser", "email": "newuser@example.com"},
            )
            assert response.status_code == 400

            # Weak password
            response = client.post(
                "/api/auth/register",
                json={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "weak",
                },
            )
            assert response.status_code == 400

    def test_user_registration_duplicate(self, client, test_user, db_session):
        """Test registration with duplicate username."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            response = client.post(
                "/api/auth/register",
                json={
                    "username": "testuser",
                    "email": "duplicate@example.com",
                    "password": "Password123",
                },
            )

            assert response.status_code == 409
            data = json.loads(response.data)
            assert "already exists" in data["error"]

    def test_user_login_success(self, client, test_user, db_session):
        """Test successful user login."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "SecurePassword123"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["username"] == "testuser"

    def test_user_login_invalid_credentials(self, client, test_user, db_session):
        """Test login with invalid credentials."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "wrongpassword"},
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "Invalid credentials" in data["error"]

    def test_token_refresh_success(self, client, test_user, db_session):
        """Test successful token refresh."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            # First login to get refresh token
            login_response = client.post(
                "/api/auth/login",
                json={"username": "testuser", "password": "SecurePassword123"},
            )
            login_data = json.loads(login_response.data)
            refresh_token = login_data["refresh_token"]

            # Use refresh token
            response = client.post(
                "/api/auth/refresh", json={"refresh_token": refresh_token}
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "access_token" in data

    def test_token_refresh_invalid(self, client, db_session):
        """Test token refresh with invalid token."""
        with patch("app.api.auth.get_db") as mock_get_db:
            mock_get_db.return_value = [db_session]

            response = client.post(
                "/api/auth/refresh", json={"refresh_token": "invalid.token.here"}
            )

            assert response.status_code == 401

    def test_get_current_user_success(self, client, test_user, db_session):
        """Test getting current user with valid token."""
        with (
            patch("app.api.auth.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get access token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(test_user)

            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["user"]["username"] == "testuser"

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Missing authentication token" in data["error"]

    def test_change_password_success(self, client, test_user, db_session):
        """Test successful password change."""
        with (
            patch("app.api.auth.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get access token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(test_user)

            response = client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={
                    "current_password": "SecurePassword123",
                    "new_password": "NewSecurePassword456",
                },
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "Password changed successfully" in data["message"]

    def test_change_password_wrong_current(self, client, test_user, db_session):
        """Test password change with wrong current password."""
        with (
            patch("app.api.auth.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get access token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(test_user)

            response = client.post(
                "/api/auth/change-password",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={
                    "current_password": "wrongpassword",
                    "new_password": "NewSecurePassword456",
                },
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "Invalid current password" in data["error"]


class TestAdminAPI:
    """Test admin API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def admin_user(self, db_session: Session):
        """Create admin user."""
        user = User(
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            is_active=True,
        )
        user.set_password("AdminPassword123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def regular_user(self, db_session: Session):
        """Create regular user."""
        user = User(
            username="regular",
            email="regular@example.com",
            role=UserRole.USER,
            is_active=True,
        )
        user.set_password("RegularPassword123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    def test_list_users_admin_access(
        self, client, admin_user, regular_user, db_session
    ):
        """Test admin can list users."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "users" in data
            assert "pagination" in data
            assert len(data["users"]) >= 2  # admin + regular user

    def test_list_users_regular_user_denied(self, client, regular_user, db_session):
        """Test regular user cannot list users."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get regular user token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(regular_user)

            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert response.status_code == 403
            data = json.loads(response.data)
            assert "Insufficient permissions" in data["error"]

    def test_update_user_role_success(
        self, client, admin_user, regular_user, db_session
    ):
        """Test admin can update user role."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            response = client.put(
                f"/api/admin/users/{regular_user.id}/role",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={"role": "moderator"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["user"]["role"] == "moderator"

    def test_update_own_role_denied(self, client, admin_user, db_session):
        """Test admin cannot update their own role."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            response = client.put(
                f"/api/admin/users/{admin_user.id}/role",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={"role": "user"},
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Cannot modify your own role" in data["error"]

    def test_activate_user_success(self, client, admin_user, regular_user, db_session):
        """Test admin can activate/deactivate users."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            # Deactivate user
            response = client.put(
                f"/api/admin/users/{regular_user.id}/activate",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={"is_active": False},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "deactivated successfully" in data["message"]

            # Reactivate user
            response = client.put(
                f"/api/admin/users/{regular_user.id}/activate",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
                json={"is_active": True},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "activated successfully" in data["message"]

    def test_get_system_stats_success(self, client, admin_user, db_session):
        """Test getting system statistics."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            response = client.get(
                "/api/admin/stats",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "users" in data
            assert "content" in data
            assert "jobs" in data

    def test_health_check_success(self, client, admin_user, db_session):
        """Test health check endpoint."""
        with (
            patch("app.api.admin.get_db") as mock_get_db,
            patch("app.middleware.auth.get_db") as mock_middleware_db,
        ):
            mock_get_db.return_value = [db_session]
            mock_middleware_db.return_value = [db_session]

            # Get admin token
            auth_service = get_auth_service()
            tokens = auth_service.create_tokens(admin_user)

            response = client.get(
                "/api/admin/health",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["database"] == "connected"


@pytest.mark.security
class TestAuthSecurity:
    """Security-focused authentication tests."""

    def test_sql_injection_prevention(self, db_session):
        """Test SQL injection prevention in authentication."""
        auth_service = get_auth_service()

        # Attempt SQL injection in username
        malicious_username = "admin'; DROP TABLE users; --"

        user = auth_service.authenticate_user(
            malicious_username, "password", db_session
        )

        assert user is None
        # Database should still be intact
        users_count = db_session.query(User).count()
        assert users_count >= 0  # Table still exists

    def test_password_timing_attack_prevention(self, db_session):
        """Test password timing attack prevention."""
        auth_service = get_auth_service()

        # Test with non-existent user vs wrong password
        # Both should take similar time to prevent timing attacks
        import time

        # Non-existent user
        start_time = time.time()
        auth_service.authenticate_user("nonexistent", "password", db_session)
        time1 = time.time() - start_time

        # Create real user for comparison
        user = User(username="realuser", is_active=True)
        user.set_password("correctpassword")
        db_session.add(user)
        db_session.commit()

        # Real user, wrong password
        start_time = time.time()
        auth_service.authenticate_user("realuser", "wrongpassword", db_session)
        time2 = time.time() - start_time

        # Times should be reasonably similar (within 50% difference)
        time_ratio = max(time1, time2) / min(time1, time2)
        assert time_ratio < 1.5

    def test_token_secret_isolation(self):
        """Test that different token managers use different secrets."""
        manager1 = AuthTokenManager()
        manager2 = AuthTokenManager()

        user = User(username="testuser", role=UserRole.USER)
        user.id = 1

        token1 = manager1.create_access_token(user)

        # Token from manager1 should not be valid for manager2
        with pytest.raises(ValueError):
            manager2.verify_access_token(token1)

    def test_token_tampering_detection(self):
        """Test detection of tampered tokens."""
        token_manager = AuthTokenManager(secret_key="test-secret")
        user = User(username="testuser", role=UserRole.USER)
        user.id = 1

        token = token_manager.create_access_token(user)

        # Tamper with token
        tampered_token = token[:-10] + "tampereddd"

        with pytest.raises(ValueError, match="Invalid token"):
            token_manager.verify_access_token(tampered_token)

    def test_role_escalation_prevention(self, db_session):
        """Test prevention of role escalation attacks."""
        # Create regular user
        user = User(username="regularuser", role=UserRole.USER, is_active=True)
        db_session.add(user)
        db_session.commit()

        auth_service = get_auth_service()
        tokens = auth_service.create_tokens(user)

        # Verify token contains correct role
        payload = auth_service.token_manager.verify_access_token(tokens["access_token"])
        assert payload["role"] == "user"

        # Even if we manually modify user role in database,
        # existing tokens should not be elevated
        user.role = UserRole.ADMIN
        db_session.commit()

        # Token should still have original role
        payload = auth_service.token_manager.verify_access_token(tokens["access_token"])
        assert payload["role"] == "user"  # Original role preserved in token
