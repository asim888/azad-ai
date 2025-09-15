```python
import os
import json
import feedparser
from unidecode import unidecode
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from datetime import datetime, timedelta

app = Flask(name)

Load environment variables
NEWS_FEED_URL = os.getenv("NEWS_FEED_URL", "https://news.google.com/rss")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
USER_LOGS_FILE = "user.json"

Load user data
try:
    with open(USER_LOGS_FILE, "r") as f:
        user_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}

def save_user_data():
    with open(USER_LOGS_FILE, "w") as f:
    json.dump(user_data, f, indent=2)

def get_news():
    feed = feedparser.parse(NEWS_FEED_URL)
    headlines = [entry.title for entry in feed.entries[:5]]
    news = "🗞️ Top News Headlines:\n\n"
    for h in headlines:
        roman = unidecode(h)
        news += f"• {h}\n  ({roman})\n\n"
    return news.strip()

def get_facebook_feed():
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        return "⚠️ Facebook feed not configured."
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/posts?access_token={FB_ACCESS_TOKEN}"
    try:
        res = requests.get(url).json()
        posts = res.get("data", [])[:3]
        if not posts:
            return "No recent Facebook posts found."
        feed = "📘 Facebook Updates:\n\n"
        for post in posts:
            message = post.get("message", "")
            if message:
                feed += f"• {message[:100]}...\n\n"
        return feed.strip()
    except Exception:
        return "❌ Failed to fetch Facebook posts."

def record_bp(user_id, systolic, diastolic):
    now = datetime.now().isoformat()
    user_data.setdefault(user_id, {})
    user_data[user_id]["bp"] = {
        "systolic": systolic,
        "diastolic": diastolic,
        "timestamp": now
    }
    save_user_data()
        return str(response)

    if "news" in msg:
        response.message(get_news())
    elif "facebook" in msg:
        response.message(get_facebook_feed())
    elif msg.startswith("bp "):
        parts = msg.split()
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            response.message(record_bp(user_id, int(parts[1]), int(parts[2])))
        else:
            response.message("❗ Send BP like this: bp 120 80")
    elif "help" in msg:
        help_text = (
            "🤖 Azad AI Help Menu:\n\n"
            "• news – Latest news headlines\n"
            "• facebook – FB page posts\n"
            "• bp 120 80 – Log BP reading\n"
            "• subscribe – Start ₹599 monthly plan\n"
        )
        response.message(help_text)
    else:
        response.message("❓ Unknown command. Type help to see options.")
    return str(response)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    user_id = request.form.get("From", "")
    msg = request.form.get("Body", "")
    media_urls = [request.form.get(f"MediaUrl{i}") for i in range(int(request.form.get("NumMedia", 0)))]
    return handle_message(user_id, msg, media_urls)

def send_daily_news():
    print("🗞️ Scheduled news broadcast — integrate messaging logic here.")
    return f"✅ BP recorded: {systolic}/{diastolic} mmHg at {now[:16].replace('T', ' ')}"

def check_subscription(user_id):
    user = user_data.get(user_id, {})
    until = user.get("subscribed_until")
    if until:
        try:
            return datetime.fromisoformat(until) > datetime.now()
        except:
            return False
    return False

def activate_subscription(user_id):
    subscribed_until = (datetime.now() + timedelta(days=30)).isoformat()
    user_data.setdefault(user_id, {})
    user_data[user_id]["subscribed_until"] = subscribed_until
    save_user_data()
    return f"🎉 Subscription active till {subscribed_until[:10]}."

def handle_message(user_id, msg, media_urls=None):
    msg = msg.lower().strip()
    response = MessagingResponse()
    subscribed = check_subscription(user_id)

    if "subscribe" in msg:
        response.message(
            "💳 To subscribe, send ₹599 to GPay: 7508556789.\n"
            "Then reply with the screenshot or write 'paid'."
        )
        return str(response)

    if media_urls or "paid" in msg:
        response.message("🧾 Payment received. " + activate_subscription(user_id))
        return str(response)

    if not subscribed:
        response.message("🔒 You're not subscribed. Type subscribe to begin.")
        if name == "main":
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_news, "cron", hour=9, minute=0)
    scheduler.start()
    app.run(debug=True)
