from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
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

class Message(BaseModel):
    text: str

@app.post("/chat")
def chat(msg: Message):
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

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        return {
            "intent": "unknown",
            "reply": "Sorry bro, little confusion aagaya 😅 Can you say that again?"
        }
