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

import asyncio
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


_HINTS = (
    "air conditioning, AC, A C unit, furnace, heating, cooling, heat pump, thermostat, "
    "ductwork, compressor, refrigerant, blower, filter, vents, no heat, no cool, no air, "
    "smoke, burning smell, gas leak, carbon monoxide, flooding, water leak, frozen pipes, "
    "not working, broken, stopped working, making noise, loud noise, repair, maintenance, "
    "installation, emergency, tune up, inspection, "
    "my name is, first name, last name, street, avenue, boulevard, drive, road, lane, court, "
    "apartment, suite, north, south, east, west, "
    "yes, no, yeah, nope, that's right, correct, that's all, nothing else, that's everything, "
    "anything else, goodbye, that's it"
)


def _gather_twiml(say_text: str, action_url: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" action="{action_url}" method="POST"
          speechTimeout="auto" speechModel="phone_call"
          enhanced="true" timeout="10" language="en-US"
          hints="{_HINTS}">
    <Say voice="{VOICE}">{say_text}</Say>
  </Gather>
  <Say voice="{VOICE}">I'm sorry I couldn't hear you. Please don't hesitate to call us back anytime — we're always here to help. Have a wonderful day!</Say>
</Response>"""


def _say_and_hangup(text: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="{VOICE}">{text}</Say>
  <Hangup/>
</Response>"""


def _base_url(request: Request) -> str:
    # Derive from the incoming request so every callback URL automatically
    # matches the URL Twilio used to reach us — works with any tunnel
    # without needing to keep PUBLIC_URL in sync.
    host   = request.headers.get("host") or request.url.netloc
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    return f"{scheme}://{host}"


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
        f"Hey there, thanks so much for calling {settings.business_name}! "
        "I'm here to help — whatever's going on, we'll get it sorted out for you. "
        "What can I help you with today?"
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
        f"Hi! Sorry we just missed you — our team is tied up at the moment. "
        f"I'm the AI assistant for {settings.business_name} and I can take care of you right now. "
        f"What's going on today?"
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


async def _book_job_background(payload: JobPayload, call_sid: str) -> None:
    try:
        job = await asyncio.to_thread(create_job, payload)
        await notify_job_created(job)
    except Exception as e:
        print(f"[gather] Background job creation failed for {call_sid}: {e}")


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

    # ── Silence / no speech detected ─────────────────────────────────────────
    if not speech:
        # After booking, silence = caller is done — say goodbye and hang up
        if session.state == "ANYTHING_ELSE":
            return _xml_response(_say_and_hangup(
                "You can always call us back anytime — take care, goodbye!"
            ))
        session.attempts += 1
        update_session(session)
        if session.attempts >= 3:
            return _xml_response(_say_and_hangup(
                "I'm having trouble hearing you — please give us a call back anytime. Take care!"
            ))
        # Repeat the last question the AI asked so the caller knows exactly
        # what to say — a generic "please repeat" loses context
        last_ai_line = next(
            (m.content for m in reversed(session.conversation_history) if m.role == "assistant"),
            None,
        )
        retry = (
            f"Sorry, I didn't catch that. {last_ai_line}"
            if last_ai_line
            else "Sorry, I didn't catch that — could you say that again?"
        )
        return _xml_response(_gather_twiml(retry, gather_url))

    # ── Post-booking "anything else?" — handle yes/no directly in code ───────
    _DONE = {"no", "nope", "nah", "nothing", "none", "that's all", "that's it",
             "no thank you", "no thanks", "all good", "i'm good", "im good",
             "goodbye", "bye", "good bye", "that's everything", "nothing else"}
    if session.state == "ANYTHING_ELSE" and any(w in speech.lower() for w in _DONE):
        return _xml_response(_say_and_hangup(
            "You can always call us back anytime — take care, goodbye!"
        ))

    # ── Normal AI turn ────────────────────────────────────────────────────────
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
        asyncio.create_task(_book_job_background(payload, CallSid))
        session.state = "ANYTHING_ELSE"
        update_session(session)

        # Play the booking confirmation then ask "anything else?" directly
        booking_speech = ai_response.speech_to_say
        return _xml_response(_gather_twiml(
            f"{booking_speech} Is there anything else I can help you with today?",
            gather_url
        ))

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
