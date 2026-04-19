import os
import sys
from rich.console import Console
from rich.panel import Panel
from login import start_login
from api import fetch_bharatpe_data
from utr_finder import fast_find
from database import db

console = Console()

def show_menu():
    console.print(Panel.fit(
        "[bold cyan]BharatPe Multi-User Manager (MySQL Edition)[/bold cyan]\n"
        "1. [green]Add New Merchant (Login)[/green]\n"
        "2. [blue]Fetch Transactions (All Users)[/blue]\n"
        "3. [magenta]Search by UTR (Across All Users)[/magenta]\n"
        "4. [yellow]List Active Sessions[/yellow]\n"
        "5. [cyan]View Database Stats[/cyan]\n"
        "6. [bright_white]Start Background Watcher[/bright_white]\n"
        "7. [red]Exit[/red]",
        title="Main Menu", border_style="bright_blue"
    ))

def list_sessions():
    """List all active sessions from database"""
    sessions = db.get_all_sessions()

    if not sessions:
        console.print("[yellow]No active sessions found.[/yellow]")
        return []

    console.print(f"[bold white]Found {len(sessions)} Active Account(s):[/bold white]")
    for i, session in enumerate(sessions, 1):
        mobile = session['mobile']
        merchant_id = session.get('merchant_id', 'N/A')
        updated = session.get('updated_at', 'Unknown')
        console.print(f"{i}. {mobile} (MID: {merchant_id}) - Last updated: {updated}")
    return sessions

def show_db_stats():
    """Show database statistics"""
    try:
        sessions = db.get_all_sessions()
        all_txns = db.fetchall("SELECT COUNT(*) as count FROM transactions")
        all_notifications = db.fetchall("SELECT COUNT(*) as count FROM notifications")
        all_utr_logs = db.fetchall("SELECT COUNT(*) as count FROM utr_logs")
        
        console.print(Panel(
            f"[bold cyan]Database Statistics[/bold cyan]\n\n"
            f"Active Sessions: [green]{len(sessions)}[/green]\n"
            f"Total Transactions: [green]{all_txns[0]['count'] if all_txns else 0}[/green]\n"
            f"Total Notifications: [green]{all_notifications[0]['count'] if all_notifications else 0}[/green]\n"
            f"UTR Searches: [green]{all_utr_logs[0]['count'] if all_utr_logs else 0}[/green]",
            title="Stats", border_style="cyan"
        ))
        
        recent_searches = db.get_utr_search_history(limit=5)
        if recent_searches:
            console.print("\n[bold]Recent UTR Searches:[/bold]")
            for search in recent_searches:
                status = "[green]✓ Found[/green]" if search['found'] else "[red]✗ Not Found[/red]"
                console.print(f"  {search['utr']} - {status} ({search['searched_at']})")
                
    except Exception as e:
        console.print(f"[red]Error getting stats: {e}[/red]")

def main():
    # Initialize database connection
    try:
        db.get_config()
        console.print("[dim green]✓ Connected to MySQL database[/dim green]\n")
    except Exception as e:
        console.print(f"[bold red]✗ Database connection failed: {e}[/bold red]")
        console.print("[yellow]Please check your .env file and ensure MySQL is running.[/yellow]")
        sys.exit(1)
    
    while True:
        show_menu()
        choice = console.input("[bold white]Select an option: [/bold white]")
        
        if choice == "1":
            start_login()
        
        elif choice == "2":
            sessions = list_sessions()
            if sessions:
                fetch_bharatpe_data()
        
        elif choice == "3":
            utr = console.input("[bold white]Enter UTR Number: [/bold white]").strip()
            if utr:
                fast_find(utr)
        
        elif choice == "4":
            list_sessions()
        
        elif choice == "5":
            show_db_stats()
        
        elif choice == "6":
            console.print("[bold green]Moving to Background Watcher... (Press Ctrl+C to exit)[/bold green]")
            try:
                import watcher
                watcher.run()
            except KeyboardInterrupt:
                console.print("\n[yellow]Watcher stopped. Back to menu.[/yellow]")

        elif choice == "7":
            console.print("[italic white]Goodbye![/italic white]")
            db.close()
            break
        
        else:
            console.print("[red]Invalid choice. Try again.[/red]")

if __name__ == "__main__":
    main()