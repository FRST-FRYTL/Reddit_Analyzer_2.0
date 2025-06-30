# Phase 4B CLI Commands Test Report

**Generated**: 2025-06-30 15:43:00

## Summary

- **Total Tests**: 38
- **Passed**: 17 ✓
- **Failed**: 21 ✗
- **Success Rate**: 44.7%
- **Duration**: 36.09 seconds

## Failed Tests

### ❌ Create test user (may already exist)
- **Command**: `uv run reddit-analyzer admin create-user --username user_test --password user123 --email user@test.com --role user`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin create-user [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin create-user --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮...

### ❌ Login with valid credentials
- **Command**: `uv run reddit-analyzer auth login --username user_test --password user123`
- **Exit Code**: 1 (expected: 0)

### ❌ Data collection status
- **Command**: `uv run reddit-analyzer data status`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer data status [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer data status --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ Database health check
- **Command**: `uv run reddit-analyzer data health`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer data health [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer data health --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ Collect sample data from r/python
- **Command**: `uv run reddit-analyzer data collect --subreddit python --limit 5`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer data collect [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer data collect --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such...

### ❌ Show trending posts for r/python
- **Command**: `uv run reddit-analyzer viz trends --subreddit python --days 7`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer viz trends [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer viz trends --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such opt...

### ❌ Sentiment analysis for r/python
- **Command**: `uv run reddit-analyzer viz sentiment python`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer viz sentiment [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer viz sentiment --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missi...

### ❌ Activity trends for r/python
- **Command**: `uv run reddit-analyzer viz activity --subreddit python --period daily`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer viz activity [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer viz activity --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such...

### ❌ Generate daily report for r/python
- **Command**: `uv run reddit-analyzer report daily --subreddit python`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer report daily [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer report daily --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such...

### ❌ Generate weekly report for r/python
- **Command**: `uv run reddit-analyzer report weekly --subreddit python`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer report weekly [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer report weekly --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No su...

### ❌ Export data to CSV
- **Command**: `uv run reddit-analyzer report export --format csv --output /tmp/test_export.csv`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer report export [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer report export --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No su...

### ❌ Export data to JSON
- **Command**: `uv run reddit-analyzer report export --format json --output /tmp/test_export.json`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer report export [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer report export --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No su...

### ❌ Admin stats without authentication
- **Command**: `uv run reddit-analyzer admin stats`
- **Exit Code**: 2 (expected: 1)
- **Error**: Usage: reddit-analyzer admin stats [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin stats --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ Create admin test user (may already exist)
- **Command**: `uv run reddit-analyzer admin create-user --username admin_test --password admin123 --email admin@test.com --role admin`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin create-user [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin create-user --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮...

### ❌ Login as regular user
- **Command**: `uv run reddit-analyzer auth login --username user_test --password user123`
- **Exit Code**: 1 (expected: 0)

### ❌ Admin stats as regular user
- **Command**: `uv run reddit-analyzer admin stats`
- **Exit Code**: 2 (expected: 1)
- **Error**: Usage: reddit-analyzer admin stats [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin stats --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ Login as admin user
- **Command**: `uv run reddit-analyzer auth login --username admin_test --password admin123`
- **Exit Code**: 1 (expected: 0)

### ❌ Admin stats with admin auth
- **Command**: `uv run reddit-analyzer admin stats`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin stats [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin stats --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ List all users
- **Command**: `uv run reddit-analyzer admin users`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin users [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin users --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ Missing a...

### ❌ Full system health check
- **Command**: `uv run reddit-analyzer admin health-check`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin health-check [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer admin health-check --help' for help.
╭─ Error ─────────────────────────────────────────────────────────────────────...

### ❌ Invalid subreddit name
- **Command**: `uv run reddit-analyzer viz trends --subreddit this_subreddit_does_not_exist_12345`
- **Exit Code**: 2 (expected: 1)
- **Error**: Usage: reddit-analyzer viz trends [OPTIONS] ARGS KWARGS
Try 'reddit-analyzer viz trends --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such opt...

## All Test Results

| Status | Command | Duration | Exit Code |
|--------|---------|----------|----------|
| ✓ | uv run reddit-analyzer --help | 1.70s | 0 |
| ✓ | uv run reddit-analyzer status | 0.93s | 0 |
| ✓ | uv run reddit-analyzer version | 0.89s | 0 |
| ✓ | uv run reddit-analyzer auth --help | 0.90s | 0 |
| ✓ | uv run reddit-analyzer auth status | 0.91s | 0 |
| ✓ | uv run reddit-analyzer auth login --username wrong... | 0.92s | 1 |
| ✗ | uv run reddit-analyzer admin create-user --usernam... | 0.90s | 2 |
| ✗ | uv run reddit-analyzer auth login --username user_... | 0.92s | 1 |
| ✓ | uv run reddit-analyzer auth status | 0.92s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | 1.07s | 0 |
| ✓ | uv run reddit-analyzer auth logout | 0.88s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | 0.88s | 1 |
| ✓ | uv run reddit-analyzer data --help | 0.89s | 0 |
| ✗ | uv run reddit-analyzer data status | 0.89s | 2 |
| ✗ | uv run reddit-analyzer data health | 0.88s | 2 |
| ✗ | uv run reddit-analyzer data collect --subreddit py... | 0.87s | 2 |
| ✓ | uv run reddit-analyzer viz --help | 0.87s | 0 |
| ✗ | uv run reddit-analyzer viz trends --subreddit pyth... | 0.88s | 2 |
| ✗ | uv run reddit-analyzer viz sentiment python | 0.86s | 2 |
| ✗ | uv run reddit-analyzer viz activity --subreddit py... | 0.87s | 2 |
| ✓ | uv run reddit-analyzer report --help | 0.88s | 0 |
| ✗ | uv run reddit-analyzer report daily --subreddit py... | 0.87s | 2 |
| ✗ | uv run reddit-analyzer report weekly --subreddit p... | 0.88s | 2 |
| ✗ | uv run reddit-analyzer report export --format csv ... | 0.88s | 2 |
| ✗ | uv run reddit-analyzer report export --format json... | 0.86s | 2 |
| ✓ | uv run reddit-analyzer admin --help | 0.89s | 0 |
| ✗ | uv run reddit-analyzer admin stats | 0.97s | 2 |
| ✗ | uv run reddit-analyzer admin create-user --usernam... | 1.14s | 2 |
| ✗ | uv run reddit-analyzer auth login --username user_... | 1.07s | 1 |
| ✗ | uv run reddit-analyzer admin stats | 0.92s | 2 |
| ✓ | uv run reddit-analyzer auth logout | 0.91s | 0 |
| ✗ | uv run reddit-analyzer auth login --username admin... | 0.93s | 1 |
| ✗ | uv run reddit-analyzer admin stats | 0.88s | 2 |
| ✗ | uv run reddit-analyzer admin users | 0.90s | 2 |
| ✗ | uv run reddit-analyzer admin health-check | 0.87s | 2 |
| ✓ | uv run reddit-analyzer invalid-command | 1.59s | 2 |
| ✓ | uv run reddit-analyzer viz trends | 0.89s | 2 |
| ✗ | uv run reddit-analyzer viz trends --subreddit this... | 0.93s | 2 |
