python
---- Requirements for Render ----
flask==2.3.2
twilio==8.10.0
openai==1.0.0
requests
python-dotenv
python
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(_name_)

Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
incoming_msg = request.values.get('Body', '').strip()
sender = request.values.get('From', '')

# Generate reply using OpenAI
response = openai.ChatCompletion.create(
model="gpt-3.5-turbo",
messages=[
{"role": "system", "content": "You are Azad AI, a helpful assistant."},
{"role": "user", "content": incoming_msg}
]
)
reply_text = response.choices[0].message.content.strip()

# Send reply back via Twilio
resp = MessagingResponse()
resp.message(reply_text)
return str(resp)

if _name_ == "_main_":
app.run(debug=True)


---



python
import requests


Add this block inside your /whatsapp route:

python
elif "fb news" in incoming_msg.lower():
page_id = os.getenv("FB_PAGE_ID")
access_token = os.getenv("FB_ACCESS_TOKEN")
fb_url = f"https://graph.facebook.com/v18.0/{page_id}/posts?access_token={access_token}&limit=3"

res = requests.get(fb_url).json()
posts = res.get("data", [])
if posts:
reply_text = "📰 Latest Facebook Posts:\n"
for post in posts:
message = post.get("message", "[No text]")
reply_text += f"- {message[:150]}...\n"
else:
reply_text = "No recent Facebook posts found."


---


```python
elif incoming_msg.lower() in ["hi", "hello", "hey"]:
reply_text = (
"👋 Hello! I’m Azad AI — your WhatsApp assistant.\n\n"
"You can ask me to:\n"
"- Get local news (type: news)\n"
"- Show Facebook posts (type: fb news)\n"
"- Ask anything (ChatGPT)\n"
)
```

bash
git add requirements.txt
git commit -m "Add missing requirements.txt"
git push origin main
