"""Zählerstand-OCR aus Fotos – mit austauschbaren Backends.

Reihenfolge der Erkennung:

1. **Claude Vision** – wenn ``ANTHROPIC_API_KEY`` gesetzt ist (beste Qualität
   für Sieben-Segment- und mechanische Rollenzählwerke).
2. **Tesseract** – wenn ``tesseract`` installiert und ``pytesseract`` verfügbar.
3. **Kein Backend** – die App fällt auf manuelle Eingabe zurück; das Foto
   wird trotzdem als Nachweis gespeichert.

Das Ergebnis ist immer ein :class:`OcrResult`; ``value`` kann ``None`` sein,
dann bestätigt/ergänzt der Nutzer den Wert von Hand.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OcrResult:
    value: float | None      # erkannter Zählerstand
    raw_text: str            # Rohausgabe des Backends
    backend: str             # "claude" | "tesseract" | "none"
    note: str = ""


def available_backends() -> list[str]:
    backends: list[str] = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        backends.append("claude")
    if shutil.which("tesseract"):
        try:
            import pytesseract  # noqa: F401
            backends.append("tesseract")
        except Exception:
            pass
    return backends


# ---------------------------------------------------------------------------
# Zahl-Extraktion aus Rohtext
# ---------------------------------------------------------------------------

def parse_number(text: str) -> float | None:
    """Extrahiert den plausibelsten Zählerstand aus einem OCR-Text.

    Akzeptiert deutsche (12.345,67) und englische (12345.67) Schreibweise
    und wählt die längste zusammenhängende Ziffernfolge.
    """
    if not text:
        return None
    kandidaten = re.findall(r"\d[\d.\s,]*\d|\d", text)
    if not kandidaten:
        return None
    kandidaten.sort(key=lambda c: sum(ch.isdigit() for ch in c), reverse=True)
    roh = kandidaten[0].replace(" ", "")

    # Dezimaltrenner bestimmen: das letzte Vorkommen von ',' oder '.'.
    if "," in roh and "." in roh:
        dezimal = "," if roh.rfind(",") > roh.rfind(".") else "."
    elif "," in roh:
        dezimal = ","
    else:
        dezimal = "."
    tausender = "." if dezimal == "," else ","
    roh = roh.replace(tausender, "").replace(dezimal, ".")
    try:
        return float(roh)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def _read_tesseract(image_path: Path) -> OcrResult:
    import pytesseract
    from PIL import Image

    # Zeichensatz auf Ziffern und Trenner beschränken -> weniger Fehltreffer.
    cfg = "--psm 6 -c tessedit_char_whitelist=0123456789.,"
    text = pytesseract.image_to_string(Image.open(image_path), config=cfg)
    return OcrResult(parse_number(text), text.strip(), "tesseract")


_CLAUDE_MODEL = "claude-opus-4-8"
_CLAUDE_URL = "https://api.anthropic.com/v1/messages"


_PROMPT_METER = ("Lies den Zählerstand vom Foto ab. Antworte NUR mit der "
                 "Zahl (mit Nachkommastellen, ohne Einheit, ohne Text). "
                 "Wenn nicht erkennbar, antworte 'unbekannt'.")

_PROMPT_AMOUNT = ("Dies ist eine Rechnung. Nenne den zu zahlenden Gesamtbetrag "
                  "in Euro. Antworte NUR mit der Zahl (Format 1234.56, ohne "
                  "Währungszeichen, ohne Text). Wenn nicht erkennbar, antworte "
                  "'unbekannt'.")


def _read_claude(image_path: Path, prompt: str) -> OcrResult:
    key = os.environ["ANTHROPIC_API_KEY"]
    data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    suffix = Path(image_path).suffix.lower().lstrip(".")
    media = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix or 'png'}"

    payload = {
        "model": _CLAUDE_MODEL,
        "max_tokens": 64,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media, "data": data}},
                {"type": "text", "text": prompt},
            ],
        }],
    }
    req = urllib.request.Request(
        _CLAUDE_URL, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json",
                 "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    text = "".join(b.get("text", "") for b in body.get("content", [])).strip()
    return OcrResult(parse_number(text), text, "claude")


def _read(image_path: str | Path, prompt: str, prefer: str | None = None) -> OcrResult:
    """Gemeinsamer Erkennungspfad für Zählerstände und Rechnungsbeträge."""
    path = Path(image_path)
    backends = available_backends()
    if prefer and prefer in backends:
        backends = [prefer]

    for backend in backends:
        try:
            if backend == "claude":
                return _read_claude(path, prompt)
            if backend == "tesseract":
                return _read_tesseract(path)
        except Exception as ex:  # Backend-Fehler -> manuell
            return OcrResult(None, "", backend, note=f"OCR-Fehler: {ex}")

    return OcrResult(None, "", "none",
                     note="Kein OCR-Backend verfügbar – bitte Wert manuell eingeben.")


def read_meter(image_path: str | Path, prefer: str | None = None) -> OcrResult:
    """Liest einen Zählerstand aus einem Foto mit dem besten verfügbaren Backend."""
    return _read(image_path, _PROMPT_METER, prefer)


def read_amount(image_path: str | Path, prefer: str | None = None) -> OcrResult:
    """Liest den Gesamtbetrag einer Rechnung aus einem Foto."""
    return _read(image_path, _PROMPT_AMOUNT, prefer)
