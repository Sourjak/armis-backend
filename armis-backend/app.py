from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import smtplib, ssl, os

app = Flask(__name__)
CORS(app)

# Secret key for login sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

# In-memory storage for latest sensor data
latest_data = {}

# -------------------------------------
# Email alert function
# -------------------------------------
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

# -------------------------------------
# Chief Engine thresholds (existing logic)
# -------------------------------------
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
        print("Trigger check failed:", e)

# -------------------------------------
# Risk Analysis Logic
# -------------------------------------
def calculate_risk(data):
    score = 0
    factors = {}

    # Rain factor (40%)
    rain = data.get("rain", "").lower()
    if "heavy" in rain:
        score += 40
        factors["Rainfall"] = 40
    elif "light" in rain:
        score += 20
        factors["Rainfall"] = 20

    # Soil factor (30%)
    soil = data.get("soil", "").lower()
    if "wet" in soil:
        score += 30
        factors["Soil"] = 30
    elif "dry" in soil:
        score += 10
        factors["Soil"] = 10

    # Vibration factor (20%)
    vibration = data.get("vibration", "").lower()
    if "strong" in vibration:
        score += 20
        factors["Vibration"] = 20
    elif "mild" in vibration:
        score += 10
        factors["Vibration"] = 10

    # Temperature factor (10%)
    try:
        temp = float(data.get("temperature", 0))
        if temp > 35:
            score += 10
            factors["Temperature"] = 10
    except:
        pass

    # Determine main factor
    main_factor = max(factors, key=factors.get) if factors else "Unknown"

    return {
        "risk_percent": score,
        "risk_level": (
            "Low" if score <= 30 else
            "Medium" if score <= 60 else
            "High"
        ),
        "main_factor": main_factor
    }

# -------------------------------------
# Upload endpoint (Arduino → Backend)
# -------------------------------------
@app.route("/upload", methods=["POST"])
def upload_data():
    global latest_data
    data = request.json
    latest_data = data
    check_triggers(data)
    return jsonify({"status": "ok", "received": data})

# -------------------------------------
# Data endpoint (Frontend fetches live data)
# -------------------------------------
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(latest_data if latest_data else {"message": "no data yet"})

# -------------------------------------
# Login page
# -------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# -------------------------------------
# Dashboard page
# -------------------------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# -------------------------------------
# Risk Analysis Page
# -------------------------------------
@app.route("/risk")
def risk():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("risk.html")

@app.route("/risk-data")
def risk_data():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    analysis = calculate_risk(latest_data)
    return jsonify(analysis)

# -------------------------------------
# Manual Trigger Alert
# -------------------------------------
@app.route("/trigger-alert", methods=["POST"])
def trigger_alert():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    send_alert("🚨 Manual Risk Alert", "Alert triggered manually by admin/chief engineer.")
    return jsonify({"status": "ok", "message": "Alert triggered"})

# -------------------------------------
# Run Flask
# -------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
