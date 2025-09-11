

import os
import json
import requests
import tempfile
from flask import Flask, request
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g. whatsapp:+1234567890

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

openai.api_key = OPENAI_API_KEY
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

USERS_FILE = "users.json"
BP_LOGS_FILE = "bp_logs.json"


def load_json(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("{}")
    with open(file_path, "r") as f:
        return json.load(f)


def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def send_message(to, body):
    try:
        client.messages.create(
            from_=TWILIO_WHATSAPP,
            to=f"whatsapp:{to}",
            body=body
        )
    except Exception as e:
        print(f"❌ Failed to send message to {to}: {e}")


def get_gnews_headlines(limit=5):
    url = f"https://gnews.io/api/v4/top-headlines?token={GNEWS_API_KEY}&lang=en&max={limit}"
    res = requests.get(url).json()
    headlines = []
    if "articles" in res:
        for art in res["articles"]:
            headlines.append(f"- {art['title']}")
    return headlines or ["No news found."]


def get_facebook_feed(limit=3):
    url = f"https://graph.facebook.com/v15.0/{FACEBOOK_PAGE_ID}/posts"
    params = {
        "access_token": FACEBOOK_ACCESS_TOKEN,
        "limit": limit,
        "fields": "message,story,permalink_url"
    }
    res = requests.get(url, params=params).json()
    posts = []
    if "data" in res:
        for post in res["data"]:
            text = post.get("message") or post.get("story") or "No content"
            link = post.get("permalink_url", "")
            posts.append(f"{text}\n{link}")
    return posts or ["No Facebook posts found."]


def get_qibla_direction(lat, lon):
    url = f"http://api.aladhan.com/v1/qibla/{lat}/{lon}"
    res = requests.get(url).json()
    if res.get("code") == 200:
        return res["data"]["direction"]
    return None


def process_bp_log(user, reading):
    bp_logs = load_json(BP_LOGS_FILE)
    if user not in bp_logs:
        bp_logs[user] = []
    bp_logs[user].append(reading)
    save_json(BP_LOGS_FILE, bp_logs)


def gpt_answer(question):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()


@app.route("/webhook", methods=["POST"])
def webhook():
    from_number = request.values.get("From", "").replace("whatsapp:", "")
    incoming_msg = request.values.get("Body", "").strip()
    num_media = int(request.values.get("NumMedia", 0))
    reply = ""

    # Voice message handling
    if num_media > 0:
        media_type = request.values.get("MediaContentType0", "")
        media_url = request.values.get("MediaUrl0", "")
        if "audio" in media_type:
            audio_response = requests.get(media_url)
            with tempfile.NamedTemporaryFile(suffix=".ogg") as tmp:
                tmp.write(audio_response.content)
                tmp.flush()
                with open(tmp.name, "rb") as audio_file:
                    transcript = openai.Audio.transcribe("whisper-1", audio_file)
                    incoming_msg = transcript["text"].strip()

    msg_lower = incoming_msg.lower()

    users = load_json(USERS_FILE)

    # Handle commands
    if msg_lower in ["hi", "hello", "start"]:
        reply = ("Hello! I am Azad AI 🤖.\n"
                 "You can send commands like:\n"
                 "- news\n- facebook\n- bp <systolic>/<diastolic>\n"
                 "- qibla <lat> <lon>\n- navigate <from_lat> <from_lon> <to_lat> <to_lon>\n"
                 "- ask <your question>")
    elif msg_lower == "help":
        reply = ("Commands:\n"
                 "news - get latest news headlines\n"
                 "facebook - get Facebook page updates\n"
                 "bp 120/80 - log blood pressure\n"
                 "qibla <lat> <lon> - get Qibla direction\n"
                 "navigate <from_lat> <from_lon> <to_lat> <to_lon> - get Google Maps link\n"
                 "ask <question> - ask AI\n")
    elif msg_lower == "news":
        headlines = get_gnews_headlines()
        reply = "🗞️ Latest News:\n" + "\n".join(headlines)
    elif msg_lower == "facebook":
        posts = get_facebook_feed()
        reply = "📘 Facebook Updates:\n" + "\n\n".join(posts)
    elif msg_lower.startswith("bp "):
        try:
            bp_values = msg_lower.split(" ")[1].split("/")
            systolic = int(bp_values[0])
            diastolic = int(bp_values[1])
            reading = {"systolic": systolic, "diastolic": diastolic}
            process_bp_log(from_number, reading)
            reply = f"✅ Logged your BP reading: {systolic}/{diastolic}"
        except:
            reply = "❌ Invalid BP format. Use: bp systolic/diastolic (e.g., bp 120/80)"
    elif msg_lower.startswith("qibla "):
        parts = msg_lower.split()
        if len(parts) == 3:
            try:
                lat = float(parts[1])
                lon = float(parts[2])
                direction = get_qibla_direction(lat, lon)
                if direction:
                    reply = f"🕋 Qibla direction is approx {direction:.1f}° from North."
                else:
                    reply = "❌ Could not fetch Qibla direction."
            except:
                reply = "❌ Invalid coordinates."
        else:
            reply = "❌ Usage: qibla <latitude> <longitude>"
    elif msg_lower.startswith("navigate "):
        parts = msg_lower.split()
        if len(parts) == 5:
            try:
                from_lat = float(parts[1])
                from_lon = float(parts[2])
                to_lat = float(parts[3])
                to_lon = float(parts[4])
                maps_url = f"https://www.google.com/maps/dir/{from_lat},{from_lon}/{to_lat},{to_lon}"
                reply = f"🗺️ Navigation link: {maps_url}"
            except:
                reply = "❌ Invalid coordinates."
        else:
            reply = "❌ Usage: navigate <from_lat> <from_lon> <to_lat> <to_lon>"
    elif msg_lower.startswith("ask "):
        question = incoming_msg[4:].strip()
        if question:
            try:
                answer = gpt_answer(question)
                reply = answer
            except:
                reply = "❌ Sorry, I couldn't get an answer."
        else:
            reply = "❌ Please ask a question after 'ask'"
    else:
        reply = ("❓ Unknown command.\nSend 'help' for commands list.")

    send_message(from_number, reply)
    return "OK"


def send_daily_news():
    users = load_json(USERS_FILE)
    headlines = get_gnews_headlines()
    facebook_posts = get_facebook_feed()
    message = "🗞️ Daily News Update\n\n"
    message += "Latest Headlines:\n" + "\n".join(headlines) + "\n\n"
    message += "Facebook Updates:\n" + "\n\n".join(facebook_posts)

    for user, info in users.items():
        if info.get("plan") == "premium":
            try:
                send_message(user, message)
            except Exception as e:
                print(f"Failed to send daily news to {user}: {e}")


if __name__ == "__main
