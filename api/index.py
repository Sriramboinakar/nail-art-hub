from flask import Flask, render_template, jsonify, request
from datetime import date, datetime
import json
import os, urllib.request, urllib.parse
import sys
import hashlib
import hmac
import smtplib
from email.mime.text import MIMEText

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
    {"id": 2, "name": "Moula Ali", "address": "Moula Ali, Hyderabad", "phone": "TBA", "timings": "10 AM - 8 PM", "maps": "https://www.google.com/maps/place/Nail+art+hub/@17.4643312,78.5619509,17z/data=!4m6!3m5!1s0x3bcb9bdb56a47b4f:0xc50177815d76c392!8m2!3d17.4643312!4d78.5645258!16s%2Fg%2F11yg2cwk43"}
]

FALLBACK_REVIEWS = [
    {"author": "Priya S.", "rating": 5, "text": "Ayesha did my bridal nails and they were absolutely stunning. Got so many compliments throughout the wedding. Highly recommend!", "date": "2 months ago"},
    {"author": "Sneha R.", "rating": 5, "text": "Best nail artist in Hyderabad. My GelX extensions lasted over 3 weeks and looked so natural. Love coming here!", "date": "1 month ago"},
    {"author": "Riya K.", "rating": 5, "text": "Been coming to Ayesha for months now. Every time she nails the design perfectly. My go-to place for everything nails.", "date": "3 weeks ago"},
    {"author": "Ananya M.", "rating": 4, "text": "Great service and very professional. The gel polish lasted 2 weeks without chipping. Will definitely come back!", "date": "2 weeks ago"},
    {"author": "Pooja G.", "rating": 5, "text": "Amazing mehandi work for my engagement. So detailed and lasted over a week. Ayesha is incredibly talented!", "date": "1 week ago"}
]

PLACE_ID = "0x3bcb9bdb56a47b4f:0xc50177815d76c392"

TIME_SLOTS = ["10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM", "6:00 PM"]

# Razorpay
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
try:
    import razorpay
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    else:
        razorpay_client = None
except Exception:
    razorpay_client = None

# SMTP
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_booking_email(booking):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return
    try:
        body = """New Booking - Nail Art Hub

Client: {name}
Phone: {phone}
Service: {service}
Branch: {branch}
Date: {date}
Time: {time}
Payment: {payment}
Status: Confirmed
""".format(name=booking["client_name"], phone=booking["phone"], service=booking["service_name"],
           branch=booking["branch_name"], date=booking["date"], time=booking["time"],
           payment=booking.get("payment_status", "pending"))
        msg = MIMEText(body)
        msg["Subject"] = "New Booking - {name} - {service}".format(name=booking["client_name"], service=booking["service_name"])
        msg["To"] = SMTP_EMAIL
        msg["From"] = SMTP_EMAIL
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception:
        pass

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

REVIEWS_FILE = os.path.join(DATA_DIR, "reviews_cache.json")

@app.route("/api/reviews")
def get_reviews():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if api_key:
        try:
            cached = load_json(REVIEWS_FILE, [])
            if cached:
                return jsonify(cached)
            url = "https://maps.googleapis.com/maps/api/place/details/json?place_id=" + urllib.parse.quote(PLACE_ID) + "&fields=name,rating,reviews&key=" + api_key
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == "OK" and "result" in data:
                result = data["result"]
                reviews = []
                for r in result.get("reviews", []):
                    reviews.append({
                        "author": r.get("author_name", "Anonymous"),
                        "rating": r.get("rating", 5),
                        "text": r.get("text", ""),
                        "date": r.get("relative_time_description", "")
                    })
                if reviews:
                    save_json(REVIEWS_FILE, reviews)
                    return jsonify(reviews)
        except Exception:
            pass
    return jsonify(FALLBACK_REVIEWS)

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
    send_booking_email(booking)
    return jsonify(booking), 201

@app.route("/api/razorpay-config")
def razorpay_config():
    if not RAZORPAY_KEY_ID:
        return jsonify({"key": ""}), 200
    return jsonify({"key": RAZORPAY_KEY_ID})

@app.route("/api/create-order", methods=["POST"])
def create_order():
    if not razorpay_client:
        return jsonify({"error": "Razorpay not configured"}), 503
    try:
        order = razorpay_client.order.create({
            "amount": 9900,
            "currency": "INR",
            "receipt": "booking_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "payment_capture": 1
        })
        return jsonify({"id": order["id"], "amount": order["amount"], "currency": order["currency"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/verify-payment", methods=["POST"])
def verify_payment():
    d = request.json
    sig = d.get("razorpay_signature", "")
    order_id = d.get("razorpay_order_id", "")
    pay_id = d.get("razorpay_payment_id", "")
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        (order_id + "|" + pay_id).encode(),
        hashlib.sha1
    ).hexdigest()
    if sig == expected:
        return jsonify({"verified": True})
    return jsonify({"verified": False}), 400

@app.route("/admin/bookings")
def admin_bookings():
    bookings = load_json(BOOKINGS_FILE, [])
    return jsonify(sorted(bookings, key=lambda b: b["id"], reverse=True))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
