"""
Análisis de compatibilidad candidato–vacante vía API Anthropic (opcional).
Requiere ANTHROPIC_API_KEY en el entorno / .env.
"""
from __future__ import annotations

import os

import logging

_log = logging.getLogger("talentflow.ai")


def analizar_compatibilidad(
    titulo_vacante: str,
    descripcion_vacante: str,
    resumen_candidato: str,
    habilidades: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Devuelve (ok, texto). Si no hay clave o falla la llamada, ok=False y mensaje de error.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return (
            False,
            "Falta la clave de Anthropic. En el archivo .env de la raíz del proyecto define "
            "ANTHROPIC_API_KEY= (obtén la clave en https://console.anthropic.com/), guarda y "
            "reinicia el servidor (python app.py).",
        )

    try:
        from anthropic import Anthropic
    except ImportError:
        return False, "Paquete anthropic no instalado."

    skills_txt = ", ".join(habilidades or [])[:2000]
    prompt = f"""Eres un asistente de RRHH. Resume la compatibilidad entre el candidato y la vacante.
Vacante: {titulo_vacante}
Descripción vacante (extracto): {(descripcion_vacante or '')[:3500]}
Perfil / resumen candidato: {(resumen_candidato or '')[:3500]}
Habilidades candidato: {skills_txt}

Responde en español, máximo 12 líneas, con secciones: Fortalezas, Brechas, Recomendación (contratar / dudoso / no recomendado).
Sé concreto y profesional."""

    try:
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in msg.content:
            if hasattr(block, "text"):
                text += block.text
        return True, (text or "").strip()
    except Exception as exc:
        _log.warning("Anthropic match error: %s", exc)
        return False, f"No se pudo obtener análisis: {exc}"
