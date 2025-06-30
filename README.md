# Reddit Analyzer

A comprehensive data analysis application for collecting, processing, and analyzing Reddit data using the Reddit API.

> 🚀 **Phase 4B Update**: Now using standard Python package structure with root-level CLI access. All commands use `uv run` for simplified development workflow.

## Features

- **Reddit API Integration**: Seamless data collection using PRAW (Python Reddit API Wrapper)
- **Database Management**: PostgreSQL with SQLAlchemy ORM for reliable data storage
- **Data Processing**: Structured analysis of posts, comments, users, and subreddits
- **Caching Layer**: Redis integration for improved performance
- **Command Line Interface**: Comprehensive CLI for data visualization and management
- **Authentication System**: JWT-based authentication with role-based access control
- **Testing Suite**: Comprehensive test coverage with pytest
- **Code Quality**: Automated formatting (Black) and linting (Ruff)

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Reddit API credentials

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd reddit_analyzer
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync --extra cli --extra dev
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Reddit API credentials
   ```

4. **Set up the database**:
   ```bash
   # Start PostgreSQL service
   sudo systemctl start postgresql  # Linux
   # or
   brew services start postgresql   # macOS

   # Create database and user
   sudo -u postgres createdb reddit_analyzer
   sudo -u postgres createuser reddit_user
   sudo -u postgres psql -c "ALTER USER reddit_user WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer TO reddit_user;"

   # Run migrations
   alembic upgrade head
   ```

5. **Start Redis**:
   ```bash
   sudo systemctl start redis-server  # Linux
   # or
   brew services start redis          # macOS
   ```

### CLI Usage

After installation, use the Reddit Analyzer CLI with `uv run`:

**Authenticate**:
```bash
uv run reddit-analyzer auth login --username your_username --password your_password
```

**Check system status**:
```bash
uv run reddit-analyzer status
```

**Analyze data**:
```bash
uv run reddit-analyzer viz trends --subreddit python --days 7
uv run reddit-analyzer viz sentiment javascript
uv run reddit-analyzer viz activity --subreddit datascience
```

**Generate reports**:
```bash
uv run reddit-analyzer report daily --subreddit python
uv run reddit-analyzer report weekly --subreddit javascript
uv run reddit-analyzer report export --format csv --output data.csv
```

**Admin functions** (requires admin role):
```bash
uv run reddit-analyzer admin stats
uv run reddit-analyzer admin users
uv run reddit-analyzer admin health-check
```

### Development

**Install dependencies**:
```bash
uv sync --extra dev
```

**Run tests**:
```bash
uv run pytest
```

**Format and lint code**:
```bash
uv run black . && uv run ruff check .
```

**Run CLI commands during development**:
```bash
uv run reddit-analyzer --help
```

## Project Structure (Phase 4B - Standard Python Package)

```
reddit_analyzer/
├── reddit_analyzer/           # Main Python package
│   ├── cli/                  # Command line interface
│   │   ├── auth.py          # Authentication commands
│   │   ├── data.py          # Data management commands
│   │   ├── visualization.py # Visualization commands
│   │   ├── reports.py       # Report generation commands
│   │   ├── admin.py         # Admin commands
│   │   └── utils/           # CLI utilities and ASCII charts
│   ├── models/               # Database models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration management
│   └── database.py           # Database setup
├── tests/                     # Test suite
├── alembic/                   # Database migrations
├── database/                  # Database initialization
├── scripts/                   # Setup and utility scripts
├── specs/                     # Documentation and specifications
├── pyproject.toml             # Project configuration
├── .env.example               # Environment template
└── README.md                  # This file
```

## Technology Stack

- **Backend**: Python 3.9+, FastAPI
- **CLI Framework**: Typer with Rich for terminal formatting
- **Visualization**: ASCII charts for terminal, matplotlib/seaborn for exports
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Authentication**: JWT tokens with bcrypt password hashing
- **Reddit API**: PRAW (Python Reddit API Wrapper)
- **Package Management**: uv
- **Testing**: pytest with coverage
- **Code Quality**: Black, Ruff, pre-commit hooks

## Environment Variables

Required environment variables in `.env`:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=your_app_name/1.0
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# Database
DATABASE_URL=postgresql://reddit_user:password@localhost/reddit_analyzer

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## CLI Commands Reference

### Authentication Commands
```bash
uv run reddit-analyzer auth login     # Login with username/password
uv run reddit-analyzer auth logout    # Logout and clear session
uv run reddit-analyzer auth status    # Show authentication status
uv run reddit-analyzer auth whoami    # Show current user info
```

### Data Management Commands
```bash
uv run reddit-analyzer data status    # Show data collection status
uv run reddit-analyzer data health    # Check database health
uv run reddit-analyzer data collect   # Start data collection
```

### Visualization Commands
```bash
uv run reddit-analyzer viz trends --subreddit NAME [--days N]     # Show trending posts
uv run reddit-analyzer viz sentiment SUBREDDIT                    # Sentiment analysis
uv run reddit-analyzer viz activity --subreddit NAME [--period P] # Activity trends
```

### Report Commands
```bash
uv run reddit-analyzer report daily --subreddit NAME [--date DATE]     # Daily report
uv run reddit-analyzer report weekly --subreddit NAME [--weeks N]      # Weekly report
uv run reddit-analyzer report export --format FORMAT --output FILE     # Export data
```

### Admin Commands (Admin role required)
```bash
uv run reddit-analyzer admin stats        # System statistics
uv run reddit-analyzer admin users        # List all users
uv run reddit-analyzer admin health-check # Full system health check
```

### General Commands
```bash
uv run reddit-analyzer status      # Overall system status
uv run reddit-analyzer version     # Show version info
uv run reddit-analyzer --help      # Show help for any command
```

## Database Schema

The application uses a normalized relational database with the following core entities:

- **Users**: Reddit user profiles and karma scores (with authentication system)
- **Subreddits**: Community metadata and statistics
- **Posts**: Reddit submissions with scores and metadata
- **Comments**: Threaded comments with relationships

## Testing

Run the complete test suite:
```bash
uv run pytest
```

Run tests with coverage report:
```bash
uv run pytest --cov=reddit_analyzer --cov-report=html
```

Test specific functionality:
```bash
uv run pytest tests/test_models.py
```

## Development Workflow

1. **Install dependencies**: `uv sync --extra dev`
2. **Make changes**: Follow existing code patterns and conventions
3. **Test**: Run `uv run pytest` to ensure all tests pass
4. **Format**: Use `uv run black .` to format code
5. **Lint**: Use `uv run ruff check .` to check for issues
6. **Commit**: Pre-commit hooks will run automatically

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Ensure all tests pass before committing
4. Use descriptive commit messages

## License

This project is licensed under the MIT License.
