# Phase 4A: Visualization CLI & Database Interface (Week 7)

## Overview
Build a command-line interface (CLI) for the Reddit Analyzer with basic visualization capabilities, leveraging the authentication system from Phase 4. This phase creates a testable interface for data exploration and visualization before developing the full web dashboard in Phase 4B.

## Objectives
- Create comprehensive CLI for data interaction and testing
- Implement basic visualization capabilities with ASCII charts and export
- Integrate with existing authentication system for secure access
- Build foundation for web dashboard development
- Provide immediate user feedback and testing capabilities
- Enable data exploration and basic reporting through terminal

## Tasks & Requirements

### CLI Framework Development
- [ ] Create modular CLI application using Click/Typer
- [ ] Implement command groups for different functionalities
- [ ] Add rich terminal output with colors and formatting
- [ ] Create interactive prompts for user input
- [ ] Implement command history and auto-completion
- [ ] Add progress bars for long-running operations
- [ ] Create configuration file management

### Authentication Integration
- [ ] Integrate CLI with existing JWT authentication system
- [ ] Implement login/logout commands
- [ ] Add session management for CLI operations
- [ ] Create user role-based command access
- [ ] Implement secure credential storage
- [ ] Add authentication status display
- [ ] Create admin-only CLI commands

### Data Visualization Commands
- [ ] Create ASCII chart generation for terminal display
- [ ] Implement basic statistical summaries
- [ ] Add trend analysis with text-based graphs
- [ ] Create export capabilities (JSON, CSV, PNG)
- [ ] Build subreddit comparison tools
- [ ] Implement sentiment analysis displays
- [ ] Add topic modeling visualization

### Database Management CLI
- [ ] Create database initialization and migration commands
- [ ] Implement data collection status monitoring
- [ ] Add database health check utilities
- [ ] Create data cleanup and maintenance tools
- [ ] Implement backup and restore commands
- [ ] Add performance monitoring commands
- [ ] Create database schema introspection tools

### Reporting & Export System
- [ ] Generate text-based reports
- [ ] Create CSV export functionality
- [ ] Implement JSON data dumps
- [ ] Add basic PDF report generation
- [ ] Create scheduled report commands
- [ ] Implement email delivery for reports
- [ ] Add report template management

## Technical Specifications

### CLI Application Structure
```python
from typer import Typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import click

# Main CLI application
app = Typer(
    name="reddit-analyzer",
    help="Reddit Analyzer CLI - Data exploration and visualization tool",
    add_completion=True
)

# Subcommand groups
auth_app = Typer(name="auth", help="Authentication commands")
data_app = Typer(name="data", help="Data management commands")
viz_app = Typer(name="viz", help="Visualization commands")
report_app = Typer(name="report", help="Reporting commands")
admin_app = Typer(name="admin", help="Admin commands (requires admin role)")

app.add_typer(auth_app)
app.add_typer(data_app)
app.add_typer(viz_app)
app.add_typer(report_app)
app.add_typer(admin_app)

console = Console()

# Authentication commands
@auth_app.command("login")
def login(username: str = typer.Option(..., prompt=True),
          password: str = typer.Option(..., prompt=True, hide_input=True)):
    """Login to Reddit Analyzer"""
    # Authenticate using existing JWT system
    pass

@auth_app.command("logout")
def logout():
    """Logout from Reddit Analyzer"""
    pass

@auth_app.command("status")
def auth_status():
    """Show current authentication status"""
    pass

# Data management commands
@data_app.command("status")
def data_status():
    """Show data collection status"""
    pass

@data_app.command("collect")
def collect_data(subreddit: str, limit: int = 100):
    """Collect data from specified subreddit"""
    pass

# Visualization commands
@viz_app.command("trends")
def show_trends(subreddit: str = None, days: int = 7):
    """Display trending topics and sentiment"""
    pass

@viz_app.command("sentiment")
def show_sentiment(subreddit: str, format: str = "ascii"):
    """Show sentiment analysis visualization"""
    pass
```

### Authentication Integration
```python
import os
import json
from pathlib import Path
from app.utils.auth import get_auth_service, AuthService
from app.models.user import User, UserRole

class CLIAuth:
    """CLI Authentication manager"""

    def __init__(self):
        self.config_dir = Path.home() / ".reddit-analyzer"
        self.token_file = self.config_dir / "tokens.json"
        self.config_dir.mkdir(exist_ok=True)
        self.auth_service = get_auth_service()

    def login(self, username: str, password: str) -> bool:
        """Authenticate user and store tokens"""
        try:
            # Use existing authentication system
            db = next(get_db())
            user = self.auth_service.authenticate_user(username, password, db)

            if user:
                tokens = self.auth_service.create_tokens(user)
                self._store_tokens(tokens)
                console.print(f"✅ Logged in as {user.username} ({user.role.value})", style="green")
                return True
            else:
                console.print("❌ Invalid credentials", style="red")
                return False
        except Exception as e:
            console.print(f"❌ Login failed: {e}", style="red")
            return False

    def _store_tokens(self, tokens: dict):
        """Securely store authentication tokens"""
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        os.chmod(self.token_file, 0o600)  # Read/write for owner only

    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)

            db = next(get_db())
            user = self.auth_service.get_current_user(tokens['access_token'], db)
            return user
        except:
            return None

    def require_auth(self, required_role: UserRole = None):
        """Decorator to require authentication for CLI commands"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = self.get_current_user()
                if not user:
                    console.print("❌ Authentication required. Run 'reddit-analyzer auth login'", style="red")
                    raise typer.Exit(1)

                if required_role and not self.auth_service.require_role(user, required_role):
                    console.print(f"❌ {required_role.value} role required", style="red")
                    raise typer.Exit(1)

                return func(*args, **kwargs)
            return wrapper
        return decorator

# Global auth instance
cli_auth = CLIAuth()
```

### ASCII Visualization System
```python
from rich.table import Table
from rich.chart import Chart
from rich.panel import Panel
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

class ASCIIVisualizer:
    """ASCII-based visualization for terminal output"""

    def __init__(self):
        self.console = Console()

    def sentiment_bar_chart(self, data: dict) -> str:
        """Create ASCII bar chart for sentiment distribution"""
        table = Table(title="Sentiment Distribution")
        table.add_column("Sentiment", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        table.add_column("Bar", style="blue")

        total = sum(data.values())
        max_width = 40

        for sentiment, count in data.items():
            percentage = (count / total) * 100
            bar_length = int((count / max(data.values())) * max_width)
            bar = "█" * bar_length

            table.add_row(
                sentiment.title(),
                str(count),
                f"{percentage:.1f}%",
                bar
            )

        return table

    def trend_line_chart(self, dates: list, values: list, title: str) -> Panel:
        """Create ASCII line chart for trends"""
        # Normalize values for ASCII display
        min_val, max_val = min(values), max(values)
        height = 10
        width = 60

        normalized = [(v - min_val) / (max_val - min_val) * height for v in values]

        lines = []
        for i in range(height, -1, -1):
            line = ""
            for norm_val in normalized:
                if abs(norm_val - i) < 0.5:
                    line += "●"
                elif norm_val > i:
                    line += "│"
                else:
                    line += " "
            lines.append(line)

        chart_text = "\\n".join(lines)
        return Panel(chart_text, title=title, border_style="blue")

    def export_chart(self, data: dict, chart_type: str, filename: str):
        """Export chart as PNG using matplotlib"""
        plt.figure(figsize=(10, 6))

        if chart_type == "bar":
            plt.bar(data.keys(), data.values())
        elif chart_type == "line":
            plt.plot(list(data.keys()), list(data.values()))

        plt.title(f"Reddit Data Visualization")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        console.print(f"📊 Chart exported to {filename}", style="green")
```

### Database CLI Commands
```python
@data_app.command("init")
@cli_auth.require_auth(UserRole.ADMIN)
def init_database():
    """Initialize database with required tables and data"""
    with console.status("[bold green]Initializing database..."):
        try:
            # Run database migrations
            from alembic import command
            from alembic.config import Config

            config = Config("alembic.ini")
            command.upgrade(config, "head")

            console.print("✅ Database initialized successfully", style="green")
        except Exception as e:
            console.print(f"❌ Database initialization failed: {e}", style="red")

@data_app.command("migrate")
@cli_auth.require_auth(UserRole.ADMIN)
def migrate_database():
    """Run pending database migrations"""
    # Database migration logic
    pass

@data_app.command("backup")
@cli_auth.require_auth(UserRole.ADMIN)
def backup_database(output_file: str):
    """Create database backup"""
    # Database backup logic
    pass

@data_app.command("health")
@cli_auth.require_auth()
def database_health():
    """Check database health and performance"""
    with console.status("[bold blue]Checking database health..."):
        try:
            db = next(get_db())

            # Test database connection
            result = db.execute("SELECT 1").scalar()

            # Get table counts
            user_count = db.query(func.count(User.id)).scalar()
            post_count = db.query(func.count(Post.id)).scalar()

            table = Table(title="Database Health Check")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Connection", "✅ Healthy")
            table.add_row("Users", str(user_count))
            table.add_row("Posts", str(post_count))

            console.print(table)

        except Exception as e:
            console.print(f"❌ Database health check failed: {e}", style="red")
```

## CLI Command Examples

### Authentication Commands
```bash
# Login to the system
reddit-analyzer auth login
# Username: admin
# Password: ••••••••••
# ✅ Logged in as admin (admin)

# Check authentication status
reddit-analyzer auth status
# 👤 Logged in as: admin (admin)
# 🔑 Token expires: 2025-06-27 15:30:00
# ✅ Status: Active

# Logout
reddit-analyzer auth logout
# 👋 Logged out successfully
```

### Data Management Commands
```bash
# Initialize database (admin only)
reddit-analyzer data init
# ✅ Database initialized successfully

# Check data collection status
reddit-analyzer data status
# 📊 Data Collection Status
# ┌─────────────┬───────┬──────────────┬─────────────────────┐
# │ Subreddit   │ Posts │ Comments     │ Last Updated        │
# ├─────────────┼───────┼──────────────┼─────────────────────┤
# │ python      │ 1,250 │ 8,420        │ 2025-06-27 14:30:00 │
# │ datascience │ 890   │ 5,680        │ 2025-06-27 14:25:00 │
# └─────────────┴───────┴──────────────┴─────────────────────┘

# Collect data from subreddit
reddit-analyzer data collect --subreddit python --limit 100
# 🚀 Starting data collection from r/python
# [████████████████████████████████████████] 100% 100/100 posts
# ✅ Collected 100 posts and 456 comments

# Database health check
reddit-analyzer data health
# 📊 Database Health Check
# ┌────────────┬─────────────┐
# │ Metric     │ Value       │
# ├────────────┼─────────────┤
# │ Connection │ ✅ Healthy   │
# │ Users      │ 25          │
# │ Posts      │ 2,140       │
# │ Comments   │ 14,100      │
# └────────────┴─────────────┘
```

### Visualization Commands
```bash
# Show trending topics
reddit-analyzer viz trends --subreddit python --days 7
# 🔥 Trending Topics in r/python (Last 7 days)
# ┌──────────────────────────────┬───────────┬─────────────┐
# │ Topic                        │ Posts     │ Avg Score   │
# ├──────────────────────────────┼───────────┼─────────────┤
# │ machine learning, AI         │ 45        │ 127.3       │
# │ django, web development      │ 32        │ 89.2        │
# │ data analysis, pandas        │ 28        │ 156.8       │
# └──────────────────────────────┴───────────┴─────────────┘

# Show sentiment analysis
reddit-analyzer viz sentiment --subreddit python
# 😊 Sentiment Analysis for r/python
# ┌───────────┬───────┬─────────────┬──────────────────────────┐
# │ Sentiment │ Count │ Percentage  │ Bar                      │
# ├───────────┼───────┼─────────────┼──────────────────────────┤
# │ Positive  │ 856   │ 68.5%       │ ████████████████████████ │
# │ Neutral   │ 312   │ 25.0%       │ ████████                 │
# │ Negative  │ 82    │ 6.5%        │ ██                       │
# └───────────┴───────┴─────────────┴──────────────────────────┘

# Export visualization as PNG
reddit-analyzer viz sentiment --subreddit python --export sentiment_python.png
# 😊 Sentiment Analysis for r/python
# [ASCII chart display]
# 📊 Chart exported to sentiment_python.png

# Show user activity trends
reddit-analyzer viz activity --subreddit python --period 24h
# 📈 Activity Trends for r/python (Last 24 hours)
# Posts per hour:
#  24 ●
#  20 │  ●
#  16 │  │  ●
#  12 │  │  │    ●
#   8 │  │  │    │  ●
#   4 │  │  │    │  │    ●
#   0 └──┴──┴────┴──┴────┴──
#     00 04 08   12 16   20 24
```

### Reporting Commands
```bash
# Generate daily report
reddit-analyzer report daily --subreddit python
# 📋 Daily Report for r/python (2025-06-27)
#
# Summary:
# • Posts: 45 (+12% from yesterday)
# • Comments: 287 (+8% from yesterday)
# • Average Score: 156.3
# • Top Topic: "machine learning tutorial"
# • Sentiment: 72% positive, 22% neutral, 6% negative
#
# Top Posts:
# 1. "Complete Python ML Tutorial" (Score: 1,247)
# 2. "Django vs FastAPI Comparison" (Score: 892)
# 3. "Data Science with Pandas" (Score: 567)

# Export report as CSV
reddit-analyzer report export --subreddit python --format csv --output python_report.csv
# 📊 Report exported to python_report.csv
# Contains: 45 posts, 287 comments, sentiment analysis

# Schedule weekly report
reddit-analyzer report schedule --subreddit python --frequency weekly --email admin@example.com
# ⏰ Weekly report scheduled for r/python
# 📧 Will be sent to: admin@example.com
# 🗓️ Next report: 2025-07-04 09:00:00
```

### Admin Commands
```bash
# List all users (admin only)
reddit-analyzer admin users
# 👥 System Users
# ┌────┬─────────────┬───────────────────┬──────────┬────────────┐
# │ ID │ Username    │ Email             │ Role     │ Status     │
# ├────┼─────────────┼───────────────────┼──────────┼────────────┤
# │ 1  │ admin       │ admin@example.com │ admin    │ active     │
# │ 2  │ analyst1    │ user1@example.com │ user     │ active     │
# │ 3  │ moderator1  │ mod1@example.com  │ moderator│ active     │
# └────┴─────────────┴───────────────────┴──────────┴────────────┘

# Update user role (admin only)
reddit-analyzer admin update-role --username analyst1 --role moderator
# ✅ Updated analyst1 role to moderator

# System statistics (admin/moderator)
reddit-analyzer admin stats
# 📊 System Statistics
# ┌─────────────────┬─────────────┐
# │ Metric          │ Value       │
# ├─────────────────┼─────────────┤
# │ Total Users     │ 25          │
# │ Active Users    │ 23          │
# │ Total Subreddits│ 12          │
# │ Total Posts     │ 2,140       │
# │ Total Comments  │ 14,100      │
# │ Storage Used    │ 1.2 GB      │
# │ Last Backup     │ 2 hours ago │
# └─────────────────┴─────────────┘
```

## Database Setup Instructions

### PostgreSQL Setup with Authentication
```sql
-- Create database and user
CREATE DATABASE reddit_analyzer;
CREATE USER reddit_user WITH ENCRYPTED PASSWORD 'secure_password_here';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer TO reddit_user;
GRANT ALL ON SCHEMA public TO reddit_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO reddit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO reddit_user;

-- Create authentication-specific indexes for performance
CREATE INDEX CONCURRENTLY idx_users_username_active ON users(username) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_active = true AND email IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_users_role_active ON users(role) WHERE is_active = true;

-- Create materialized views for CLI performance
CREATE MATERIALIZED VIEW cli_subreddit_summary AS
SELECT
    s.name,
    COUNT(DISTINCT p.id) as post_count,
    COUNT(DISTINCT c.id) as comment_count,
    AVG(p.score) as avg_score,
    MAX(p.created_at) as last_activity,
    COUNT(DISTINCT p.author_id) as unique_authors
FROM subreddits s
LEFT JOIN posts p ON s.id = p.subreddit_id
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY s.id, s.name;

-- Refresh views automatically
CREATE OR REPLACE FUNCTION refresh_cli_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY cli_subreddit_summary;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to refresh views
CREATE OR REPLACE FUNCTION trigger_refresh_views()
RETURNS trigger AS $$
BEGIN
    PERFORM refresh_cli_views();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

### Environment Configuration

#### Development Environment Setup (.env.example)
```bash
# Database Configuration
DATABASE_URL=postgresql://reddit_user:CHANGE_THIS_PASSWORD@localhost:5432/reddit_analyzer
REDIS_URL=redis://localhost:6379/0

# Authentication Configuration
SECRET_KEY=GENERATE_SECURE_KEY_FOR_PRODUCTION
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=reddit-analyzer-cli/1.0.0
REDDIT_USERNAME=your_reddit_username_here
REDDIT_PASSWORD=your_reddit_password_here

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO

# CLI-specific Settings
CLI_CONFIG_DIR=~/.reddit-analyzer
CLI_LOG_LEVEL=INFO
CLI_EXPORT_DIR=./exports
CLI_MAX_RESULTS=1000
CLI_TIMEOUT_SECONDS=30
```

#### Production Environment (.env)
```bash
# SECURITY WARNING: Never commit this file to version control
# Copy from .env.example and update all placeholder values

# Database Configuration - Use strong passwords in production
DATABASE_URL=postgresql://reddit_user:$(openssl rand -base64 32)@localhost:5432/reddit_analyzer
REDIS_URL=redis://localhost:6379/0

# Authentication Configuration - Generate secure keys
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Shorter for production
REFRESH_TOKEN_EXPIRE_DAYS=7

# Reddit API Credentials
REDDIT_CLIENT_ID=actual_client_id
REDDIT_CLIENT_SECRET=actual_client_secret
REDDIT_USER_AGENT=reddit-analyzer-production/1.0.0
REDDIT_USERNAME=actual_username
REDDIT_PASSWORD=actual_password

# Production Configuration
APP_ENV=production
LOG_LEVEL=WARNING
```

### Complete Database Setup Process

#### Step 1: Install PostgreSQL and Redis
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib redis-server python3-dev

# macOS with Homebrew
brew install postgresql redis

# Start services
sudo systemctl start postgresql redis-server  # Linux
brew services start postgresql redis          # macOS
```

#### Step 2: Create Database and User Account
```bash
# Create database and user (run as postgres user)
sudo -u postgres psql << EOF
-- Create database
CREATE DATABASE reddit_analyzer;
CREATE DATABASE reddit_analyzer_test;

-- Create user with secure password
CREATE USER reddit_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer TO reddit_user;
GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer_test TO reddit_user;
GRANT ALL ON SCHEMA public TO reddit_user;

-- Additional permissions for authentication tables
ALTER USER reddit_user CREATEDB;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO reddit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO reddit_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO reddit_user;
EOF
```

#### Step 3: Initialize Application Database
```bash
# Set up environment
cd backend
source .venv/bin/activate

# Run database migrations for authentication system
alembic upgrade head

# Initialize CLI application
reddit-analyzer data init

# Create initial admin user
reddit-analyzer admin create-user \
  --username admin \
  --email admin@example.com \
  --role admin \
  --password "$(openssl rand -base64 32)"

# Set up performance views
reddit-analyzer admin setup-views
```

#### Step 4: Verify Setup
```bash
# Test database connection
reddit-analyzer data health

# Test authentication
reddit-analyzer auth login
# Username: admin
# Password: [enter the generated password]

# Test data collection
reddit-analyzer data collect --subreddit test --limit 10

# Test visualization
reddit-analyzer viz trends --subreddit test
```

### Security Configuration

#### Database Security Best Practices
```sql
-- Create dedicated user with minimal privileges
CREATE USER reddit_app WITH ENCRYPTED PASSWORD 'generated_secure_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE reddit_analyzer TO reddit_app;
GRANT USAGE ON SCHEMA public TO reddit_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO reddit_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO reddit_app;

-- Create read-only user for reporting
CREATE USER reddit_readonly WITH ENCRYPTED PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE reddit_analyzer TO reddit_readonly;
GRANT USAGE ON SCHEMA public TO reddit_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reddit_readonly;

-- Enable row level security for sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_isolation ON users FOR ALL TO reddit_app USING (true);
```

#### Environment Security
```bash
# Secure file permissions for environment files
chmod 600 backend/.env
chmod 644 backend/.env.example

# Secure CLI configuration directory
mkdir -p ~/.reddit-analyzer
chmod 700 ~/.reddit-analyzer

# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Database Migration Commands
```bash
# Initialize database with authentication tables
reddit-analyzer data init

# Run migrations to add new tables
reddit-analyzer data migrate

# Create initial admin user with secure password
reddit-analyzer admin create-user \
  --username admin \
  --email admin@example.com \
  --role admin \
  --generate-password

# Set up materialized views for performance
reddit-analyzer admin setup-views

# Create backup schedule
reddit-analyzer admin backup-schedule --frequency daily --retention 7

# Test all components
reddit-analyzer admin health-check --full
```

### Database Setup Troubleshooting

#### Common Issues and Solutions

**Issue: PostgreSQL connection refused**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Start PostgreSQL if not running
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS

# Check PostgreSQL configuration
sudo -u postgres psql -c "SHOW port;"
sudo -u postgres psql -c "SHOW listen_addresses;"
```

**Issue: Authentication failed for user**
```bash
# Check if user exists
sudo -u postgres psql -c "\du"

# Reset user password
sudo -u postgres psql -c "ALTER USER reddit_user PASSWORD 'new_password';"

# Check database permissions
sudo -u postgres psql -c "\l" | grep reddit_analyzer
sudo -u postgres psql reddit_analyzer -c "\dp"
```

**Issue: Alembic migration errors**
```bash
# Check current migration status
cd backend && alembic current

# Check pending migrations
alembic heads
alembic history

# Force migration to specific version
alembic stamp head
alembic upgrade head --sql  # Show SQL without executing
```

**Issue: Redis connection errors**
```bash
# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli config get "*"

# Restart Redis
sudo systemctl restart redis-server  # Linux
brew services restart redis  # macOS
```

#### Setup Validation Script
```bash
#!/bin/bash
# validate_setup.sh - Comprehensive setup validation

echo "🔍 Validating Reddit Analyzer Setup..."

# Check PostgreSQL
echo "Checking PostgreSQL..."
if pg_isready -h localhost -p 5432; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not accessible"
    exit 1
fi

# Check Redis
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not accessible"
    exit 1
fi

# Check database connection
echo "Checking database connection..."
cd backend
source .venv/bin/activate
python -c "
from app.database import get_db
try:
    db = next(get_db())
    db.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Check authentication system
echo "Checking authentication system..."
python -c "
from app.models.user import User
from app.utils.auth import get_auth_service
print('✅ Authentication system imported successfully')
"

# Check CLI installation
echo "Checking CLI installation..."
if command -v reddit-analyzer &> /dev/null; then
    echo "✅ CLI is installed"
    reddit-analyzer --help > /dev/null
    echo "✅ CLI is functional"
else
    echo "❌ CLI is not installed"
    exit 1
fi

echo "🎉 All setup validation checks passed!"
```

### Quick Start Guide

#### For New Users (Complete Setup)
```bash
# 1. Clone repository and install dependencies
git clone https://github.com/your-repo/reddit_analyzer.git
cd reddit_analyzer
./scripts/setup.sh

# 2. Set up database (follow prompts)
./scripts/db_setup.sh

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your Reddit API credentials

# 4. Initialize application
cd backend && source .venv/bin/activate
reddit-analyzer data init
reddit-analyzer admin create-user --username admin --role admin

# 5. Test setup
reddit-analyzer auth login
reddit-analyzer data health
reddit-analyzer viz --help
```

#### For Existing Users (Update Only)
```bash
# 1. Update codebase
git pull origin main

# 2. Update dependencies
cd backend && uv sync --extra cli

# 3. Run migrations
alembic upgrade head

# 4. Update CLI
pip install -e .

# 5. Verify everything works
reddit-analyzer data health
reddit-analyzer auth status
```

### Reddit API Setup Requirements

#### Creating Reddit API Account
Before you can use the Reddit Analyzer, you need to set up a Reddit API application:

1. **Create Reddit Account**
   - Go to [reddit.com](https://reddit.com) and create an account if you don't have one
   - Verify your email address

2. **Create Reddit App**
   - Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
   - Click "Create App" or "Create Another App"
   - Fill in the form:
     - **Name**: `Reddit Analyzer CLI`
     - **App type**: `script`
     - **Description**: `Data analysis tool for Reddit content`
     - **About URL**: Leave blank
     - **Redirect URI**: `http://localhost:8080` (required but not used)

3. **Get API Credentials**
   After creating the app, you'll see:
   - **Client ID**: The string under your app name (looks like: `abc123def456`)
   - **Client Secret**: The "secret" field (looks like: `abc123def456ghi789jkl012`)

4. **Update Environment File**
```bash
# Add to backend/.env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=reddit-analyzer-cli/1.0.0
```

#### Testing Reddit API Connection
```bash
# Test Reddit API credentials
reddit-analyzer data test-reddit-connection

# Expected output:
# ✅ Reddit API connection successful
# 📊 Account: your_username
# 🔑 API Rate Limit: 60 requests/minute
# 📅 Account Created: 2020-01-01
```

#### Reddit API Rate Limits
- **Personal use script**: 60 requests per minute
- **OAuth app**: 60 requests per minute per user
- **Production**: Contact Reddit for higher limits

The CLI automatically handles rate limiting and will show progress for large data collection operations.

## File Structure Extensions
```
backend/
├── app/
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # Main CLI application
│   │   ├── auth.py              # Authentication commands
│   │   ├── data.py              # Data management commands
│   │   ├── visualization.py     # Visualization commands
│   │   ├── reports.py           # Reporting commands
│   │   ├── admin.py             # Admin commands
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── ascii_charts.py  # ASCII visualization utilities
│   │       ├── formatters.py    # Output formatting utilities
│   │       ├── exporters.py     # Export functionality
│   │       └── auth_manager.py  # CLI authentication manager
│   ├── api/
│   │   └── cli_endpoints.py     # API endpoints for CLI data access
│   └── schemas/
│       ├── cli_responses.py     # CLI-specific response schemas
│       └── cli_commands.py      # Command validation schemas
├── scripts/
│   ├── setup_cli.sh            # CLI setup script
│   ├── install_deps.sh         # Dependency installation
│   └── db_setup.sql            # Database setup SQL
└── cli_requirements.txt        # CLI-specific dependencies
```

## Dependencies Updates

### CLI Dependencies (pyproject.toml)
```toml
[project.optional-dependencies]
cli = [
    "typer[all]>=0.7.0",
    "rich>=12.0.0",
    "click>=8.0.0",
    "matplotlib>=3.5.0",
    "seaborn>=0.11.0",
    "tabulate>=0.9.0",
    "plotext>=5.0.0",
    "ascii-graph>=1.5.0",
    "questionary>=1.10.0",
    "keyring>=23.0.0",
    "cryptography>=37.0.0",
    "schedule>=1.1.0"
]
```

### Installation Commands
```bash
# Install CLI dependencies
cd backend && uv sync --extra cli

# Install CLI as executable
cd backend && pip install -e .

# Verify installation
reddit-analyzer --help
```

## Success Criteria
- [ ] CLI authenticates users using existing JWT system
- [ ] All database operations work through CLI commands
- [ ] ASCII visualizations display correctly in terminal
- [ ] Export functionality creates PNG/CSV files
- [ ] Admin commands respect role-based permissions
- [ ] CLI performance under 2 seconds for most commands
- [ ] Authentication tokens stored securely
- [ ] Database health monitoring works accurately
- [ ] Report generation completes within 10 seconds
- [ ] CLI works across different terminal environments

## Testing Strategy

### Manual Testing Checklist
- [ ] Authentication flow (login/logout/status)
- [ ] Data collection and status monitoring
- [ ] ASCII chart generation and display
- [ ] Export functionality (PNG, CSV, JSON)
- [ ] Admin command access control
- [ ] Database health and migration commands
- [ ] Report generation and scheduling
- [ ] Error handling and user feedback
- [ ] Cross-platform compatibility
- [ ] Performance with large datasets

### Integration Testing
- [ ] CLI authentication with backend JWT system
- [ ] Database operations through CLI
- [ ] Export file generation and validation
- [ ] Role-based access control enforcement
- [ ] Error handling for network/database issues

## Security Considerations
- [ ] Secure token storage in user home directory
- [ ] File permissions (600) for credential files
- [ ] Input validation for all CLI parameters
- [ ] SQL injection prevention in database queries
- [ ] Role-based access control for admin commands
- [ ] Secure password prompts (hidden input)
- [ ] Session timeout and token refresh

## Performance Optimizations
- [ ] Database query optimization with indexes
- [ ] Materialized views for frequently accessed data
- [ ] Caching for repeated CLI operations
- [ ] Lazy loading for large datasets
- [ ] Progress bars for long-running operations
- [ ] Concurrent processing where applicable

## Next Phase Integration
This CLI foundation will support:
- API testing and validation for Phase 4B web dashboard
- Data quality verification before web interface development
- Admin tools for production deployment management
- Performance benchmarking for API optimization
- User workflow testing and refinement

## Deliverables
1. Complete CLI application with authentication integration
2. ASCII-based visualization system
3. Database management and monitoring tools
4. Report generation and export capabilities
5. Admin tools for user and system management
6. Documentation and usage examples
7. Installation and setup scripts
8. Testing framework for CLI operations

The CLI provides immediate functionality for testing and validates the authentication system while building the foundation for the full web dashboard in Phase 4B.
