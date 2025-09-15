import os
import json
import feedparser
from unidecode import unidecode
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from datetime import datetime, timedelta
from twilio.rest import Client
import re

# --- Configuration ---
app = Flask(__name__)

# Load environment variables (create .env file!)
NEWS_FEED_URL = os.getenv("NEWS_FEED_URL", "https://news.google.com/rss")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")  # e.g., +14155238886
USER_LOGS_FILE = "user.json"

# --- Helper: Normalize Phone Number ---
def normalize_phone(raw):
    """Convert WhatsApp number to standard +91... format"""
    if not raw:
        return None
    clean = re.sub(r'^whatsapp:', '', raw.strip())
    digits_only = re.sub(r'[^\d+]', '', clean)
    if digits_only.startswith('+91') and len(digits_only) == 13:
        return digits_only
    elif digits_only.startswith('91') and len(digits_only) == 12:
        return f'+{digits_only}'
    elif len(digits_only) == 10 and digits_only[0] in '6789':
        return f'+91{digits_only}'
    return None

# --- Load & Save User Data ---
try:
    with open(USER_LOGS_FILE, "r", encoding="utf-8") as f:
        user_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}

def save_user_data():
    with open(USER_LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

# --- News Feed Parser ---
def get_news():
    """Fetch top 5 news headlines from Google News RSS"""
    try:
        feed = feedparser.parse(NEWS_FEED_URL)
        if not feed.entries:
            return "❌ Unable to fetch news. Please check the RSS feed URL."
        
        headlines = [entry.title for entry in feed.entries[:5]]
        news = "📢 *Top News Headlines* (Google News)\n\n"
        for h in headlines:
            roman = unidecode(h)
            news += f"• {h}\n  _({roman})_\n\n"
        return news.strip()
    except Exception as e:
        return f"⚠️ Error fetching news: {str(e)}"

# --- Facebook Feed Fetcher ---
def get_facebook_feed():
    """Fetch last 3 posts from Facebook Page"""
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        return "❌ Facebook feed not configured. Ask admin to set FB_ACCESS_TOKEN and FB_PAGE_ID."

    url = f"https://graph.facebook.com/{FB_PAGE_ID}/posts?access_token={FB_ACCESS_TOKEN}&limit=3"
    try:
        res = requests.get(url, timeout=5).json()
        posts = res.get("data", [])
        if not posts:
            return "📌 No recent Facebook posts found."

        feed = "📘 *Facebook Updates*\n\n"
        for post in posts:
            message = post.get("message", "").strip()
            if message:
                # Truncate long messages
                if len(message) > 120:
                    message = message[:117] + "..."
                feed += f"• {message}\n\n"
        return feed.strip()
    except Exception as e:
        return f"⚠️ Failed to fetch Facebook posts: {str(e)}"

# --- Blood Pressure Logger ---
def record_bp(user_id, systolic, diastolic):
    """Record BP reading and save to JSON"""
    if not (70 <= systolic <= 250) or not (40 <= diastolic <= 150):
        return "❌ Invalid BP reading. Use format: `bp 120 80` (systolic/diastolic)"

    now = datetime.now().isoformat()
    user_data.setdefault(user_id, {})
    user_data[user_id]["bp"] = {
        "systolic": systolic,
        "diastolic": diastolic,
        "timestamp": now
    }
    save_user_data()
    timestamp_display = now[:16].replace('T', ' ')
    return f"✅ BP recorded: *{systolic}/{diastolic} mmHg* at {timestamp_display}"

# --- Subscription Checker ---
def check_subscription(user_id):
    """Check if user's subscription is active"""
    user = user_data.get(user_id, {})
    until = user.get("subscribed_until")
    if not until:
        return False
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except:
        return False

def activate_subscription(user_id):
    """Activate 30-day subscription"""
    subscribed_until = (datetime.now() + timedelta(days=30)).isoformat()
    user_data.setdefault(user_id, {})
    user_data[user_id]["subscribed_until"] = subscribed_until
    save_user_data()
    return f"🎉 Subscription activated! Valid till *{subscribed_until[:10]}*."

# --- Main Message Handler ---
def handle_message(user_id, msg, media_urls=None):
    msg = msg.lower().strip()
    response = MessagingResponse()

    # Check subscription status
    subscribed = check_subscription(user_id)

    # Handle subscription request
    if "subscribe" in msg:
        response.message(
            "💰 To subscribe to Azad AI Premium:\n"
            "Send ₹599 via GPay to: *7508556789*\n"
            "Then reply with ‘paid’ or send a screenshot of the payment.\n"
            "We’ll confirm within 5 minutes!"
        )
        return str(response)

    # Handle payment confirmation (text or media)
    if media_urls or "paid" in msg:
        response.message("✅ Payment received! " + activate_subscription(user_id))
        return str(response)

    # Block non-subscribers
    if not subscribed:
        response.message(
            "🔐 You're not subscribed yet.\n"
            "Type *subscribe* to start your ₹599/month plan.\n"
            "Get daily news, FB updates & BP tracking!"
        )
        return str(response)

    # Handle commands for subscribed users
    if "news" in msg:
        response.message(get_news())
    elif "facebook" in msg or "fb" in msg:
        response.message(get_facebook_feed())
    elif msg.startswith("bp "):
        parts = msg.split()
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            response.message(record_bp(user_id, int(parts[1]), int(parts[2])))
        else:
            response.message("❌ Use: *bp 120 80* (e.g., bp 130 85)")
    elif "help" in msg:
        help_text = (
            "*🤖 Azad AI - Your Personal Assistant*\n\n"
            "*Available Commands:* \n"
            "• *news* – Latest headlines from Google News\n"
            "• *facebook* or *fb* – Recent posts from our page\n"
            "• *bp 120 80* – Log your blood pressure\n"
            "• *subscribe* – Activate premium features (₹599/month)\n"
            "• *help* – Show this menu\n\n"
            "*Note:* All features require an active subscription."
        )
        response.message(help_text)
    else:
        response.message(
            "❓ I didn't understand that.\n"
            "Type *help* to see available commands."
        )

    return str(response)

# --- Daily News Scheduler ---
def send_daily_news():
    """Send curated news to all active subscribers every day at 9 AM"""
    if not TWILIO_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE:
        print("❌ Twilio credentials missing. Daily news disabled.")
        return

    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    news = get_news()
    print(f"📅 Preparing to send daily news to {len(user_data)} users...")

    for user_id in user_data.keys():
        if check_subscription(user_id):
            try:
                client.messages.create(
                    body=news,
                    from_=TWILIO_PHONE,
                    to=f"whatsapp:{user_id}"
                )
                print(f"✅ Sent daily news to {user_id}")
            except Exception as e:
                print(f"❌ Failed to send to {user_id}: {e}")

    print("📅 Scheduled news dispatch completed.")

# --- WhatsApp Webhook Endpoint ---
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    raw_phone = request.form.get("From")
    if not raw_phone:
        return "Missing user identifier", 400

    user_id = normalize_phone(raw_phone)
    if not user_id:
        return "Invalid phone number", 400

    msg = request.form.get("Body", "")
    media_urls = [
        request.form.get(f"MediaUrl{i}")
        for i in range(int(request.form.get("NumMedia", 0)))
    ]

    return handle_message(user_id, msg, media_urls)

# --- Health Check ---
@app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "healthy",
        "users": len(user_data),
        "twilio_ready": bool(TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE),
        "news_url": NEWS_FEED_URL,
        "fb_configured": bool(FB_ACCESS_TOKEN and FB_PAGE_ID)
    }

# --- Scheduler Startup ---
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_news, "cron", hour=9, minute=0, timezone="Asia/Kolkata")
    scheduler.start()

    try:
        print("🚀 Starting Azad AI WhatsApp Bot...")
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("🛑 Scheduler shut down gracefully.")
        @app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "healthy",
        "users": len(user_data),
        "twilio_ready": bool(TWILIO_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE),
        "fb_configured": bool(FB_ACCESS_TOKEN and FB_PAGE_ID)
    }