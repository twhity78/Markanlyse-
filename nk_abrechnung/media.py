"""Bildkompression für Foto-Uploads (Zähler- und Belegfotos).

Handyfotos sind oft 3-8 MB groß. Da Fotos direkt in der Datenbank
gespeichert werden (damit beide Parteien sie jederzeit von überall sehen
können, auch nach einem Neustart der App), werden sie vor dem Speichern
verkleinert – wichtig für kostenlose Supabase/Postgres-Kontingente.
"""

from __future__ import annotations

import io


def compress_image(data: bytes, max_dim: int = 1600, quality: int = 85) -> tuple[bytes, str]:
    """Verkleinert ein Foto auf max. ``max_dim`` Pixel Kantenlänge (JPEG)."""
    from PIL import Image

    img = Image.open(io.BytesIO(data))
    img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue(), "image/jpeg"


def is_image(filename: str, content_type: str | None = None) -> bool:
    if content_type and content_type.startswith("image/"):
        return True
    return filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".heic"))
