from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import json
import os
import requests
from dotenv import load_dotenv
from groq import Groq
from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load business config
with open("business_config.json", "r") as f:
    business_info = json.load(f)

# ----------------------------
# In-memory booking state
# ----------------------------
pending_bookings = {}

# ----------------------------
# Constants for WhatsApp
# ----------------------------
VERIFY_TOKEN = "make_webhook_verify"   # MUST match Meta verify token
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/bnris781v64i4icxwfdk39m1x9lw1wqn"

# ----------------------------
# Request model
# ----------------------------
class Message(BaseModel):
    session_id: str
    text: str


# =========================================================
# CHAT ENDPOINT (UNCHANGED LOGIC)
# =========================================================
@app.post("/chat")
def chat(msg: Message):
    session_id = msg.session_id
    user_text = msg.text.lower()

    # Step 1: If user is confirming an existing booking
    if session_id in pending_bookings and user_text in ["yes", "haan", "confirm", "ok", "yeah"]:
        booking = pending_bookings.pop(session_id)

        booking_id = f"SALON-{hash(session_id) % 10000}"

        return {
            "intent": "booking_confirmed",
            "booking_id": booking_id,
            "details": booking,
            "reply": f"✅ Booking confirmed bro!\nRef ID: {booking_id}\nSee you {booking['date']} {booking['time']} 👍"
        }

    # Step 2: Otherwise, ask LLM to understand intent
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(business_info=business_info)
            },
            {
                "role": "user",
                "content": msg.text
            }
        ],
        temperature=0.2
    )

    raw_output = completion.choices[0].message.content
    data = json.loads(raw_output)

    # Step 3: If booking request → store & ask for confirmation
    if data["intent"] == "booking_request":
        pending_bookings[session_id] = {
            "service": data["service"],
            "date": data["date"],
            "time": data["time"]
        }

        return {
            "intent": "booking_pending",
            "reply": f"Yes bro 👍 {data['service']} is available {data['date']} {data['time']}.\nShall I confirm the booking?"
        }

    # Step 4: All other intents → pass through
    return data


# =========================================================
# WHATSAPP WEBHOOK — VERIFICATION (GET)
# =========================================================
@app.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge"))

    return PlainTextResponse("Verification failed", status_code=403)


# =========================================================
# WHATSAPP WEBHOOK — INCOMING MESSAGES (POST)
# =========================================================

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(payload: dict):
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        message = value["messages"][0]

        clean_payload = {
            "from": message["from"],
            "text": message["text"]["body"]
        }

        requests.post(MAKE_WEBHOOK_URL, json=clean_payload)

    except Exception as e:
        print("Webhook parse error:", e)

    return {"status": "ok"}

