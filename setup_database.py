#!/usr/bin/env python3
"""
Database Setup Script for BharatPe MySQL Integration
Run this first: python setup_database.py
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create database if not exists"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = conn.cursor()
        
        db_name = os.getenv('DB_NAME', 'bharatpe_db')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Database '{db_name}' created or already exists")
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def create_tables():
    """Create all tables"""
    from database import db
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            mobile VARCHAR(15) UNIQUE NOT NULL,
            token TEXT NOT NULL,
            merchant_id VARCHAR(50),
            csrf_token TEXT,
            cookies JSON,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_mobile (mobile),
            INDEX idx_merchant (merchant_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_mobile VARCHAR(15) NOT NULL,
            transaction_id VARCHAR(100),
            utr VARCHAR(50),
            amount DECIMAL(15, 2),
            status VARCHAR(50),
            payer_name VARCHAR(255),
            payer_vpa VARCHAR(255),
            payment_timestamp BIGINT,
            transaction_date DATETIME,
            raw_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_utr (utr),
            INDEX idx_session_mobile (session_mobile),
            INDEX idx_payment_date (transaction_date),
            UNIQUE KEY unique_txn (session_mobile, transaction_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS utr_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            utr VARCHAR(50) NOT NULL,
            session_mobile VARCHAR(15),
            found BOOLEAN DEFAULT FALSE,
            amount DECIMAL(15, 2),
            status VARCHAR(50),
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_utr (utr),
            INDEX idx_searched_at (searched_at)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_mobile VARCHAR(15) NOT NULL,
            amount DECIMAL(15, 2),
            payer VARCHAR(255),
            utr VARCHAR(50),
            status VARCHAR(50),
            notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            webhook_sent BOOLEAN DEFAULT FALSE,
            telegram_sent BOOLEAN DEFAULT FALSE,
            INDEX idx_session_mobile (session_mobile),
            INDEX idx_notified_at (notified_at)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS config (
            id INT PRIMARY KEY DEFAULT 1,
            polling_interval INT DEFAULT 120,
            webhook_url TEXT,
            webhook_secret VARCHAR(255),
            webhook_enabled BOOLEAN DEFAULT FALSE,
            telegram_token VARCHAR(255),
            telegram_chat_id VARCHAR(50),
            telegram_enabled BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
    ]
    
    for table_sql in tables:
        try:
            db.execute(table_sql)
            print("✓ Table created successfully")
        except Error as e:
            print(f"✗ Error creating table: {e}")
    
    # Insert default config
    try:
        db.execute("INSERT INTO config (id) VALUES (1) ON DUPLICATE KEY UPDATE id=id")
        db.commit()
        print("✓ Default config inserted")
    except Error as e:
        print(f"✗ Error inserting config: {e}")
    
    print("\n✓ Database setup complete!")

if __name__ == "__main__":
    print("=== BharatPe Database Setup ===\n")
    
    if create_database():
        create_tables()
        print("\nYou can now run: python main.py")
    else:
        print("\n✗ Setup failed. Please check your MySQL connection settings in .env file")