import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Paciente


def normalizar(telefono: str | None) -> str | None:
    """Deja solo dígitos: '+54 9 11 2233-4455' -> '5491122334455'."""
    if not telefono:
        return None
    digitos = re.sub(r"\D", "", telefono)
    return digitos or None


def pacientes_por_telefono(db: Session, telefono: str) -> list[Paciente]:
    """Compara los últimos 10 dígitos, así '5491122334455' (WhatsApp) coincide con '011 2233-4455'."""
    sufijo = (normalizar(telefono) or "")[-10:]
    if len(sufijo) < 8:
        return []
    return list(db.scalars(select(Paciente).where(func.right(Paciente.telefono, 10) == sufijo)))
