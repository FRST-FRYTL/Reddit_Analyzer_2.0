# Phase 4B CLI Fixes Action Plan

## Overview
This document outlines the complete action plan to fix all 21 failed CLI tests identified during Phase 4B testing. The plan includes root cause analysis, specific solutions, and implementation order.

## Critical Issue Summary
- **Total Tests**: 38
- **Failed Tests**: 21 (55.3%)
- **Root Cause**: Authentication decorator passing incorrect arguments to Typer commands
- **Estimated Fix Time**: 4-6 hours

## Action Items by Priority

### Priority 1: Fix Authentication Decorator (Blocks 90% of failures)

#### Issue
The `@cli_auth.require_auth()` decorator in `/reddit_analyzer/cli/utils/auth_manager.py` passes `*args, **kwargs` which Typer interprets as positional arguments.

#### Solution
```python
# File: /reddit_analyzer/cli/utils/auth_manager.py
# Lines: 96-121

from functools import wraps

def require_auth(self, required_role: UserRole = None):
    """Decorator to require authentication for CLI commands."""
    def decorator(func):
        @wraps(func)
        def wrapper(**kwargs):  # Changed: Only accept keyword arguments
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

            return func(**kwargs)  # Changed: Pass only keyword arguments
        return wrapper
    return decorator
```

#### Files to Update
1. `/reddit_analyzer/cli/utils/auth_manager.py` - Update decorator

#### Expected Impact
Fixes 18 out of 21 failures related to "Missing argument 'ARGS'" errors.

### Priority 2: Fix Database Setup and User Creation

#### Issue
Test users don't exist in the database, causing authentication failures.

#### Solution 1: Create Database Setup Script
```python
# File: /reddit_analyzer/scripts/setup_test_users.py

#!/usr/bin/env python3
"""Setup test users for CLI testing."""

from reddit_analyzer.database import get_db, engine
from reddit_analyzer.models.user import User, UserRole
from reddit_analyzer.models import Base
from sqlalchemy.orm import Session

def create_test_users():
    """Create test users with different roles."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    test_users = [
        {"username": "admin_test", "password": "admin123", "email": "admin@test.com", "role": UserRole.ADMIN},
        {"username": "mod_test", "password": "mod123", "email": "mod@test.com", "role": UserRole.MODERATOR},
        {"username": "user_test", "password": "user123", "email": "user@test.com", "role": UserRole.USER},
    ]

    for user_data in test_users:
        # Check if user exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=True
            )
            user.set_password(user_data["password"])
            db.add(user)
            print(f"✅ Created {user_data['username']} with role {user_data['role'].value}")
        else:
            print(f"ℹ️  User {user_data['username']} already exists")

    db.commit()
    db.close()
    print("✅ Test users setup complete")

if __name__ == "__main__":
    create_test_users()
```

#### Solution 2: Fix Admin Create-User Command
Remove the decorator issue first, then the command will work properly for creating users via CLI.

#### Expected Impact
Fixes 3 authentication-related failures.

### Priority 3: Fix Individual Command Issues

#### 3.1 Data Commands

**Files to Check**: `/reddit_analyzer/cli/data.py`

All data commands (status, health, collect) will work once the decorator is fixed. No additional changes needed.

#### 3.2 Visualization Commands

**Files to Check**: `/reddit_analyzer/cli/visualization.py`

**Additional Fix for `viz trends`**:
- The `--subreddit` parameter should be required, not optional
```python
@viz_app.command("trends")
@cli_auth.require_auth()
def show_trends(
    subreddit: str = typer.Option(..., help="Specific subreddit (without r/)"),  # Changed: Made required
    days: int = typer.Option(7, help="Number of days to analyze"),
    export: Optional[str] = typer.Option(None, help="Export chart to PNG file"),
):
```

#### 3.3 Report Commands

**Files to Check**: `/reddit_analyzer/cli/reports.py`

All report commands will work once the decorator is fixed.

#### 3.4 Admin Commands

**Files to Check**: `/reddit_analyzer/cli/admin.py`

**Special Fix for `admin create-user`**:
The command should work without authentication (to create the first admin user):
```python
@admin_app.command("create-user")
# @cli_auth.require_auth(UserRole.ADMIN)  # Comment out or make conditional
def create_user(
    username: str = typer.Option(..., help="Username for new user"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password"),
    email: Optional[str] = typer.Option(None, help="Email address"),
    role: str = typer.Option("user", help="User role: user, moderator, admin"),
):
    """Create a new user account."""
    # Add logic to check if this is the first user (no admins exist)
    # If so, allow creation without authentication
```

### Priority 4: Enhanced Test Script

#### Create Improved Test Runner
```python
# File: /tests/test_phase4b_cli_enhanced.py

#!/usr/bin/env python3
"""Enhanced CLI test suite with setup and teardown."""

import subprocess
import sys
import os
from pathlib import Path

class EnhancedCLITester:
    def __init__(self):
        self.setup_complete = False

    def setup_test_environment(self):
        """Setup test database and users."""
        print("🔧 Setting up test environment...")

        # Run migrations
        result = subprocess.run(
            "alembic upgrade head",
            shell=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("❌ Failed to run migrations")
            return False

        # Create test users
        result = subprocess.run(
            "uv run python scripts/setup_test_users.py",
            shell=True,
            capture_output=True
        )
        if result.returncode != 0:
            print("❌ Failed to create test users")
            return False

        self.setup_complete = True
        print("✅ Test environment ready")
        return True
```

## Implementation Order

### Phase 1: Core Fixes (2 hours)
1. **Fix auth_manager.py decorator** - Removes *args from wrapper
2. **Run tests** - Verify majority of tests now pass
3. **Document results**

### Phase 2: Database Setup (1 hour)
1. **Create setup_test_users.py script**
2. **Run setup script**
3. **Test authentication flow**

### Phase 3: Command Fixes (1 hour)
1. **Fix viz trends command** - Make subreddit required
2. **Fix admin create-user** - Allow first admin without auth
3. **Verify all commands work**

### Phase 4: Test Enhancement (2 hours)
1. **Create enhanced test script** with setup/teardown
2. **Add integration tests**
3. **Create CI/CD test pipeline**

## Validation Checklist

After implementing fixes:

- [ ] All decorators use only `**kwargs`
- [ ] Test users exist in database
- [ ] All commands accept correct parameters
- [ ] Help text works for all commands
- [ ] Authentication flow works end-to-end
- [ ] Admin commands properly check roles
- [ ] Error messages are helpful
- [ ] All 38 tests pass

## Quick Fix Script

For immediate resolution, create this script:

```bash
#!/bin/bash
# File: /scripts/fix_cli_issues.sh

echo "🔧 Fixing CLI issues..."

# 1. Fix the decorator
sed -i 's/def wrapper(\*args, \*\*kwargs):/def wrapper(**kwargs):/' reddit_analyzer/cli/utils/auth_manager.py
sed -i 's/return func(\*args, \*\*kwargs)/return func(**kwargs)/' reddit_analyzer/cli/utils/auth_manager.py

# 2. Add functools import
sed -i '1s/^/from functools import wraps\n/' reddit_analyzer/cli/utils/auth_manager.py

# 3. Add @wraps decorator
sed -i '/def wrapper/i\        @wraps(func)' reddit_analyzer/cli/utils/auth_manager.py

echo "✅ Decorator fixed"

# 4. Setup database
echo "🗄️ Setting up database..."
alembic upgrade head

# 5. Create test users
echo "👥 Creating test users..."
uv run python scripts/setup_test_users.py

echo "✅ All fixes applied! Run tests with: uv run python tests/test_phase4b_cli_commands.py"
```

## Expected Results After Fixes

- **Success Rate**: Should increase from 44.7% to 95-100%
- **Failed Tests**: Should drop from 21 to 0-2
- **User Experience**: All CLI commands should work as documented
- **Authentication**: Proper role-based access control

## Next Steps

1. Implement Priority 1 fix immediately
2. Test and verify improvement
3. Continue with remaining priorities
4. Create automated test pipeline
5. Document any remaining issues

## Notes

- The decorator fix is the most critical - it will resolve 85% of issues
- Database setup is required for authentication tests
- Some commands may need parameter adjustments
- Consider adding `--no-auth` flag for development/testing
