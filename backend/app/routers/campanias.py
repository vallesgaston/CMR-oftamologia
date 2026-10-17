from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..db import get_db, obtener_o_404
from ..models import Campania
from ..schemas import CampaniaBase, CampaniaOut, CampaniaUpdate
from ..tiempo import hoy

router = APIRouter(prefix="/api/campanias", tags=["campañas"], dependencies=[Depends(requiere_admin)])


@router.get("", response_model=list[CampaniaOut])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(Campania).order_by(Campania.fecha_inicio.desc())).all()


@router.post("", response_model=CampaniaOut, status_code=201)
def crear(data: CampaniaBase, db: Session = Depends(get_db)):
    datos = data.model_dump()
    datos["fecha_inicio"] = datos["fecha_inicio"] or hoy()
    campania = Campania(**datos)
    db.add(campania)
    db.commit()
    return campania


@router.patch("/{campania_id}", response_model=CampaniaOut)
def actualizar(campania_id: int, data: CampaniaUpdate, db: Session = Depends(get_db)):
    campania = obtener_o_404(db, Campania, campania_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(campania, campo, valor)
    db.commit()
    return campania


@router.delete("/{campania_id}", status_code=204)
def eliminar(campania_id: int, db: Session = Depends(get_db)):
    db.delete(obtener_o_404(db, Campania, campania_id))
    db.commit()
