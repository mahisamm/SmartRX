"""Single shared Gemini client wrapper (eng review: DRY — one client for vision + summary).

Two real calls go through here:
  - vision_extract(): image -> structured prescription JSON (validated downstream).
  - generate_summary(): a patient's medicine log -> a readable doctor-facing summary.

If GEMINI_API_KEY is unset the wrapper runs in **stub mode**: both functions return
canned data so the whole app boots and round-trips without a key. Set the key in .env
to go live.
"""
import json
import re
from typing import Optional

from .config import get_settings

settings = get_settings()

# Lazily created so the app boots without a GEMINI_API_KEY (stub mode).
_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            return None  # stub mode
        from google import genai  # imported lazily so stub mode needs no SDK install

        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _extract_json(text: str) -> dict:
    """Pull a JSON object out of a model response, tolerating ```json fences / prose."""
    if not text:
        return {}
    # Strip ```json ... ``` fences if present.
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    # Greedy first-brace-to-last-brace span survives nested objects/arrays.
    span = re.search(r"\{.*\}", text, re.DOTALL)
    candidate = span.group(0) if span else text
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return {}


_VISION_PROMPT = """You are a medical prescription reader. Read this prescription image and
return ONLY a JSON object (no prose, no markdown) with exactly these keys:
{
  "doctor_name": string or null,
  "hospital": string or null,
  "date": "YYYY-MM-DD" or null,
  "confidence": number between 0 and 1 (your confidence in the extraction),
  "medicines": [
    { "name": string, "dose": string or null, "frequency": string or null,
      "duration": string or null, "instructions": string or null }
  ]
}
If a field is unreadable, use null. Never invent medicines that are not on the image.
Return [] for medicines if none are legible."""


def vision_extract(image_bytes: bytes, mime: str) -> dict:
    """Send an image to Gemini vision, return a structured prescription dict.

    The dict matches schemas.ExtractionResult fields (minus engine, which the caller
    sets). In stub mode returns a fixed sample so the flow works without a key.
    """
    client = _get_client()
    if client is None:
        return _STUB_EXTRACTION

    from google.genai import types

    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            _VISION_PROMPT,
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    data = _extract_json(getattr(resp, "text", "") or "")
    # Normalize: guarantee the keys the caller reads exist.
    return {
        "doctor_name": data.get("doctor_name"),
        "hospital": data.get("hospital"),
        "date": data.get("date"),
        "confidence": data.get("confidence"),
        "medicines": data.get("medicines") or [],
    }


def generate_summary(name: str, prescriptions: list[dict]) -> str:
    """Generate a readable medical summary from a patient's prescriptions."""
    client = _get_client()
    if client is None:
        meds = [m["name"] for p in prescriptions for m in p.get("medicines", [])]
        return f"[stub summary] {name} has {len(meds)} medicine(s) on record: " + ", ".join(meds)

    prompt = (
        "You are a clinical assistant. Write a concise, factual summary (2-4 sentences) "
        f"for a doctor reviewing patient {name}. Base it ONLY on the prescription data "
        "below. Mention current medications with dose/frequency, the prescribing doctor "
        "and date where available, and flag if multiple prescriptions overlap. Do not "
        "give new medical advice or diagnoses.\n\n"
        f"Prescription data (JSON):\n{json.dumps(prescriptions, default=str)}"
    )
    resp = client.models.generate_content(model=settings.gemini_model, contents=prompt)
    return (getattr(resp, "text", "") or "").strip()


_STUB_EXTRACTION = {
    "doctor_name": "Dr. Mehta",
    "hospital": "City Clinic",
    "date": "2026-06-15",
    "confidence": 0.85,
    "medicines": [
        {"name": "Amoxicillin", "dose": "500mg", "frequency": "1-0-1",
         "duration": "5 days", "instructions": "after food"}
    ],
}
