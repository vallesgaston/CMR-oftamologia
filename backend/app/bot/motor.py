"""Motor del bot de respuestas automáticas.

Es independiente del canal: recibe (teléfono, texto) y devuelve la respuesta (o None si
la conversación está derivada a una persona). El estado de cada conversación se guarda
en la tabla `conversaciones`, así sobrevive a reinicios.
"""
import re
import unicodedata
from datetime import date, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import TURNOS_ACTIVOS, Campania, Conversacion, Mensaje, Paciente, PedidoAnteojos, Turno
from ..services.agenda import horarios_disponibles, proximos_dias_disponibles
from ..services.mensajeria import registrar
from ..services.telefono import normalizar, pacientes_por_telefono
from ..tiempo import ahora

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

TEXTO_PEDIDO = {
    "recibido": "📝 Recibido — ya registramos tu pedido",
    "en_laboratorio": "🔬 En laboratorio — se están fabricando tus cristales",
    "listo": "✅ ¡Listo para retirar!",
    "entregado": "📦 Entregado",
    "cancelado": "❌ Cancelado",
}

MENU = (
    "¿En qué te puedo ayudar?\n\n"
    "1️⃣ Reservar un turno\n"
    "2️⃣ Ver o cancelar mis turnos\n"
    "3️⃣ Estado de mis anteojos\n"
    "4️⃣ Campañas vigentes\n"
    "5️⃣ Horarios y ubicación\n"
    "6️⃣ Hablar con una persona\n\n"
    "Respondé con el número de la opción."
)
VOLVER = "\n\nEscribí *menu* para ver otras opciones."

EXPIRACION = timedelta(minutes=30)

RE_RESET = re.compile(r"^(hola|holis|buenas|buen dia|buenos dias|buenas tardes|buenas noches|menu|inicio|volver|0)\b")
RE_SALIR_HUMANO = re.compile(r"^(menu|0)$")
RE_NO_TEXTO = re.compile(r"^\[\w+\]$")  # el webhook marca audios/imágenes como "[audio]"

INTENCIONES = [
    ("6", re.compile(r"humano|persona|secretari|operador|hablar con|atencion al")),
    ("2", re.compile(r"cancel|mis turnos|reprogram|anular")),
    ("3", re.compile(r"anteojo|lente|gafa|cristal|pedido|optica")),
    ("1", re.compile(r"turno|reserv|cita|agend")),
    ("4", re.compile(r"campa|promo|descuento|jornada")),
    ("5", re.compile(r"horario|direcc|ubicac|donde|atienden|obra social")),
]


# ---------- utilidades ----------
def normalizar_texto(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def fmt_dia(d: date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def fmt_hora(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def fmt_dinero(valor) -> str:
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _set(conv: Conversacion, estado: str, **datos) -> None:
    conv.estado = estado
    conv.datos = {**(conv.datos or {}), **datos}  # reasignar para que SQLAlchemy detecte el cambio


def _reset(conv: Conversacion) -> None:
    conv.estado = "MENU"
    conv.datos = {}


def _elegir(t: str, opciones: list):
    m = re.match(r"^(\d{1,2})\b", t)
    if not m:
        return None
    i = int(m.group(1)) - 1
    return opciones[i] if 0 <= i < len(opciones) else None


def _dni(t: str) -> str | None:
    dni = re.sub(r"\D", "", t)
    return dni if 6 <= len(dni) <= 9 else None


# ---------- punto de entrada ----------
def procesar_mensaje(db: Session, telefono: str, texto: str, wa_id: str | None = None) -> str | None:
    telefono = normalizar(telefono) or "desconocido"
    if wa_id and db.scalar(select(Mensaje.id).where(Mensaje.wa_id == wa_id)):
        return None  # WhatsApp reenvió un mensaje ya procesado

    registrar(db, telefono, "in", texto, wa_id=wa_id)
    conv = db.get(Conversacion, telefono)
    if conv is None:
        conv = Conversacion(telefono=telefono, estado="MENU", datos={}, requiere_atencion=False)
        db.add(conv)
    elif conv.estado not in ("MENU", "HUMANO") and ahora() - conv.actualizado_en > EXPIRACION:
        _reset(conv)

    t = normalizar_texto(texto)

    if conv.estado == "HUMANO":
        if RE_SALIR_HUMANO.match(t):
            _reset(conv)
            conv.requiere_atencion = False
            respuesta = MENU
        else:
            conv.requiere_atencion = True
            respuesta = None  # lo atiende la secretaría desde el panel
    elif RE_NO_TEXTO.match(texto.strip()):
        respuesta = "Por ahora solo puedo leer mensajes de texto 🙂" + VOLVER
    else:
        if RE_RESET.match(t):
            _reset(conv)
        handler = HANDLERS.get(conv.estado, estado_menu)
        respuesta = handler(db, conv, t, texto)

    if respuesta:
        registrar(db, telefono, "out", respuesta)
    conv.actualizado_en = ahora()
    db.commit()
    return respuesta


# ---------- menú ----------
def _detectar_opcion(t: str) -> str | None:
    m = re.match(r"^([1-6])\b", t)
    if m:
        return m.group(1)
    for opcion, patron in INTENCIONES:
        if patron.search(t):
            return opcion
    return None


def estado_menu(db, conv, t, raw):
    acciones = {"1": iniciar_reserva, "2": mis_turnos, "3": anteojos,
                "4": campanias, "5": info, "6": derivar_humano}
    opcion = _detectar_opcion(t)
    if opcion:
        return acciones[opcion](db, conv)
    return f"👋 ¡Hola! Soy el asistente virtual de *{settings.nombre_consultorio}*.\n\n{MENU}"


# ---------- reserva de turnos ----------
def iniciar_reserva(db, conv):
    _set(conv, "RESERVA_DNI")
    return "📅 ¡Vamos a reservar tu turno!\n\nEscribí el *DNI del paciente* (solo números)."


def reserva_dni(db, conv, t, raw):
    dni = _dni(t)
    if not dni:
        return "Ese DNI no parece válido. Escribí solo los números, por ejemplo *30123456*.\n(0 para volver al menú)"
    pac = db.scalar(select(Paciente).where(Paciente.dni == dni))
    if pac:
        _set(conv, conv.estado, paciente_id=pac.id)
        return ofrecer_dias(db, conv, saludo=f"Perfecto, {pac.nombre}. ")
    _set(conv, "RESERVA_NOMBRE", dni=dni)
    return ("No encontramos ese DNI, así que te vamos a registrar 📝\n\n"
            "¿Cuál es el *nombre y apellido* del paciente?")


def reserva_nombre(db, conv, t, raw):
    nombre = " ".join(raw.split())
    if len(nombre) < 3 or any(c.isdigit() for c in nombre):
        return "Escribí el nombre y apellido del paciente, por ejemplo *María González*."
    nombre = nombre.title()
    _set(conv, conv.estado, nombre_completo=nombre)
    return ofrecer_dias(db, conv, saludo=f"Gracias, {nombre.split()[0]}. ")


def ofrecer_dias(db, conv, saludo=""):
    dias = proximos_dias_disponibles(db, settings.dias_a_ofrecer)
    if not dias:
        _reset(conv)
        return "😕 No hay turnos disponibles en los próximos días. Escribí *6* para que la secretaría te ayude."
    _set(conv, "RESERVA_DIA", dias=[d.isoformat() for d in dias])
    lista = "\n".join(f"*{i}.* {fmt_dia(d).capitalize()}" for i, d in enumerate(dias, 1))
    return f"{saludo}¿Qué día preferís?\n\n{lista}\n\nRespondé con el número."


def reserva_dia(db, conv, t, raw):
    elegido = _elegir(t, conv.datos.get("dias", []))
    if not elegido:
        return "Respondé con el número del día (o *0* para volver al menú)."
    dia = date.fromisoformat(elegido)
    horarios = horarios_disponibles(db, dia)
    if not horarios:
        return ofrecer_dias(db, conv, saludo="Ese día se acaba de completar. ")
    _set(conv, "RESERVA_HORA", horarios=[h.isoformat() for h in horarios])
    lista = "\n".join(f"*{i}.* {fmt_hora(h)}" for i, h in enumerate(horarios, 1))
    return f"Horarios libres para el *{fmt_dia(dia)}*:\n\n{lista}\n\nRespondé con el número del horario."


def reserva_hora(db, conv, t, raw):
    elegido = _elegir(t, conv.datos.get("horarios", []))
    if not elegido:
        return "Respondé con el número del horario (o *0* para volver al menú)."
    _set(conv, "RESERVA_CONFIRMAR", fecha_hora=elegido)
    dt = datetime.fromisoformat(elegido)
    d = conv.datos
    if d.get("paciente_id"):
        pac = db.get(Paciente, d["paciente_id"])
        nombre = f"{pac.nombre} {pac.apellido or ''}".strip()
    else:
        nombre = d.get("nombre_completo", "")
    return (f"Confirmemos 👇\n\n👤 {nombre}\n📅 {fmt_dia(dt.date()).capitalize()}\n"
            f"🕐 {fmt_hora(dt)} hs\n📍 {settings.direccion}\n\n"
            "¿Confirmás el turno? Respondé *SI* o *NO*.")


def reserva_confirmar(db, conv, t, raw):
    if re.match(r"^(no|cancel)", t):
        _reset(conv)
        return "Listo, no reservé nada." + VOLVER
    if not re.match(r"^(si|s|ok|dale|confirm|de acuerdo)\b", t):
        return "Respondé *SI* para confirmar o *NO* para cancelar."

    d = conv.datos
    fecha_hora = datetime.fromisoformat(d["fecha_hora"])
    if fecha_hora not in horarios_disponibles(db, fecha_hora.date()):
        return ofrecer_dias(db, conv, saludo="😕 Ese horario ya no está disponible. ")

    pac = db.get(Paciente, d["paciente_id"]) if d.get("paciente_id") else None
    try:
        with db.begin_nested():
            if pac is None:
                partes = d["nombre_completo"].split(" ", 1)
                pac = Paciente(nombre=partes[0], apellido=partes[1] if len(partes) > 1 else None,
                               dni=d["dni"], telefono=conv.telefono)
                db.add(pac)
            db.add(Turno(paciente=pac, fecha_hora=fecha_hora, duracion_min=settings.duracion_turno_min,
                         estado="confirmado", origen="bot", motivo="Reservado por WhatsApp"))
    except IntegrityError:
        return ofrecer_dias(db, conv, saludo="😕 Ese horario se acaba de ocupar. ")

    _reset(conv)
    return (f"✅ *¡Turno reservado!*\n\n📅 {fmt_dia(fecha_hora.date()).capitalize()} a las "
            f"{fmt_hora(fecha_hora)} hs\n📍 {settings.direccion}\n\n"
            "Traé DNI, credencial de la obra social y tus anteojos actuales si usás. "
            "Si no podés venir, escribí *2* para cancelar." + VOLVER)


# ---------- mis turnos / cancelar ----------
def mis_turnos(db, conv):
    pacientes = pacientes_por_telefono(db, conv.telefono)
    turnos = []
    if pacientes:
        turnos = list(db.scalars(
            select(Turno).where(
                Turno.paciente_id.in_([p.id for p in pacientes]),
                Turno.estado.in_(TURNOS_ACTIVOS),
                Turno.fecha_hora >= ahora(),
            ).order_by(Turno.fecha_hora)
        ).unique())
    if not turnos:
        _reset(conv)
        return "No encontramos turnos próximos asociados a este número. Escribí *1* para reservar uno."
    _set(conv, "CANCELAR_TURNO", turnos=[tu.id for tu in turnos])
    lista = "\n".join(
        f"*{i}.* {fmt_dia(tu.fecha_hora.date()).capitalize()} {fmt_hora(tu.fecha_hora)} hs — {tu.paciente.nombre}"
        for i, tu in enumerate(turnos, 1)
    )
    return (f"🗓️ Tus próximos turnos:\n\n{lista}\n\n"
            "Si querés *cancelar* alguno, respondé con su número. Escribí *0* para volver al menú.")


def cancelar_turno(db, conv, t, raw):
    turno_id = _elegir(t, conv.datos.get("turnos", []))
    if not turno_id:
        return "Respondé con el número del turno a cancelar, o *0* para volver al menú."
    turno = db.get(Turno, turno_id)
    _reset(conv)
    if not turno or turno.estado not in TURNOS_ACTIVOS:
        return "Ese turno ya no está activo." + VOLVER
    turno.estado = "cancelado"
    return (f"❌ Cancelé el turno del {fmt_dia(turno.fecha_hora.date())} a las {fmt_hora(turno.fecha_hora)} hs. "
            "¡Gracias por avisar! Escribí *1* si querés reservar otro.")


# ---------- anteojos ----------
def anteojos(db, conv):
    pacientes = pacientes_por_telefono(db, conv.telefono)
    if not pacientes:
        _set(conv, "ANTEOJOS_DNI")
        return "👓 Para consultar tu pedido escribí el *DNI del paciente*."
    return responder_pedidos(db, conv, pacientes)


def anteojos_dni(db, conv, t, raw):
    dni = _dni(t)
    if not dni:
        return "Escribí el DNI (solo números) o *0* para volver al menú."
    pac = db.scalar(select(Paciente).where(Paciente.dni == dni))
    if not pac:
        _reset(conv)
        return "No encontramos pacientes con ese DNI. Escribí *6* si querés hablar con la secretaría."
    return responder_pedidos(db, conv, [pac])


def responder_pedidos(db, conv, pacientes):
    _reset(conv)
    limite = ahora().date() - timedelta(days=60)
    pedidos = list(db.scalars(
        select(PedidoAnteojos).where(
            PedidoAnteojos.paciente_id.in_([p.id for p in pacientes]),
            or_(PedidoAnteojos.estado.notin_(("entregado", "cancelado")), PedidoAnteojos.fecha_pedido >= limite),
        ).order_by(PedidoAnteojos.fecha_pedido.desc()).limit(5)
    ).unique())
    if not pedidos:
        return "No encontramos pedidos de anteojos recientes." + VOLVER

    bloques = []
    for p in pedidos:
        lineas = [f"👓 *{p.tipo or 'Anteojos'}* — {p.paciente.nombre} (pedido del {p.fecha_pedido:%d/%m})",
                  f"Estado: {TEXTO_PEDIDO.get(p.estado, p.estado)}"]
        if p.estado in ("recibido", "en_laboratorio") and p.fecha_estimada:
            lineas.append(f"Entrega estimada: {fmt_dia(p.fecha_estimada)}")
        if p.estado == "listo":
            lineas.append(f"Podés retirarlos en {settings.direccion} ({settings.horario_texto}).")
        if p.saldo and p.estado not in ("entregado", "cancelado"):
            lineas.append(f"Saldo a abonar: {fmt_dinero(p.saldo)}")
        bloques.append("\n".join(lineas))
    return "\n\n".join(bloques) + VOLVER


# ---------- información ----------
def campanias(db, conv):
    hoy = ahora().date()
    activas = list(db.scalars(
        select(Campania).where(
            Campania.activa.is_(True),
            Campania.fecha_inicio <= hoy,
            or_(Campania.fecha_fin.is_(None), Campania.fecha_fin >= hoy),
        ).order_by(Campania.fecha_inicio)
    ))
    if not activas:
        return "En este momento no tenemos campañas vigentes. ¡Te avisaremos por acá cuando haya novedades!" + VOLVER
    bloques = []
    for c in activas:
        txt = f"*{c.titulo}*\n{c.descripcion}"
        if c.fecha_fin:
            txt += f"\n🗓️ Hasta el {fmt_dia(c.fecha_fin)}"
        bloques.append(txt)
    return "📢 *Campañas vigentes*\n\n" + "\n\n".join(bloques) + "\n\nEscribí *1* para reservar un turno." + VOLVER


def info(db, conv):
    txt = f"🏥 *{settings.nombre_consultorio}*\n📍 {settings.direccion}\n🕐 {settings.horario_texto}"
    if settings.telefono_contacto:
        txt += f"\n📞 {settings.telefono_contacto}"
    if settings.info_extra:
        txt += f"\n\n{settings.info_extra}"
    return txt + VOLVER


def derivar_humano(db, conv):
    _set(conv, "HUMANO")
    conv.requiere_atencion = True
    return ("🙋 Listo, ya le avisé a la secretaría. Te van a responder por acá a la brevedad "
            "(en horario de atención).\n\nSi querés volver al asistente automático escribí *menu*.")


HANDLERS = {
    "MENU": estado_menu,
    "RESERVA_DNI": reserva_dni,
    "RESERVA_NOMBRE": reserva_nombre,
    "RESERVA_DIA": reserva_dia,
    "RESERVA_HORA": reserva_hora,
    "RESERVA_CONFIRMAR": reserva_confirmar,
    "CANCELAR_TURNO": cancelar_turno,
    "ANTEOJOS_DNI": anteojos_dni,
}
