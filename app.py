# ============================================
# PREDICTIVE ANALYTICS FOR DISEASE OUTBREAKS
# Building Real Health Informatics Projects
# By Emmanuel Owusu Adu
# ============================================

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("outbreaks.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disease_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease TEXT NOT NULL,
            region TEXT NOT NULL,
            predicted_cases INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            prediction_date TEXT NOT NULL,
            target_date TEXT NOT NULL
        )
    """)

    conn.commit()
    seed_historical_data(cursor, conn)
    conn.close()

def seed_historical_data(cursor, conn):
    cursor.execute("SELECT COUNT(*) FROM disease_history")
    if cursor.fetchone()[0] > 0:
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

    cursor.executemany("""
        INSERT INTO disease_history (disease, region, cases, deaths, week_number, year, report_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, records)

    risk_data = [
        ("Greater Accra", 45.2, 28.5, 1200, 7.2, 6.8, datetime.now().strftime("%Y-%m-%d")),
        ("Ashanti", 62.1, 26.8, 850, 6.5, 6.2, datetime.now().strftime("%Y-%m-%d")),
        ("Northern", 89.4, 32.1, 320, 4.2, 3.8, datetime.now().strftime("%Y-%m-%d")),
        ("Western", 71.3, 27.4, 480, 5.8, 5.5, datetime.now().strftime("%Y-%m-%d")),
        ("Eastern", 58.7, 27.9, 620, 6.1, 5.9, datetime.now().strftime("%Y-%m-%d")),
    ]

    cursor.executemany("""
        INSERT INTO risk_factors (region, rainfall_mm, temperature_celsius, population_density, healthcare_access_score, sanitation_score, report_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, risk_data)

    conn.commit()


def simple_linear_prediction(values, weeks_ahead=4):
    n = len(values)
    if n < 2:
        return values[-1] if values else 0

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator

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
                WHERE disease = ? AND region = ?
                ORDER BY report_date DESC
                LIMIT 12
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]
            recent_data.reverse()

            if not recent_data:
                continue

            cursor.execute("""
                SELECT * FROM risk_factors WHERE region = ?
            """, (region,))
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
                WHERE disease = ? AND region = ?
                ORDER BY report_date DESC
                LIMIT 8
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]

            if recent_data:
                cursor.execute("SELECT * FROM risk_factors WHERE region = ?", (region,))
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

        region_risks[region] = {
            "risk_score": avg_risk,
            "risk_level": risk_level
        }

    conn.close()
    return jsonify(region_risks)


@app.route("/api/disease-forecast/<disease>")
def get_disease_forecast(disease):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT report_date, SUM(cases) as total_cases
        FROM disease_history
        WHERE disease = ? AND year >= 2024
        GROUP BY report_date
        ORDER BY report_date
    """, (disease,))
    historical = cursor.fetchall()
    conn.close()

    if not historical:
        return jsonify({"error": "No data found"})

    dates = [row["report_date"] for row in historical]
    cases = [row["total_cases"] for row in historical]

    future_predictions = simple_linear_prediction(cases, weeks_ahead=8)
    last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    future_dates = [(last_date + timedelta(weeks=i+1)).strftime("%Y-%m-%d") for i in range(8)]

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
                WHERE disease = ? AND region = ?
                ORDER BY report_date DESC
                LIMIT 8
            """, (disease, region))
            recent_data = [row["cases"] for row in cursor.fetchall()]

            if recent_data:
                cursor.execute("SELECT * FROM risk_factors WHERE region = ?", (region,))
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
    conn.close()
    return jsonify(all_risks[:10])


if __name__ == "__main__":
    create_database()
    print("Disease Outbreak Prediction System starting...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    app.run(debug=True)
