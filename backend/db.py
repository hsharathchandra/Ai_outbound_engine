import sqlite3

conn = sqlite3.connect("leads.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    company TEXT,
    role TEXT,
    email TEXT,
    message TEXT,
    subject TEXT
)
""")

conn.commit()


def save_lead(name, company, role, email, message, subject, status="sent"):
    import sqlite3
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "leads.db")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads (name, company, role, email, message, subject, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, company, role, email, message, subject, status))

    conn.commit()
    conn.close()


def get_leads():
    cursor.execute("SELECT * FROM leads")
    return cursor.fetchall()
    
