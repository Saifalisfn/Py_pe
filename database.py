import mysql.connector
import json
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'bharatpe_db'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True,
            'pool_name': 'bharatpe_pool',
            'pool_size': int(os.getenv('DB_POOL_SIZE', 5))
        }
        self.conn = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Create database connection"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor(dictionary=True)
            print("[DB] Connected to MySQL successfully")
        except Error as e:
            print(f"[DB Error] {e}")
            raise
    
    def reconnect(self):
        """Reconnect if connection lost"""
        try:
            self.conn.ping(reconnect=True, attempts=3, delay=5)
        except:
            self.connect()
    
    def execute(self, query, params=None):
        """Execute query"""
        try:
            self.reconnect()
            self.cursor.execute(query, params)
            return self.cursor
        except Error as e:
            print(f"[DB Error] {e}")
            raise
    
    def fetchone(self, query, params=None):
        """Fetch single row"""
        self.execute(query, params)
        return self.cursor.fetchone()
    
    def fetchall(self, query, params=None):
        """Fetch all rows"""
        self.execute(query, params)
        return self.cursor.fetchall()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def close(self):
        """Close connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("[DB] Connection closed")

    # Session methods
    def save_session(self, mobile, token, merchant_id, csrf_token, cookies, user_agent):
        """Save or update session"""
        query = """
            INSERT INTO sessions (mobile, token, merchant_id, csrf_token, cookies, user_agent, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                token = VALUES(token),
                merchant_id = VALUES(merchant_id),
                csrf_token = VALUES(csrf_token),
                cookies = VALUES(cookies),
                user_agent = VALUES(user_agent),
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
        """
        self.execute(query, (mobile, token, merchant_id, csrf_token, json.dumps(cookies), user_agent))
        self.commit()
    
    def get_session(self, mobile):
        """Get session by mobile"""
        query = "SELECT * FROM sessions WHERE mobile = %s AND is_active = TRUE"
        return self.fetchone(query, (mobile,))
    
    def get_all_sessions(self):
        """Get all active sessions"""
        query = "SELECT * FROM sessions WHERE is_active = TRUE ORDER BY updated_at DESC"
        return self.fetchall(query)
    
    def delete_session(self, mobile):
        """Soft delete session"""
        query = "UPDATE sessions SET is_active = FALSE WHERE mobile = %s"
        self.execute(query, (mobile,))
        self.commit()

    # Transaction methods
    def save_transaction(self, session_mobile, txn_data):
        """Save transaction"""
        query = """
            INSERT INTO transactions 
            (session_mobile, transaction_id, utr, amount, status, payer_name, payer_vpa, payment_timestamp, transaction_date, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s/1000), %s)
            ON DUPLICATE KEY UPDATE
                status = VALUES(status),
                raw_data = VALUES(raw_data)
        """
        params = (
            session_mobile,
            txn_data.get('id') or txn_data.get('transactionId'),
            txn_data.get('bankReferenceNo') or txn_data.get('utr'),
            txn_data.get('amount', 0),
            txn_data.get('status'),
            txn_data.get('payerName'),
            txn_data.get('payerVpa') or txn_data.get('customerVpa'),
            txn_data.get('paymentTimestamp') or txn_data.get('transactionTimestamp'),
            txn_data.get('paymentTimestamp') or txn_data.get('transactionTimestamp'),
            json.dumps(txn_data)
        )
        self.execute(query, params)
        self.commit()
    
    def get_transaction_by_utr(self, utr):
        """Find transaction by UTR"""
        query = "SELECT * FROM transactions WHERE utr = %s ORDER BY transaction_date DESC"
        return self.fetchall(query, (utr,))
    
    def get_transactions_by_mobile(self, mobile, limit=50):
        """Get transactions for a mobile"""
        query = """
            SELECT * FROM transactions 
            WHERE session_mobile = %s 
            ORDER BY transaction_date DESC 
            LIMIT %s
        """
        return self.fetchall(query, (mobile, limit))

    # UTR Log methods
    def log_utr_search(self, utr, session_mobile, found, amount=None, status=None):
        """Log UTR search"""
        query = """
            INSERT INTO utr_logs (utr, session_mobile, found, amount, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.execute(query, (utr, session_mobile, found, amount, status))
        self.commit()
    
    def get_utr_search_history(self, utr=None, limit=100):
        """Get UTR search history"""
        if utr:
            query = "SELECT * FROM utr_logs WHERE utr = %s ORDER BY searched_at DESC LIMIT %s"
            return self.fetchall(query, (utr, limit))
        else:
            query = "SELECT * FROM utr_logs ORDER BY searched_at DESC LIMIT %s"
            return self.fetchall(query, (limit,))

    # Notification methods
    def save_notification(self, session_mobile, amount, payer, utr, status, webhook_sent=False, telegram_sent=False):
        """Save notification"""
        query = """
            INSERT INTO notifications (session_mobile, amount, payer, utr, status, webhook_sent, telegram_sent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.execute(query, (session_mobile, amount, payer, utr, status, webhook_sent, telegram_sent))
        self.commit()
    
    def get_notifications(self, session_mobile=None, limit=100):
        """Get notifications"""
        if session_mobile:
            query = "SELECT * FROM notifications WHERE session_mobile = %s ORDER BY notified_at DESC LIMIT %s"
            return self.fetchall(query, (session_mobile, limit))
        else:
            query = "SELECT * FROM notifications ORDER BY notified_at DESC LIMIT %s"
            return self.fetchall(query, (limit,))

    # Config methods
    def get_config(self):
        """Get config"""
        query = "SELECT * FROM config WHERE id = 1"
        result = self.fetchone(query)
        if not result:
            self.execute("INSERT INTO config (id) VALUES (1)")
            self.commit()
            return self.fetchone(query)
        return result
    
    def update_config(self, **kwargs):
        """Update config"""
        allowed_fields = ['polling_interval', 'webhook_url', 'webhook_secret', 
                         'webhook_enabled', 'telegram_token', 'telegram_chat_id', 'telegram_enabled']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)
        
        if updates:
            query = f"UPDATE config SET {', '.join(updates)} WHERE id = 1"
            self.execute(query, tuple(values))
            self.commit()

# Global database instance
db = Database()