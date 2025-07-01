# Test Users for Reddit Analyzer CLI

The following test users have been created for testing the Reddit Analyzer CLI:

## Test User Credentials

| Username   | Password      | Role       | Description                           |
|------------|---------------|------------|---------------------------------------|
| testuser   | testpass123   | user       | Basic user with standard permissions  |
| testmod    | modpass123    | moderator  | Moderator with enhanced permissions   |
| testadmin  | adminpass123  | admin      | Administrator with full access        |

## Scripts

- **create_test_users.py** - Creates the test users in the database
- **verify_test_users.py** - Verifies that test users can authenticate
- **reset_test_users.py** - Resets passwords for existing test users

## Usage

To create test users:
```bash
uv run python scripts/create_test_users.py
```

To verify authentication:
```bash
uv run python scripts/verify_test_users.py
```

To reset passwords:
```bash
uv run python scripts/reset_test_users.py
```

## Testing with CLI

You can use these test users to test the CLI authentication:

```bash
# Login as regular user
uv run reddit-analyzer auth login --username testuser --password testpass123

# Login as moderator
uv run reddit-analyzer auth login --username testmod --password modpass123

# Login as admin
uv run reddit-analyzer auth login --username testadmin --password adminpass123

# Check authentication status
uv run reddit-analyzer auth status
```
