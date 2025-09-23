from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import smtplib, ssl, os

app = Flask(__name__)
CORS(app)

# Secret key for login sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

# In-memory storage for latest sensor data
latest_data = {}

# Email alert function
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

# Chief Engine thresholds
def check_triggers(data):
    try:
        temp = float(data.get("Temp", "0").replace(" °C", ""))
    except:
        temp = 0
    soil = data.get("Soil", "").lower()
    rain = data.get("Rain", "").lower()

    if temp > 35:
        send_alert("🔥 High Temperature Alert", f"Temperature reached {temp} °C")
    if "dry" in soil:
        send_alert("🌱 Soil Dry Alert", f"Soil condition: {soil}")
    if "rain" in rain and "no" not in rain:
        send_alert("🌧️ Rain Alert", f"Rain status: {rain}")

# -----------------------------
# API Endpoints
# -----------------------------

# Upload endpoint (Arduino → Backend)
@app.route("/upload", methods=["POST"])
def upload_data():
    global latest_data
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    latest_data.update(data)
    check_triggers(data)
    return jsonify({"status": "ok", "received": data})

# Data endpoint (Frontend fetches this)
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(latest_data if latest_data else {"message": "no data yet"})

# Login page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "password":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# Dashboard page
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

if __name__ == "__main__":
    # Use port 10000 for Render deployment
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
