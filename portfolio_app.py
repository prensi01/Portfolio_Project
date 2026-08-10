import os
import re
import uuid
import sqlite3
import requests
import threading 
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

    visitor_id = session.get("visitor_id")

    if not visitor_id:
        visitor_id = str(uuid.uuid4())
        session["visitor_id"] = visitor_id

    ip = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    ).split(",")[0].strip()

    user_agent = request.headers.get("User-Agent")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO analytics
            (
                visitor_id,
                ip,
                user_agent,
                page
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visitor_id,
                ip,
                user_agent,
                "Home"
            )
        )

        conn.commit()
        conn.close()

        print("ANALYTICS: VISIT SAVED")

    except Exception as analytics_error:

        print(
            "ANALYTICS ERROR:",
            analytics_error
        )

    return render_template("index.html")
# ================= CONTACT FORM =================

@app.route('/contact', methods=['POST'])
@limiter.limit("2 per minute")
def contact():

    try:
        # ---------- FORM DATA ----------
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # ---------- HONEYPOT ----------
        website = request.form.get('website', '').strip()

        print("========================================")
        print("CONTACT FORM RECEIVED")
        print("Name:", fullname)
        print("Email:", email)
        print("Mobile:", mobile)
        print("Subject:", subject)
        print("========================================")

        # ---------- BOT CHECK ----------
        if website:
            print("BOT DETECTED")
            return redirect(url_for('home'))

        # ---------- VALIDATION ----------
        if not fullname or not email or not message:
            print("VALIDATION ERROR: Required fields missing")

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(url_for('home'))

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(email_pattern, email):

            print("VALIDATION ERROR: Invalid email")

            flash(
                "Invalid email address.",
                "error"
            )

            return redirect(url_for('home'))

        # =================================================
        # CAPTCHA
        # =================================================

        captcha = request.form.get("g-recaptcha-response")

        if not captcha:

            print("CAPTCHA ERROR: No CAPTCHA response")

            flash(
                "Please complete the CAPTCHA.",
                "error"
            )

            return redirect(url_for("home"))

        captcha_secret = os.getenv("RECAPTCHA_SECRET")

        if not captcha_secret:

            print("CAPTCHA ERROR: RECAPTCHA_SECRET missing")

            flash(
                "CAPTCHA configuration error.",
                "error"
            )

            return redirect(url_for("home"))

        try:

            print("CAPTCHA: VERIFYING...")

            captcha_response = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",

                data={
                    "secret": captcha_secret,
                    "response": captcha
                },

                timeout=10
            )

            captcha_result = captcha_response.json()

            print("CAPTCHA RESULT:", captcha_result)

            if not captcha_result.get("success"):

                print("CAPTCHA VERIFICATION FAILED")

                flash(
                    "CAPTCHA verification failed. Please try again.",
                    "error"
                )

                return redirect(url_for("home"))

            print("CAPTCHA: VERIFIED SUCCESSFULLY")

        except requests.RequestException as captcha_error:

            print("CAPTCHA REQUEST ERROR:", captcha_error)

            flash(
                "CAPTCHA service is temporarily unavailable.",
                "error"
            )

            return redirect(url_for("home"))

        # =================================================
        # DATABASE SAVE
        # =================================================

        try:

            print("DATABASE: SAVING MESSAGE...")

            conn = sqlite3.connect(DB_PATH)

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO contacts
                (
                    fullname,
                    email,
                    mobile,
                    subject,
                    message
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fullname,
                    email,
                    mobile,
                    subject,
                    message
                )
            )

            conn.commit()

            conn.close()

            print("DATABASE: MESSAGE SAVED SUCCESSFULLY")

        except Exception as db_error:

            print("DATABASE ERROR:", db_error)

            flash(
                "Unable to save your message.",
                "error"
            )

            return redirect(url_for("home"))

        # =================================================
        # EMAIL BACKGROUND THREAD
        # =================================================

        def email_task():

            print("EMAIL THREAD: STARTED")

            try:

                success = send_email(
                    fullname,
                    email,
                    mobile,
                    subject,
                    message
                )

                if success:

                    print(
                        "EMAIL THREAD: SENT SUCCESSFULLY"
                    )

                else:

                    print(
                        "EMAIL THREAD: FAILED"
                    )

            except Exception as email_error:

                print(
                    "EMAIL THREAD ERROR:",
                    email_error
                )

        threading.Thread(
            target=email_task,
            daemon=True
        ).start()

        print("EMAIL THREAD: STARTED")

        # =================================================
        # IMMEDIATE RESPONSE
        # =================================================

        flash(
            "Message sent successfully!",
            "success"
        )

        print("CONTACT: REDIRECTING TO HOME")

        return redirect(url_for("home"))

    except Exception as e:

        print("CONTACT ERROR:", e)

        flash(
            "Something went wrong. Please try again.",
            "error"
        )

        return redirect(url_for("home"))


# =====================================================
# RESEND EMAIL
# =====================================================

def send_email(
    fullname,
    email,
    mobile,
    subject,
    message
):

    try:

        resend_api_key = os.getenv("RESEND_API_KEY")
        receiver_email = os.getenv("EMAIL_USER")

        # ---------- CHECK ENV ----------

        if not resend_api_key:

            print("EMAIL ERROR: RESEND_API_KEY is missing")

            return False

        if not receiver_email:

            print("EMAIL ERROR: EMAIL_USER is missing")

            return False

        # ---------- EMAIL HTML ----------

        html_body = f"""
        <html>

        <body style="font-family: Arial, sans-serif; line-height: 1.6;">

            <h2>New Portfolio Contact Form Submission</h2>

            <hr>

            <p>
                <strong>Name:</strong><br>
                {fullname}
            </p>

            <p>
                <strong>Email:</strong><br>
                {email}
            </p>

            <p>
                <strong>Mobile:</strong><br>
                {mobile}
            </p>

            <p>
                <strong>Subject:</strong><br>
                {subject}
            </p>

            <p>
                <strong>Message:</strong><br>
                {message}
            </p>

            <hr>

            <p>
                This message was sent from your portfolio contact form.
            </p>

        </body>

        </html>
        """

        # ---------- RESEND API ----------

        print("EMAIL: CONNECTING TO RESEND...")

        response = requests.post(

            "https://api.resend.com/emails",

            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },

            json={

                "from": "Portfolio <onboarding@resend.dev>",

                "to": [receiver_email],

                "subject": f"New Portfolio Contact: {subject}",

                "html": html_body,

                "reply_to": email

            },

            timeout=10
        )

        print("RESEND STATUS:", response.status_code)

        print("RESEND RESPONSE:", response.text)

        # ---------- SUCCESS ----------

        if response.status_code in (200, 201):

            print("EMAIL: RESEND SENT SUCCESSFULLY")

            return True

        # ---------- FAILED ----------

        print("EMAIL: RESEND FAILED")

        return False

    except requests.RequestException as e:

        print("RESEND NETWORK ERROR:", e)

        return False

    except Exception as e:

        print("RESEND EMAIL ERROR:", e)

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