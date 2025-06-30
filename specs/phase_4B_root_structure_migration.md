# Phase 4B: Root Structure Migration

## Overview

Migrate the Reddit Analyzer project from the current backend-subfolder structure to a standard Python package root structure. This will improve developer experience, follow Python packaging conventions, and simplify CLI usage.

## Current Structure Issues

- CLI commands require `cd backend && uv run reddit-analyzer`
- Non-standard Python project layout
- Complicates development workflow
- Backend folder creates unnecessary nesting
- Breaks IDE auto-detection patterns

## Target Structure

```
reddit_analyzer/
├── reddit_analyzer/           # Main package (renamed from backend/app/)
│   ├── __init__.py
│   ├── cli/                   # CLI commands
│   ├── models/                # Database models  
│   ├── services/              # Business logic
│   ├── utils/                 # Utilities
│   ├── api/                   # API endpoints (future)
│   ├── middleware/            # Middleware
│   ├── config.py
│   └── database.py
├── tests/                     # Test suite (moved from backend/tests/)
├── alembic/                   # Database migrations (moved from backend/alembic/)
├── scripts/                   # Setup and utility scripts
├── database/                  # Database initialization
├── specs/                     # Documentation
├── pyproject.toml             # Package configuration (moved from backend/)
├── .env.example               # Environment template
├── .pre-commit-config.yaml    # Pre-commit hooks
├── README.md
└── CLAUDE.md
```

## Migration Tasks

### Phase 1: Package Structure Migration

#### 1.1 Create New Package Directory
- [ ] Create `reddit_analyzer/` package directory at root
- [ ] Create `reddit_analyzer/__init__.py` with package metadata
- [ ] Move `backend/app/` contents to `reddit_analyzer/`
- [ ] Update all internal imports from `app.` to `reddit_analyzer.`

#### 1.2 Configuration Migration  
- [ ] Move `backend/pyproject.toml` to root
- [ ] Update package name from `reddit-analyzer` to `reddit_analyzer` 
- [ ] Update CLI entry point path: `reddit_analyzer.cli.main:app`
- [ ] Move `backend/.env` to root as `.env.example`
- [ ] Move `backend/.env.example` to root (if exists)

#### 1.3 Development Files Migration
- [ ] Move `backend/tests/` to `tests/`
- [ ] Move `backend/alembic/` to `alembic/`
- [ ] Update `alembic.ini` database connection path
- [ ] Move `backend/.pre-commit-config.yaml` to root (if exists)

### Phase 2: Import and Path Updates

#### 2.1 Update Import Statements
- [ ] Update all `from app.` imports to `from reddit_analyzer.`
- [ ] Update CLI modules import paths
- [ ] Update test import statements
- [ ] Update alembic migration imports

#### 2.2 Update Configuration Files
- [ ] Update `alembic/env.py` imports
- [ ] Update `pyproject.toml` package discovery
- [ ] Update any hardcoded paths in config files
- [ ] Update `.gitignore` paths if needed

#### 2.3 Update Documentation
- [ ] Update `README.md` installation instructions
- [ ] Update `CLAUDE.md` development commands
- [ ] Update command examples to remove `cd backend`
- [ ] Update project structure diagram

### Phase 3: Testing and Validation

#### 3.1 Import Validation
- [ ] Verify all imports resolve correctly
- [ ] Test CLI commands from root directory
- [ ] Validate database connections work
- [ ] Check alembic migrations function

#### 3.2 Functional Testing
- [ ] Run complete test suite: `pytest`
- [ ] Test CLI installation: `uv sync --extra cli`
- [ ] Test CLI commands: `uv run reddit-analyzer --help`
- [ ] Verify Reddit API connection works
- [ ] Test database operations

#### 3.3 Development Workflow
- [ ] Test development setup from scratch
- [ ] Verify pre-commit hooks work
- [ ] Test code formatting: `black .` and `ruff check .`
- [ ] Validate environment setup script

### Phase 4: Cleanup and Optimization

#### 4.1 Remove Legacy Structure
- [ ] Delete empty `backend/` directory
- [ ] Clean up any remaining backend references
- [ ] Update any shell scripts or automation

#### 4.2 Optimization
- [ ] Optimize package imports for faster CLI startup
- [ ] Review and clean up `__init__.py` files
- [ ] Ensure minimal import overhead for CLI

## Migration Script

Create automated migration script: `scripts/migrate_to_root.sh`

```bash
#!/bin/bash
# Phase 4B Migration Script

set -e

echo "🚀 Starting Phase 4B: Root Structure Migration"

# 1. Create new package structure
echo "📁 Creating new package structure..."
mkdir -p reddit_analyzer
mv backend/app/* reddit_analyzer/
mv backend/tests .
mv backend/alembic .
mv backend/pyproject.toml .

# 2. Update imports (requires manual verification)
echo "🔄 Updating import statements..."
find reddit_analyzer tests alembic -name "*.py" -exec sed -i 's/from app\./from reddit_analyzer\./g' {} \;
find reddit_analyzer tests alembic -name "*.py" -exec sed -i 's/import app\./import reddit_analyzer\./g' {} \;

# 3. Update pyproject.toml
echo "⚙️  Updating configuration..."
sed -i 's/reddit-analyzer = "app\.cli\.main:app"/reddit-analyzer = "reddit_analyzer.cli.main:app"/' pyproject.toml

# 4. Environment setup
echo "🔧 Setting up environment..."
if [ -f backend/.env ]; then
    cp backend/.env .env.example
fi

# 5. Cleanup
echo "🧹 Cleaning up..."
rm -rf backend/

echo "✅ Migration complete! Run 'uv sync --extra cli' to reinstall."
```

## Validation Checklist

### ✅ Pre-Migration Verification
- [ ] Backup current working directory
- [ ] Commit all current changes
- [ ] Document current CLI commands that work
- [ ] List all import paths for verification

### ✅ Post-Migration Validation  
- [ ] `uv sync --extra cli` succeeds
- [ ] `uv run reddit-analyzer --help` works from root
- [ ] `uv run reddit-analyzer status` connects to database
- [ ] `pytest` passes all tests
- [ ] CLI demo script works: `python cli_demo.py`
- [ ] Code quality tools work: `black .` and `ruff check .`

## Rollback Plan

If migration fails:
1. **Git Reset**: `git reset --hard HEAD` (if committed)
2. **Manual Rollback**: Restore from backup
3. **Selective Revert**: Move files back to `backend/` structure

## Benefits After Migration

### ✅ Developer Experience
- Run CLI from project root: `uv run reddit-analyzer`
- Standard Python project layout
- Better IDE integration and auto-completion
- Simplified development commands

### ✅ Operations
- Cleaner deployment process
- Standard packaging and distribution
- Easier CI/CD pipeline configuration
- Better Docker container structure

### ✅ Community Standards
- Follows Python packaging best practices
- Matches open source project conventions
- Easier for contributors to understand
- Better documentation and examples

## Risk Assessment

### 🟡 Medium Risk
- **Import path changes**: Requires careful find/replace
- **Configuration updates**: Multiple files need path updates
- **Testing disruption**: Temporary test failures during migration

### 🟢 Low Risk  
- **Rollback available**: Git provides easy recovery
- **Non-breaking**: No external API changes
- **Incremental**: Can be done step-by-step

## Timeline

- **Planning**: 30 minutes
- **Migration execution**: 2-3 hours
- **Testing and validation**: 1-2 hours  
- **Documentation updates**: 1 hour
- **Total**: ~6 hours

## Success Criteria

1. ✅ CLI works from root: `uv run reddit-analyzer --help`
2. ✅ All tests pass: `pytest`
3. ✅ Database connections work
4. ✅ Reddit API integration functions
5. ✅ Code quality tools pass
6. ✅ Development workflow simplified
7. ✅ Documentation updated

## Dependencies

- Current Phase 4A CLI implementation must be working
- All tests should be passing before migration
- Database and Reddit API credentials configured
- Git repository should be clean

## Frontend Integration Benefits

### 🚀 Future-Proof Architecture

The root structure migration **improves** frontend integration rather than hindering it:

#### ✅ Modern Full-Stack Patterns
```
reddit_analyzer/
├── reddit_analyzer/           # Python backend package
│   ├── cli/                   # CLI commands ✓
│   ├── api/                   # FastAPI endpoints (future)
│   ├── models/                # Shared data models
│   ├── services/              # Business logic (CLI + API)
│   └── utils/                 # Utilities
├── frontend/                  # React/Vue/Next.js (future)
│   ├── src/
│   ├── package.json
│   └── dist/
├── tests/
├── docker-compose.yml         # Full-stack orchestration
└── pyproject.toml
```

#### ✅ Key Advantages for Frontend Development

1. **Shared Business Logic**
   - CLI and API reuse same `reddit_analyzer.services`
   - Consistent data models across CLI and web interface
   - DRY principle maintained

2. **API-First Development**
   ```python
   # reddit_analyzer/api/posts.py
   from reddit_analyzer.services.reddit_client import RedditClient
   
   @app.get("/api/subreddit/{name}/posts")
   async def get_posts(name: str):
       client = RedditClient()  # Same service as CLI!
       return client.get_subreddit_posts(name)
   ```

3. **Standard Project Layout**
   - Frontend developers immediately understand structure
   - Follows patterns from Django, FastAPI, Flask projects
   - Better IDE support and tooling integration

4. **Simplified Deployment**
   ```dockerfile
   # Single Dockerfile for full-stack
   FROM python:3.9
   COPY reddit_analyzer/ reddit_analyzer/
   COPY frontend/dist/ static/
   RUN pip install .
   CMD ["uvicorn", "reddit_analyzer.api:app", "--host", "0.0.0.0"]
   ```

5. **Development Workflow**
   ```bash
   # All commands from project root
   uv run reddit-analyzer status           # CLI tool
   uvicorn reddit_analyzer.api:app         # API server
   cd frontend && npm run dev               # Frontend dev server
   docker-compose up                       # Full stack
   ```

#### 🎯 No Disadvantages

The migration **eliminates** common full-stack development pain points:
- ❌ No more nested `backend/` confusion
- ❌ No import path complications
- ❌ No deployment complexity from non-standard structure
- ✅ Standard Python package that frontend can easily consume

## Next Phase

After successful migration, Phase 4B enables:
- **Phase 5**: Web API development with FastAPI (enhanced by shared services)
- **Phase 6**: Frontend integration (simplified by standard structure)
- **Production deployment** improvements (containerization, orchestration)
- **Package distribution** to PyPI (standard packaging)

## Future Integration Examples

### Shared Data Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CLI Commands   │    │  FastAPI Web    │    │  React Frontend │
│                 │    │     API         │    │                 │
│ reddit-analyzer │───▶│ /api/posts      │───▶│ Dashboard UI    │
│ viz trends      │    │ /api/sentiment  │    │ Charts & Graphs │
│                 │    │ /api/reports    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────▼───────────────────────┘
                   reddit_analyzer.services
                   (Shared Business Logic)
```

### Technology Stack Evolution
- **Phase 4A**: CLI with ASCII visualizations ✓
- **Phase 4B**: Root structure migration ✓  
- **Phase 5**: FastAPI web API (reuses CLI services)
- **Phase 6**: React/Vue frontend (consumes API)
- **Phase 7**: Real-time dashboards (WebSocket integration)

---

*This migration aligns the Reddit Analyzer with Python packaging best practices, significantly improves the developer experience, and creates an optimal foundation for full-stack development.*