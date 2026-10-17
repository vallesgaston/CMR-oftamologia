from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..db import get_db, guardar, obtener_o_404
from ..models import Consulta, Paciente, PedidoAnteojos, Turno
from ..schemas import HistorialOut, PacienteCreate, PacienteOut, PacienteUpdate
from ..services.telefono import normalizar

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"], dependencies=[Depends(requiere_admin)])

DNI_DUPLICADO = "Ya existe un paciente con ese DNI"


@router.get("", response_model=list[PacienteOut])
def listar(q: str = "", db: Session = Depends(get_db)):
    stmt = select(Paciente).order_by(Paciente.apellido.asc().nulls_last(), Paciente.nombre).limit(100)
    if q.strip():
        like = f"%{q.strip()}%"
        nombre_completo = Paciente.nombre + " " + func.coalesce(Paciente.apellido, "")
        stmt = stmt.where(or_(
            nombre_completo.ilike(like),
            Paciente.apellido.ilike(like),
            Paciente.dni.ilike(like),
            Paciente.telefono.ilike(like),
        ))
    return db.scalars(stmt).all()


@router.post("", response_model=PacienteOut, status_code=201)
def crear(data: PacienteCreate, db: Session = Depends(get_db)):
    pac = Paciente(**data.model_dump())
    pac.telefono = normalizar(pac.telefono)
    db.add(pac)
    guardar(db, DNI_DUPLICADO)
    return pac


@router.get("/{paciente_id}", response_model=PacienteOut)
def obtener(paciente_id: int, db: Session = Depends(get_db)):
    return obtener_o_404(db, Paciente, paciente_id)


@router.patch("/{paciente_id}", response_model=PacienteOut)
def actualizar(paciente_id: int, data: PacienteUpdate, db: Session = Depends(get_db)):
    pac = obtener_o_404(db, Paciente, paciente_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(pac, campo, valor)
    pac.telefono = normalizar(pac.telefono)
    guardar(db, DNI_DUPLICADO)
    return pac


@router.delete("/{paciente_id}", status_code=204)
def eliminar(paciente_id: int, db: Session = Depends(get_db)):
    db.delete(obtener_o_404(db, Paciente, paciente_id))
    db.commit()


@router.get("/{paciente_id}/historial", response_model=HistorialOut)
def historial(paciente_id: int, db: Session = Depends(get_db)):
    pac = obtener_o_404(db, Paciente, paciente_id)
    return HistorialOut(
        paciente=pac,
        consultas=db.scalars(select(Consulta).where(Consulta.paciente_id == pac.id)
                             .order_by(Consulta.fecha.desc())).all(),
        pedidos=db.scalars(select(PedidoAnteojos).where(PedidoAnteojos.paciente_id == pac.id)
                           .order_by(PedidoAnteojos.fecha_pedido.desc())).unique().all(),
        turnos=db.scalars(select(Turno).where(Turno.paciente_id == pac.id)
                          .order_by(Turno.fecha_hora.desc())).unique().all(),
    )
