import os
import json
import time
import requests
import datetime
from rich.console import Console
from rich.panel import Panel
from database import db

console = Console()

def load_config():
    """Load config from database"""
    return db.get_config()

def send_notification(config, payload):
    """Send notification and save to database"""
    # Terminal Alert
    console.print(Panel(
        f"[bold green]💰 NEW PAYMENT RECEIVED![/bold green]\n"
        f"Account: {payload['merchant']}\n"
        f"Amount: Rs. {payload['amount']}\n"
        f"Payer: {payload['payer']}\n"
        f"UTR: {payload['utr']}",
        title="Payment Alert", border_style="green"
    ))

    # Save to database
    db.save_notification(
        session_mobile=payload['merchant'],
        amount=payload['amount'],
        payer=payload['payer'],
        utr=payload['utr'],
        status=payload['status']
    )

    # Webhook Alert
    if config.get("webhook_enabled") and config.get("webhook_url"):
        headers = {
            "x-webhook-secret": config.get("webhook_secret", ""),
            "Content-Type": "application/json"
        }
        try:
            requests.post(config["webhook_url"], json=payload, headers=headers, timeout=10)
        except Exception as e:
            console.print(f"[red]Webhook failed: {e}[/red]")

    # Telegram Alert
    if config.get("telegram_enabled") and config.get("telegram_token"):
        msg = (f"💰 *New Payment*\n"
               f"Merchant: {payload['merchant']}\n"
               f"Amount: ₹{payload['amount']}\n"
               f"Payer: {payload['payer']}\n"
               f"UTR: `{payload['utr']}`")
        url = f"https://api.telegram.org/bot{config['telegram_token']}/sendMessage"
        try:
            requests.post(url, json={"chat_id": config["telegram_chat_id"], "text": msg, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            console.print(f"[red]Telegram failed: {e}[/red]")

def check_for_updates():
    """Check for new transactions"""
    config = load_config()
    interval = config.get("polling_interval", 120)

    sessions = db.get_all_sessions()
    
    if not sessions:
        console.print("[grey]No active sessions to monitor.[/grey]")
        return

    for session in sessions:
        mobile = session['mobile']
        m_id = session['merchant_id']
        token = session['token']
        cookies = json.loads(session['cookies']) if isinstance(session['cookies'], str) else session['cookies']
        
        # Get last seen UTR from database
        last_notifications = db.get_notifications(mobile, limit=1)
        last_utr = last_notifications[0]['utr'] if last_notifications else None
        
        url = "https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions"
        params = {
            "module": "PAYMENT_QR",
            "merchantId": m_id,
            "pageSize": "10",
            "pageCount": "0"
        }
        headers = {
            "token": token,
            "Authorization": f"Bearer {token}",
            "User-Agent": session.get("user_agent", "Mozilla/5.0")
        }

        try:
            res = requests.get(url, headers=headers, params=params, cookies=cookies, timeout=15)
            if res.status_code == 200:
                data = res.json()
                txs = data.get("data", {}).get("transactions", [])
                
                if txs:
                    latest_tx = txs[0]
                    current_utr = latest_tx.get("bankReferenceNo") or latest_tx.get("id")
                    
                    if last_utr is None:
                        console.print(f"[grey]Initialized {mobile}. Last UTR: {current_utr}[/grey]")
                        db.save_notification(
                            session_mobile=mobile,
                            amount=latest_tx.get('amount', 0),
                            payer=latest_tx.get('payerName', 'Unknown'),
                            utr=current_utr,
                            status='INIT'
                        )
                    elif current_utr != last_utr:
                        # New transaction(s) found!
                        for tx in txs:
                            utr = tx.get("bankReferenceNo") or tx.get("id")
                            if utr == last_utr:
                                break
                            
                            payload = {
                                "merchant": mobile,
                                "amount": tx.get("amount", 0),
                                "payer": tx.get("payerName", "Unknown"),
                                "utr": utr,
                                "status": tx.get("status"),
                                "timestamp": str(datetime.datetime.now())
                            }
                            send_notification(config, payload)
                            db.save_transaction(mobile, tx)
                            
            elif res.status_code in [302, 401]:
                console.print(f"[red]Session expired for {mobile}[/red]")
                db.delete_session(mobile)
                
        except Exception as e:
            console.print(f"[grey]Watcher error for {mobile}: {e}[/grey]")

    console.print(f"[grey]{datetime.datetime.now().strftime('%H:%M:%S')} - Heartbeat OK...[/grey]")

def run():
    console.print("[bold bright_green]🚀 BharatPe Background Watcher Started (DB Mode)![/bold bright_green]")
    console.print("[grey]To stop, press Ctrl+C[/grey]\n")
    while True:
        check_for_updates()
        config = load_config()
        time.sleep(config.get("polling_interval", 120))

if __name__ == "__main__":
    run()