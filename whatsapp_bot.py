requirements.txt:

flask
twilio
openai
requests
python-dotenv
schedule
datetime
feedparser

 
main.py:

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
import requests
import schedule
import datetime
import feedparser
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# API Keys
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
incoming_msg = request.values.get('Body', '').strip()
sender = request.values.get('From', '')

# Handle greetings
if incoming_msg.lower() in ["hi", "hello", "hey"]:
reply_text = (
"👋 Hello! I'm your AI assistant.\n\n"
"Available commands:\n"
"📰 'news' - Local & national news\n"
"📱 'fb news' - Facebook feed\n"
"📅 'schedule [task] at [time]' - Add reminder\n"
"❓ Ask me anything else!"
)

# Fetch local and national news
elif "news" in incoming_msg.lower() and "fb" not in incoming_msg.lower():
try:
# RSS feeds for news sources
news_sources = [
"http://feeds.bbci.co.uk/news/rss.xml", # BBC News
"https://rss.cnn.com/rss/edition.rss" # CNN
]

reply_text = "📰 Latest News:\n\n"
for source in news_sources:
feed = feedparser.parse(source)
for i, entry in enumerate(feed.entries[:2]): # Top 2 from each
reply_text += f"• {entry.title}\n"
if i < len(feed.entries) - 1:
reply_text += "\n"
except Exception as e:
reply_text = "Sorry, couldn't fetch news right now."

# Facebook feed access
elif "fb news" in incoming_msg.lower():
page_id = os.getenv("FB_PAGE_ID")
access_token = os.getenv("FB_ACCESS_TOKEN")
fb_url = f"https://graph.facebook.com/v18.0/{page_id}/posts?access_token={access_token}&limit=3"

try:
res = requests.get(fb_url).json()
posts = res.get("data", [])
if posts:
reply_text = "📱 Latest Facebook Posts:\n\n"
for post in posts:
message = post.get("message", "[No text]")
reply_text += f"• {message[:100]}...\n\n"
else:
reply_text = "No recent Facebook posts found."
except Exception as e:
reply_text = "Sorry, couldn't access Facebook feed."

# Schedule management
elif "schedule" in incoming_msg.lower():
try:
# Parse schedule command: "schedule [task] at [time]"
parts = incoming_msg.lower().split(" at ")
if len(parts) == 2:
task = parts[0].replace("schedule ", "")
time_str = parts[1]

# Store in simple format (you can enhance with database)
reply_text = f"✅ Scheduled: '{task}' at {time_str}\n\nI'll remind you when the time comes!"
else:
reply_text = "Please use format: 'schedule [task] at [time]'\nExample: 'schedule meeting at 3pm'"
except Exception as e:
reply_text = "Sorry, couldn't process your schedule request."

# AI-powered responses for everything else
else:
try:
response = openai.ChatCompletion.create(
model="gpt-3.5-turbo",
messages=[
{"role": "system", "content": "You are an advanced AI assistant with capabilities to help with various tasks including news, scheduling, and general questions."},
{"role": "user", "content": incoming_msg}
]
)
reply_text = response.choices[0].message.content.strip()
except Exception as e:
reply_text = "Sorry, I'm having trouble processing that request."

# Send response
resp = MessagingResponse()
resp.message(reply_text)
return str(resp)

if __name__ == "__main__":
app.run(debug=True)
