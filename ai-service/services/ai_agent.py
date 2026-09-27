"""
ai_agent.py — Core AI reasoning via Anthropic Claude

Processes each caller speech turn and returns structured data:
  - What to say back to the caller (TwiML speech)
  - Extracted booking data (name, address, etc.)
  - Next conversation state
  - Emergency flag

The system prompt is loaded once and cached with business info substituted in.
FAQ context is injected per-turn when relevant.
"""

import json
import os
import re
from pathlib import Path

import anthropic

from config.settings   import settings
from models.call_session import CallSession, Message
from services.faq_handler import get_relevant_faqs, format_faqs_for_prompt
from services.tech_availability import get_available_techs


# ── System prompt ──────────────────────────────────────────────────────────

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"

def _build_system_prompt(faq_context: str = "") -> str:
    prompt = _PROMPT_PATH.read_text()
    prompt = prompt.replace("{business_name}",   settings.business_name)
    prompt = prompt.replace("{business_phone}",  settings.business_phone)
    prompt = prompt.replace("{service_area}",    settings.service_area)
    prompt = prompt.replace("{business_hours}",  settings.business_hours)
    prompt = prompt.replace("{emergency_hours}", settings.emergency_hours)
    if faq_context:
        prompt += f"\n\n{faq_context}"
    return prompt


# ── Anthropic client ───────────────────────────────────────────────────────

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ── Tool definitions ───────────────────────────────────────────────────────

_TOOLS = [
    {
        "name": "check_tech_availability",
        "description": (
            "Returns the list of active HVAC technicians and how many jobs each "
            "currently has. Use this when the caller asks who will come, who is "
            "available, whether any technicians are free, or how long until someone "
            "can arrive."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    }
]


def _handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Dispatches a tool_use request and returns the result as a JSON string."""
    if tool_name == "check_tech_availability":
        techs = get_available_techs()
        if not techs:
            return json.dumps({"techs": [], "message": "No active technicians found."})
        return json.dumps({"techs": techs})
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


# ── AI response model ──────────────────────────────────────────────────────

class AIResponse:
    def __init__(self, raw: dict):
        self.speech_to_say:   str  = raw.get("speech_to_say", "I'm sorry, could you repeat that?")
        self.next_state:      str  = raw.get("next_state", "COLLECTING_INFO")
        self.is_emergency:    bool = raw.get("is_emergency", False)
        extracted = raw.get("extracted_data", {}) or {}
        self.caller_name:     str | None = extracted.get("caller_name")
        self.service_type:    str | None = extracted.get("service_type")
        self.address:         str | None = extracted.get("address")
        self.city:            str | None = extracted.get("city")
        self.description:     str | None = extracted.get("description")
        self.scheduled_at:    str | None = extracted.get("scheduled_at")


# ── Main entry point ───────────────────────────────────────────────────────

def process_speech(session: CallSession, speech_input: str) -> AIResponse:
    """
    Sends the conversation history + new caller speech to Claude and
    returns a structured AIResponse with the next action.

    Injects FAQ context when the caller appears to be asking a question
    (detected by question words in their speech).
    """
    # Inject FAQ context if caller is asking a question
    faq_context = ""
    question_words = ["how much", "how many", "what", "when", "where", "why",
                      "do you", "can you", "is there", "price", "cost", "hours", "open"]
    if any(w in speech_input.lower() for w in question_words):
        faqs = get_relevant_faqs(speech_input)
        faq_context = format_faqs_for_prompt(faqs)

    system_prompt = _build_system_prompt(faq_context)

    # Build the messages list for Claude
    messages = [
        {"role": m.role, "content": m.content}
        for m in session.conversation_history
    ]
    messages.append({"role": "user", "content": speech_input})

    try:
        response = _client.messages.create(
            model=settings.ai_model,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
            tools=_TOOLS,
        )

        # Tool-use loop: Claude may call a tool before returning the final JSON.
        while response.stop_reason == "tool_use":
            tool_use_block = next(
                b for b in response.content if b.type == "tool_use"
            )
            tool_result = _handle_tool_call(tool_use_block.name, tool_use_block.input)
            print(f"[ai_agent] Tool called: {tool_use_block.name} → {tool_result[:120]}")

            # Append assistant turn (with tool_use) + tool result, then call again.
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_result,
                    }
                ],
            })
            response = _client.messages.create(
                model=settings.ai_model,
                max_tokens=512,
                system=system_prompt,
                messages=messages,
                tools=_TOOLS,
            )

        # Final response — parse JSON as before.
        raw_text = next(
            b.text for b in response.content if hasattr(b, "text")
        ).strip()

        # Strip markdown code blocks if Claude wraps the JSON (safety net)
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        data = json.loads(raw_text)
        return AIResponse(data)

    except json.JSONDecodeError as e:
        print(f"[ai_agent] JSON parse error: {e} | raw: {raw_text[:200]}")
        return _fallback_response(session.state)
    except Exception as e:
        print(f"[ai_agent] Claude API error: {e}")
        return _fallback_response(session.state)


def _fallback_response(current_state: str) -> AIResponse:
    """Returns a safe fallback when Claude fails or returns invalid JSON."""
    return AIResponse({
        "speech_to_say": "I'm sorry, I didn't catch that. Could you please repeat?",
        "next_state": current_state,
        "is_emergency": False,
        "extracted_data": {},
    })
