from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..config import settings
from ..db import get_db, guardar, obtener_o_404
from ..models import Paciente, Turno
from ..schemas import LimiteTurnos, TurnoCreate, TurnoOut, TurnoUpdate
from ..services.agenda import dia_completo, horarios_disponibles
from ..tiempo import hoy

router = APIRouter(prefix="/api/turnos", tags=["turnos"], dependencies=[Depends(requiere_admin)])

HORARIO_OCUPADO = "Ya hay un turno activo en ese horario"


def _validar_cupo(db: Session, dia: date, excluir_id: int | None = None) -> None:
    if dia_completo(db, dia, excluir_id):
        raise HTTPException(status_code=409,
                            detail=f"Se alcanzó el límite de {settings.max_turnos_dia} turnos para ese día")


@router.get("", response_model=list[TurnoOut])
def listar(desde: date | None = None, hasta: date | None = None, paciente_id: int | None = None,
           incluir_cancelados: bool = False, db: Session = Depends(get_db)):
    desde = desde or hoy()
    hasta = hasta or desde
    stmt = select(Turno).where(
        Turno.fecha_hora >= datetime.combine(desde, time.min),
        Turno.fecha_hora < datetime.combine(hasta + timedelta(days=1), time.min),
    ).order_by(Turno.fecha_hora)
    if paciente_id:
        stmt = stmt.where(Turno.paciente_id == paciente_id)
    if not incluir_cancelados:
        stmt = stmt.where(Turno.estado != "cancelado")
    return db.scalars(stmt).unique().all()


@router.get("/disponibles", response_model=list[datetime])
def disponibles(fecha: date, db: Session = Depends(get_db)):
    return horarios_disponibles(db, fecha)


@router.get("/limite", response_model=LimiteTurnos)
def ver_limite():
    return LimiteTurnos(max_turnos_dia=settings.max_turnos_dia)


@router.post("", response_model=TurnoOut, status_code=201)
def crear(data: TurnoCreate, db: Session = Depends(get_db)):
    obtener_o_404(db, Paciente, data.paciente_id)
    _validar_cupo(db, data.fecha_hora.date())
    datos = data.model_dump()
    datos["duracion_min"] = datos["duracion_min"] or settings.duracion_turno_min
    turno = Turno(**datos, origen="manual")
    db.add(turno)
    guardar(db, HORARIO_OCUPADO)
    db.refresh(turno)
    return turno


@router.patch("/{turno_id}", response_model=TurnoOut)
def actualizar(turno_id: int, data: TurnoUpdate, db: Session = Depends(get_db)):
    turno = obtener_o_404(db, Turno, turno_id)
    cambios = data.model_dump(exclude_unset=True)
    # Ocupa cupo si pasa a otro día o si se reactiva un turno cancelado
    nuevo_dia = cambios.get("fecha_hora", turno.fecha_hora).date()
    activo = cambios.get("estado", turno.estado) != "cancelado"
    if activo and (turno.estado == "cancelado" or nuevo_dia != turno.fecha_hora.date()):
        _validar_cupo(db, nuevo_dia, excluir_id=turno.id)
    for campo, valor in cambios.items():
        setattr(turno, campo, valor)
    guardar(db, HORARIO_OCUPADO)
    return turno
