# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
- **Install dependencies**: `uv sync --extra dev`
- **Install CLI dependencies**: `uv sync --extra cli`
- **Add new package**: `uv add package_name`
- **Activate environment**: `source .venv/bin/activate`

### CLI Commands (Phase 4B - Root Structure)
- **Run CLI from root**: `uv run reddit-analyzer --help`
- **System status**: `uv run reddit-analyzer status`
- **Authentication**: `uv run reddit-analyzer auth login`
- **Data analysis**: `uv run reddit-analyzer viz trends --subreddit python`
- **Generate reports**: `uv run reddit-analyzer report daily --subreddit python`
- **Admin functions**: `uv run reddit-analyzer admin stats`

### Testing
- **Run all tests**: `pytest`
- **Run CLI tests**: `pytest tests/test_phase4a_cli*`
- **Run tests with coverage**: `pytest --cov=reddit_analyzer --cov-report=html`
- **Test specific file**: `pytest tests/test_filename.py`

### Code Quality
- **Format code**: `black .`
- **Lint code**: `ruff check .`
- **Run pre-commit hooks**: `pre-commit run --all-files`

### Database
- **Run migrations**: `alembic upgrade head`
- **Create new migration**: `alembic revision --autogenerate -m "description"`
- **Database setup**: See `scripts/setup.sh` for complete setup instructions

## Architecture Overview

### Core Structure (Phase 4B - Standard Python Package)
- **reddit_analyzer/**: Main application package
  - **cli/**: Command line interface (Phase 4B)
    - **auth.py**: Authentication commands (login, logout, status)
    - **data.py**: Data management commands (status, health, collect)
    - **visualization.py**: Visualization commands (trends, sentiment, activity)
    - **reports.py**: Report generation commands (daily, weekly, export)
    - **admin.py**: Admin commands (stats, users, health-check)
    - **utils/**: CLI utilities including ASCII chart generation
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
- **CLI Framework**: Typer with Rich for terminal formatting
- **Visualization**: ASCII charts for terminal, matplotlib/seaborn for exports
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
- Required environment variables in `.env`:
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
  - `REDDIT_USERNAME`, `REDDIT_PASSWORD`
  - `REDDIT_USER_AGENT`
  - `DATABASE_URL`, `REDIS_URL`
  - `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`

### Project Structure (Phase 4B - Current)
Standard Python package layout:
- `reddit_analyzer/`: Main Python package (CLI and core functionality)
  - `cli/`: Command line interface implementation
  - `models/`: Database models
  - `services/`: Business logic and Reddit API client
  - `api/`: API endpoints (future web interface)
  - `utils/`: Shared utilities
- `tests/`: Test suite including CLI tests
- `alembic/`: Database migrations
- `scripts/`: Setup and utility scripts
- `specs/`: Project documentation and specifications
- `cli_demo.py`: Interactive CLI demonstration script
- `pyproject.toml`: Package configuration (moved from backend/)
- `frontend/`: Future web interface
- Benefits: Standard Python packaging, simplified CLI usage from root

## Development Workflow

1. **Environment Setup**: Run `scripts/setup.sh` for complete setup
2. **Activate Environment**: `source .venv/bin/activate`
3. **Code Changes**: Make changes following existing patterns
4. **Testing**: Run `pytest` before committing
5. **Code Quality**: Format with `black` and lint with `ruff`
6. **Pre-commit**: Hooks automatically run on commit

## Testing Framework
- **Location**: `tests/`
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

## CLI System (Phase 4B)

### CLI Command Groups
- **Authentication**: `reddit-analyzer auth` - login, logout, status, whoami
- **Data Management**: `reddit-analyzer data` - status, health, collect
- **Visualization**: `reddit-analyzer viz` - trends, sentiment, activity analysis
- **Reporting**: `reddit-analyzer report` - daily/weekly reports, data export
- **Admin**: `reddit-analyzer admin` - system stats, user management, health checks

### CLI Features
- **ASCII Visualizations**: Terminal-based charts and graphs
- **JWT Authentication**: Secure token-based CLI authentication
- **Role-based Access**: Different commands for users, moderators, admins
- **Data Export**: CSV/JSON export capabilities
- **Real-time Analysis**: Live Reddit data collection and analysis

### CLI Usage Examples
```bash
# Authentication
reddit-analyzer auth login --username user --password pass
reddit-analyzer auth status

# Data Analysis
reddit-analyzer viz trends --subreddit python --days 7
reddit-analyzer viz sentiment javascript
reddit-analyzer viz activity --subreddit datascience

# Reporting
reddit-analyzer report daily --subreddit python
reddit-analyzer report export --format csv --output data.csv

# Administration
reddit-analyzer admin stats
reddit-analyzer admin users
```

## Authentication System

### User Roles
- **USER**: Basic user access (default)
- **MODERATOR**: Enhanced permissions for moderation tasks
- **ADMIN**: Full system administration access

### CLI Authentication
- **Token Storage**: Secure token storage in `~/.reddit-analyzer/tokens.json`
- **Session Management**: JWT access and refresh tokens
- **Role Enforcement**: CLI commands respect user roles

### API Endpoints
- **Authentication**: `/api/auth/` - login, register, refresh, logout
- **Admin**: `/api/admin/` - user management, system stats (protected)

### Usage Examples
```python
# CLI Authentication Manager
from app.cli.utils.auth_manager import cli_auth

@cli_auth.require_auth()
def protected_cli_command():
    user = cli_auth.get_current_user()
    return f"Hello {user.username}"

# Protect endpoint with authentication
@auth_required
def protected_endpoint():
    user = g.current_user  # Current authenticated user
    return jsonify({"user": user.username})

# Get authentication service
from app.utils.auth import get_auth_service
auth_service = get_auth_service()
```
