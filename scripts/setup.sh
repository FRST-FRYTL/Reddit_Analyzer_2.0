#!/bin/bash
set -e

echo "🚀 Setting up Reddit Analyzer development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on supported OS
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for Linux and macOS"
    exit 1
fi

# Install system dependencies (requires sudo)
echo "📦 Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    echo "Detected Ubuntu/Debian system"
    print_warning "This step requires sudo access for system packages"
    echo "Run the following commands manually if needed:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y python3-dev postgresql postgresql-contrib redis-server"
elif command -v brew &> /dev/null; then
    # macOS with Homebrew
    echo "Detected macOS with Homebrew"
    print_warning "Installing PostgreSQL and Redis via Homebrew..."
    brew install postgresql redis
    print_status "macOS dependencies installed"
else
    print_warning "Could not detect package manager. Please install PostgreSQL and Redis manually."
fi

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo "📥 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env || source $HOME/.local/bin/env
    print_status "uv installed successfully"
else
    print_status "uv already installed"
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
cd backend
if [ ! -d ".venv" ]; then
    uv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Install dependencies
echo "📚 Installing Python dependencies..."
uv sync --extra dev
print_status "Dependencies installed"

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
cd ..
source backend/.venv/bin/activate
pre-commit install
print_status "Pre-commit hooks installed"

# Set up environment file
echo "⚙️  Setting up environment configuration..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    print_warning "Environment file created from example. Please update with your Reddit API credentials."
    print_warning "Edit backend/.env and add your Reddit API credentials:"
    echo "  - REDDIT_CLIENT_ID"
    echo "  - REDDIT_CLIENT_SECRET"
    echo "  - REDDIT_USERNAME"
    echo "  - REDDIT_PASSWORD"
else
    print_status "Environment file already exists"
fi

# Test basic setup
echo "🧪 Testing basic setup..."
if python scripts/test_basic_setup.py; then
    print_status "Basic setup tests passed"
else
    print_error "Basic setup tests failed"
    exit 1
fi

# Database setup instructions
echo ""
echo "🗄️  Database Setup Instructions:"
echo "1. Start PostgreSQL service:"
if command -v systemctl &> /dev/null; then
    echo "   sudo systemctl start postgresql"
    echo "   sudo systemctl enable postgresql"
elif command -v brew &> /dev/null; then
    echo "   brew services start postgresql"
fi
echo ""
echo "2. Create database and user:"
echo "   sudo -u postgres createdb reddit_analyzer"
echo "   sudo -u postgres createuser reddit_user"
echo "   sudo -u postgres psql -c \"ALTER USER reddit_user WITH PASSWORD 'password';\""
echo "   sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE reddit_analyzer TO reddit_user;\""
echo ""
echo "3. Run database migrations:"
echo "   cd backend && source .venv/bin/activate && alembic upgrade head"
echo ""

# Redis setup instructions
echo "🔴 Redis Setup Instructions:"
if command -v systemctl &> /dev/null; then
    echo "   sudo systemctl start redis-server"
    echo "   sudo systemctl enable redis-server"
elif command -v brew &> /dev/null; then
    echo "   brew services start redis"
fi
echo ""

# Final instructions
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your Reddit API credentials"
echo "2. Set up database (see instructions above)"
echo "3. Start Redis (see instructions above)"
echo "4. Run tests: cd backend && source .venv/bin/activate && pytest"
echo "5. Test Reddit API: python scripts/test_connection.py"
echo ""
echo "Development workflow:"
echo "- Activate environment: source backend/.venv/bin/activate"
echo "- Run tests: cd backend && pytest"
echo "- Format code: cd backend && black . && ruff check ."
echo "- Install new packages: cd backend && uv add package_name"
echo ""
print_status "Reddit Analyzer development environment is ready!"
