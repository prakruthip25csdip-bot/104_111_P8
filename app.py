from datetime import datetime
import sqlite3

from flask import Flask, redirect, render_template, request

from dfa_validation import classify_loan_type, dfa_validate

app = Flask(__name__)
DB_NAME = "database.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            applicant TEXT,
            code TEXT,
            amount REAL,
            description TEXT,
            category TEXT,
            priority TEXT,
            status TEXT,
            handler TEXT,
            reason TEXT,
            submitted_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    applicant = request.form.get("applicant", "").strip()
    code = request.form.get("code", "").strip().upper()
    amount_text = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Normal").strip()

    if not applicant or not code or not description or not amount_text:
        return "Please fill in all required fields.", 400

    try:
        amount = float(amount_text)
    except ValueError:
        return "Loan amount must be a valid number.", 400

    if amount <= 0:
        return "Loan amount must be greater than zero.", 400

    reason = ""
    category = "Invalid"
    status = "Pending"
    handler = "Correction Queue"

    if dfa_validate(code):
        category = classify_loan_type(code)
        reason = ""
        status = "Assigned"
        handler = category + " Loan Branch"
    else:
        reason = "Invalid application code"

    report_id = "RPT" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    conn.execute(
        """
        INSERT INTO reports (
            report_id, applicant, code, amount, description, category,
            priority, status, handler, reason, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            applicant,
            code,
            amount,
            description,
            category,
            priority,
            status,
            handler,
            reason,
            submitted_at,
        ),
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    search = request.args.get("search", "")
    conn = get_db()
    cur = conn.execute(
        "SELECT * FROM reports WHERE report_id LIKE ? ORDER BY id DESC",
        ("%" + search + "%",),
    )
    reports = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", reports=reports)


@app.route("/handler")
def handler():
    conn = get_db()
    reports = conn.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("handler.html", reports=reports)


@app.route("/routes")
def routes():
    routing_rules = [
        {"loan_type": "Home", "amount": "Up to ₹10 lakh", "branch": "Home Team A"},
        {"loan_type": "Home", "amount": "Above ₹10 lakh", "branch": "Home Team B"},
        {"loan_type": "Vehicle", "amount": "Up to ₹5 lakh", "branch": "Vehicle Team A"},
        {"loan_type": "Vehicle", "amount": "Above ₹5 lakh", "branch": "Vehicle Team B"},
        {"loan_type": "Personal", "amount": "Up to ₹3 lakh", "branch": "Personal Team A"},
        {"loan_type": "Personal", "amount": "Above ₹3 lakh", "branch": "Personal Team B"},
        {"loan_type": "Education", "amount": "Up to ₹5 lakh", "branch": "Education Team A"},
        {"loan_type": "Education", "amount": "Above ₹5 lakh", "branch": "Education Team B"},
    ]
    return render_template("routes.html", routing_rules=routing_rules)


@app.route("/analytics")
def analytics():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS count FROM reports").fetchone()["count"]
    pending = conn.execute("SELECT COUNT(*) AS count FROM reports WHERE status = 'Pending'").fetchone()["count"]
    assigned = conn.execute("SELECT COUNT(*) AS count FROM reports WHERE status = 'Assigned'").fetchone()["count"]
    resolved = conn.execute("SELECT COUNT(*) AS count FROM reports WHERE status = 'Resolved'").fetchone()["count"]
    conn.close()

    return render_template(
        "analytics.html",
        total=total,
        pending=pending,
        assigned=assigned,
        resolved=resolved,
    )


@app.route("/update/<int:report_id>", methods=["POST"])
def update(report_id):
    status = request.form.get("status", "").strip()
    allowed = ["Pending", "Assigned", "In Progress", "Resolved"]
    if status not in allowed:
        return "Invalid status.", 400

    conn = get_db()
    conn.execute("UPDATE reports SET status=? WHERE id=?", (status, report_id))
    conn.commit()
    conn.close()
    return redirect("/handler")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
