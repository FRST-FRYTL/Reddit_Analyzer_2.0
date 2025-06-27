# Phase 1: Foundation (Weeks 1-2)

## Overview
Establish the foundational infrastructure for the Reddit API data analysis application, including project setup, environment configuration, Reddit API authentication, database design, and basic data collection capabilities.

## Objectives
- Set up development environment and project structure
- Implement Reddit API authentication and basic connectivity
- Design and implement database schema
- Create basic data collection for single subreddit
- Establish testing framework and CI/CD pipeline

## Tasks & Requirements

### Project Setup & Environment Configuration
- [ ] Initialize Git repository with proper .gitignore
- [ ] Install and configure uv package manager
- [ ] Create pyproject.toml with project configuration
- [ ] Set up virtual environment using uv
- [ ] Configure environment variables management (.env files)
- [ ] Set up pre-commit hooks for code quality

### Reddit API Integration
- [ ] Register Reddit application for API access
- [ ] Implement OAuth 2.0 authentication flow
- [ ] Create Reddit API client wrapper using PRAW
- [ ] Test basic API connectivity (fetch single post)
- [ ] Implement API credentials management
- [ ] Add basic error handling for API calls

### Database Design & Setup
- [ ] Install and configure PostgreSQL
- [ ] Design database schema for posts, comments, users, subreddits
- [ ] Create database migration system
- [ ] Implement database connection pooling
- [ ] Set up Redis for caching and session management
- [ ] Create database backup and restore procedures

### Basic Data Collection
- [ ] Implement single subreddit data fetching
- [ ] Create data models for posts and basic metadata
- [ ] Add data validation and sanitization
- [ ] Implement basic logging system
- [ ] Create simple data storage mechanism
- [ ] Test data collection with sample subreddit

### Testing Framework
- [ ] Set up pytest testing framework
- [ ] Create unit tests for API client
- [ ] Add integration tests for database operations
- [ ] Set up test database configuration
- [ ] Create mock data for testing
- [ ] Implement test coverage reporting

## Technical Specifications

### Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: uv (ultra-fast Python package installer)
- **API Client**: PRAW (Python Reddit API Wrapper)
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **ORM**: SQLAlchemy
- **Testing**: pytest, pytest-mock
- **Environment**: Python virtual environments

### Project Structure
```
reddit_analyzer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── post.py
│   │   │   ├── comment.py
│   │   │   ├── user.py
│   │   │   └── subreddit.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── reddit_client.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logging.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_reddit_client.py
│   │   └── test_models.py
│   ├── alembic/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .env.example
├── database/
│   └── init.sql
├── scripts/
│   ├── setup.sh
│   ├── install_deps.sh
│   └── test_connection.py
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

### Database Schema (Initial)
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    created_utc TIMESTAMP,
    comment_karma INTEGER DEFAULT 0,
    link_karma INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subreddits table
CREATE TABLE subreddits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    subscribers INTEGER DEFAULT 0,
    created_utc TIMESTAMP,
    is_nsfw BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table
CREATE TABLE posts (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    selftext TEXT,
    url VARCHAR(2000),
    author_id INTEGER REFERENCES users(id),
    subreddit_id INTEGER REFERENCES subreddits(id),
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT DEFAULT 0.5,
    num_comments INTEGER DEFAULT 0,
    created_utc TIMESTAMP NOT NULL,
    is_self BOOLEAN DEFAULT FALSE,
    is_nsfw BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments table (basic structure)
CREATE TABLE comments (
    id VARCHAR(255) PRIMARY KEY,
    post_id VARCHAR(255) REFERENCES posts(id),
    parent_id VARCHAR(255),
    author_id INTEGER REFERENCES users(id),
    body TEXT,
    score INTEGER DEFAULT 0,
    created_utc TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Environment Configuration
```bash
# Reddit API Configuration
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_user_agent
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/reddit_analyzer
REDIS_URL=redis://localhost:6379/0

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
```

## Environment Setup Scripts

### Setup Script (scripts/setup.sh)
```bash
#!/bin/bash
set -e

echo "Setting up Reddit Analyzer development environment..."

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-dev postgresql postgresql-contrib redis-server

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create project directory structure
mkdir -p backend/app/{models,services,utils}
mkdir -p backend/tests
mkdir -p backend/alembic
mkdir -p database
mkdir -p scripts

# Initialize uv project
cd backend
uv init --no-readme
uv venv
source .venv/bin/activate

# Install dependencies
uv sync --extra dev

# Set up pre-commit hooks
uv run pre-commit install

# Setup database
sudo -u postgres createdb reddit_analyzer || echo "Database already exists"
sudo -u postgres createuser reddit_user || echo "User already exists"

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo "Setup complete! Activate virtual environment with: source backend/.venv/bin/activate"
```

### Dependency Installation Script (scripts/install_deps.sh)
```bash
#!/bin/bash
set -e

echo "Installing dependencies with uv..."

# Navigate to backend directory
cd backend

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install all dependencies
echo "Installing core dependencies..."
uv sync

echo "Installing development dependencies..."
uv sync --extra dev

echo "Verifying installation..."
uv run python -c "import praw, sqlalchemy, redis; print('All core dependencies installed successfully')"
uv run pytest --version

echo "Dependencies installed successfully!"
```

## Dependencies

### pyproject.toml Configuration
```toml
[project]
name = "reddit-analyzer"
version = "0.1.0"
description = "Reddit API data analysis application"
requires-python = ">=3.9"
dependencies = [
    "praw>=7.6.0",
    "sqlalchemy>=1.4.0",
    "psycopg2-binary>=2.9.0",
    "redis>=4.3.0",
    "python-dotenv>=0.19.0",
    "alembic>=1.8.0",
    "fastapi>=0.85.0",
    "uvicorn[standard]>=0.18.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.8.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "ruff>=0.1.0",
    "pre-commit>=2.20.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-mock>=3.8.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "ruff>=0.1.0",
    "pre-commit>=2.20.0"
]

[tool.ruff]
line-length = 88
target-version = "py39"

[tool.black]
line-length = 88
target-version = ['py39']

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=app --cov-report=html --cov-report=term-missing"
```

### Installation Commands
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project with uv
uv init reddit-analyzer
cd reddit-analyzer

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev

# Verify installation
uv run python --version
uv run pytest --version
```

## Success Criteria
- [ ] Successfully authenticate with Reddit API
- [ ] Database tables created and accessible
- [ ] Fetch and store 100 posts from a test subreddit
- [ ] All unit tests pass with >80% coverage
- [ ] Virtual environment runs without errors
- [ ] Basic logging captures API calls and database operations

## Testing Requirements

### Unit Tests
- Reddit API client initialization and authentication
- Database model creation and validation
- Configuration loading and validation
- Error handling for API failures

### Integration Tests
- End-to-end data flow from Reddit API to database
- Database connection and query operations
- Redis caching functionality
- Virtual environment activation and package installation

### Manual Testing Checklist
- [ ] uv installation and virtual environment creation works
- [ ] All dependencies install without conflicts
- [ ] Reddit API authentication works
- [ ] Database connection established
- [ ] Sample data collection completes successfully
- [ ] Environment variables loaded correctly
- [ ] Logging system captures expected events
- [ ] Pre-commit hooks execute successfully
- [ ] Tests run with uv run pytest

## Deliverables
1. Fully configured development environment
2. Working Reddit API authentication
3. Database schema with sample data
4. Basic data collection script
5. Test suite with passing tests
6. Documentation for setup and configuration

### uv Commands Reference
```bash
# Common uv commands for this phase
uv sync                    # Install dependencies
uv sync --extra dev       # Install with dev dependencies
uv add package_name       # Add new dependency
uv remove package_name    # Remove dependency
uv run command            # Run command in virtual environment
uv run pytest            # Run tests
uv run black .            # Format code
uv run ruff check .       # Lint code
uv pip list               # List installed packages
uv pip show package_name  # Show package info
```

### Development Workflow
1. **Initial Setup**: Run `scripts/setup.sh` for first-time setup
2. **Daily Development**:
   - `source backend/.venv/bin/activate` (activate environment)
   - `uv sync` (ensure dependencies are up-to-date)
   - `uv run pytest` (run tests)
   - `uv run black .` (format code)
   - `uv run ruff check .` (lint code)
3. **Adding Dependencies**: Use `uv add package_name` instead of pip install
4. **Updating Dependencies**: Use `uv sync` to update all packages

## Next Phase Dependencies
Phase 2 requires:
- Stable Reddit API client from this phase
- Database schema and models
- Basic error handling and logging
- Environment configuration system
- Working uv virtual environment with all dependencies
- Functional development workflow scripts
