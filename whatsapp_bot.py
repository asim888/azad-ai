from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests, json, os
from dotenv import load_dotenv
import feedparser

app = Flask(__name__)
load_dotenv()

# Env Variables
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
INSTAMOJO_API_KEY = os.getenv("INSTAMOJO_API_KEY")
INSTAMOJO_AUTH_TOKEN = os.getenv("INSTAMOJO_AUTH_TOKEN")
INSTAMOJO_WEBHOOK_SECRET = os.getenv("INSTAMOJO_WEBHOOK_SECRET")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")

users_file = "users.json"

# ---- User Handling ----
def load_users():
    if not os.path.exists(users_file):
        return {}
    with open(users_file, "r") as f:
        return json.load(f)

def save_users(users):
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

# ---- Payment ----
def create_payment_link(phone):
    url = "https://www.instamojo.com/api/1.1/payment-requests/"
    payload = {
        "purpose": "Azad AI Bot Subscription",
        "amount": "10",
        "phone": phone,
        "buyer_name": phone,
        "redirect_url": "https://example.com/thankyou",
        "send_email": False,
        "allow_repeated_payments": False
    }
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN
    }
    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["payment_request"]["longurl"]
    else:
        return "Payment link error"

# ---- News Fetch ----
def get_news():
    try:
        hindi = feedparser.parse("https://www.aajtak.in/rssfeed/cms/national-news-109.xml")
        fb = feedparser.parse("https://www.facebook.com/feeds/page.php?format=rss20&id=100064790306684")

        top_hindi = hindi.entries[0].title if hindi.entries else "No news found"
        top_fb = fb.entries[0].title if fb.entries else "No FB news found"
        roman = top_hindi.encode("ascii", "ignore").decode()

        return f"*AajTak (Hindi):* {top_hindi}\n\n*Roman English:* {roman}\n\n*FB News:* {top_fb}"
    except Exception as e:
        return f"Error fetching news: {e}"

# ---- WhatsApp Webhook ----
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form
    sender = data.get("From", "")
    msg = data.get("Body", "").strip().lower()
    phone = sender.split(":")[-1]

    users = load_users()
    if phone not in users:
        users[phone] = {"subscribed": False}
        save_users(users)

    resp = MessagingResponse()
    reply = ""

    if "subscribe" in msg:
        link = create_payment_link(phone)
        reply = f"Click to pay & subscribe: {link}"

    elif "news" in msg:
        reply = get_news()

    elif "qibla" in msg:
        reply = "To find Qibla direction, enable location & visit:\nhttps://qiblafinder.withgoogle.com"

    elif "location" in msg:
        reply = "Send your live location to receive Qibla direction."

    elif "help" in msg:
        reply = "Commands:\n- news\n- subscribe\n- qibla\n- location\n- help"

    else:
        reply = "Send 'news', 'subscribe', or 'qibla'."

    resp.message(reply)
    return str(resp)

# ---- Run ----
if __name__ == "__main__":
    app.run(debug=True)