# WhatsApp AI Receptionist (Phase 1)

This is Phase 1 of an AI-powered virtual receptionist designed for small Indian businesses.

## What it does
- Accepts customer messages (English + local slang)
- Identifies intent (booking, service query, business info)
- Extracts structured data (date, time, service)
- Responds like a local staff member
- Returns clean JSON for automation systems

## Tech Stack
- FastAPI (backend)
- Groq LLM (Llama 3.1)
- Python
- REST API
- Prompt-based intent extraction

## Example Input
Bro tomorrow evening haircut slot free aa?

## Example Output
```json
{
  "intent": "booking_request",
  "service": "Haircut",
  "date": "tomorrow",
  "time": "evening",
  "reply": "Yes bro, evening slot available hai 👍 Shall I book it?"
}
```

## Status
- Phase 1 complete.
- Next phases will include booking confirmation, WhatsApp integration, and voice support.