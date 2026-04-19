import requests
import json
import urllib.parse
from rich.console import Console
from database import db

console = Console()

def find_utr(utr_number, mobile=None):
    """
    Search for UTR across all sessions or specific mobile
    Returns: (found: bool, data: dict)
    """
    if not utr_number:
        console.print("[red]No UTR provided[/red]")
        return False, None

    # First check database cache
    cached_txn = db.get_transaction_by_utr(utr_number)
    if cached_txn:
        console.print(f"[bold green]✅ UTR found in database cache![/bold green]")
        for txn in cached_txn:
            console.print(f"[green]Account: {txn['session_mobile']}, Amount: ₹{txn['amount']}, Status: {txn['status']}[/green]")
        return True, cached_txn[0]

    # Get sessions to search
    if mobile:
        sessions = [db.get_session(mobile)]
    else:
        sessions = db.get_all_sessions()
    
    if not sessions:
        console.print("[red]No active sessions found in database.[/red]")
        return False, None

    console.print(f"[grey]Searching across {len(sessions)} merchant account(s)...[/grey]\n")
    
    any_found = False
    
    for session in sessions:
        if not session:
            continue
            
        mobile_num = session['mobile']
        token = session['token']
        cookies = json.loads(session['cookies']) if isinstance(session['cookies'], str) else session['cookies']
        ua = session['user_agent']
        
        s = requests.Session()
        s.cookies.update(cookies)
        
        xsrf_cookie = cookies.get('XSRF-TOKEN', '')
        decoded_xsrf = urllib.parse.unquote(xsrf_cookie)

        url = "https://enterprise.bharatpe.in/v1/api/transaction/recon"
        params = {'utr': utr_number}

        headers = {
            "Authorization": f"Bearer {token}",
            "X-XSRF-TOKEN": decoded_xsrf,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "Referer": "https://enterprise.bharatpe.in/transactionhistory",
            "User-Agent": ua
        }

        console.print(f"[cyan]🔍 Searching {mobile_num}'s records...[/cyan]")

        try:
            response = s.get(url, headers=headers, params=params, allow_redirects=False, timeout=15)

            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') is True or data.get('data'):
                    console.print(f"[bold green]✅ Transaction Found in {mobile_num}'s account![/bold green]")
                    
                    txn_data = data.get('data', {})
                    
                    # Save to database
                    db.save_transaction(mobile_num, txn_data)
                    
                    # Log the search
                    db.log_utr_search(
                        utr=utr_number,
                        session_mobile=mobile_num,
                        found=True,
                        amount=txn_data.get('amount'),
                        status=txn_data.get('status')
                    )
                    
                    console.print_json(data=data)
                    any_found = True
                    return True, txn_data
                else:
                    db.log_utr_search(
                        utr=utr_number,
                        session_mobile=mobile_num,
                        found=False
                    )
                    
            elif response.status_code == 302:
                console.print(f"[red]❌ Auth Failed for {mobile_num} (Session expired)[/red]")
                db.delete_session(mobile_num)
            else:
                console.print(f"[grey]No match in {mobile_num} (Status: {response.status_code})[/grey]")
                
        except Exception as e:
            console.print(f"[red]❌ Error searching {mobile_num}: {e}[/red]")
            continue

    if not any_found:
        console.print(f"\n[bold red]❌ UTR {utr_number} was NOT found in any logged-in accounts.[/bold red]")
        console.print("[grey]Note: BharatPe's recon API may take a few minutes to index very recent transactions.[/grey]")
    
    return any_found, None

def fast_find(utr_number):
    """Quick UTR search with database logging"""
    console.print("[bold cyan]🔍 BharatPe Fast UTR Search (DB Integrated)[/bold cyan]")
    
    found, data = find_utr(utr_number)
    return found

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fast_find(sys.argv[1])
    else:
        utr = console.input("[bold white]Enter UTR Number: [/bold white]").strip()
        fast_find(utr)