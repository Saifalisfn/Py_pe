import requests
import json
import urllib.parse
import time
from rich.console import Console
from rich.table import Table
from database import db

console = Console()

def fetch_bharatpe_data(mobile=None, save_to_db=True):
    """
    Fetch transactions from BharatPe API
    If mobile is None, fetch for all active sessions
    """
    if mobile:
        sessions = [db.get_session(mobile)]
    else:
        sessions = db.get_all_sessions()
    
    if not sessions or not any(sessions):
        console.print("[red][Error] No active sessions found in database.[/red]")
        return

    for session in sessions:
        if not session:
            continue
            
        mobile_num = session['mobile']
        m_id = session['merchant_id']
        token = session['token']
        cookies = json.loads(session['cookies']) if isinstance(session['cookies'], str) else session['cookies']
        ua = session['user_agent']
        csrf_id = session.get('csrf_token', '')

        console.print(f"\n[bold yellow]🔍 Fetching Data for Account: {mobile_num} (MID: {m_id})[/bold yellow]")

        s = requests.Session()
        for name, value in cookies.items():
            s.cookies.set(name, value)

        xsrf_cookie = cookies.get("XSRF-TOKEN", "")
        xsrf_header = urllib.parse.unquote(xsrf_cookie) if xsrf_cookie else ""

        end_date = int(time.time() * 1000)
        start_date = end_date - (30 * 24 * 60 * 60 * 1000)

        headers = {
            "x-merchant-id": str(m_id),
            "X-XSRF-TOKEN": xsrf_header,
            "X-CSRF-TOKEN": csrf_id,
            "token": token,
            "Authorization": f"Bearer {token}",
            "User-Agent": ua,
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://enterprise.bharatpe.in/dashboard"
        }

        endpoints = [
            {
                "name": "Transactions",
                "url": "https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions",
                "params": {
                    "module": "PAYMENT_QR",
                    "merchantId": m_id,
                    "sDate": start_date,
                    "eDate": end_date,
                    "pageSize": "100",
                    "pageCount": "0",
                    "isFromOtDashboard": "1"
                }
            }
        ]

        for ep in endpoints:
            try:
                response = s.get(ep["url"], headers=headers, params=ep["params"], allow_redirects=False, timeout=15)
                
                if response.status_code == 200:
                    console.print(f"[bold green][Success] {ep['name']} fetched.[/bold green]")
                    data = response.json()
                    display_and_save_transactions(data, mobile_num, save_to_db)
                elif response.status_code in [301, 302, 401]:
                    console.print(f"[bold red][Auth] Session EXPIRED for {mobile_num}. Please login again.[/bold red]")
                    db.delete_session(mobile_num)
                else:
                    console.print(f"[red][Fail] Failed with status {response.status_code}[/red]")

            except Exception as e:
                console.print(f"[red][Error] Problem with {mobile_num}: {e}[/red]")

def display_and_save_transactions(data, mobile, save_to_db=True):
    """Display transactions and save to database"""
    tx_list = data.get("data", {}).get("transactions", [])
    if not tx_list:
        console.print(f"[yellow]No transactions found for {mobile} in the last 30 days.[/yellow]")
        return

    table = Table(title=f"Transactions: {mobile}")
    table.add_column("Date", style="magenta")
    table.add_column("Amount", style="green")
    table.add_column("Status", style="cyan")
    table.add_column("UTR", style="white")

    saved_count = 0
    for tx in tx_list:
        raw_date = tx.get("paymentTimestamp") or tx.get("transactionDate") or tx.get("createdAt")
        if isinstance(raw_date, int) and len(str(raw_date)) >= 10:
            readable_date = time.strftime('%Y-%m-%d %H:%M', time.localtime(raw_date/1000))
        else:
            readable_date = str(raw_date) if raw_date else "N/A"

        table.add_row(
            readable_date,
            f"Rs. {tx.get('amount', 0)}",
            tx.get("status", "UNKNOWN"),
            tx.get("bankReferenceNo", tx.get("utr", "N/A"))
        )
        
        if save_to_db:
            try:
                db.save_transaction(mobile, tx)
                saved_count += 1
            except Exception as e:
                console.print(f"[dim red]Error saving transaction: {e}[/dim red]")
    
    console.print(table)
    if save_to_db:
        console.print(f"[dim green]✓ Saved {saved_count} transactions to database[/dim green]")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fetch_bharatpe_data(sys.argv[1])
    else:
        fetch_bharatpe_data()