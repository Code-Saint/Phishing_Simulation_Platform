import os
from flask import Flask, render_template, request, redirect, url_for, render_template_string, Response, flash
from config import Config
import sqlite3
import csv
from datetime import datetime, timezone
from io import StringIO
from utils.email_sender import send_phishing_email
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    return conn

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/email-builder', methods=['GET', 'POST'])
def email_builder():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        template_type = request.form['type']

        cursor.execute("INSERT INTO templates (subject, body, type) VALUES (?, ?, ?)",
                       (subject, body, template_type))
        conn.commit()

    cursor.execute("SELECT * FROM templates")
    templates = cursor.fetchall()
    conn.close()
    return render_template('email_builder.html', templates=templates)

@app.route('/preview/<int:template_id>')
def preview_template(template_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT subject, body FROM templates WHERE template_id=?", (template_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        subject, body = result
        return render_template('email_preview.html', subject=subject, body=body)
    return "Template not found", 404

@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates")
    templates = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        template_id = request.form['template_id']

        # Get template
        cursor.execute("SELECT subject, body FROM templates WHERE template_id=?", (template_id,))
        template = cursor.fetchone()
        if not template:
            return "Template not found", 400

        subject, body = template

        # Insert user first to get ID
        cursor.execute("INSERT INTO users (name, email, department, received_at) VALUES (?, ?, ?, datetime('now'))",
                    (name, email, 'General'))
        user_id = cursor.lastrowid  # Get the ID of the inserted user

        # Use Jinja2-style rendering
        rendered_body = render_template_string(body, name=name, user_id=user_id)

        success = send_phishing_email(name, email, subject, rendered_body)

        if success:
            conn.commit()
            conn.close()
            flash(f"Email sent to {email}", "success")
            return redirect(url_for('send_email'))
        else:
            # Optional: delete user if email failed
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return "Failed to send email"


    return render_template('send_email.html', templates=templates)


@app.route('/click')
def click():
    user_id = request.args.get("user_id")
    ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_db()  # ✅ This MUST be here
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO analytics (user_id, timestamp, ip_address, user_agent, page)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, timestamp, ip, user_agent, '/click'))
    conn.commit()
    conn.close()

    return redirect("/login")


@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = request.args.get('user_id')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        timestamp = datetime.now(timezone.utc).isoformat()

        # Store credential submission
        conn = get_db()  # ✅ Consistent with the rest of your app
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics (user_id, timestamp, ip_address, user_agent, page)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, timestamp, ip_address, user_agent, 'submitted'))
        conn.commit()
        conn.close()

        return redirect(url_for('awareness', user_id=user_id))

    return render_template('login.html', user_id=user_id)

from datetime import datetime

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = request.args.get('user_id') or request.form.get('user_id')

    # Common: Log analytics
    if user_id:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO analytics (user_id, timestamp, ip_address, user_agent, page)
            VALUES (?, datetime('now'), ?, ?, ?)
        ''', (
            user_id,
            request.remote_addr,
            request.headers.get('User-Agent'),
            'clicked' if request.method == 'GET' else 'submitted'
        ))

        # For click tracking
        if request.method == 'GET':
            cursor.execute("UPDATE users SET clicked_at = datetime('now') WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()

    # Form submitted (POST)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if user_id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET submitted_credentials = ?
                WHERE id = ?
            ''', (f'{username}:{password}', user_id))
            conn.commit()
            conn.close()

        return redirect(url_for('awareness', user_id=user_id))

    return render_template('reset_password.html', user_id=user_id)


@app.route('/admin')
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # Fetch all users
    cursor.execute('''
        SELECT id, name, email, department, received_at, clicked_at, submitted_credentials
        FROM users
    ''')
    users = cursor.fetchall()

    # Fetch summary stats
    cursor.execute("SELECT COUNT(*) FROM users")
    total_sent = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE clicked_at IS NOT NULL")
    total_clicked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE submitted_credentials IS NOT NULL")
    total_submitted = cursor.fetchone()[0]

    # Fetch analytics logs and group by user_id
    cursor.execute('''
        SELECT user_id, timestamp, ip_address, user_agent, page
        FROM analytics
        ORDER BY timestamp DESC
    ''')
    raw_analytics = cursor.fetchall()

    analytics_by_user = {}
    for entry in raw_analytics:
        user_id = entry[0]
        analytics_by_user.setdefault(user_id, []).append(entry[1:])  # timestamp, ip, agent, page

    conn.close()

    return render_template('admin.html',
                           users=users,
                           total_sent=total_sent,
                           total_clicked=total_clicked,
                           total_submitted=total_submitted,
                           analytics_by_user=analytics_by_user)

@app.route('/awareness')
def awareness():
    user_id = request.args.get('user_id')

    if user_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics (user_id, timestamp, ip_address, user_agent, page)
            VALUES (?, datetime('now'), ?, ?, ?)
        ''', (
            user_id,
            request.remote_addr,
            request.headers.get('User-Agent'),
            'awareness'
        ))
        conn.commit()
        conn.close()

    return render_template('awareness.html')


@app.route('/export/users')
def export_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, department, received_at, clicked_at, submitted_credentials FROM users")
    rows = cursor.fetchall()
    conn.close()

    def generate():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'Department', 'Received At', 'Clicked At', 'Submitted Credentials'])
        for row in rows:
            writer.writerow([r if r is not None else '' for r in row])
        return output.getvalue()

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=users_report.csv"})


@app.route('/export/analytics')
def export_analytics():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, timestamp, ip_address, user_agent, page FROM analytics")
    rows = cursor.fetchall()
    conn.close()

    def generate():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['User ID', 'Timestamp', 'IP Address', 'User Agent', 'Page'])
        for row in rows:
            writer.writerow([r if r is not None else '' for r in row])
        return output.getvalue()

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=analytics_report.csv"})


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=False)
