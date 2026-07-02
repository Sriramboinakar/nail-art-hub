from flask import Flask, render_template, jsonify, request
from datetime import date, datetime
import json
import os
import sys

IS_VERCEL = os.environ.get("VERCEL") == "1" or os.environ.get("VERCEL_ENV") is not None

# Paths - local vs Vercel
if IS_VERCEL:
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
    DATA_DIR = "/tmp/data"
else:
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
    DATA_DIR = os.path.join(BASE_DIR, "data")

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR, static_url_path="/static")

os.makedirs(DATA_DIR, exist_ok=True)

BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
BRANCHES_FILE = os.path.join(DATA_DIR, "branches.json")

DEFAULT_SERVICES = [
    {"id": 1, "name": "Gel Polish", "price": 35, "desc": "Long-lasting shine with gel finish"},
    {"id": 2, "name": "GelX Extensions", "price": 45, "desc": "Lightweight natural-looking extensions"},
    {"id": 3, "name": "Gel Extensions", "price": 50, "desc": "Strong durable gel for added length"},
    {"id": 4, "name": "Acrylic Extensions", "price": 50, "desc": "Perfect shape and length with acrylic"},
    {"id": 5, "name": "Gel/Acrylic Refills", "price": 30, "desc": "Refill and refresh your extensions"},
    {"id": 6, "name": "Gel Polish Removal", "price": 15, "desc": "Safe and gentle gel removal"},
    {"id": 7, "name": "Extensions Removal", "price": 20, "desc": "Professional removal without damage"},
    {"id": 8, "name": "Legs Gel Polish", "price": 40, "desc": "Gel pedicure with long-lasting color"},
    {"id": 9, "name": "Legs Extensions", "price": 45, "desc": "Toe nail extensions for perfect feet"},
    {"id": 10, "name": "Mehandi", "price": 49, "desc": "Intricate henna designs for all occasions"},
    {"id": 11, "name": "Makeup", "price": 99, "desc": "Professional makeup for brides and events"}
]

DEFAULT_BRANCHES = [
    {"id": 1, "name": "Dammaiguda", "address": "Dammaiguda, Hyderabad", "phone": "TBA", "timings": "10 AM - 8 PM", "maps": "https://share.google/BO8n1BS5hnwJsdkFb"},
    {"id": 2, "name": "Moula Ali", "address": "Moula Ali, Hyderabad", "phone": "TBA", "timings": "10 AM - 8 PM", "maps": "https://share.google/YaLRVzZx8LbY6POBY"}
]

TIME_SLOTS = ["10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM", "6:00 PM"]

def load_json(path, default):
    if not os.path.exists(path):
        try:
            with open(path, "w") as f:
                json.dump(default, f, indent=2)
        except OSError:
            return default
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass

@app.route("/")
def home():
    services = load_json(SERVICES_FILE, DEFAULT_SERVICES)
    branches = load_json(BRANCHES_FILE, DEFAULT_BRANCHES)
    return render_template("index.html", services=services, branches=branches, time_slots=TIME_SLOTS)

@app.route("/api/services")
def get_services():
    return jsonify(load_json(SERVICES_FILE, DEFAULT_SERVICES))

@app.route("/api/branches")
def get_branches():
    return jsonify(load_json(BRANCHES_FILE, DEFAULT_BRANCHES))

@app.route("/api/slots")
def get_slots():
    branch_id = request.args.get("branch", "1")
    date_str = request.args.get("date", date.today().isoformat())
    bookings = load_json(BOOKINGS_FILE, [])
    booked_list = [b["time"] for b in bookings if b.get("branch_id") == branch_id and b.get("date") == date_str and b.get("status") != "cancelled"]
    slots = [{"time": s, "booked": s in booked_list} for s in TIME_SLOTS]
    return jsonify(slots)

@app.route("/api/book", methods=["POST"])
def book():
    d = request.json
    bookings = load_json(BOOKINGS_FILE, [])
    new_id = max([b["id"] for b in bookings], default=0) + 1
    booking = {
        "id": new_id,
        "client_name": d.get("name"),
        "phone": d.get("phone"),
        "service_id": d.get("service_id"),
        "service_name": d.get("service_name"),
        "branch_id": d.get("branch_id"),
        "branch_name": d.get("branch_name"),
        "date": d.get("date"),
        "time": d.get("time"),
        "total": int(d.get("total", 0)),
        "advance": int(d.get("advance", 0)),
        "payment_status": d.get("payment_status", "pending"),
        "status": "confirmed",
        "created": datetime.now().isoformat()
    }
    bookings.append(booking)
    save_json(BOOKINGS_FILE, bookings)
    return jsonify(booking), 201

@app.route("/admin/bookings")
def admin_bookings():
    bookings = load_json(BOOKINGS_FILE, [])
    return jsonify(sorted(bookings, key=lambda b: b["id"], reverse=True))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
