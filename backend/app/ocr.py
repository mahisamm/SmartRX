"""OCR + extraction pipeline (eng review locked decision).

    image ──> Tesseract OCR (raw text + mean word-confidence)
          └─> Gemini vision analyze (primary structured extractor)
    Tesseract runs alongside as a cross-check / printed-text signal.
    Result is validated by schemas.ExtractionResult before it reaches the DB.

Day 1: Tesseract call is guarded (optional dependency) and Gemini is stubbed, so the
endpoint round-trips. Day 3: enable both for real.
"""
from .config import get_settings
from .schemas import ExtractionResult
from . import gemini_client

settings = get_settings()


def _tesseract_confidence(image_bytes: bytes) -> float | None:
    """Mean word-confidence from Tesseract, or None if unavailable.

    Used only as a cross-check signal (eng review A2 threshold lives in config).
    """
    try:
        import io
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data["conf"] if c not in ("-1", -1)]
        return sum(confs) / len(confs) if confs else None
    except Exception:
        return None  # Tesseract not installed / failed — Gemini vision still runs


def extract_prescription(image_bytes: bytes, mime: str) -> ExtractionResult:
    """Run the two-engine pipeline and return a validated ExtractionResult."""
    tess_conf = _tesseract_confidence(image_bytes)

    raw = gemini_client.vision_extract(image_bytes, mime)

    # Decide engine label + confidence for the report/UI.
    if tess_conf is not None and tess_conf >= settings.tesseract_confidence_floor:
        engine = "tesseract+gemini"
        confidence = round(tess_conf / 100, 2)
    else:
        engine = "gemini_vision"
        confidence = raw.get("confidence", 0.85)

    # Validate the raw dict against the schema (guards malformed LLM JSON).
    return ExtractionResult(
        engine=engine,
        confidence=confidence,
        doctor_name=raw.get("doctor_name"),
        hospital=raw.get("hospital"),
        date=raw.get("date"),
        medicines=raw.get("medicines", []),
    )
