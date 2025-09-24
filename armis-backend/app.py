from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import smtplib, ssl, os

app = Flask(__name__)
CORS(app)

# Secret key for login sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

# In-memory storage for latest sensor data
latest_data = {}

# -----------------------------
# Email alert function (future)
# -----------------------------
def send_alert(subject, body):
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    alert_to = os.getenv("ALERT_TO")

    if not (smtp_user and smtp_pass and alert_to):
        print("⚠️ Email credentials not set in environment variables.")
        return

    msg = f"Subject: {subject}\n\n{body}"
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, alert_to.split(","), msg)
        print("✅ Alert email sent")
    except Exception as e:
        print("❌ Failed to send email:", e)

# -----------------------------
# Chief Engine thresholds
# -----------------------------
def check_triggers(data):
    try:
        temp = float(data.get("temperature", 0))
        soil = data.get("soil", "").lower()
        rain = data.get("rain", "").lower()

        if temp > 35:
            send_alert("🔥 High Temperature Alert", f"Temperature reached {temp} °C")
        if "dry" in soil:
            send_alert("🌱 Soil Dry Alert", f"Soil condition: {soil}")
        if "rain" in rain and "no" not in rain:
            send_alert("🌧️ Rain Alert", f"Rain status: {rain}")
    except Exception as e:
        print("⚠️ Trigger check failed:", e)

# -----------------------------
# Risk Analysis calculation
# -----------------------------
def calculate_risk(data):
    try:
        temp = float(data.get("temperature", 0))
        soil = data.get("soil", "").lower()
        rain = data.get("rain", "").lower()
        vibration = data.get("vibration", "").lower()

        risk_score = 0
        factors = []

        if temp > 35:
            risk_score += 25
            factors.append("Temperature")
        if "dry" in soil:
            risk_score += 25
            factors.append("Soil")
        if "rain" in rain and "no" not in rain:
            risk_score += 25
            factors.append("Rain")
        if "strong" in vibration or "high" in vibration:
            risk_score += 25
            factors.append("Vibration")

        if risk_score >= 75:
            risk_level = "High"
        elif risk_score >= 50:
            risk_level = "Medium"
        elif risk_score > 0:
            risk_level = "Low"
        else:
            risk_level = "Safe"

        return {
            "risk_percent": risk_score,
            "risk_level": risk_level,
            "main_factor": factors[0] if factors else "None"
        }
    except Exception as e:
        print("⚠️ Risk analysis failed:", e)
        return {
            "risk_percent": 0,
            "risk_level": "Error",
            "main_factor": "N/A"
        }

# -----------------------------
# Upload endpoint (Arduino → Backend)
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload_data():
    global latest_data
    data = request.json or {}
    latest_data = data
    check_triggers(data)
    return jsonify({"status": "ok", "received": data})

# -----------------------------
# Data endpoint (Frontend fetches this)
# -----------------------------
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(latest_data if latest_data else {"message": "no data yet"})

# -----------------------------
# Risk Data endpoint
# -----------------------------
@app.route("/risk-data")
def risk_data():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if not latest_data:  # Prevent crash when no Arduino data
        return jsonify({
            "risk_percent": 0,
            "risk_level": "No Data",
            "main_factor": "N/A"
        })

    analysis = calculate_risk(latest_data)
    return jsonify(analysis)

# -----------------------------
# Login page
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        if request.form["username"] == "chief" and request.form["password"] == "engineer":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# -----------------------------
# Dashboard page
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# -----------------------------
# Risk Analysis page
# -----------------------------
@app.route("/risk")
def risk():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("risk.html")

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
