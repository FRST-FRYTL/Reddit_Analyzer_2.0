# Reddit Analyzer

A comprehensive data analysis application for collecting, processing, and analyzing Reddit data using the Reddit API.

## Features

- **Reddit API Integration**: Seamless data collection using PRAW (Python Reddit API Wrapper)
- **Database Management**: PostgreSQL with SQLAlchemy ORM for reliable data storage
- **Data Processing**: Structured analysis of posts, comments, users, and subreddits
- **Caching Layer**: Redis integration for improved performance
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

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure environment variables**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your Reddit API credentials
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
   cd backend && source .venv/bin/activate && alembic upgrade head
   ```

5. **Start Redis**:
   ```bash
   sudo systemctl start redis-server  # Linux
   # or
   brew services start redis          # macOS
   ```

### Development

**Activate the environment**:
```bash
source backend/.venv/bin/activate
```

**Run tests**:
```bash
cd backend && pytest
```

**Format and lint code**:
```bash
cd backend && black . && ruff check .
```

## Project Structure

```
reddit_analyzer/
├── backend/                    # Main application backend
│   ├── app/                   # Core application code
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Utility functions
│   │   ├── config.py         # Configuration management
│   │   └── database.py       # Database setup
│   ├── tests/                # Test suite
│   ├── alembic/              # Database migrations
│   └── pyproject.toml        # Project configuration
├── database/                  # Database initialization
├── scripts/                   # Setup and utility scripts
└── specs/                     # Documentation and specifications
```

## Technology Stack

- **Backend**: Python 3.9+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis
- **Reddit API**: PRAW (Python Reddit API Wrapper)
- **Package Management**: uv
- **Testing**: pytest with coverage
- **Code Quality**: Black, Ruff, pre-commit hooks

## Environment Variables

Required environment variables in `backend/.env`:

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
```

## Database Schema

The application uses a normalized relational database with the following core entities:

- **Users**: Reddit user profiles and karma scores
- **Subreddits**: Community metadata and statistics
- **Posts**: Reddit submissions with scores and metadata
- **Comments**: Threaded comments with relationships

## Testing

Run the complete test suite:
```bash
cd backend && pytest
```

Run tests with coverage report:
```bash
cd backend && pytest --cov=app --cov-report=html
```

Test specific functionality:
```bash
cd backend && pytest tests/test_models.py
```

## Development Workflow

1. **Make changes**: Follow existing code patterns and conventions
2. **Test**: Run `pytest` to ensure all tests pass
3. **Format**: Use `black .` to format code
4. **Lint**: Use `ruff check .` to check for issues
5. **Commit**: Pre-commit hooks will run automatically

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Ensure all tests pass before committing
4. Use descriptive commit messages

## License

This project is licensed under the MIT License.
