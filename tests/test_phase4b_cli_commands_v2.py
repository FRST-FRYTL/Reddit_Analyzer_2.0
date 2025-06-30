#!/usr/bin/env python3
"""
Phase 4B CLI Commands Test Suite V2
Improved version with proper authentication state management
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import time


class ImprovedCLITester:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.test_users = {
            "admin": {
                "username": "admin_test",
                "password": "admin123",
                "email": "admin@test.com",
                "role": "admin",
            },
            "moderator": {
                "username": "mod_test",
                "password": "mod123",
                "email": "mod@test.com",
                "role": "moderator",
            },
            "user": {
                "username": "user_test",
                "password": "user123",
                "email": "user@test.com",
                "role": "user",
            },
        }
        self.current_user = None

    def run_command(self, cmd, expected_exit_code=0, description=None):
        """Run a CLI command and return result"""
        print(f"\n{'=' * 60}")
        print(f"Testing: {cmd}")
        if description:
            print(f"Description: {description}")
        if self.current_user:
            print(f"Authenticated as: {self.current_user}")
        print(f"{'=' * 60}")

        start = time.time()
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        duration = time.time() - start

        success = result.returncode == expected_exit_code

        test_result = {
            "command": cmd,
            "description": description or cmd,
            "exit_code": result.returncode,
            "expected_exit_code": expected_exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "authenticated_as": self.current_user,
        }

        self.results.append(test_result)

        # Print immediate result
        print(f"Exit Code: {result.returncode} (expected: {expected_exit_code})")
        print(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
        print(f"Duration: {duration:.2f}s")

        if result.stdout:
            print(
                f"\nOutput:\n{result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}"
            )
        if result.stderr:
            print(
                f"\nError:\n{result.stderr[:500]}{'...' if len(result.stderr) > 500 else ''}"
            )

        return test_result

    def login(self, user_type="user"):
        """Helper to login as a specific user type"""
        user = self.test_users[user_type]
        result = self.run_command(
            f"uv run reddit-analyzer auth login --username {user['username']} "
            f"--password {user['password']}",
            description=f"Login as {user_type} user",
        )
        if result["success"]:
            self.current_user = user["username"]
        return result["success"]

    def logout(self):
        """Helper to logout"""
        result = self.run_command("uv run reddit-analyzer auth logout")
        if result["success"]:
            self.current_user = None
        return result["success"]

    def test_general_commands(self):
        """Test general commands like help, status, version"""
        print("\n\n" + "=" * 80)
        print("TESTING GENERAL COMMANDS")
        print("=" * 80)

        # Help command
        self.run_command(
            "uv run reddit-analyzer --help", description="Main help command"
        )

        # Status command
        self.run_command(
            "uv run reddit-analyzer status", description="System status check"
        )

        # Version command
        self.run_command(
            "uv run reddit-analyzer version", description="Version information"
        )

    def test_auth_commands(self):
        """Test authentication commands"""
        print("\n\n" + "=" * 80)
        print("TESTING AUTHENTICATION COMMANDS")
        print("=" * 80)

        # Auth help
        self.run_command(
            "uv run reddit-analyzer auth --help", description="Auth command help"
        )

        # Check initial auth status
        self.run_command(
            "uv run reddit-analyzer auth status",
            description="Auth status (not logged in)",
        )

        # Test login with wrong credentials
        self.run_command(
            "uv run reddit-analyzer auth login --username wrong_user --password wrong_pass",
            expected_exit_code=1,
            description="Login with invalid credentials",
        )

        # Test login with valid credentials
        self.login("user")

        # Check auth status after login
        self.run_command(
            "uv run reddit-analyzer auth status", description="Auth status (logged in)"
        )

        # Whoami command
        self.run_command(
            "uv run reddit-analyzer auth whoami", description="Current user information"
        )

        # Logout
        self.logout()

        # Whoami after logout (should fail)
        self.run_command(
            "uv run reddit-analyzer auth whoami",
            expected_exit_code=1,
            description="Whoami when not authenticated",
        )

    def test_data_commands(self):
        """Test data management commands"""
        print("\n\n" + "=" * 80)
        print("TESTING DATA MANAGEMENT COMMANDS")
        print("=" * 80)

        # Data help
        self.run_command(
            "uv run reddit-analyzer data --help", description="Data command help"
        )

        # Login first for authenticated commands
        self.login("user")

        # Data status
        self.run_command(
            "uv run reddit-analyzer data status", description="Data collection status"
        )

        # Data health
        self.run_command(
            "uv run reddit-analyzer data health", description="Database health check"
        )

        # Data collect (correct syntax - SUBREDDIT is positional)
        self.run_command(
            "uv run reddit-analyzer data collect python --limit 5",
            description="Collect sample data from r/python",
        )

        # Logout after tests
        self.logout()

    def test_viz_commands(self):
        """Test visualization commands"""
        print("\n\n" + "=" * 80)
        print("TESTING VISUALIZATION COMMANDS")
        print("=" * 80)

        # Viz help
        self.run_command(
            "uv run reddit-analyzer viz --help",
            description="Visualization command help",
        )

        # Login first
        self.login("user")

        # Trends command
        self.run_command(
            "uv run reddit-analyzer viz trends --subreddit python --days 7",
            description="Show trending posts for r/python",
        )

        # Sentiment command
        self.run_command(
            "uv run reddit-analyzer viz sentiment python",
            description="Sentiment analysis for r/python",
        )

        # Activity command
        self.run_command(
            "uv run reddit-analyzer viz activity --subreddit python --period daily",
            description="Activity trends for r/python",
        )

        # Logout after tests
        self.logout()

    def test_report_commands(self):
        """Test report generation commands"""
        print("\n\n" + "=" * 80)
        print("TESTING REPORT COMMANDS")
        print("=" * 80)

        # Report help
        self.run_command(
            "uv run reddit-analyzer report --help", description="Report command help"
        )

        # Login first
        self.login("user")

        # Daily report
        self.run_command(
            "uv run reddit-analyzer report daily --subreddit python",
            description="Generate daily report for r/python",
        )

        # Weekly report
        self.run_command(
            "uv run reddit-analyzer report weekly --subreddit python",
            description="Generate weekly report for r/python",
        )

        # Export to CSV
        self.run_command(
            "uv run reddit-analyzer report export --format csv --output /tmp/test_export.csv",
            description="Export data to CSV",
        )

        # Export to JSON
        self.run_command(
            "uv run reddit-analyzer report export --format json --output /tmp/test_export.json",
            description="Export data to JSON",
        )

        # Verify exports
        if os.path.exists("/tmp/test_export.csv"):
            print("✓ CSV export file created successfully")
            os.remove("/tmp/test_export.csv")

        if os.path.exists("/tmp/test_export.json"):
            print("✓ JSON export file created successfully")
            os.remove("/tmp/test_export.json")

        # Logout after tests
        self.logout()

    def test_admin_commands(self):
        """Test admin commands with proper authentication"""
        print("\n\n" + "=" * 80)
        print("TESTING ADMIN COMMANDS")
        print("=" * 80)

        # Admin help
        self.run_command(
            "uv run reddit-analyzer admin --help", description="Admin command help"
        )

        # Try admin command without auth (should fail)
        self.run_command(
            "uv run reddit-analyzer admin stats",
            expected_exit_code=1,
            description="Admin stats without authentication",
        )

        # Login as regular user first
        self.login("user")

        # Try admin command as regular user (should fail)
        self.run_command(
            "uv run reddit-analyzer admin stats",
            expected_exit_code=1,
            description="Admin stats as regular user",
        )

        # Logout and login as admin
        self.logout()
        self.login("admin")

        # Admin stats
        self.run_command(
            "uv run reddit-analyzer admin stats",
            description="Admin stats with admin auth",
        )

        # Admin users
        self.run_command(
            "uv run reddit-analyzer admin users", description="List all users"
        )

        # Admin health check
        self.run_command(
            "uv run reddit-analyzer admin health-check",
            description="Full system health check",
        )

        # Test admin create-user with --generate-password
        self.run_command(
            "uv run reddit-analyzer admin create-user --username test_new_user "
            "--email test_new@test.com --role user --generate-password",
            description="Create user with generated password",
        )

        # Logout after tests
        self.logout()

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n\n" + "=" * 80)
        print("TESTING ERROR HANDLING")
        print("=" * 80)

        # Invalid command
        self.run_command(
            "uv run reddit-analyzer invalid-command",
            expected_exit_code=2,
            description="Invalid command",
        )

        # Missing required parameter
        self.run_command(
            "uv run reddit-analyzer viz trends",
            expected_exit_code=2,
            description="Missing required --subreddit parameter",
        )

        # Login first for authenticated test
        self.login("user")

        # Invalid subreddit
        self.run_command(
            "uv run reddit-analyzer viz trends --subreddit this_subreddit_does_not_exist_12345",
            expected_exit_code=1,
            description="Invalid subreddit name",
        )

        # Logout
        self.logout()

    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Create report
        report = {
            "summary": {
                "title": "Phase 4B CLI Commands Test Report V2",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
            },
            "test_results": self.results,
            "failed_tests": [r for r in self.results if not r["success"]],
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cwd": os.getcwd(),
            },
        }

        # Create reports directory
        reports_dir = Path("tests/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON report
        json_path = (
            reports_dir
            / f"cli_test_report_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)

        # Create markdown report
        md_path = (
            reports_dir
            / f"cli_test_report_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(md_path, "w") as f:
            f.write("# Phase 4B CLI Commands Test Report V2\n\n")
            f.write(f"**Generated**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Passed**: {passed_tests} ✓\n")
            f.write(f"- **Failed**: {failed_tests} ✗\n")
            f.write(f"- **Success Rate**: {success_rate:.1f}%\n")
            f.write(f"- **Duration**: {duration:.2f} seconds\n\n")

            if failed_tests > 0:
                f.write("## Failed Tests\n\n")
                for test in report["failed_tests"]:
                    f.write(f"### ❌ {test['description']}\n")
                    f.write(f"- **Command**: `{test['command']}`\n")
                    f.write(
                        f"- **Exit Code**: {test['exit_code']} (expected: {test['expected_exit_code']})\n"
                    )
                    f.write(
                        f"- **Authenticated as**: {test.get('authenticated_as', 'None')}\n"
                    )
                    if test["stderr"]:
                        f.write(f"- **Error**: {test['stderr'][:200]}...\n")
                    f.write("\n")

            f.write("## All Test Results\n\n")
            f.write("| Status | Command | Auth | Duration | Exit Code |\n")
            f.write("|--------|---------|------|----------|----------|\n")
            for test in self.results:
                status = "✓" if test["success"] else "✗"
                cmd = (
                    test["command"][:40] + "..."
                    if len(test["command"]) > 40
                    else test["command"]
                )
                auth = test.get("authenticated_as") or "-"
                f.write(
                    f"| {status} | {cmd} | {auth} | {test['duration']:.2f}s | {test['exit_code']} |\n"
                )

        # Print summary
        print("\n\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✓")
        print(f"Failed: {failed_tests} ✗")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print("\nReports saved:")
        print(f"  - JSON: {json_path}")
        print(f"  - Markdown: {md_path}")

        return report


def main():
    """Run all CLI tests"""
    tester = ImprovedCLITester()

    try:
        # Run all test categories
        tester.test_general_commands()
        tester.test_auth_commands()
        tester.test_data_commands()
        tester.test_viz_commands()
        tester.test_report_commands()
        tester.test_admin_commands()
        tester.test_error_handling()

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
    finally:
        # Always generate report
        report = tester.generate_report()

        # Exit with appropriate code
        sys.exit(0 if report["summary"]["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
