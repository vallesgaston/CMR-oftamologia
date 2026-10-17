from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..db import get_db, obtener_o_404
from ..models import Consulta, Paciente
from ..schemas import ConsultaCreate, ConsultaOut, ConsultaUpdate

router = APIRouter(prefix="/api/consultas", tags=["historia clínica"], dependencies=[Depends(requiere_admin)])


@router.get("", response_model=list[ConsultaOut])
def listar(paciente_id: int, db: Session = Depends(get_db)):
    return db.scalars(select(Consulta).where(Consulta.paciente_id == paciente_id)
                      .order_by(Consulta.fecha.desc())).all()


@router.post("", response_model=ConsultaOut, status_code=201)
def crear(data: ConsultaCreate, db: Session = Depends(get_db)):
    obtener_o_404(db, Paciente, data.paciente_id)
    datos = data.model_dump()
    if datos["fecha"] is None:
        del datos["fecha"]  # usa la hora actual
    consulta = Consulta(**datos)
    db.add(consulta)
    db.commit()
    return consulta


@router.patch("/{consulta_id}", response_model=ConsultaOut)
def actualizar(consulta_id: int, data: ConsultaUpdate, db: Session = Depends(get_db)):
    consulta = obtener_o_404(db, Consulta, consulta_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(consulta, campo, valor)
    db.commit()
    return consulta


@router.delete("/{consulta_id}", status_code=204)
def eliminar(consulta_id: int, db: Session = Depends(get_db)):
    db.delete(obtener_o_404(db, Consulta, consulta_id))
    db.commit()
