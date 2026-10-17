"""Hora local del consultorio. Todas las fechas se guardan en hora local (sin zona)."""
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings


def ahora() -> datetime:
    return datetime.now(ZoneInfo(settings.tz)).replace(tzinfo=None, microsecond=0)


def hoy():
    return ahora().date()
