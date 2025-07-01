#!/usr/bin/env python3
"""List all users in the database without requiring authentication."""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from reddit_analyzer.models.user import User
from reddit_analyzer.config import Config
from rich.console import Console
from rich.table import Table

console = Console()


def list_users():
    """List all users in the database."""
    # Create engine directly
    engine = create_engine(Config.DATABASE_URL)

    with Session(engine) as session:
        # Query all users
        users = session.execute(select(User).order_by(User.created_at)).scalars().all()

        if not users:
            console.print("[yellow]No users found in database[/yellow]")
            return

        # Create table
        table = Table(title="Existing Users in Database")
        table.add_column("ID", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Email", style="blue")
        table.add_column("Role", style="magenta")
        table.add_column("Active", style="yellow")
        table.add_column("Created", style="dim")

        for user in users:
            table.add_row(
                str(user.id),
                user.username,
                user.email or "N/A",
                user.role.value,
                "✓" if user.is_active else "✗",
                user.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"\n[green]Total users: {len(users)}[/green]")

        # Show test user credentials hint
        console.print(
            "\n[yellow]Hint: Check scripts/setup_test_users.py or scripts/create_test_users.py for test credentials[/yellow]"
        )


if __name__ == "__main__":
    try:
        list_users()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
