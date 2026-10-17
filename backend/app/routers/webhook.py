"""Webhook de WhatsApp Cloud API (Meta)."""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse

from ..bot.motor import procesar_mensaje
from ..config import settings
from ..db import SessionLocal
from ..services.mensajeria import enviar_whatsapp

router = APIRouter(prefix="/webhook", tags=["webhook"])
log = logging.getLogger("webhook")


@router.get("/whatsapp", response_class=PlainTextResponse)
def verificar(mode: str = Query(alias="hub.mode", default=""),
              token: str = Query(alias="hub.verify_token", default=""),
              challenge: str = Query(alias="hub.challenge", default="")):
    """Meta llama a este endpoint una vez al configurar el webhook."""
    if mode == "subscribe" and hmac.compare_digest(token, settings.whatsapp_verify_token):
        return challenge
    raise HTTPException(status_code=403, detail="Verificación fallida")


@router.post("/whatsapp")
async def recibir(request: Request):
    cuerpo = await request.body()
    if settings.whatsapp_app_secret:
        firma = request.headers.get("X-Hub-Signature-256", "")
        esperada = "sha256=" + hmac.new(settings.whatsapp_app_secret.encode(), cuerpo, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, esperada):
            raise HTTPException(status_code=403, detail="Firma inválida")
    await run_in_threadpool(_procesar_payload, json.loads(cuerpo or b"{}"))
    return {"ok": True}


def _procesar_payload(payload: dict) -> None:
    with SessionLocal() as db:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                for msg in change.get("value", {}).get("messages", []):
                    telefono = msg.get("from")
                    tipo = msg.get("type")
                    if tipo == "text":
                        texto = msg["text"]["body"]
                    elif tipo == "interactive":
                        inter = msg.get("interactive", {})
                        texto = (inter.get("button_reply") or inter.get("list_reply") or {}).get("title", "")
                    else:
                        texto = f"[{tipo}]"
                    try:
                        respuesta = procesar_mensaje(db, telefono, texto, wa_id=msg.get("id"))
                    except Exception:
                        log.exception("Error procesando mensaje de %s", telefono)
                        db.rollback()
                        continue
                    if respuesta:
                        enviar_whatsapp(telefono, respuesta)
