# Reddit Analyzer

A comprehensive data analysis application for collecting, processing, and analyzing Reddit data using the Reddit API.

> 🚀 **Phase 4D Update**: New political analysis features for topic detection, multi-dimensional political analysis, and discussion quality metrics. See [Political Analysis](#political-analysis) section below.

## Features

- **Reddit API Integration**: Seamless data collection using PRAW (Python Reddit API Wrapper)
- **Database Management**: PostgreSQL with SQLAlchemy ORM for reliable data storage
- **Data Processing**: Structured analysis of posts, comments, users, and subreddits
- **NLP Analysis**: Sentiment analysis, keyword extraction, topic modeling, and emotion detection
- **Caching Layer**: Redis integration for improved performance
- **Command Line Interface**: Comprehensive CLI for data visualization and management
- **Authentication System**: JWT-based authentication with role-based access control
- **Political Analysis**: Topic detection, multi-dimensional political analysis, and discussion quality metrics
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

# Political analysis
uv run reddit-analyzer analyze topics politics --days 30
uv run reddit-analyzer analyze dimensions worldnews
uv run reddit-analyzer analyze political-diversity moderatepolitics
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
│   │   ├── analyze.py       # Political analysis commands
│   │   └── utils/           # CLI utilities and ASCII charts
│   ├── models/               # Database models
│   ├── services/             # Business logic
│   │   ├── topic_analyzer.py           # Political topic analysis
│   │   └── political_dimensions_analyzer.py # Multi-dimensional analysis
│   ├── data/                 # Static data and taxonomies
│   │   └── political_topics.py # Political topic definitions
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration management
│   └── database.py           # Database setup
├── tests/                     # Test suite
│   ├── fixtures/             # Test data and fixtures
│   │   ├── real_data.py     # Real Reddit data fixtures
│   │   ├── test_data.db     # SQLite test database
│   │   └── golden_outputs/  # Expected outputs for validation
│   ├── reports/              # All test reports (see Testing section)
│   │   ├── phase_1/ through phase_4d/  # Phase-specific reports
│   │   └── misc/            # Coverage and security reports
│   └── test_*.py            # Test files by phase
├── alembic/                   # Database migrations
├── database/                  # Database initialization
├── scripts/                   # Setup and utility scripts
│   ├── setup.sh             # Initial setup script
│   ├── collect_test_data.py # Real Reddit data collection
│   └── generate_golden_outputs.py # Generate expected outputs
├── specs/                     # Documentation and specifications
│   ├── political_bias_feature.md  # Political analysis spec
│   └── phase5_heavy_models_plan.md # Advanced NLP plan
├── pyproject.toml             # Project configuration
├── .env.example               # Environment template
├── CLAUDE.md                  # Development guidelines
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

# Political Analysis (Optional)
MIN_USERS_FOR_ANALYSIS=25
MIN_TIME_WINDOW_DAYS=7
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

### Political Analysis Commands
```bash
uv run reddit-analyzer analyze topics SUBREDDIT [--days N]            # Analyze political topics
uv run reddit-analyzer analyze sentiment SUBREDDIT --topic TOPIC      # Topic-specific sentiment
uv run reddit-analyzer analyze quality SUBREDDIT [--min-comments N]   # Discussion quality metrics
uv run reddit-analyzer analyze overlap SUBREDDIT1 SUBREDDIT2          # Community comparison
uv run reddit-analyzer analyze dimensions SUBREDDIT [--save]          # Multi-dimensional political analysis
uv run reddit-analyzer analyze political-compass SUBREDDIT            # Generate political compass
uv run reddit-analyzer analyze political-diversity SUBREDDIT          # Analyze political diversity
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
- **TextAnalysis**: NLP analysis results including sentiment and political topics
- **PoliticalDimensionsAnalysis**: Multi-dimensional political scoring
- **SubredditTopicProfile**: Aggregate political topic analysis
- **SubredditPoliticalDimensions**: Community-level political metrics

## Testing

### Running Tests

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
uv run pytest tests/test_phase4d_cli_basic_real_data.py -v  # Real data tests
```

### Test Organization

The test suite is organized by development phase:
- **Phase 1**: Foundation tests (models, database)
- **Phase 2**: Authentication system tests
- **Phase 3**: Analytics and data processing tests
- **Phase 4**: CLI implementation tests
- **Phase 4a-4d**: Specialized CLI features (auth, NLP, political analysis)

### Test Reports

All test reports are stored in `tests/reports/` following a consistent naming convention:
```
phase_<phase>_<type>_<version>_<description>.md
```

Example reports:
- `phase_1_foundation_v2_complete_test.md`
- `phase_4d_validation_v10_real_data_test.md`

View the latest test results:
```bash
ls tests/reports/phase_4d/  # Latest political analysis tests
cat tests/reports/README.md  # Overview of all test reports
```

### Real Data Testing

The project uses real Reddit data for testing (Phase 4D v10+):
```bash
# Collect test data from Reddit
python scripts/collect_test_data.py

# Generate golden outputs for validation
python scripts/generate_golden_outputs.py

# Run tests with real data
uv run pytest tests/test_phase4d_cli_basic_real_data.py
```

Test data is stored in `tests/fixtures/test_data.db` with expected outputs in `tests/fixtures/golden_outputs/`.

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

## Political Analysis

The Reddit Analyzer includes comprehensive political analysis capabilities designed for research and understanding political discourse patterns. All analysis is performed at the aggregate level with strong privacy protections.

### Features

#### Political Topic Detection
- Identifies 9 major political topics: Healthcare, Economy, Climate, Immigration, Education, Foreign Policy, Social Issues, Technology, Democracy
- Keyword-based detection with confidence scoring
- Topic-specific sentiment analysis

#### Multi-Dimensional Political Analysis
Instead of oversimplified left-right classification, the system uses three dimensions:
- **Economic**: Market-oriented ↔ Planned economy
- **Social**: Individual liberty ↔ Social authority
- **Governance**: Decentralized ↔ Centralized power

Each dimension includes:
- Score from -1.0 to +1.0
- Confidence level
- Evidence tracking (keywords/phrases that influenced the score)
- Human-readable labels

#### Discussion Quality Metrics
- **Civility Score**: Measures respectful discourse
- **Constructiveness**: Evaluates substantive contributions
- **Viewpoint Diversity**: Assesses range of perspectives
- **Engagement Quality**: Tracks positive interactions

#### Community Analysis
- User overlap detection between subreddits
- Political topic comparison across communities
- Political diversity index calculation
- Clustering to identify distinct political groups

### Privacy and Ethics

All political analysis follows strict ethical guidelines:
- **Aggregate Only**: No individual user analysis or scoring
- **Minimum Thresholds**: Requires 25+ users for any analysis
- **Time Windows**: Minimum 7-day aggregation periods
- **No User Tracking**: Analysis at content level only
- **Opt-Out Support**: Subreddits can request exclusion
- **Transparency**: All outputs include confidence levels and limitations

### Example Usage

```bash
# Analyze political topics in r/politics over 30 days
uv run reddit-analyzer analyze topics politics --days 30

# Get topic-specific sentiment for healthcare discussions
uv run reddit-analyzer analyze sentiment politics --topic healthcare

# Generate political compass visualization
uv run reddit-analyzer analyze political-compass worldnews

# Compare political communities
uv run reddit-analyzer analyze overlap conservative liberal

# Analyze political diversity
uv run reddit-analyzer analyze political-diversity moderatepolitics
```

### Output Example

```
Political Topics in r/politics (2024-01-01 to 2024-01-31)
=========================================================

Healthcare    : ████████████████ (32%) [+0.3 sentiment]
Economy       : ██████████ (20%) [-0.1 sentiment]
Climate       : ████████ (16%) [+0.5 sentiment]
Immigration   : ██████ (12%) [-0.2 sentiment]
Education     : █████ (10%) [+0.2 sentiment]

Discussion Quality: 0.72/1.0 (Good)
- Civility: 0.85
- Constructiveness: 0.68
- Viewpoint Diversity: 0.63

Confidence Level: 82% (1,234 posts analyzed)
```

## Development Documentation

### Key Documentation Files

- **[CLAUDE.md](CLAUDE.md)**: Comprehensive development guidelines including:
  - Development commands and workflows
  - Detailed project structure
  - Testing strategies and conventions
  - Troubleshooting guides
  - Performance optimization tips

- **[tests/reports/](tests/reports/)**: All test execution reports organized by phase
  - View the [naming convention](tests/reports/NAMING_CONVENTION.md)
  - Browse [all reports](tests/reports/README.md)

- **[specs/](specs/)**: Feature specifications and plans
  - [Political analysis features](specs/political_bias_feature.md)
  - [Phase 5 heavy models plan](specs/phase5_heavy_models_plan.md)

### Development Resources

**Test Infrastructure**:
- Real data fixtures: `tests/fixtures/`
- Golden outputs: `tests/fixtures/golden_outputs/`
- Test utilities: `scripts/collect_test_data.py`, `scripts/generate_golden_outputs.py`

**Code Quality**:
- Pre-commit hooks configured in `.pre-commit-config.yaml`
- Ruff configuration in `pyproject.toml`
- Type hints throughout the codebase

**Database**:
- Migrations in `alembic/versions/`
- Models in `reddit_analyzer/models/`
- Schema documentation in test reports

## License

This project is licensed under the MIT License.
