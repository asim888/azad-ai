---

✅ whatsapp_bot.py

python
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import requests, json, os, hmac, hashlib
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(_name_)

Environment variables
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
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

def create_instamojo_payment(phone):
    url = "https://www.instamojo.com/api/1.1/payment-requests/"
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN,
    }
    payload = {
        "purpose": "Azad AI Subscription",
        "amount": "99",
        "buyer_name": phone,
"phone": phone,
        "send_email": False,
        "send_sms": True,
        "allow_repeated_payments": False,
        "redirect_url": "https://www.google.com", # Optional
        "webhook": "https://your-render-url.onrender.com/instamojo_webhook"
    }
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["payment_request"]["longurl"]
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
    incoming_msg = request.values.get("Body", "").lower()

"Body": "📰 Daily News Headline: ..."
            }
            auth = (os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            requests.post(url, data=payload, auth=auth)

if _name_ == "_main_":
    send_daily_news() # Optional test
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_news, "cron", hour=9, minute=0)
    scheduler.start()
    app.run()


---

✅ What this includes:
- Payment link generation via Instamojo
- Auto-subscription using webhook
- WhatsApp interaction via Twilio
- Daily news scheduler (optional)
- users.json storage for subscriptions

---

Let me know if you want:
- Voice command handling
- Facebook feed
- News API integration
- Multi-language support (e.g., Roman Urdu)

Also tell me if you need updated requirements.txt.

from_number = request.values.get("From", "").replace("whatsapp:", "")
    resp = MessagingResponse()
    msg = resp.message()
    users = load_users()

    if from_number not in users or not users[from_number].get("subscribed"):
        pay_link = create_instamojo_payment(from_number)
        if pay_link:
            msg.body(f"🔒 To subscribe to Azad AI, please pay ₹99:pay_link")
        else:
            msg.body("⚠️ Unable to generate payment link. Try again later.")
        return str(resp)

    # Your AI logic or command handling here
    if "news" in incoming_msg:
        msg.body("📰 Today's news: ...")
    elif "hi" in incoming_msg:
        msg.body("👋 Hello! I'm Azad AI. Ask me anything or type 'news' to get updates.")
    else:
        msg.body("🤖 I’m thinking... (AI response here)")
    
    return str(resp)

@app.route("/", methods=["GET"])
def home():
    return "Azad AI is running!"

Scheduler (e.g. for daily news — optional)
def send_daily_news():
    users = load_users()
    for phone, info in users.items():
        if info.get("subscribed"):
            url = f"https://api.twilio.com/2010-04-01/Accounts/{os.getenv('TWILIO_SID')}/Messages.json"
            payload = {
                "From": f"whatsapp:{TWILIO_PHONE}",
                "To": f"whatsapp:{phone}",