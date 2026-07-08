# ============================================
# DISEASE OUTBREAK PREDICTOR - COMMUNITY SUBMISSIONS MODULE
# Adds user submission form + admin review dashboard
# By Emmanuel Owusu Adu
# ============================================


app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key-before-deploying"

ADMIN_PASSWORD = "changeThisPassword123"  # CHANGE THIS before deploying

def get_db():
    conn = sqlite3.connect("submissions.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_submissions_table():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submitters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            organization TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitter_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            disease TEXT NOT NULL,
            number_of_cases INTEGER NOT NULL,
            date_observed TEXT NOT NULL,
            observation_notes TEXT,
            submitted_at TEXT NOT NULL,
            FOREIGN KEY (submitter_id) REFERENCES submitters (id)
        )
    """)

    conn.commit()
    conn.close()


# ============ PUBLIC ROUTES ============

@app.route("/submit")
def submit_form():
    return render_template("submit.html")


@app.route("/api/submit-report", methods=["POST"])
def submit_report():
    data = request.json

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    organization = data.get("organization", "").strip()
    region = data.get("region", "").strip()
    disease = data.get("disease", "").strip()
    number_of_cases = data.get("number_of_cases")
    date_observed = data.get("date_observed", "").strip()
    notes = data.get("notes", "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    if not region or not disease or not date_observed:
        return jsonify({"error": "Region, disease, and date observed are required"}), 400

    try:
        number_of_cases = int(number_of_cases)
        if number_of_cases < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Number of cases must be a valid positive number"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM submitters WHERE email = ?", (email,))
    existing = cursor.fetchone()

    if existing:
        submitter_id = existing["id"]
    else:
        cursor.execute("""
            INSERT INTO submitters (name, email, organization, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, email, organization, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        submitter_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO submissions (submitter_id, region, disease, number_of_cases, date_observed, observation_notes, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (submitter_id, region, disease, number_of_cases, date_observed, notes,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Thank you. Your report has been submitted successfully."})


# ============ ADMIN ROUTES ============

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password. Please try again."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


def admin_required():
    return session.get("is_admin", False)


@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")


@app.route("/api/admin/submissions")
def admin_get_submissions():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.region, s.disease, s.number_of_cases, s.date_observed,
               s.observation_notes, s.submitted_at,
               sub.name as submitter_name, sub.email as submitter_email, sub.organization
        FROM submissions s
        JOIN submitters sub ON s.submitter_id = sub.id
        ORDER BY s.submitted_at DESC
    """)
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)


@app.route("/api/admin/summary")
def admin_summary():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM submissions")
    total_submissions = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT submitter_id) as total FROM submissions")
    total_submitters = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(number_of_cases) as total FROM submissions")
    total_cases_reported = cursor.fetchone()["total"] or 0

    cursor.execute("""
        SELECT region, COUNT(*) as report_count, SUM(number_of_cases) as total_cases
        FROM submissions
        GROUP BY region
        ORDER BY total_cases DESC
    """)
    by_region = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT disease, COUNT(*) as report_count, SUM(number_of_cases) as total_cases
        FROM submissions
        GROUP BY disease
        ORDER BY total_cases DESC
    """)
    by_disease = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "total_submissions": total_submissions,
        "total_submitters": total_submitters,
        "total_cases_reported": total_cases_reported,
        "by_region": by_region,
        "by_disease": by_disease
    })


@app.route("/api/admin/export-csv")
def export_csv():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.region, s.disease, s.number_of_cases, s.date_observed,
               s.observation_notes, s.submitted_at,
               sub.name as submitter_name, sub.email as submitter_email, sub.organization
        FROM submissions s
        JOIN submitters sub ON s.submitter_id = sub.id
        ORDER BY s.submitted_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Region", "Disease", "Cases", "Date Observed", "Notes",
                      "Submitted At", "Submitter Name", "Submitter Email", "Organization"])

    for row in rows:
        writer.writerow([row["id"], row["region"], row["disease"], row["number_of_cases"],
                          row["date_observed"], row["observation_notes"], row["submitted_at"],
                          row["submitter_name"], row["submitter_email"], row["organization"]])

    csv_data = output.getvalue()
    output.close()

    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=outbreak_submissions.csv"
    }


create_submissions_table()

if __name__ == "__main__":
    print("Community Submissions module ready.")
    print("Public form: http://127.0.0.1:5000/submit")
    print("Admin login: http://127.0.0.1:5000/admin/login")
