# ============================================
# PREDICTIVE ANALYTICS FOR DISEASE OUTBREAKS
# Converted to PostgreSQL for persistent storage on Render
# By Emmanuel Owusu Adu
# ============================================

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import random
import csv
import io
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-dev-secret-change-this")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "local-dev-password-change-this")

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def create_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disease_history (
            id SERIAL PRIMARY KEY,
            disease TEXT NOT NULL,
            region TEXT NOT NULL,
            cases INTEGER NOT NULL,
            deaths INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            report_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_factors (
            id SERIAL PRIMARY KEY,
            region TEXT NOT NULL,
            rainfall_mm REAL NOT NULL,
            temperature_celsius REAL NOT NULL,
            population_density INTEGER NOT NULL,
            healthcare_access_score REAL NOT NULL,
            sanitation_score REAL NOT NULL,
            report_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submitters (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            organization TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id SERIAL PRIMARY KEY,
            submitter_id INTEGER NOT NULL REFERENCES submitters (id),
            region TEXT NOT NULL,
            disease TEXT NOT NULL,
            number_of_cases INTEGER NOT NULL,
            date_observed TEXT NOT NULL,
            observation_notes TEXT,
            submitted_at TEXT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    seed_historical_data(conn)
    conn.close()


def seed_historical_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM disease_history")
    if cursor.fetchone()["count"] > 0:
        cursor.close()
        return

    regions = ["Greater Accra", "Ashanti", "Northern", "Western", "Eastern"]
    diseases = ["Malaria", "Cholera", "Typhoid", "Meningitis", "COVID-19"]

    base_cases = {
        "Malaria": {"Greater Accra": 200, "Ashanti": 350, "Northern": 500, "Western": 150, "Eastern": 250},
        "Cholera": {"Greater Accra": 40, "Ashanti": 30, "Northern": 80, "Western": 20, "Eastern": 35},
        "Typhoid": {"Greater Accra": 60, "Ashanti": 45, "Northern": 90, "Western": 30, "Eastern": 50},
        "Meningitis": {"Greater Accra": 15, "Ashanti": 10, "Northern": 45, "Western": 8, "Eastern": 12},
        "COVID-19": {"Greater Accra": 150, "Ashanti": 100, "Northern": 70, "Western": 60, "Eastern": 80},
    }

    seasonal_factors = {
        1: 1.2, 2: 1.1, 3: 0.9, 4: 0.8, 5: 1.0, 6: 1.3,
        7: 1.5, 8: 1.6, 9: 1.4, 10: 1.2, 11: 1.0, 12: 1.1
    }

    records = []
    start_date = datetime(2023, 1, 1)

    for week in range(104):
        current_date = start_date + timedelta(weeks=week)
        month = current_date.month
        week_number = week % 52 + 1
        year = current_date.year
        seasonal = seasonal_factors[month]

        for disease in diseases:
            for region in regions:
                base = base_cases[disease][region]
                trend = 1 + (week * 0.002)
                noise = random.uniform(0.7, 1.3)
                cases = max(0, int(base * seasonal * trend * noise))
                deaths = max(0, int(cases * random.uniform(0.01, 0.05)))

                records.append((
                    disease, region, cases, deaths,
                    week_number, year,
                    current_date.strftime("%Y-%m-%d")
                ))

    execute_values(cursor, """
        INSERT INTO disease_history (disease, region, cases, deaths, week_number, year, report_date)
        VALUES %s
    """, records)

    risk_data = [
        ("Greater Accra", 45.2, 28.5, 1200, 7.2, 6.8, datetime.now().strftime("%Y-%m-%d")),
        ("Ashanti", 62.1, 26.8, 850, 6.5, 6.2, datetime.now().strftime("%Y-%m-%d")),
        ("Northern", 89.4, 32.1, 320, 4.2, 3.8, datetime.now().strftime("%Y-%m-%d")),
        ("Western", 71.3, 27.4, 480, 5.8, 5.5, datetime.now().strftime("%Y-%m-%d")),
        ("Eastern", 58.7, 27.9, 620, 6.1, 5.9, datetime.now().strftime("%Y-%m-%d")),
    ]

    execute_values(cursor, """
        INSERT INTO risk_factors (region, rainfall_mm, temperature_celsius, population_density, healthcare_access_score, sanitation_score, report_date)
        VALUES %s
    """, risk_data)

    conn.commit()
    cursor.close()


def simple_linear_prediction(values, weeks_ahead=4):
    n = len(values)
    if n < 2:
        return [values[-1]] if values else [0]

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    predictions = []

    for i in range(weeks_ahead):
        pred = intercept + slope * (n + i)
        predictions.append(max(0, int(pred)))

    return predictions


def calculate_risk_score(disease, region, recent_cases, trend_slope, risk_factors):
    base_risk = min(100, (recent_cases / 500) * 40)
    trend_risk = min(30, max(0, trend_slope * 10))

    environmental_risk = 0
    if risk_factors:
        rainfall = risk_factors["rainfall_mm"]
        temperature = risk_factors["temperature_celsius"]
        healthcare = risk_factors["healthcare_access_score"]
        sanitation = risk_factors["sanitation_score"]

        if disease == "Malaria":
            environmental_risk = min(30, (rainfall / 100) * 15 + (temperature - 25) * 2)
        elif disease == "Cholera":
            environmental_risk = min(30, (rainfall / 100) * 20 + (10 - sanitation) * 3)
        elif disease == "Meningitis":
            environmental_risk = min(30, (temperature - 20) * 3 + (10 - healthcare) * 2)
        else:
            environmental_risk = min(30, (10 - healthcare) * 2 + (10 - sanitation) * 1)

    total_risk = base_risk + trend_risk + environmental_risk

    if total_risk >= 70:
        risk_level = "Critical"
    elif total_risk >= 50:
        risk_level = "High"
    elif total_risk >= 30:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    confidence = min(95, 60 + random.uniform(10, 30))
    return round(total_risk, 1), risk_level, round(confidence, 1)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/historical-trends")
def get_historical_trends():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT disease, report_date, SUM(cases) as total_cases
        FROM disease_history
        WHERE year >= 2024
        GROUP BY disease, report_date
        ORDER BY report_date
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    result = {}
    for row in data:
        disease = row["disease"]
        if disease not in result:
            result[disease] = {"dates": [], "cases": []}
        result[disease]["dates"].append(row["report_date"])
        result[disease]["cases"].append(row["total_cases"])

    every_nth = 4
    for disease in result:
        result[disease]["dates"] = result[disease]["dates"][::every_nth]
        result[disease]["cases"] = result[disease]["cases"][::every_nth]

    return jsonify(result)


@app.route("/api/predictions")
def get_predictions():
    conn = get_db()
    cursor = conn.cursor()

    diseases = ["Malaria", "Cholera", "Typhoid", "Meningitis", "COVID-19"]
    regions = ["Greater Accra", "Ashanti", "Northern", "Western", "Eastern"]
    predictions = []

    for disease in diseases:
        for region in regions:
            cursor.execute("""
                SELECT cases FROM disease_history
                WHERE disease = %s AND region = %s
                ORDER BY report_date DESC
                LIMIT 12
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]
            recent_data.reverse()

            if not recent_data:
                continue

            cursor.execute("SELECT * FROM risk_factors WHERE region = %s", (region,))
            risk_row = cursor.fetchone()
            risk_factors = dict(risk_row) if risk_row else {}

            predicted_values = simple_linear_prediction(recent_data, weeks_ahead=4)
            predicted_cases = predicted_values[-1] if predicted_values else recent_data[-1]

            n = len(recent_data)
            x_mean = (n - 1) / 2
            y_mean = sum(recent_data) / n
            numerator = sum((i - x_mean) * (recent_data[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            trend_slope = numerator / denominator if denominator != 0 else 0

            risk_score, risk_level, confidence = calculate_risk_score(
                disease, region, recent_data[-1], trend_slope, risk_factors
            )

            target_date = (datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%d")

            predictions.append({
                "disease": disease,
                "region": region,
                "current_cases": recent_data[-1],
                "predicted_cases": predicted_cases,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "confidence": confidence,
                "trend": "Increasing" if trend_slope > 5 else "Decreasing" if trend_slope < -5 else "Stable",
                "target_date": target_date
            })

    cursor.close()
    conn.close()
    predictions.sort(key=lambda x: x["risk_score"], reverse=True)
    return jsonify(predictions)


@app.route("/api/risk-summary")
def get_risk_summary():
    conn = get_db()
    cursor = conn.cursor()

    diseases = ["Malaria", "Cholera", "Typhoid", "Meningitis", "COVID-19"]
    regions = ["Greater Accra", "Ashanti", "Northern", "Western", "Eastern"]
    region_risks = {}

    for region in regions:
        total_risk = 0
        disease_count = 0

        for disease in diseases:
            cursor.execute("""
                SELECT cases FROM disease_history
                WHERE disease = %s AND region = %s
                ORDER BY report_date DESC
                LIMIT 8
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]

            if recent_data:
                cursor.execute("SELECT * FROM risk_factors WHERE region = %s", (region,))
                risk_row = cursor.fetchone()
                risk_factors = dict(risk_row) if risk_row else {}

                n = len(recent_data)
                x_mean = (n - 1) / 2
                y_mean = sum(recent_data) / n
                numerator = sum((i - x_mean) * (recent_data[i] - y_mean) for i in range(n))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                trend_slope = numerator / denominator if denominator != 0 else 0

                risk_score, _, _ = calculate_risk_score(disease, region, recent_data[0], trend_slope, risk_factors)
                total_risk += risk_score
                disease_count += 1

        avg_risk = round(total_risk / disease_count, 1) if disease_count > 0 else 0

        if avg_risk >= 70:
            risk_level = "Critical"
        elif avg_risk >= 50:
            risk_level = "High"
        elif avg_risk >= 30:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        region_risks[region] = {"risk_score": avg_risk, "risk_level": risk_level}

    cursor.close()
    conn.close()
    return jsonify(region_risks)


@app.route("/api/disease-forecast/<disease>")
def get_disease_forecast(disease):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT report_date, SUM(cases) as total_cases
        FROM disease_history
        WHERE disease = %s AND year >= 2024
        GROUP BY report_date
        ORDER BY report_date
    """, (disease,))
    historical = cursor.fetchall()
    cursor.close()
    conn.close()

    if not historical:
        return jsonify({"error": "No data found"})

    dates = [row["report_date"] for row in historical]
    cases = [row["total_cases"] for row in historical]

    future_predictions = simple_linear_prediction(cases, weeks_ahead=8)
    last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    future_dates = [(last_date + timedelta(weeks=i + 1)).strftime("%Y-%m-%d") for i in range(8)]

    every_nth = 3
    return jsonify({
        "disease": disease,
        "historical_dates": dates[::every_nth],
        "historical_cases": cases[::every_nth],
        "forecast_dates": future_dates,
        "forecast_cases": future_predictions
    })


@app.route("/api/top-risks")
def get_top_risks():
    conn = get_db()
    cursor = conn.cursor()

    diseases = ["Malaria", "Cholera", "Typhoid", "Meningitis", "COVID-19"]
    regions = ["Greater Accra", "Ashanti", "Northern", "Western", "Eastern"]
    all_risks = []

    for disease in diseases:
        for region in regions:
            cursor.execute("""
                SELECT cases FROM disease_history
                WHERE disease = %s AND region = %s
                ORDER BY report_date DESC
                LIMIT 8
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]

            if recent_data:
                cursor.execute("SELECT * FROM risk_factors WHERE region = %s", (region,))
                risk_row = cursor.fetchone()
                risk_factors = dict(risk_row) if risk_row else {}

                n = len(recent_data)
                x_mean = (n - 1) / 2
                y_mean = sum(recent_data) / n
                numerator = sum((i - x_mean) * (recent_data[i] - y_mean) for i in range(n))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                trend_slope = numerator / denominator if denominator != 0 else 0

                risk_score, risk_level, confidence = calculate_risk_score(
                    disease, region, recent_data[0], trend_slope, risk_factors
                )

                all_risks.append({
                    "disease": disease,
                    "region": region,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "current_cases": recent_data[0]
                })

    all_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    cursor.close()
    conn.close()
    return jsonify(all_risks[:10])


# ============ PUBLIC SUBMISSION ROUTES ============

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

    cursor.execute("SELECT id FROM submitters WHERE email = %s", (email,))
    existing = cursor.fetchone()

    if existing:
        submitter_id = existing["id"]
    else:
        cursor.execute("""
            INSERT INTO submitters (name, email, organization, created_at)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (name, email, organization, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        submitter_id = cursor.fetchone()["id"]

    cursor.execute("""
        INSERT INTO submissions (submitter_id, region, disease, number_of_cases, date_observed, observation_notes, submitted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (submitter_id, region, disease, number_of_cases, date_observed, notes,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    cursor.close()
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
    cursor.close()
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

    cursor.execute("SELECT COALESCE(SUM(number_of_cases), 0) as total FROM submissions")
    total_cases_reported = cursor.fetchone()["total"]

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

    cursor.close()
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
    cursor.close()
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


create_database()

if __name__ == "__main__":
    print("Disease Outbreak Prediction System starting...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    print("Public submission form: http://127.0.0.1:5000/submit")
    print("Admin login: http://127.0.0.1:5000/admin/login")
    app.run(debug=True)
