import os
import re
import uuid
import sqlite3
import smtplib
import requests
from flask import session
from dotenv import load_dotenv
load_dotenv()
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, session, url_for, flash

from werkzeug.security import check_password_hash

from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "portfolio.db")
app = Flask(__name__)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
app.secret_key = os.environ["SECRET_KEY"]
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[]
)

csrf = CSRFProtect(app)
@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True
)


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        mobile TEXT,
        subject TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP           
    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS analytics(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id TEXT,
    ip TEXT,
    user_agent TEXT,
    page TEXT,
    visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

    conn.commit()
    conn.close()
# Function ko sirf ek baar call karo
init_db()
@app.route("/")
def home():

    if "visitor_id" not in session:
        session["visitor_id"] = str(uuid.uuid4())

    if not session.get("visited"):

        ip = request.headers.get(
            "X-Forwarded-For",
            request.remote_addr
        ).split(",")[0].strip()

        user_agent = request.headers.get("User-Agent")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO analytics
            (visitor_id, ip, user_agent, page)
            VALUES (?, ?, ?, ?)
            """,
            (
                session["visitor_id"],
                ip,
                user_agent,
                "Home"
            )
        )

        conn.commit()
        conn.close()

        session["visited"] = True

    return render_template("index.html")
# ================= CONTACT FORM =================
@app.route('/contact', methods=['POST'])
@limiter.limit("2 per minute")
def contact():
    try:
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        website = request.form.get('website', '').strip()  # honeypot

        print("FORM DATA:", fullname, email, mobile, subject, message)

        # ---------- BOT CHECK ----------
        if website:
            print("BOT DETECTED")
            return redirect(url_for('home'))

        # ---------- VALIDATION ----------
        if not fullname or not email or not message:
            flash("Required fields missing", "error")
            return redirect(url_for('home'))

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(email_pattern, email):
            flash("Invalid email address", "error")
            return redirect(url_for('home'))

        # ---------- CAPTCHA ----------
        captcha = request.form.get("g-recaptcha-response")

        if not captcha:
            flash("Please complete the CAPTCHA.", "error")
            return redirect(url_for("home"))

        data = {
            "secret": os.getenv("RECAPTCHA_SECRET"),
            "response": captcha
        }

        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            timeout=10
        )

        result = response.json()

        if not result.get("success"):
            flash("Captcha verification failed.", "error")
            return redirect(url_for("home"))

        # ---------- DATABASE ----------
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO contacts
                (fullname, email, mobile, subject, message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                fullname,
                email,
                mobile,
                subject,
                message
            ))

            conn.commit()
            conn.close()

            print("DATA SAVED SUCCESSFULLY")

        except Exception as db_error:
            print("DB ERROR:", db_error)

            flash("Unable to save your message.", "error")
            return redirect(url_for('home'))

        # ---------- EMAIL ----------
        email_sent = send_email(
            fullname,
            email,
            mobile,
            subject,
            message
        )

        if email_sent:
            print("EMAIL SENT SUCCESSFULLY")
            flash("Message sent successfully!", "success")
        else:
            print("EMAIL COULD NOT BE SENT")
            flash(
                "Your message was saved, but email notification could not be sent.",
                "error"
            )

        return redirect(url_for('home'))

    except Exception as e:
        print("CONTACT ERROR:", e)

        flash("Something went wrong", "error")
        return redirect(url_for('home'))

 # ---------- EMAIL SEND ----------
def send_email(fullname, email, mobile, subject, message):
    try:
        sender_email = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")

        if not sender_email or not password:
            print("EMAIL ENV NOT SET")
            return False

        body = f"""
New Contact Form Submission
============================

Name: {fullname}
Email: {email}
Mobile: {mobile}
Subject: {subject}

Message:
{message}

============================
This message was sent from your portfolio contact form.
"""

        msg = MIMEText(body, "plain", "utf-8")

        msg["Subject"] = f"New Portfolio Contact: {subject}"
        msg["From"] = sender_email
        msg["To"] = sender_email
        msg["Reply-To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(sender_email, password)

            server.sendmail(
                sender_email,
                sender_email,
                msg.as_string()
            )

        print("EMAIL SENT SUCCESSFULLY")
        return True

    except Exception as e:
        print("EMAIL ERROR:", str(e))
        return False


# ================= ADMIN LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():

    if request.method == 'POST':

        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if (
            username == ADMIN_USERNAME and
            check_password_hash(ADMIN_PASSWORD_HASH, password)
        ):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template(
                "login.html",
                error="Invalid Username or Password!"
            )

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))
@app.errorhandler(429)
def ratelimit_handler(e):
    return """
    <h2>⚠️ Too Many Requests</h2>
    <p>You have submitted too many requests. Please wait 1 minute and try again.</p>
    """, 429

# ================= BLOG ROUTES =================
@app.route('/blog1')
def blog1():
    return render_template("blog1.html")

@app.route('/blog2')
def blog2():
    return render_template("blog2.html")

@app.route('/blog3')
def blog3():
    return render_template("blog3.html")

@app.route("/blog4")
def blog4():
    return render_template("blog4.html")

@app.route('/delete-id/<int:id>', methods=['POST'])
def delete_id(id):

    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM contacts WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))
# ================= ADMIN PANEL =================
@app.route('/admin')
def admin():

    # Login check
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            fullname,
            email,
            mobile,
            subject,
            message,
            datetime(created_at, '+5 hours', '+30 minutes') AS created_at
        FROM contacts
        ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        messages=data
    )
@app.route('/analytics')
def analytics():

    # Login check (नई 2 लाइनें)
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM analytics")
    total_visits = cursor.fetchone()[0]
    cursor.execute("""
SELECT COUNT(DISTINCT visitor_id)
FROM analytics
""")
    unique_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM contacts")
    total_messages = cursor.fetchone()[0]

    conn.close()

    return render_template(
    "analytics.html",
    total_visits=total_visits,
    unique_visitors=unique_visitors,
    total_messages=total_messages
)

# ================= RUN APP =================
if __name__ == "__main__":
    app.run(debug=False)