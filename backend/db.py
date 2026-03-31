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


def save_lead(name, company, role, email, message):
    cursor.execute(
        "INSERT INTO leads (name, company, role, email, message, subject) VALUES (?, ?, ?, ?, ?, ?)",
        (name, company, role, email, message, subject),
    )
    conn.commit()


def get_leads():
    cursor.execute("SELECT * FROM leads")
    return cursor.fetchall()
    
