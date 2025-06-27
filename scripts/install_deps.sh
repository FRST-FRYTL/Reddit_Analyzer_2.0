#!/bin/bash
set -e

echo "📦 Installing Reddit Analyzer dependencies with uv..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Navigate to backend directory
if [ ! -d "backend" ]; then
    print_error "backend directory not found. Please run from project root."
    exit 1
fi

cd backend

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found in backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    uv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Install core dependencies
echo "📚 Installing core dependencies..."
uv sync
print_status "Core dependencies installed"

# Install development dependencies
echo "🛠️  Installing development dependencies..."
uv sync --extra dev
print_status "Development dependencies installed"

# Verify installation
echo "🧪 Verifying installation..."

# Check if key packages are installed
echo "Checking key packages..."
source .venv/bin/activate

# Test imports
if python -c "import praw, sqlalchemy, redis, fastapi, pytest; print('✅ All key packages imported successfully')" 2>/dev/null; then
    print_status "Package verification passed"
else
    print_error "Package verification failed"
    exit 1
fi

# Check versions
echo ""
echo "📋 Installed package versions:"
echo "Python: $(python --version)"
echo "uv: $(uv --version)"
uv pip list | grep -E "(praw|sqlalchemy|fastapi|redis|pytest|black|ruff)" | sed 's/^/  /'

echo ""
print_status "Dependencies installed successfully!"
echo ""
echo "Usage:"
echo "  Activate environment: source backend/.venv/bin/activate"
echo "  Run tests: cd backend && pytest"
echo "  Install new package: cd backend && uv add package_name"
echo "  Update dependencies: cd backend && uv sync"
