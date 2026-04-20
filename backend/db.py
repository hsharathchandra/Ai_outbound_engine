import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "leads.db")


def get_connection():
    """Single connection factory. Always use this — never open conn directly."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            company TEXT,
            role TEXT,
            email TEXT,
            message TEXT,
            subject TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


# Initialize on import
init_db()


def save_lead(name, company, role, email, message, subject, status="sent"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leads (name, company, role, email, message, subject, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, company, role, email, message, subject, status))
    conn.commit()
    conn.close()


def get_leads():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    conn.close()
    return rows
