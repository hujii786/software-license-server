"""
Database helper and models using standard sqlite3 for maximum speed and zero hassle.
"""
import sqlite3
import os
import hashlib
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "server_hub.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    # SHA-256 with salt for simple and fast hashing
    salt = "custom_software_hub_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table (Admin & Clients)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        plain_password TEXT,
        role TEXT NOT NULL DEFAULT 'client', -- 'admin' or 'client'
        full_name TEXT,
        company_name TEXT,
        phone TEXT,
        email TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    # Softwares table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS softwares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        version TEXT NOT NULL DEFAULT '1.0.0',
        description TEXT,
        download_url TEXT,
        is_local_file INTEGER DEFAULT 0,
        file_name TEXT,
        file_size TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    # Licenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        software_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'SUSPENDED', 'EXPIRED'
        machine_id TEXT,
        hardware_lock_enabled INTEGER DEFAULT 1,
        expiry_date TEXT DEFAULT 'LIFETIME', -- ISO 'YYYY-MM-DD' or 'LIFETIME'
        notes TEXT,
        last_checked_at TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (software_id) REFERENCES softwares(id) ON DELETE CASCADE
    )
    """)

    # Verification / Access logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT,
        app_code TEXT,
        machine_id TEXT,
        ip_address TEXT,
        status TEXT,
        details TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    """)

    # Create default Admin if not exists (admin / admin123)
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    if not admin:
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name, company_name, phone)
        VALUES (?, ?, 'admin', 'Master Admin', 'My Software House', '+92 300 0000000')
        """, ('admin', hash_password('admin123')))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_FILE)
