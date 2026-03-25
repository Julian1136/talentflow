"""
Extracción básica de texto desde CV en PDF (sin garantía de precisión).
Revisión humana obligatoria antes de confiar en los datos sugeridos.
"""
from __future__ import annotations

import re
from typing import Any


def extract_text_from_pdf(path: str, max_pages: int = 8) -> str:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return ""

    try:
        return extract_text(path, max_pages=max_pages) or ""
    except Exception:
        return ""


def suggest_fields_from_text(text: str) -> dict[str, Any]:
    """Heurísticas simples sobre texto plano (español)."""
    text = text or ""
    out: dict[str, Any] = {"correos": [], "telefonos": [], "fragmento": text[:2000]}

    emails = re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        text,
    )
    out["correos"] = list(dict.fromkeys(emails))[:5]

    phones = re.findall(
        r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
        text,
    )
    out["telefonos"] = list(dict.fromkeys(phones))[:5]

    return out
