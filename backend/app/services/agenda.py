from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Turno
from ..tiempo import ahora


def _franjas() -> list[tuple[time, time]]:
    franjas = []
    for franja in settings.franjas_horarias.split(","):
        inicio, fin = franja.strip().split("-")
        franjas.append((time.fromisoformat(inicio), time.fromisoformat(fin)))
    return franjas


def slots_del_dia(dia: date) -> list[datetime]:
    if dia.weekday() not in settings.dias_laborales_set:
        return []
    paso = timedelta(minutes=settings.duracion_turno_min)
    slots = []
    for inicio, fin in _franjas():
        actual, limite = datetime.combine(dia, inicio), datetime.combine(dia, fin)
        while actual + paso <= limite:
            slots.append(actual)
            actual += paso
    return slots


def turnos_del_dia(db: Session, dia: date, excluir_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(Turno).where(
        Turno.fecha_hora >= datetime.combine(dia, time.min),
        Turno.fecha_hora < datetime.combine(dia + timedelta(days=1), time.min),
        Turno.estado != "cancelado",
    )
    if excluir_id:
        stmt = stmt.where(Turno.id != excluir_id)
    return db.scalar(stmt)


def dia_completo(db: Session, dia: date, excluir_id: int | None = None) -> bool:
    limite = settings.max_turnos_dia
    return limite > 0 and turnos_del_dia(db, dia, excluir_id) >= limite


def horarios_disponibles(db: Session, dia: date) -> list[datetime]:
    slots = slots_del_dia(dia)
    if not slots or dia_completo(db, dia):
        return []
    ocupados = set(db.scalars(
        select(Turno.fecha_hora).where(
            Turno.fecha_hora >= datetime.combine(dia, time.min),
            Turno.fecha_hora < datetime.combine(dia + timedelta(days=1), time.min),
            Turno.estado != "cancelado",
        )
    ))
    minimo = ahora() + timedelta(hours=settings.anticipacion_min_horas)
    return [s for s in slots if s not in ocupados and s >= minimo]


def proximos_dias_disponibles(db: Session, cantidad: int, max_dias: int = 45) -> list[date]:
    inicio = ahora().date()
    dias = []
    for i in range(max_dias):
        dia = inicio + timedelta(days=i)
        if horarios_disponibles(db, dia):
            dias.append(dia)
            if len(dias) >= cantidad:
                break
    return dias
