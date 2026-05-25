"""
twilio_voice.py — Twilio voice webhook endpoints

Handles the full lifecycle of an inbound call:

  1. POST /twilio/voice/incoming  — Call arrives, play greeting, start gather
  2. POST /twilio/voice/gather    — Speech transcribed, process with AI, respond
  3. POST /twilio/voice/status    — Call ended, clean up session
  4. POST /twilio/voice/fallback  — No-answer fallback: AI takes over missed calls

Twilio sends form-encoded data (not JSON), so we use Form() parameters.
Each endpoint returns TwiML (XML) — Twilio parses this to control the call.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Form, Request
from fastapi.responses import Response

from config.settings         import settings
from models.call_session     import CallSession, Message
from models.job              import JobPayload
from services.call_state     import create_session, get_session, update_session, delete_session
from services.ai_agent       import process_speech
from services.job_creator    import create_job
from services.dispatcher_notify import notify_job_created


router = APIRouter(prefix="/twilio/voice", tags=["twilio"])

VOICE = "Polly.Joanna-Neural"


# ── Business hours check ───────────────────────────────────────────────────

def is_business_hours() -> bool:
    tz    = ZoneInfo(settings.business_timezone)
    now   = datetime.now(tz)
    today = now.strftime("%a")  # "Mon", "Tue", etc.

    days = [d.strip() for d in settings.business_days.split(",")]
    if today not in days:
        return False

    start_h, start_m = map(int, settings.business_hours_start.split(":"))
    end_h,   end_m   = map(int, settings.business_hours_end.split(":"))
    now_minutes   = now.hour * 60 + now.minute
    start_minutes = start_h  * 60 + start_m
    end_minutes   = end_h    * 60 + end_m

    return start_minutes <= now_minutes < end_minutes


# ── TwiML helpers ──────────────────────────────────────────────────────────

def _xml_response(twiml: str) -> Response:
    return Response(content=twiml, media_type="application/xml")


def _gather_twiml(say_text: str, action_url: str, hints: str = "") -> str:
    hints_attr = f'hints="{hints}"' if hints else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{action_url}" method="POST"
          speechTimeout="auto" language="en-US" {hints_attr}>
    <Say voice="{VOICE}">{say_text}</Say>
  </Gather>
  <Say voice="{VOICE}">I'm sorry I couldn't hear you. Please don't hesitate to call us back anytime — we're always here to help. Have a wonderful day, and stay comfortable!</Say>
</Response>"""


def _say_and_hangup(text: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="{VOICE}">{text}</Say>
  <Hangup/>
</Response>"""


def _base_url(request: Request) -> str:
    return settings.public_url.rstrip("/") if settings.public_url else str(request.base_url).rstrip("/")


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/incoming")
async def incoming_call(
    request:  Request,
    CallSid:  str = Form(...),
    From:     str = Form(...),
):
    # During business hours, try the receptionist first
    if is_business_hours() and settings.receptionist_phone:
        missed_url = f"{_base_url(request)}/twilio/voice/missed"
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial action="{missed_url}" method="POST" timeout="12">
    <Number>{settings.receptionist_phone}</Number>
  </Dial>
</Response>"""
        return _xml_response(twiml)

    # Outside business hours or no receptionist configured — AI answers directly
    caller_phone = From.replace(" ", "")
    create_session(call_sid=CallSid, caller_phone=caller_phone)

    greeting = (
        f"Thank you for calling {settings.business_name}. "
        "I'm your AI assistant, and I'm here to help you. "
        "Whatever you're dealing with, we'll make sure it gets taken care of. "
        "How can I help you today?"
    )

    gather_url = f"{_base_url(request)}/twilio/voice/gather"
    return _xml_response(_gather_twiml(greeting, gather_url))


@router.post("/missed")
async def missed_call(
    request:        Request,
    CallSid:        str = Form(...),
    From:           str = Form(...),
    DialCallStatus: str = Form(default=""),
):
    """
    Twilio POSTs here after a <Dial> completes.
    completed = receptionist answered; no-answer/busy/failed = AI takes over.
    """
    if DialCallStatus in ("completed", "canceled"):
        return _xml_response('<?xml version="1.0" encoding="UTF-8"?><Response/>')

    caller_phone = From.replace(" ", "")
    create_session(call_sid=CallSid, caller_phone=caller_phone)

    greeting = (
        f"Hi there — I apologize, our team wasn't able to pick up just now. "
        f"I'm the AI assistant for {settings.business_name}, and I can absolutely help you right now. "
        f"Please don't hang up — what can I help you with today?"
    )

    gather_url = f"{_base_url(request)}/twilio/voice/gather"
    return _xml_response(_gather_twiml(greeting, gather_url))


@router.post("/fallback")
async def fallback_call(
    request:  Request,
    CallSid:  str = Form(...),
    From:     str = Form(...),
):
    """
    Called by Twilio when the primary handler fails or nobody answers.
    The AI steps in so no call goes unanswered.
    """
    caller_phone = From.replace(" ", "")
    create_session(call_sid=CallSid, caller_phone=caller_phone)

    greeting = (
        "Hi there — I'm sorry we missed you. "
        "I'm the AI assistant for ABC HVAC Services, and I can still help you right now. "
        "Please don't hang up — what can I help you with today?"
    )

    gather_url = f"{_base_url(request)}/twilio/voice/gather"
    return _xml_response(_gather_twiml(greeting, gather_url))


@router.post("/gather")
async def gather_speech(
    request:      Request,
    CallSid:      str = Form(...),
    SpeechResult: str = Form(default=""),
):
    gather_url = f"{_base_url(request)}/twilio/voice/gather"

    session = get_session(CallSid)
    if not session:
        session = CallSession(call_sid=CallSid, caller_phone="unknown")

    speech = SpeechResult.strip()

    if not speech:
        session.attempts += 1
        update_session(session)
        if session.attempts >= 3:
            return _xml_response(_say_and_hangup(
                "I'm so sorry I'm having trouble hearing you clearly. "
                "Please give us a call back when you're ready — we truly want to help. "
                "Take care, and we hope to speak with you soon!"
            ))
        return _xml_response(_gather_twiml(
            "I'm sorry, I didn't quite catch that. Could you please say that again? I'm here and listening.",
            gather_url
        ))

    session.conversation_history.append(Message(role="user", content=speech))

    ai_response = process_speech(session, speech)

    if ai_response.caller_name:   session.caller_name  = ai_response.caller_name
    if ai_response.service_type:  session.service_type = ai_response.service_type
    if ai_response.address:       session.address      = ai_response.address
    if ai_response.city:          session.city         = ai_response.city
    if ai_response.description:   session.description  = ai_response.description
    if ai_response.scheduled_at:  session.scheduled_at = ai_response.scheduled_at
    if ai_response.is_emergency:  session.is_emergency = True

    session.conversation_history.append(
        Message(role="assistant", content=ai_response.speech_to_say)
    )

    session.state    = ai_response.next_state
    session.attempts = 0
    update_session(session)

    if session.state == "BOOKING":
        try:
            payload = JobPayload(
                caller_name=session.caller_name,
                caller_phone=session.caller_phone,
                service_type=session.service_type,
                description=session.description,
                address=session.address,
                city=session.city,
                priority="emergency" if session.is_emergency else "normal",
                call_sid=session.call_sid,
                scheduled_at=session.scheduled_at,
            )
            job = create_job(payload)
            await notify_job_created(job)
        except Exception as e:
            print(f"[gather] Failed to create job for call {CallSid}: {e}")

        # Advance to ANYTHING_ELSE so the AI can ask "anything else?" before farewell
        session.state = ai_response.next_state if ai_response.next_state != "BOOKING" else "ANYTHING_ELSE"
        update_session(session)

    if session.state == "FAREWELL":
        return _xml_response(_say_and_hangup(ai_response.speech_to_say))

    return _xml_response(_gather_twiml(ai_response.speech_to_say, gather_url))


@router.post("/status")
async def call_status(
    CallSid:    str = Form(...),
    CallStatus: str = Form(default=""),
):
    print(f"[twilio] Call {CallSid} ended with status: {CallStatus}")
    delete_session(CallSid)
    return _xml_response("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response/>")
