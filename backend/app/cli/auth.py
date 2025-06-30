"""Authentication CLI commands."""

import typer
from rich.console import Console
from rich.prompt import Prompt

from app.cli.utils.auth_manager import cli_auth

auth_app = typer.Typer(help="Authentication commands")
console = Console()


@auth_app.command("login")
def login(
    username: str = typer.Option(None, "--username", "-u", help="Username"),
    password: str = typer.Option(None, "--password", "-p", help="Password (will prompt if not provided)")
):
    """Login to Reddit Analyzer."""
    if not username:
        username = Prompt.ask("Username")
    
    if not password:
        password = Prompt.ask("Password", password=True)
    
    success = cli_auth.login(username, password)
    if not success:
        raise typer.Exit(1)


@auth_app.command("logout")
def logout():
    """Logout from Reddit Analyzer."""
    success = cli_auth.logout()
    if not success:
        raise typer.Exit(1)


@auth_app.command("status")
def status():
    """Show current authentication status."""
    cli_auth.auth_status()


@auth_app.command("whoami")
def whoami():
    """Show current user information."""
    user = cli_auth.get_current_user()
    
    if user:
        from rich.table import Table
        
        table = Table(title="Current User Information")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Username", user.username)
        table.add_row("Role", user.role.value.title())
        table.add_row("Email", user.email or "Not set")
        table.add_row("Active", "Yes" if user.is_active else "No")
        table.add_row("Verified", "Yes" if user.is_verified else "No")
        table.add_row("Comment Karma", str(user.comment_karma))
        table.add_row("Link Karma", str(user.link_karma))
        
        console.print(table)
    else:
        console.print("❌ Not authenticated", style="red")
        raise typer.Exit(1)