from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..config import settings
from ..db import get_db, obtener_o_404
from ..models import Paciente, PedidoAnteojos
from ..schemas import PedidoCreate, PedidoOut, PedidoUpdate
from ..services.mensajeria import enviar_whatsapp, registrar
from ..tiempo import hoy

router = APIRouter(prefix="/api/anteojos", tags=["anteojos"], dependencies=[Depends(requiere_admin)])


@router.get("", response_model=list[PedidoOut])
def listar(estado: str = "", paciente_id: int | None = None, db: Session = Depends(get_db)):
    """estado vacío = pedidos en curso; 'todos' = todos."""
    stmt = select(PedidoAnteojos).order_by(PedidoAnteojos.fecha_pedido.desc(), PedidoAnteojos.id.desc()).limit(300)
    if estado == "":
        stmt = stmt.where(PedidoAnteojos.estado.notin_(("entregado", "cancelado")))
    elif estado != "todos":
        stmt = stmt.where(PedidoAnteojos.estado == estado)
    if paciente_id:
        stmt = stmt.where(PedidoAnteojos.paciente_id == paciente_id)
    return db.scalars(stmt).unique().all()


@router.post("", response_model=PedidoOut, status_code=201)
def crear(data: PedidoCreate, db: Session = Depends(get_db)):
    obtener_o_404(db, Paciente, data.paciente_id)
    datos = data.model_dump()
    datos["fecha_pedido"] = datos["fecha_pedido"] or hoy()
    pedido = PedidoAnteojos(**datos)
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


@router.patch("/{pedido_id}", response_model=PedidoOut)
def actualizar(pedido_id: int, data: PedidoUpdate, db: Session = Depends(get_db)):
    pedido = obtener_o_404(db, PedidoAnteojos, pedido_id)
    estado_anterior = pedido.estado
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(pedido, campo, valor)
    if pedido.estado == "entregado" and not pedido.fecha_entrega:
        pedido.fecha_entrega = hoy()

    # Aviso automático al paciente cuando los anteojos están listos
    tel = pedido.paciente.telefono
    if estado_anterior != "listo" and pedido.estado == "listo" and tel:
        texto = (f"👓 ¡Hola {pedido.paciente.nombre}! Tus anteojos ya están *listos para retirar* en "
                 f"{settings.direccion} ({settings.horario_texto}).")
        if pedido.saldo:
            texto += f"\nSaldo a abonar: ${pedido.saldo:,.0f}".replace(",", ".")
        registrar(db, tel, "out", texto)
        enviar_whatsapp(tel, texto)
    db.commit()
    return pedido


@router.delete("/{pedido_id}", status_code=204)
def eliminar(pedido_id: int, db: Session = Depends(get_db)):
    db.delete(obtener_o_404(db, PedidoAnteojos, pedido_id))
    db.commit()
