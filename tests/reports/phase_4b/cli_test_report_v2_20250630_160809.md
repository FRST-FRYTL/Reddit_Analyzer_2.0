# Phase 4B CLI Commands Test Report V2

**Generated**: 2025-06-30 16:08:09

## Summary

- **Total Tests**: 46
- **Passed**: 41 ✓
- **Failed**: 5 ✗
- **Success Rate**: 89.1%
- **Duration**: 47.95 seconds

## Failed Tests

### ❌ Show trending posts for r/python
- **Command**: `uv run reddit-analyzer viz trends --subreddit python --days 7`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

### ❌ Sentiment analysis for r/python
- **Command**: `uv run reddit-analyzer viz sentiment python`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

### ❌ Activity trends for r/python
- **Command**: `uv run reddit-analyzer viz activity --subreddit python --period daily`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

### ❌ Generate daily report for r/python
- **Command**: `uv run reddit-analyzer report daily --subreddit python`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

### ❌ Generate weekly report for r/python
- **Command**: `uv run reddit-analyzer report weekly --subreddit python`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

## All Test Results

| Status | Command | Auth | Duration | Exit Code |
|--------|---------|------|----------|----------|
| ✓ | uv run reddit-analyzer --help | - | 1.14s | 0 |
| ✓ | uv run reddit-analyzer status | - | 0.93s | 0 |
| ✓ | uv run reddit-analyzer version | - | 0.92s | 0 |
| ✓ | uv run reddit-analyzer auth --help | - | 0.97s | 0 |
| ✓ | uv run reddit-analyzer auth status | - | 1.01s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 0.94s | 1 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.13s | 0 |
| ✓ | uv run reddit-analyzer auth status | user_test | 0.96s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | user_test | 1.02s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.89s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | - | 0.94s | 1 |
| ✓ | uv run reddit-analyzer data --help | - | 0.96s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.13s | 0 |
| ✓ | uv run reddit-analyzer data status | user_test | 0.91s | 0 |
| ✓ | uv run reddit-analyzer data health | user_test | 0.92s | 0 |
| ✓ | uv run reddit-analyzer data collect pyth... | user_test | 2.11s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 1.40s | 0 |
| ✓ | uv run reddit-analyzer viz --help | - | 0.96s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.26s | 0 |
| ✗ | uv run reddit-analyzer viz trends --subr... | user_test | 1.02s | 1 |
| ✗ | uv run reddit-analyzer viz sentiment pyt... | user_test | 0.97s | 1 |
| ✗ | uv run reddit-analyzer viz activity --su... | user_test | 1.01s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.92s | 0 |
| ✓ | uv run reddit-analyzer report --help | - | 1.00s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.21s | 0 |
| ✗ | uv run reddit-analyzer report daily --su... | user_test | 0.99s | 1 |
| ✗ | uv run reddit-analyzer report weekly --s... | user_test | 0.99s | 1 |
| ✓ | uv run reddit-analyzer report export --f... | user_test | 0.96s | 0 |
| ✓ | uv run reddit-analyzer report export --f... | user_test | 1.00s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 1.02s | 0 |
| ✓ | uv run reddit-analyzer admin --help | - | 0.89s | 0 |
| ✓ | uv run reddit-analyzer admin stats | - | 0.91s | 1 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.16s | 0 |
| ✓ | uv run reddit-analyzer admin stats | user_test | 1.10s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 1.03s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.25s | 0 |
| ✓ | uv run reddit-analyzer admin stats | admin_test | 1.01s | 0 |
| ✓ | uv run reddit-analyzer admin users | admin_test | 0.96s | 0 |
| ✓ | uv run reddit-analyzer admin health-chec... | admin_test | 0.97s | 0 |
| ✓ | uv run reddit-analyzer admin create-user... | admin_test | 1.18s | 0 |
| ✓ | uv run reddit-analyzer auth logout | admin_test | 0.89s | 0 |
| ✓ | uv run reddit-analyzer invalid-command | - | 0.89s | 2 |
| ✓ | uv run reddit-analyzer viz trends | - | 0.90s | 2 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.26s | 0 |
| ✓ | uv run reddit-analyzer viz trends --subr... | user_test | 1.06s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.90s | 0 |
