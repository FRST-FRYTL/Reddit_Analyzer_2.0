"""CLI Authentication manager."""

import os
import json
import typer
from pathlib import Path
from typing import Optional
from functools import wraps
from rich.console import Console

from reddit_analyzer.utils.auth import get_auth_service
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.database import get_db

console = Console()


class CLIAuth:
    """CLI Authentication manager."""

    def __init__(self):
        self.config_dir = Path.home() / ".reddit-analyzer"
        self.token_file = self.config_dir / "tokens.json"
        self.config_dir.mkdir(exist_ok=True)
        self.auth_service = get_auth_service()

    def login(self, username: str, password: str) -> bool:
        """Authenticate user and store tokens."""
        try:
            db = next(get_db())
            user = self.auth_service.authenticate_user(username, password, db)

            if user:
                tokens = self.auth_service.create_tokens(user)
                self._store_tokens(tokens)
                console.print(
                    f"✅ Logged in as {user.username} ({user.role.value})",
                    style="green",
                )
                return True
            else:
                console.print("❌ Invalid credentials", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Login failed: {e}", style="red")
            return False
        finally:
            db.close()

    def logout(self) -> bool:
        """Logout and remove stored tokens."""
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            console.print("👋 Logged out successfully", style="green")
            return True
        except Exception as e:
            console.print(f"❌ Logout failed: {e}", style="red")
            return False

    def _store_tokens(self, tokens: dict):
        """Securely store authentication tokens."""
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)
        os.chmod(self.token_file, 0o600)  # Read/write for owner only

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user."""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, "r") as f:
                tokens = json.load(f)

            db = next(get_db())
            user = self.auth_service.get_current_user(tokens["access_token"], db)
            return user
        except Exception:
            return None
        finally:
            if "db" in locals():
                db.close()

    def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, "r") as f:
                tokens = json.load(f)
            return tokens.get("access_token")
        except Exception:
            return None

    def get_stored_tokens(self) -> Optional[dict]:
        """Get stored authentication tokens."""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def require_auth(self, required_role: UserRole = None):
        """Decorator to require authentication for CLI commands."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check if we have tokens first
                tokens = self.get_stored_tokens()
                if not tokens:
                    console.print(
                        "❌ Authentication required. Run 'reddit-analyzer auth login'",
                        style="red",
                    )
                    raise typer.Exit(1)

                user = self.get_current_user()
                if not user:
                    console.print(
                        "❌ Authentication required. Run 'reddit-analyzer auth login'",
                        style="red",
                    )
                    raise typer.Exit(1)

                if required_role and not self.auth_service.require_role(
                    user, required_role
                ):
                    console.print(
                        f"❌ {required_role.value} role required", style="red"
                    )
                    raise typer.Exit(1)

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def auth_status(self):
        """Display current authentication status."""
        user = self.get_current_user()

        if user:
            console.print(
                f"👤 Logged in as: {user.username} ({user.role.value})", style="green"
            )

            # Check token expiry if possible
            try:
                with open(self.token_file, "r") as f:
                    json.load(f)  # Just verify file is valid JSON
                console.print("🔑 Session: Active", style="green")
            except Exception:
                console.print("🔑 Session: Error reading token", style="yellow")
        else:
            console.print("🔐 Status: Not authenticated", style="yellow")
            console.print(
                "💡 Use 'reddit-analyzer auth login' to authenticate", style="dim"
            )


# Global auth instance
cli_auth = CLIAuth()

# Export require_auth at module level for easier imports
require_auth = cli_auth.require_auth

# Export get_stored_tokens at module level for easier imports
get_stored_tokens = cli_auth.get_stored_tokens
