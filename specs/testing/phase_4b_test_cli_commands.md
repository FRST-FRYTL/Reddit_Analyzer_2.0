# Phase 4B CLI Commands Test Specification

## Overview
This document provides comprehensive test specifications for all CLI commands in the Reddit Analyzer application. Each command should be tested to ensure 100% functionality.

## Test Environment Setup

### Prerequisites
- [ ] Python 3.9+ installed
- [ ] PostgreSQL running (or SQLite for development)
- [ ] Redis server running
- [ ] Valid Reddit API credentials in `.env`
- [ ] Application installed with `uv sync --extra cli --extra dev`
- [ ] Database migrations applied with `alembic upgrade head`
- [ ] Test admin user created

### Test User Accounts
```bash
# Create test users with different roles
uv run reddit-analyzer admin create-user --username admin_test --password admin123 --email admin@test.com --role admin
uv run reddit-analyzer admin create-user --username mod_test --password mod123 --email mod@test.com --role moderator
uv run reddit-analyzer admin create-user --username user_test --password user123 --email user@test.com --role user
```

## Command Test Specifications

### 1. General Commands

#### 1.1 Help Command
```bash
uv run reddit-analyzer --help
```
**Expected Output**:
- Display main command groups (auth, data, viz, report, admin, status, version)
- Show brief description for each command group
- Exit code: 0

#### 1.2 Status Command
```bash
uv run reddit-analyzer status
```
**Expected Output**:
- Database connection status (✓ or ✗)
- Redis connection status (✓ or ✗)
- Reddit API connection status (✓ or ✗)
- Authentication status (logged in/out)
- Exit code: 0

#### 1.3 Version Command
```bash
uv run reddit-analyzer version
```
**Expected Output**:
- Application version (0.1.0)
- Python version
- Exit code: 0

### 2. Authentication Commands

#### 2.1 Login Command
```bash
# Test successful login
uv run reddit-analyzer auth login --username user_test --password user123
```
**Expected Output**:
- "Successfully logged in as user_test"
- Token saved to ~/.reddit-analyzer/tokens.json
- Exit code: 0

**Error Cases**:
```bash
# Invalid credentials
uv run reddit-analyzer auth login --username user_test --password wrong_password
```
- Error message: "Invalid username or password"
- Exit code: 1

#### 2.2 Status Command
```bash
uv run reddit-analyzer auth status
```
**Expected Output (when logged in)**:
- "Logged in as: user_test"
- "Role: user"
- "Token expires: [timestamp]"
- Exit code: 0

**Expected Output (when logged out)**:
- "Not logged in"
- Exit code: 0

#### 2.3 Whoami Command
```bash
uv run reddit-analyzer auth whoami
```
**Expected Output (when logged in)**:
- Username
- Email
- Role
- Account created date
- Exit code: 0

**Error Case (when logged out)**:
- "Not authenticated. Please login first."
- Exit code: 1

#### 2.4 Logout Command
```bash
uv run reddit-analyzer auth logout
```
**Expected Output**:
- "Successfully logged out"
- Token file cleared
- Exit code: 0

### 3. Data Management Commands

#### 3.1 Data Status Command
```bash
uv run reddit-analyzer data status
```
**Expected Output**:
- Total posts count
- Total comments count
- Total subreddits tracked
- Total users tracked
- Last collection timestamp
- Exit code: 0

#### 3.2 Data Health Command
```bash
uv run reddit-analyzer data health
```
**Expected Output**:
- Database connection: OK/Failed
- Table status for each model
- Index status
- Redis connection: OK/Failed
- Exit code: 0

#### 3.3 Data Collect Command
```bash
uv run reddit-analyzer data collect --subreddit python --limit 10
```
**Expected Output**:
- Progress bar showing collection
- "Collected X posts from r/python"
- Exit code: 0

**Error Cases**:
- Invalid subreddit: "Subreddit not found"
- API rate limit: "Rate limit exceeded"

### 4. Visualization Commands

#### 4.1 Trends Command
```bash
uv run reddit-analyzer viz trends --subreddit python --days 7
```
**Expected Output**:
- ASCII chart showing trending posts
- Top 10 posts by score
- Time period label
- Exit code: 0

**Variations**:
```bash
# Different time periods
uv run reddit-analyzer viz trends --subreddit python --days 1
uv run reddit-analyzer viz trends --subreddit python --days 30

# Different subreddits
uv run reddit-analyzer viz trends --subreddit javascript
uv run reddit-analyzer viz trends --subreddit datascience
```

#### 4.2 Sentiment Command
```bash
uv run reddit-analyzer viz sentiment python
```
**Expected Output**:
- ASCII chart showing sentiment distribution
- Positive/Negative/Neutral percentages
- Sample posts for each sentiment
- Exit code: 0

#### 4.3 Activity Command
```bash
uv run reddit-analyzer viz activity --subreddit python --period daily
```
**Expected Output**:
- ASCII chart showing activity over time
- Post counts per time period
- Comment counts per time period
- Exit code: 0

**Variations**:
```bash
# Different periods
uv run reddit-analyzer viz activity --subreddit python --period hourly
uv run reddit-analyzer viz activity --subreddit python --period weekly
```

### 5. Report Commands

#### 5.1 Daily Report Command
```bash
uv run reddit-analyzer report daily --subreddit python
```
**Expected Output**:
- Daily summary statistics
- Top posts of the day
- Most active users
- Sentiment summary
- Exit code: 0

**With Date Parameter**:
```bash
uv run reddit-analyzer report daily --subreddit python --date 2025-06-29
```

#### 5.2 Weekly Report Command
```bash
uv run reddit-analyzer report weekly --subreddit python
```
**Expected Output**:
- Weekly summary statistics
- Top posts of the week
- Trend analysis
- User engagement metrics
- Exit code: 0

**With Weeks Parameter**:
```bash
uv run reddit-analyzer report weekly --subreddit python --weeks 2
```

#### 5.3 Export Command
```bash
# CSV Export
uv run reddit-analyzer report export --format csv --output test_data.csv
```
**Expected Output**:
- "Data exported to test_data.csv"
- File created with headers and data
- Exit code: 0

```bash
# JSON Export
uv run reddit-analyzer report export --format json --output test_data.json
```
**Expected Output**:
- "Data exported to test_data.json"
- Valid JSON file created
- Exit code: 0

### 6. Admin Commands (Requires Admin Role)

#### 6.1 Admin Stats Command
```bash
# Login as admin first
uv run reddit-analyzer auth login --username admin_test --password admin123
uv run reddit-analyzer admin stats
```
**Expected Output**:
- Total users count by role
- Database size
- Cache statistics
- API usage statistics
- Exit code: 0

**Error Case (non-admin user)**:
```bash
# Login as regular user
uv run reddit-analyzer auth login --username user_test --password user123
uv run reddit-analyzer admin stats
```
- Error: "Admin access required"
- Exit code: 1

#### 6.2 Admin Users Command
```bash
uv run reddit-analyzer admin users
```
**Expected Output**:
- Table of all users
- Columns: ID, Username, Email, Role, Created
- Exit code: 0

#### 6.3 Admin Health Check Command
```bash
uv run reddit-analyzer admin health-check
```
**Expected Output**:
- System health overview
- Database checks
- Redis checks
- API connectivity
- Disk space
- Memory usage
- Exit code: 0

### 7. Error Handling Tests

#### 7.1 Database Connection Error
```bash
# Stop PostgreSQL/Redis, then run
uv run reddit-analyzer status
```
**Expected Output**:
- Database: ✗ Failed
- Appropriate error message
- Exit code: 1

#### 7.2 Invalid Command
```bash
uv run reddit-analyzer invalid-command
```
**Expected Output**:
- "Error: No such command 'invalid-command'"
- Help text
- Exit code: 2

#### 7.3 Missing Required Parameters
```bash
uv run reddit-analyzer viz trends
```
**Expected Output**:
- "Error: Missing required option '--subreddit'"
- Exit code: 2

## Test Execution Plan

### Phase 1: Basic Functionality
1. Test help and version commands
2. Test authentication flow (login, status, whoami, logout)
3. Test basic status command

### Phase 2: Data Commands
1. Test data status with empty database
2. Collect sample data
3. Test data status with populated database
4. Test data health checks

### Phase 3: Visualization Commands
1. Test each visualization type with sample data
2. Test different time periods and parameters
3. Verify ASCII chart rendering

### Phase 4: Report Generation
1. Test daily reports
2. Test weekly reports
3. Test data export in different formats

### Phase 5: Admin Functions
1. Test with admin user
2. Test access control (non-admin rejection)
3. Test user management
4. Test system health checks

### Phase 6: Error Scenarios
1. Test with stopped services
2. Test with invalid inputs
3. Test rate limiting
4. Test edge cases

## Success Criteria

- [ ] All commands execute without Python errors
- [ ] All commands return appropriate exit codes
- [ ] Help text is available for all commands
- [ ] Authentication properly restricts access
- [ ] Data visualizations render correctly in terminal
- [ ] Reports generate valid output files
- [ ] Error messages are clear and helpful
- [ ] Commands handle missing/invalid parameters gracefully

## Test Automation Script

Create `test_all_cli_commands.py`:
```python
#!/usr/bin/env python3
import subprocess
import sys
import json
import os

def run_command(cmd):
    """Run a CLI command and return result"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {
        'command': cmd,
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'success': result.returncode == 0
    }

def test_all_commands():
    """Run all CLI command tests"""
    tests = [
        # General commands
        "uv run reddit-analyzer --help",
        "uv run reddit-analyzer status",
        "uv run reddit-analyzer version",

        # Add more commands here...
    ]

    results = []
    for test in tests:
        print(f"Testing: {test}")
        result = run_command(test)
        results.append(result)
        print(f"  Result: {'✓' if result['success'] else '✗'}")

    # Summary
    passed = sum(1 for r in results if r['success'])
    print(f"\nTotal: {len(results)}, Passed: {passed}, Failed: {len(results) - passed}")

    return results

if __name__ == "__main__":
    test_all_commands()
```

## Notes

1. Some commands require authentication - test both authenticated and unauthenticated states
2. Admin commands require admin role - test access control
3. Data visualization commands require data in database - populate test data first
4. Export commands create files - verify file creation and cleanup after tests
5. Some commands may have rate limits when using real Reddit API
6. Consider using mock data for consistent testing

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify test users are created
   - Check token file permissions (~/.reddit-analyzer/tokens.json)
   - Ensure SECRET_KEY is set in .env

2. **Database Connection Errors**
   - Verify PostgreSQL/Redis are running
   - Check DATABASE_URL in .env
   - Run migrations: `alembic upgrade head`

3. **API Rate Limits**
   - Use smaller limits for data collection
   - Add delays between API calls
   - Consider using cached/mock data for testing

4. **Missing Dependencies**
   - Run `uv sync --extra cli --extra dev`
   - Verify all packages installed correctly
   - Check Python version compatibility
