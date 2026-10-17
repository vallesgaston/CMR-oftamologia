from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .tiempo import ahora, hoy

ESTADOS_TURNO = ("pendiente", "confirmado", "cancelado", "atendido", "ausente")
TURNOS_ACTIVOS = ("pendiente", "confirmado")
ESTADOS_PEDIDO = ("recibido", "en_laboratorio", "listo", "entregado", "cancelado")


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    apellido: Mapped[str | None] = mapped_column(String(100))
    dni: Mapped[str | None] = mapped_column(String(20), unique=True)
    # No es único: varios miembros de una familia pueden compartir un WhatsApp
    telefono: Mapped[str | None] = mapped_column(String(30), index=True)
    email: Mapped[str | None] = mapped_column(String(120))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    obra_social: Mapped[str | None] = mapped_column(String(100))
    nro_afiliado: Mapped[str | None] = mapped_column(String(50))
    notas: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)

    turnos: Mapped[list["Turno"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
    consultas: Mapped[list["Consulta"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
    pedidos: Mapped[list["PedidoAnteojos"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")


class Turno(Base):
    __tablename__ = "turnos"
    __table_args__ = (
        # Un solo turno activo por horario (un profesional)
        Index("uq_turno_horario_activo", "fecha_hora", unique=True,
              postgresql_where=text("estado <> 'cancelado'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, index=True)
    duracion_min: Mapped[int] = mapped_column(default=20)
    motivo: Mapped[str | None] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    origen: Mapped[str] = mapped_column(String(20), default="manual")  # manual | bot
    notas: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)

    paciente: Mapped[Paciente] = relationship(back_populates="turnos", lazy="joined")


class Consulta(Base):
    """Entrada de historia clínica."""
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=ahora)
    motivo: Mapped[str | None] = mapped_column(String(200))
    # Agudeza visual (ej. "10/10", "20/40")
    av_od: Mapped[str | None] = mapped_column(String(20))
    av_oi: Mapped[str | None] = mapped_column(String(20))
    # Presión intraocular en mmHg
    pio_od: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    pio_oi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    # Refracción (ej. "-1.25 -0.50 x 180")
    rx_od: Mapped[str | None] = mapped_column(String(60))
    rx_oi: Mapped[str | None] = mapped_column(String(60))
    adicion: Mapped[str | None] = mapped_column(String(20))
    diagnostico: Mapped[str | None] = mapped_column(Text)
    indicaciones: Mapped[str | None] = mapped_column(Text)

    paciente: Mapped[Paciente] = relationship(back_populates="consultas")


class PedidoAnteojos(Base):
    __tablename__ = "pedidos_anteojos"

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), index=True)
    consulta_id: Mapped[int | None] = mapped_column(ForeignKey("consultas.id", ondelete="SET NULL"))
    tipo: Mapped[str | None] = mapped_column(String(40))  # lejos, cerca, multifocal...
    descripcion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="recibido", index=True)
    fecha_pedido: Mapped[date] = mapped_column(Date, default=hoy)
    fecha_estimada: Mapped[date | None] = mapped_column(Date)
    fecha_entrega: Mapped[date | None] = mapped_column(Date)
    monto_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    sena: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notas: Mapped[str | None] = mapped_column(Text)

    paciente: Mapped[Paciente] = relationship(back_populates="pedidos", lazy="joined")

    @property
    def saldo(self) -> Decimal | None:
        if self.monto_total is None:
            return None
        return self.monto_total - (self.sena or 0)


class Campania(Base):
    __tablename__ = "campanias"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    fecha_inicio: Mapped[date] = mapped_column(Date, default=hoy)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Conversacion(Base):
    """Estado del bot por cada número de teléfono."""
    __tablename__ = "conversaciones"

    telefono: Mapped[str] = mapped_column(String(30), primary_key=True)
    estado: Mapped[str] = mapped_column(String(30), default="MENU")
    datos: Mapped[dict] = mapped_column(JSONB, default=dict)
    requiere_atencion: Mapped[bool] = mapped_column(Boolean, default=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)


class Mensaje(Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(primary_key=True)
    telefono: Mapped[str] = mapped_column(String(30), index=True)
    direccion: Mapped[str] = mapped_column(String(3))  # in | out
    texto: Mapped[str] = mapped_column(Text)
    wa_id: Mapped[str | None] = mapped_column(String(100), unique=True)  # evita procesar duplicados
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=ahora)
