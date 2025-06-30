# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
- **Install dependencies**: `cd backend && uv sync --extra dev`
- **Add new package**: `cd backend && uv add package_name`
- **Activate environment**: `source backend/.venv/bin/activate`

### Testing
- **Run all tests**: `cd backend && pytest`
- **Run tests with coverage**: `cd backend && pytest --cov=app --cov-report=html`
- **Test specific file**: `cd backend && pytest tests/test_filename.py`

### Code Quality
- **Format code**: `cd backend && black .`
- **Lint code**: `cd backend && ruff check .`
- **Run pre-commit hooks**: `pre-commit run --all-files`

### Database
- **Run migrations**: `cd backend && alembic upgrade head`
- **Create new migration**: `cd backend && alembic revision --autogenerate -m "description"`
- **Database setup**: See `scripts/setup.sh` for complete setup instructions

## Architecture Overview

### Core Structure
- **backend/app/**: Main application code
  - **models/**: SQLAlchemy database models (Post, User, Subreddit, Comment)
  - **services/**: Business logic, including `reddit_client.py` (PRAW wrapper)
  - **utils/**: Shared utilities like logging and authentication
  - **api/**: API endpoints for authentication and admin functions
  - **middleware/**: Authentication middleware and decorators
  - **config.py**: Environment-based configuration management
  - **database.py**: Database session and connection management

### Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: uv (ultra-fast Python package installer)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Authentication**: JWT tokens with bcrypt password hashing
- **Reddit API**: PRAW (Python Reddit API Wrapper)
- **Testing**: pytest with coverage reporting
- **Code Quality**: Black (formatting), Ruff (linting)

### Database Schema
- Normalized relational schema with proper foreign keys
- Core entities: users, subreddits, posts, comments
- Authentication: User model with password hashing and roles
- Timestamps and performance indexes included
- Alembic handles migrations

### Configuration
- Environment-based config (development, production, test)
- Required environment variables in `backend/.env`:
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
  - `REDDIT_USERNAME`, `REDDIT_PASSWORD`
  - `REDDIT_USER_AGENT`
  - `DATABASE_URL`, `REDIS_URL`
  - `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`

### Project Structure
- `backend/`: Python application (FastAPI ready)
- `database/`: SQL initialization scripts
- `scripts/`: Setup and utility scripts
- `specs/`: Project documentation and testing specs

## Development Workflow

1. **Environment Setup**: Run `scripts/setup.sh` for complete setup
2. **Activate Environment**: `source backend/.venv/bin/activate`
3. **Code Changes**: Make changes following existing patterns
4. **Testing**: Run `pytest` before committing
5. **Code Quality**: Format with `black` and lint with `ruff`
6. **Pre-commit**: Hooks automatically run on commit

## Testing Framework
- **Location**: `backend/tests/`
- **Framework**: pytest with fixtures
- **Coverage**: HTML and XML reports generated
- **Database**: In-memory SQLite for test isolation
- **Mocking**: pytest-mock for external dependencies

## Important Notes
- All code targets Python 3.9+
- Line length limit: 88 characters
- Use existing patterns and conventions from the codebase
- Database models follow SQLAlchemy best practices
- Reddit API client is centralized in `services/reddit_client.py`
- Authentication system uses JWT tokens with role-based access control
- Use `@auth_required`, `@admin_required`, `@moderator_required` decorators for endpoint protection

## Authentication System

### User Roles
- **USER**: Basic user access (default)
- **MODERATOR**: Enhanced permissions for moderation tasks
- **ADMIN**: Full system administration access

### API Endpoints
- **Authentication**: `/api/auth/` - login, register, refresh, logout
- **Admin**: `/api/admin/` - user management, system stats (protected)

### Usage Examples
```python
# Protect endpoint with authentication
@auth_required
def protected_endpoint():
    user = g.current_user  # Current authenticated user
    return jsonify({"user": user.username})

# Require admin access
@admin_required
def admin_only_endpoint():
    # Only admin users can access
    pass

# Get authentication service
from app.utils.auth import get_auth_service
auth_service = get_auth_service()
```
