import sqlite3
import os

def init_db():
    db_path = os.path.join("instance", "phishing.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        department TEXT,
        received_at TEXT,
        clicked_at TEXT,
        submitted_credentials TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        body TEXT,
        type TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        timestamp TEXT,
        ip_address TEXT,
        user_agent TEXT,
        page TEXT
    )''')

    # Only insert the template if the table is empty
    c.execute("SELECT COUNT(*) FROM templates")
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO templates (subject, body, type) VALUES (?, ?, ?)''',
            ("Reset Your Password",
             "<html><body><h3>Hi {{name}}</h3><p>Click <a href='http://localhost:5000/reset-password?user_id={{user_id}}'>here</a> to reset your password.</p></body></html>",
             "reset"))


    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
