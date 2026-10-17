from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import requiere_admin
from ..bot.motor import procesar_mensaje
from ..db import get_db, obtener_o_404
from ..models import Campania, Conversacion, Mensaje, Paciente, PedidoAnteojos, Turno
from ..schemas import ConversacionOut, MensajeOut, SimularIn, SimularOut, TextoIn
from ..services.mensajeria import enviar_whatsapp, registrar
from ..services.telefono import normalizar, pacientes_por_telefono
from ..tiempo import ahora, hoy

router = APIRouter(prefix="/api", tags=["conversaciones"], dependencies=[Depends(requiere_admin)])


@router.get("/conversaciones", response_model=list[ConversacionOut])
def listar(db: Session = Depends(get_db)):
    convs = db.scalars(select(Conversacion).order_by(
        Conversacion.requiere_atencion.desc(), Conversacion.actualizado_en.desc()).limit(100)).all()
    salida = []
    for c in convs:
        ultimo = db.scalar(select(Mensaje.texto).where(Mensaje.telefono == c.telefono)
                           .order_by(Mensaje.id.desc()).limit(1))
        nombres = ", ".join(f"{p.nombre} {p.apellido or ''}".strip() for p in pacientes_por_telefono(db, c.telefono))
        salida.append(ConversacionOut(telefono=c.telefono, estado=c.estado, requiere_atencion=c.requiere_atencion,
                                      actualizado_en=c.actualizado_en, ultimo_mensaje=ultimo,
                                      paciente=nombres or None))
    return salida


@router.get("/conversaciones/{telefono}/mensajes", response_model=list[MensajeOut])
def mensajes(telefono: str, db: Session = Depends(get_db)):
    return db.scalars(select(Mensaje).where(Mensaje.telefono == normalizar(telefono))
                      .order_by(Mensaje.id.desc()).limit(200)).all()[::-1]


@router.post("/conversaciones/{telefono}/responder", response_model=MensajeOut)
def responder(telefono: str, data: TextoIn, db: Session = Depends(get_db)):
    """La secretaría responde manualmente; el bot queda en pausa para ese número."""
    conv = obtener_o_404(db, Conversacion, normalizar(telefono))
    conv.estado, conv.datos, conv.requiere_atencion = "HUMANO", {}, False
    conv.actualizado_en = ahora()
    msg = registrar(db, conv.telefono, "out", data.texto)
    db.commit()
    enviar_whatsapp(conv.telefono, data.texto)
    return msg


@router.post("/conversaciones/{telefono}/liberar", status_code=204)
def liberar(telefono: str, db: Session = Depends(get_db)):
    """Devuelve la conversación al bot."""
    conv = obtener_o_404(db, Conversacion, normalizar(telefono))
    conv.estado, conv.datos, conv.requiere_atencion = "MENU", {}, False
    db.commit()


@router.post("/bot/simular", response_model=SimularOut)
def simular(data: SimularIn, db: Session = Depends(get_db)):
    """Prueba el bot sin WhatsApp: mismo motor, misma base de datos."""
    return SimularOut(respuesta=procesar_mensaje(db, data.telefono, data.texto))


@router.get("/resumen")
def resumen(db: Session = Depends(get_db)):
    inicio, fin = datetime.combine(hoy(), time.min), datetime.combine(hoy(), time.max)
    contar = lambda stmt: db.scalar(select(func.count()).select_from(stmt.subquery()))
    return {
        "turnos_hoy": contar(select(Turno.id).where(Turno.fecha_hora.between(inicio, fin), Turno.estado != "cancelado")),
        "anteojos_listos": contar(select(PedidoAnteojos.id).where(PedidoAnteojos.estado == "listo")),
        "anteojos_en_laboratorio": contar(select(PedidoAnteojos.id).where(PedidoAnteojos.estado == "en_laboratorio")),
        "conversaciones_pendientes": contar(select(Conversacion.telefono).where(Conversacion.requiere_atencion.is_(True))),
        "campanias_activas": contar(select(Campania.id).where(Campania.activa.is_(True))),
        "pacientes": contar(select(Paciente.id)),
    }
