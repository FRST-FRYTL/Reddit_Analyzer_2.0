# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Initial setup (run once)
./scripts/setup.sh

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv sync --extra dev --extra cli

# Install with enhanced NLP capabilities
uv sync --extra dev --extra cli --extra nlp-enhanced
```

### Package Management
- **Install dependencies**: `uv sync --extra dev --extra cli`
- **Add new package**: `uv add package_name`
- **Add dev dependency**: `uv add --dev package_name`
- **Update dependencies**: `uv sync`

### Database Commands
- **Run migrations**: `alembic upgrade head`
- **Create new migration**: `alembic revision --autogenerate -m "description"`
- **Rollback migration**: `alembic downgrade -1`
- **View migration history**: `alembic history`

### Testing Commands
- **Run all tests**: `uv run pytest`
- **Run specific test file**: `uv run pytest tests/test_filename.py`
- **Run with coverage**: `uv run pytest --cov=reddit_analyzer --cov-report=html`
- **Run CLI tests**: `uv run pytest tests/test_phase4*_cli*`
- **Run tests in parallel**: `uv run pytest -n auto`
- **Run tests with output**: `uv run pytest -v -s`

### Code Quality
- **Format code**: `uv run black .`
- **Lint code**: `uv run ruff check .`
- **Fix linting issues**: `uv run ruff check . --fix`
- **Type checking**: `uv run mypy reddit_analyzer/`
- **Run all checks**: `uv run pre-commit run --all-files`

### CLI Commands
```bash
# System
uv run reddit-analyzer --help
uv run reddit-analyzer status
uv run reddit-analyzer version

# Authentication
uv run reddit-analyzer auth login
uv run reddit-analyzer auth logout
uv run reddit-analyzer auth status
uv run reddit-analyzer auth whoami

# Data Collection
uv run reddit-analyzer data collect python --limit 100
uv run reddit-analyzer data collect javascript --skip-nlp
uv run reddit-analyzer data collect datascience --sort new --limit 50
uv run reddit-analyzer data status
uv run reddit-analyzer data health

# Visualization
uv run reddit-analyzer viz trends --subreddit python --days 7
uv run reddit-analyzer viz sentiment javascript
uv run reddit-analyzer viz activity --subreddit datascience

# NLP Analysis
uv run reddit-analyzer nlp analyze --subreddit python --limit 50
uv run reddit-analyzer nlp topics python --num-topics 10
uv run reddit-analyzer nlp keywords python --top-n 25
uv run reddit-analyzer nlp emotions --subreddit python
uv run reddit-analyzer nlp export --subreddit python --format csv

# Reports
uv run reddit-analyzer report daily --subreddit python
uv run reddit-analyzer report weekly --subreddit javascript
uv run reddit-analyzer report export --format csv --output data.csv

# Admin (requires admin role)
uv run reddit-analyzer admin stats
uv run reddit-analyzer admin users
uv run reddit-analyzer admin health-check
uv run reddit-analyzer admin create-user --username admin --role admin
```

## Architecture Overview

### Project Structure
```
reddit_analyzer/              # Main package (Phase 4B/4C structure)
├── cli/                     # CLI implementation (Typer-based)
│   ├── auth.py             # Authentication commands
│   ├── data.py             # Data collection commands
│   ├── visualization.py    # Visualization commands
│   ├── reports.py          # Report generation
│   ├── admin.py            # Admin commands
│   ├── nlp.py              # NLP analysis commands
│   └── utils/              # CLI utilities (auth_manager, charts)
├── models/                  # SQLAlchemy ORM models
│   ├── base.py             # Base model class
│   ├── user.py             # User authentication model
│   ├── reddit.py           # Reddit data models (Post, Comment, Subreddit)
│   ├── analytics.py        # Analytics models (TextAnalysis, Topic)
│   └── metrics.py          # Metrics and aggregations
├── services/                # Business logic services
│   ├── reddit_client.py    # PRAW Reddit API wrapper
│   ├── nlp_service.py      # NLP orchestration (singleton)
│   ├── auth_service.py     # Authentication service
│   └── analytics_service.py # Analytics computations
├── processing/              # NLP processing modules
│   ├── sentiment_analyzer.py # Multi-model sentiment (VADER, TextBlob, Transformers)
│   ├── topic_modeler.py    # LDA topic modeling
│   ├── feature_extractor.py # Feature extraction for ML
│   └── text_processor.py   # Text preprocessing utilities
├── api/                     # FastAPI endpoints
│   ├── auth.py             # Authentication endpoints
│   ├── admin.py            # Admin endpoints
│   └── routes.py           # Route registration
├── middleware/              # Authentication middleware
│   └── auth.py             # JWT validation, decorators
├── core/                    # Core infrastructure
│   ├── cache.py            # Redis caching
│   ├── rate_limiter.py    # Rate limiting
│   └── queue.py            # Request queuing
├── ml/                      # Machine learning models
│   ├── content_classifier.py # Content classification
│   ├── popularity_predictor.py # Popularity prediction
│   └── user_classifier.py  # User type classification
├── utils/                   # Shared utilities
│   ├── auth.py             # Authentication utilities
│   ├── logger.py           # Logging configuration
│   └── validators.py       # Data validation
├── config.py               # Environment configuration
└── database.py             # Database session management
```

### Key Technologies
- **Python 3.9+**: Target Python version
- **uv**: Ultra-fast Python package manager
- **Typer + Rich**: CLI framework with beautiful terminal UI
- **SQLAlchemy 2.0+**: Modern ORM with async support
- **PostgreSQL**: Production database (SQLite for development/testing)
- **Redis**: Caching and rate limiting
- **PRAW**: Reddit API client
- **JWT**: Token-based authentication

### NLP Stack
- **Basic NLP** (always installed):
  - VADER: Rule-based sentiment analysis
  - TextBlob: Simple sentiment and polarity
  - NLTK: Text preprocessing
  - scikit-learn: Topic modeling (LDA)

- **Enhanced NLP** (optional, via `--extra nlp-enhanced`):
  - spaCy: Entity recognition, advanced tokenization
  - Transformers: Deep learning models (sentiment, emotion)
  - Additional models: ~2GB download on first use

### Database Models
```python
# Core Reddit Models
- User: Authentication users with roles (USER, MODERATOR, ADMIN)
- Subreddit: Reddit communities
- Post: Reddit submissions
- Comment: Hierarchical comments

# Analytics Models
- TextAnalysis: NLP results (sentiment, keywords, emotions)
- Topic: Discovered topics from LDA
- UserMetric: User activity metrics
- SubredditAnalytics: Aggregated statistics

# System Models
- CollectionJob: Data collection tracking
- MLPrediction: ML model predictions
```

### Authentication System
- **JWT Tokens**: Access (15min) and refresh (7days) tokens
- **Token Storage**: CLI stores in `~/.reddit-analyzer/tokens.json`
- **Decorators**: `@auth_required`, `@admin_required`, `@moderator_required`
- **Roles**: USER (default), MODERATOR, ADMIN

### Configuration
Required environment variables (`.env` file):
```bash
# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT="RedditAnalyzer/1.0"

# Database (required)
DATABASE_URL=postgresql://user:pass@localhost/reddit_analyzer
# For development: sqlite:///./reddit_analyzer.db

# Redis (optional, defaults to localhost)
REDIS_URL=redis://localhost:6379

# Security (required)
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# NLP Configuration (optional)
NLP_ENABLE_TRANSFORMERS=true
NLP_CONFIDENCE_THRESHOLD=0.5
NLP_BATCH_SIZE=100
```

## Development Workflow

### Adding New Features
1. Create/update models in `reddit_analyzer/models/`
2. Create migration: `alembic revision --autogenerate -m "Add feature"`
3. Implement service logic in `reddit_analyzer/services/`
4. Add CLI commands in `reddit_analyzer/cli/`
5. Write tests in `tests/`
6. Update documentation

### Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- CLI command tests with isolated database
- Use fixtures for common test data
- Mock external services (Reddit API, NLP models)

### Code Style Guidelines
- Line length: 88 characters (Black default)
- Use type hints for all functions
- Follow existing patterns in the codebase
- Docstrings for all public functions
- Keep CLI output concise and user-friendly

### Common Patterns
```python
# Service pattern (singleton for expensive resources)
class NLPService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# CLI command pattern
@app.command()
def command_name(
    option: str = typer.Option(..., help="Help text"),
    ctx: typer.Context = typer.Context
):
    """Command description."""
    auth_manager = ctx.obj['auth_manager']
    # Implementation

# Database session pattern
from reddit_analyzer.database import get_session
with get_session() as session:
    # Database operations
```

### Performance Considerations
- NLP models are loaded once and cached
- Redis caching for expensive computations
- Batch processing for large datasets
- Rate limiting for Reddit API calls
- Connection pooling for database

### Security Best Practices
- Never commit credentials or API keys
- Use environment variables for sensitive data
- Validate all user inputs
- Use parameterized queries (SQLAlchemy handles this)
- JWT tokens expire and require refresh
- Passwords hashed with bcrypt

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure virtual environment is activated
2. **Database errors**: Run migrations with `alembic upgrade head`
3. **Reddit API errors**: Check API credentials and rate limits
4. **NLP model errors**: Install enhanced NLP extras if needed
5. **Permission errors**: Check user roles for admin commands

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run reddit-analyzer --debug [command]

# Check configuration
uv run reddit-analyzer status --verbose
```

### Performance Profiling
```bash
# Profile CLI commands
uv run python -m cProfile -o profile.stats reddit_analyzer/cli/main.py [command]

# Analyze profile
uv run python -m pstats profile.stats
```
