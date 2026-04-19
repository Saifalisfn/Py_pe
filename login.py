import requests
import re
import json
import time
from rich.console import Console
from database import db

console = Console()

def start_login(mobile=None):
    if not mobile:
        mobile = console.input("[bold white][Input] Enter Mobile Number to login: [/bold white]")
    
    url_home = "https://enterprise.bharatpe.in/"
    url_request_otp = "https://enterprise.bharatpe.in/v1/api/user/requestotp"
    url_verify_otp = "https://enterprise.bharatpe.in/v1/api/user/verifyotp"
    url_dashboard = "https://enterprise.bharatpe.in/dashboard"
    url_profile = "https://enterprise.bharatpe.in/api/v1/merchant/profile"

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://enterprise.bharatpe.in/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
    }

    console.print(f"[bold cyan][Connecting] Starting login for {mobile}...[/bold cyan]")
    
    try:
        session = requests.Session()
        home_res = session.get(url_home, timeout=15)
        
        token_match = re.search(r'name="_token"\s+value="([^"]+)"', home_res.text)
        if not token_match:
            console.print("[red][Error] Failed to find CSRF _token.[/red]")
            return
        
        csrf_token = token_match.group(1)
        
        payload_otp = {"mobile": mobile, "_token": csrf_token}
        res_otp = session.post(url_request_otp, data=payload_otp, headers=headers, timeout=15)
        
        try:
            otp_json = res_otp.json()
            uuid = otp_json.get('data', {}).get('uuid') or otp_json.get('uuid')
            console.print(f"[bold green][Success] OTP Sent to {mobile}. UUID: {uuid}[/bold green]")
        except:
            console.print("[yellow][Info] OTP request submitted.[/yellow]")
            uuid = ""

        otp_code = console.input("[bold white][Input] Enter OTP: [/bold white]")

        payload_verify = {
            "mobile": mobile,
            "uuid": uuid,
            "otp": otp_code,
            "_token": csrf_token
        }

        console.print("[cyan][Verifying] Verifying OTP...[/cyan]")
        res_verify = session.post(url_verify_otp, data=payload_verify, headers=headers, timeout=15)

        if res_verify.status_code == 200:
            verify_data = res_verify.json()
            console.print("[bold green][Success] OTP Verified![/bold green]")
            
            final_token = (verify_data.get('data', {}).get('token') or 
                          verify_data.get('token') or 
                          verify_data.get('data', {}).get('accessToken') or 
                          verify_data.get('access_token'))

            console.print("[cyan][Activating] Harvesting Merchant ID...[/cyan]")
            
            dashboard_headers = headers.copy()
            dashboard_headers["Authorization"] = f"Bearer {final_token}"
            dashboard_headers["token"] = final_token
            session.get(url_dashboard, headers=dashboard_headers, allow_redirects=False, timeout=15)
            
            profile_res = session.get(url_profile, headers=dashboard_headers, allow_redirects=False, timeout=15)
            
            harvested_id = "24448231"
            if profile_res.status_code == 200:
                try:
                    profile_data = profile_res.json()
                    m_data = profile_data.get('data', {})
                    harvested_id = (m_data.get('merchant', {}).get('id') or 
                                   m_data.get('merchantId') or 
                                   m_data.get('id') or harvested_id)
                    console.print(f"[bold green][Harvested] Merchant ID: {harvested_id}[/bold green]")
                except Exception as e:
                    console.print(f"[yellow]Profile parse error: {e}[/yellow]")
            
            # Save to database instead of JSON file
            cookies_dict = session.cookies.get_dict()
            db.save_session(
                mobile=mobile,
                token=final_token,
                merchant_id=str(harvested_id),
                csrf_token=csrf_token,
                cookies=cookies_dict,
                user_agent=headers["User-Agent"]
            )
            
            console.print(f"[bold bright_green]🎊 LOGIN COMPLETE for {mobile}![/bold bright_green]")
            console.print(f"[dim]Session saved to database[/dim]")
            return True
        else:
            console.print(f"[bold red][Failed] Verification Failed: {res_verify.text}[/bold red]")
            return False

    except Exception as e:
        console.print(f"[bold red][Error] Problem during login: {e}[/bold red]")
        return False

if __name__ == "__main__":
    start_login()