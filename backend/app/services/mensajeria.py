"""Registro de mensajes y envío por WhatsApp Cloud API."""
import logging

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Mensaje

log = logging.getLogger("mensajeria")


def registrar(db: Session, telefono: str, direccion: str, texto: str, wa_id: str | None = None) -> Mensaje:
    msg = Mensaje(telefono=telefono, direccion=direccion, texto=texto, wa_id=wa_id)
    db.add(msg)
    return msg


def enviar_whatsapp(telefono: str, texto: str) -> bool:
    """Envía un mensaje de texto. Sin credenciales configuradas, solo lo loguea (modo simulado).

    Ojo: WhatsApp solo permite texto libre dentro de las 24 h posteriores al último mensaje
    del paciente. Fuera de esa ventana hay que usar plantillas aprobadas por Meta.
    """
    if not settings.whatsapp_activo:
        log.info("[WhatsApp simulado] a %s: %s", telefono, texto)
        return False
    url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": texto},
    }
    try:
        r = httpx.post(url, json=payload, timeout=10,
                       headers={"Authorization": f"Bearer {settings.whatsapp_token}"})
        r.raise_for_status()
        return True
    except httpx.HTTPError as e:
        detalle = getattr(getattr(e, "response", None), "text", "")
        log.error("Error enviando WhatsApp a %s: %s %s", telefono, e, detalle)
        return False
