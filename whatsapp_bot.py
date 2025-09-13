
from flask import Flask, request
from flask_twilio.messaging_response import MessagingResponse
import requests, json, os, hmac, hashlib
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
load_dotenv()

app = Flask(_name_)

Env Variables
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
INSTAMOJO_API_KEY = os.getenv("INSTAMOJO_API_KEY")
INSTAMOJO_AUTH_TOKEN = os.getenv("INSTAMOJO_AUTH_TOKEN")
INSTAMOJO_WEBHOOK_SECRET = os.getenv("INSTAMOJO_WEBHOOK_SECRET")

users_file = "users.json"

def load_users():
    if not os.path.exists(users_file):
        return {}
    with open(users_file, "r") as f:
        return json.load(f)

def save_users(users):
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

def create_payment_link(phone):
    url = "https://www.instamojo.com/api/1.1/payment-requests/"
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN
    }
    payload = {
"purpose": "Azad AI Subscription",
        "amount": "99",
        "phone": phone,
        "buyer_name": phone,
        "send_sms": True,
        "allow_repeated_payments": False,
        "webhook": "https://your-render-app.onrender.com/instamojo_webhook"
    }
    r = requests.post(url, data=payload, headers=headers)
    if r.status_code == 200:
        return r.json()["payment_request"]["longurl"]
    return None

@app.route("/instamojo_webhook", methods=["POST"])
def instamojo_webhook():
    data = request.form.to_dict()
    received_sig = request.headers.get("X-Instamojo-Signature")

    if INSTAMOJO_WEBHOOK_SECRET:
        payload = "&".join([f"{k}={v}" for k, v in sorted(data.items())])
        digest = hmac.new(
            INSTAMOJO_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha1
        ).hexdigest()
        if digest != received_sig:
            return "Signature mismatch", 400

    if data.get("status") == "Credit":
        phone = data.get("buyer_phone")
        users = load_users()
        users[phone] = {"subscribed": True}
        save_users(users)

    return "OK", 200

@app.route("/bot", methods=["POST"])
def bot():
    incoming = request.values.get("Body", "").lower()
requests.post(url, data=payload, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN))

if _name_ == "_main_":
    send_daily_news()
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_news, "cron", hour=9, minute=0)
    scheduler.start()
    app.run()

from_number = request.values.get("From", "").replace("whatsapp:", "")
    resp = MessagingResponse()
    msg = resp.message()

    users = load_users()
    user = users.get(from_number)

    if not user or not user.get("subscribed"):
        pay_link = create_payment_link(from_number)
        if pay_link:
            msg.body(f"🔐 Please subscribe to Azad AI for ₹99:pay_link")
        else:
            msg.body("⚠️ Could not create payment link. Try again.")
        return str(resp)

    # Subscribed user: handle commands
    if "news" in incoming:
        msg.body("📰 Today's news headline: ...")
    elif "hi" in incoming:
        msg.body("👋 Hello! Ask me anything or type 'news'.")
    else:
        msg.body("🤖 AI response coming soon...")

    return str(resp)

@app.route("/", methods=["GET"])
def home():
    return "Azad AI is Live!"

Optional: Daily news scheduler
def send_daily_news():
    users = load_users()
    for phone, info in users.items():
        if info.get("subscribed"):
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
            payload = {
                "From": f"whatsapp:{TWILIO_PHONE}",
                "To": f"whatsapp:{phone}",
                "Body": "📰 Daily News: ..."
            }
---