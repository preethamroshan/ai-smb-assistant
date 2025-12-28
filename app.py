from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
from groq import Groq
from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()
pending_bookings = {}


# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# Load business config
with open("business_config.json", "r") as f:
    business_info = json.load(f)

class Message(BaseModel):
    session_id: str
    text: str

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
