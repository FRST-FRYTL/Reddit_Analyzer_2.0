# Phase 4B CLI Commands Test Report

**Generated**: 2025-06-30 15:55:57

## Summary

- **Total Tests**: 38
- **Passed**: 26 ✓
- **Failed**: 12 ✗
- **Success Rate**: 68.4%
- **Duration**: 38.62 seconds

## Failed Tests

### ❌ Create test user (may already exist)
- **Command**: `uv run reddit-analyzer admin create-user --username user_test --password user123 --email user@test.com --role user`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin create-user [OPTIONS]
Try 'reddit-analyzer admin create-user --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such o...

### ❌ Data collection status
- **Command**: `uv run reddit-analyzer data status`
- **Exit Code**: 1 (expected: 0)

### ❌ Database health check
- **Command**: `uv run reddit-analyzer data health`
- **Exit Code**: 1 (expected: 0)

### ❌ Collect sample data from r/python
- **Command**: `uv run reddit-analyzer data collect --subreddit python --limit 5`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer data collect [OPTIONS] SUBREDDIT
Try 'reddit-analyzer data collect --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such o...

### ❌ Show trending posts for r/python
- **Command**: `uv run reddit-analyzer viz trends --subreddit python --days 7`
- **Exit Code**: 1 (expected: 0)

### ❌ Sentiment analysis for r/python
- **Command**: `uv run reddit-analyzer viz sentiment python`
- **Exit Code**: 1 (expected: 0)

### ❌ Activity trends for r/python
- **Command**: `uv run reddit-analyzer viz activity --subreddit python --period daily`
- **Exit Code**: 1 (expected: 0)

### ❌ Generate daily report for r/python
- **Command**: `uv run reddit-analyzer report daily --subreddit python`
- **Exit Code**: 1 (expected: 0)

### ❌ Generate weekly report for r/python
- **Command**: `uv run reddit-analyzer report weekly --subreddit python`
- **Exit Code**: 1 (expected: 0)

### ❌ Export data to CSV
- **Command**: `uv run reddit-analyzer report export --format csv --output /tmp/test_export.csv`
- **Exit Code**: 1 (expected: 0)

### ❌ Export data to JSON
- **Command**: `uv run reddit-analyzer report export --format json --output /tmp/test_export.json`
- **Exit Code**: 1 (expected: 0)

### ❌ Create admin test user (may already exist)
- **Command**: `uv run reddit-analyzer admin create-user --username admin_test --password admin123 --email admin@test.com --role admin`
- **Exit Code**: 2 (expected: 0)
- **Error**: Usage: reddit-analyzer admin create-user [OPTIONS]
Try 'reddit-analyzer admin create-user --help' for help.
╭─ Error ──────────────────────────────────────────────────────────────────────╮
│ No such o...

## All Test Results

| Status | Command | Duration | Exit Code |
|--------|---------|----------|----------|
| ✓ | uv run reddit-analyzer --help | 0.94s | 0 |
| ✓ | uv run reddit-analyzer status | 0.91s | 0 |
| ✓ | uv run reddit-analyzer version | 1.02s | 0 |
| ✓ | uv run reddit-analyzer auth --help | 0.88s | 0 |
| ✓ | uv run reddit-analyzer auth status | 0.84s | 0 |
| ✓ | uv run reddit-analyzer auth login --username wrong... | 0.90s | 1 |
| ✗ | uv run reddit-analyzer admin create-user --usernam... | 1.00s | 2 |
| ✓ | uv run reddit-analyzer auth login --username user_... | 1.23s | 0 |
| ✓ | uv run reddit-analyzer auth status | 1.18s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | 1.18s | 0 |
| ✓ | uv run reddit-analyzer auth logout | 0.97s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | 0.95s | 1 |
| ✓ | uv run reddit-analyzer data --help | 0.95s | 0 |
| ✗ | uv run reddit-analyzer data status | 0.93s | 1 |
| ✗ | uv run reddit-analyzer data health | 0.94s | 1 |
| ✗ | uv run reddit-analyzer data collect --subreddit py... | 0.94s | 2 |
| ✓ | uv run reddit-analyzer viz --help | 1.16s | 0 |
| ✗ | uv run reddit-analyzer viz trends --subreddit pyth... | 1.81s | 1 |
| ✗ | uv run reddit-analyzer viz sentiment python | 0.92s | 1 |
| ✗ | uv run reddit-analyzer viz activity --subreddit py... | 1.00s | 1 |
| ✓ | uv run reddit-analyzer report --help | 0.90s | 0 |
| ✗ | uv run reddit-analyzer report daily --subreddit py... | 0.97s | 1 |
| ✗ | uv run reddit-analyzer report weekly --subreddit p... | 0.99s | 1 |
| ✗ | uv run reddit-analyzer report export --format csv ... | 0.95s | 1 |
| ✗ | uv run reddit-analyzer report export --format json... | 0.98s | 1 |
| ✓ | uv run reddit-analyzer admin --help | 1.17s | 0 |
| ✓ | uv run reddit-analyzer admin stats | 0.95s | 1 |
| ✗ | uv run reddit-analyzer admin create-user --usernam... | 0.89s | 2 |
| ✓ | uv run reddit-analyzer auth login --username user_... | 1.15s | 0 |
| ✓ | uv run reddit-analyzer admin stats | 0.89s | 1 |
| ✓ | uv run reddit-analyzer auth logout | 0.91s | 0 |
| ✓ | uv run reddit-analyzer auth login --username admin... | 1.17s | 0 |
| ✓ | uv run reddit-analyzer admin stats | 0.93s | 0 |
| ✓ | uv run reddit-analyzer admin users | 1.03s | 0 |
| ✓ | uv run reddit-analyzer admin health-check | 1.18s | 0 |
| ✓ | uv run reddit-analyzer invalid-command | 1.07s | 2 |
| ✓ | uv run reddit-analyzer viz trends | 0.86s | 2 |
| ✓ | uv run reddit-analyzer viz trends --subreddit this... | 0.99s | 1 |
