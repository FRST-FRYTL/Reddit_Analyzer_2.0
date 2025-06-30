# Phase 4B CLI Commands Test Report V2

**Generated**: 2025-06-30 16:21:50

## Summary

- **Total Tests**: 46
- **Passed**: 44 ✓
- **Failed**: 2 ✗
- **Success Rate**: 95.7%
- **Duration**: 47.99 seconds

## Failed Tests

### ❌ Activity trends for r/python
- **Command**: `uv run reddit-analyzer viz activity --subreddit python --period daily`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: user_test

### ❌ Create user with generated password
- **Command**: `uv run reddit-analyzer admin create-user --username test_new_user --email test_new@test.com --role user --generate-password`
- **Exit Code**: 1 (expected: 0)
- **Authenticated as**: admin_test

## All Test Results

| Status | Command | Auth | Duration | Exit Code |
|--------|---------|------|----------|----------|
| ✓ | uv run reddit-analyzer --help | - | 1.11s | 0 |
| ✓ | uv run reddit-analyzer status | - | 0.96s | 0 |
| ✓ | uv run reddit-analyzer version | - | 1.11s | 0 |
| ✓ | uv run reddit-analyzer auth --help | - | 1.02s | 0 |
| ✓ | uv run reddit-analyzer auth status | - | 0.93s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 0.94s | 1 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.18s | 0 |
| ✓ | uv run reddit-analyzer auth status | user_test | 0.91s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | user_test | 0.94s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.89s | 0 |
| ✓ | uv run reddit-analyzer auth whoami | - | 0.89s | 1 |
| ✓ | uv run reddit-analyzer data --help | - | 0.88s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.13s | 0 |
| ✓ | uv run reddit-analyzer data status | user_test | 1.04s | 0 |
| ✓ | uv run reddit-analyzer data health | user_test | 0.92s | 0 |
| ✓ | uv run reddit-analyzer data collect pyth... | user_test | 2.72s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 1.57s | 0 |
| ✓ | uv run reddit-analyzer viz --help | - | 0.99s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.15s | 0 |
| ✓ | uv run reddit-analyzer viz trends --subr... | user_test | 0.94s | 0 |
| ✓ | uv run reddit-analyzer viz sentiment pyt... | user_test | 0.93s | 0 |
| ✗ | uv run reddit-analyzer viz activity --su... | user_test | 0.98s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.87s | 0 |
| ✓ | uv run reddit-analyzer report --help | - | 0.79s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.06s | 0 |
| ✓ | uv run reddit-analyzer report daily --su... | user_test | 0.93s | 0 |
| ✓ | uv run reddit-analyzer report weekly --s... | user_test | 0.91s | 0 |
| ✓ | uv run reddit-analyzer report export --f... | user_test | 0.93s | 0 |
| ✓ | uv run reddit-analyzer report export --f... | user_test | 0.92s | 0 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.90s | 0 |
| ✓ | uv run reddit-analyzer admin --help | - | 0.88s | 0 |
| ✓ | uv run reddit-analyzer admin stats | - | 0.90s | 1 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.16s | 0 |
| ✓ | uv run reddit-analyzer admin stats | user_test | 0.92s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 0.89s | 0 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.35s | 0 |
| ✓ | uv run reddit-analyzer admin stats | admin_test | 1.04s | 0 |
| ✓ | uv run reddit-analyzer admin users | admin_test | 1.17s | 0 |
| ✓ | uv run reddit-analyzer admin health-chec... | admin_test | 0.93s | 0 |
| ✗ | uv run reddit-analyzer admin create-user... | admin_test | 0.95s | 1 |
| ✓ | uv run reddit-analyzer auth logout | admin_test | 1.00s | 0 |
| ✓ | uv run reddit-analyzer invalid-command | - | 1.00s | 2 |
| ✓ | uv run reddit-analyzer viz trends | - | 1.06s | 2 |
| ✓ | uv run reddit-analyzer auth login --user... | - | 1.26s | 0 |
| ✓ | uv run reddit-analyzer viz trends --subr... | user_test | 1.02s | 1 |
| ✓ | uv run reddit-analyzer auth logout | user_test | 1.00s | 0 |
