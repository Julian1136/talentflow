"""
Puntaje 0–100 aproximado: coincidencia de habilidades del candidato con texto de requisitos.
"""
from __future__ import annotations

from models import Aplicacion


def calcular_score_aplicacion(aplicacion: Aplicacion) -> float | None:
    vac = aplicacion.vacante
    cand = aplicacion.candidato
    req = (vac.requisitos or "").lower() if vac else ""
    skills: list[str] = []
    hdv = getattr(cand, "hoja_de_vida", None)
    if hdv and hdv.habilidades:
        skills = [str(s).lower() for s in hdv.habilidades if s]

    if not req.strip():
        return None
    tokens = [
        t.strip(".,;:\n\r\t")
        for t in req.replace("/", " ").replace(",", " ").split()
        if len(t.strip()) > 3
    ]
    if not tokens:
        return None
    if not skills:
        return round(25.0, 2)

    hits = 0
    for tok in tokens:
        if any(tok in sk or sk in tok for sk in skills):
            hits += 1
    ratio = hits / len(tokens)
    base = 20.0 + 80.0 * ratio
    return round(min(100.0, max(0.0, base)), 2)
