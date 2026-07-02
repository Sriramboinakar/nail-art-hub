from flask import Flask, render_template, jsonify, request
from datetime import date, datetime
import json
import os

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
BRANCHES_FILE = os.path.join(DATA_DIR, "branches.json")

os.makedirs(DATA_DIR, exist_ok=True)

# Default data
DEFAULT_SERVICES = [
    {"id": 1, "name": "Gel Manicure", "price": 35, "desc": "Long-lasting shine with gel finish"},
    {"id": 2, "name": "Nail Art Design", "price": 55, "desc": "Custom artistic nail designs"},
    {"id": 3, "name": "Acrylic Full Set", "price": 50, "desc": "Perfect shape and length"},
    {"id": 4, "name": "Gel Pedicure", "price": 40, "desc": "Relaxing foot care with gel"},
    {"id": 5, "name": "Manicure + Pedicure Combo", "price": 65, "desc": "Full hand and foot care"}
]

DEFAULT_BRANCHES = [
    {"id": 1, "name": "Dammaiguda", "address": "Dammaiguda, Hyderabad", "phone": "TBA", "timings": "10 AM - 8 PM", "maps": "https://share.google/BO8n1BS5hnwJsdkFb"},
    {"id": 2, "name": "Moula Ali", "address": "Moula Ali, Hyderabad", "phone": "TBA", "timings": "10 AM - 8 PM", "maps": "https://share.google/YaLRVzZx8LbY6POBY"}
]

TIME_SLOTS = ["10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM", "6:00 PM"]

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=2)
        return default
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

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
    booked = [b["time"] for b in bookings if b["branch_id"] == branch_id and b["date"] == date_str and b["status"] != "cancelled"]
    slots = []
    for s in TIME_SLOTS:
        slots.append({"time": s, "booked": s in booked})
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
