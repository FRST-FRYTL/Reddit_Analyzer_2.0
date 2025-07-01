# Reddit Analyzer

A comprehensive data analysis application for collecting, processing, and analyzing Reddit data using the Reddit API.

> 🚀 **Phase 4B Update**: Now using standard Python package structure with root-level CLI access. All commands use `uv run` for simplified development workflow.

## Features

- **Reddit API Integration**: Seamless data collection using PRAW (Python Reddit API Wrapper)
- **Database Management**: PostgreSQL with SQLAlchemy ORM for reliable data storage
- **Data Processing**: Structured analysis of posts, comments, users, and subreddits
- **NLP Analysis**: Sentiment analysis, keyword extraction, topic modeling, and emotion detection
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
   # For development with SQLite (recommended for quick start)
   alembic upgrade head

   # For production with PostgreSQL
   # sudo systemctl start postgresql  # Linux
   # sudo -u postgres createdb reddit_analyzer
   # sudo -u postgres createuser reddit_user
   # Update DATABASE_URL in .env to postgresql://reddit_user:password@localhost:5432/reddit_analyzer
   ```

5. **Create an admin user**:
   ```bash
   uv run reddit-analyzer admin create-user --username admin --password your_password --email admin@example.com --role admin
   ```

6. **Start Redis**:
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

**Collect data from Reddit**:
```bash
# Collect posts from a subreddit
uv run reddit-analyzer data collect python --limit 100

# Collect without NLP analysis (faster)
uv run reddit-analyzer data collect javascript --skip-nlp

# Collect newest posts
uv run reddit-analyzer data collect datascience --sort new --limit 50

# Check data collection status
uv run reddit-analyzer data status
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

## NLP Features Installation

The Reddit Analyzer includes advanced NLP capabilities. Basic sentiment analysis works out of the box, but for full functionality, additional models are required.

### Basic NLP (Included)
- **VADER Sentiment**: Rule-based sentiment analysis
- **TextBlob**: Simple text processing and sentiment
- **Basic keyword extraction**: TF-IDF based

### Enhanced NLP Setup

#### 1. Install spaCy Language Model (Recommended)
```bash
# Install English language model (~13 MB)
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# For better accuracy (medium model, ~40 MB)
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl

# For best results (large model, ~750 MB)
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl
```

This enables:
- Named entity recognition
- Advanced keyword extraction
- Part-of-speech tagging
- Dependency parsing

#### 2. Install Transformers for Deep Learning Models (Optional)

⚠️ **Note**: This requires ~2-3 GB of disk space and significant download time.

```bash
# Option 1: CPU-only PyTorch (smaller, ~750 MB)
uv add torch --index-url https://download.pytorch.org/whl/cpu
uv add transformers

# Option 2: Full PyTorch with CUDA support (larger, ~2 GB)
uv add torch transformers

# Download a specific model (e.g., DistilBERT for sentiment, ~250 MB)
python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"
```

This enables:
- State-of-the-art sentiment analysis
- Emotion detection
- Zero-shot classification
- Advanced text embeddings

#### 3. Recommended Model Configurations

For different use cases:

**Minimal Setup** (Default):
- Works out of the box
- Uses VADER + TextBlob
- No additional downloads

**Standard Setup** (Recommended):
```bash
# Install spaCy small model
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

**Advanced Setup** (Best accuracy):
```bash
# Install spaCy large model
uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl

# Install transformers with CPU-only PyTorch
uv add torch --index-url https://download.pytorch.org/whl/cpu
uv add transformers

# Pre-download models
python -c "
from transformers import pipeline
# Sentiment analysis model
pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
# Emotion detection model
pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')
"
```

### Verifying NLP Installation

Check which NLP features are available:
```bash
# Check NLP status
uv run python -c "
from reddit_analyzer.services.nlp_service import get_nlp_service
nlp = get_nlp_service()
print('NLP Service initialized successfully')
"

# Test sentiment analysis
uv run reddit-analyzer nlp analyze --subreddit python --limit 1
```

### Troubleshooting NLP

**"No module named spacy model"**: Install the spaCy model as shown above

**"Transformers not available"**: This is normal if you haven't installed PyTorch. Basic sentiment analysis still works.

**Out of memory**: Use smaller models (distilbert instead of bert-base) or CPU-only PyTorch

**Slow processing**:
- Use `--skip-nlp` flag during data collection for faster processing
- Process in smaller batches with `--limit` flag
- Consider using GPU if available

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
- **NLP Stack**:
  - VADER & TextBlob for sentiment analysis
  - spaCy for NER and keyword extraction (optional)
  - Transformers for deep learning models (optional)
  - scikit-learn for topic modeling
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

### NLP Commands
```bash
uv run reddit-analyzer nlp analyze --subreddit NAME [--limit N]        # Analyze posts without NLP data
uv run reddit-analyzer nlp topics SUBREDDIT --num-topics N            # Discover topics
uv run reddit-analyzer nlp keywords SUBREDDIT --top-n N               # Extract keywords
uv run reddit-analyzer nlp emotions --subreddit NAME                  # Analyze emotions
uv run reddit-analyzer nlp export SUBREDDIT --format csv --output FILE # Export NLP results
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
