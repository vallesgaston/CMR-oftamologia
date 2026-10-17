from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoTurno = Literal["pendiente", "confirmado", "cancelado", "atendido", "ausente"]
EstadoPedido = Literal["recibido", "en_laboratorio", "listo", "entregado", "cancelado"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Pacientes ----------
class PacienteBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str | None = None
    dni: str | None = None
    telefono: str | None = None
    email: str | None = None
    fecha_nacimiento: date | None = None
    obra_social: str | None = None
    nro_afiliado: str | None = None
    notas: str | None = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = None
    dni: str | None = None
    telefono: str | None = None
    email: str | None = None
    fecha_nacimiento: date | None = None
    obra_social: str | None = None
    nro_afiliado: str | None = None
    notas: str | None = None


class PacienteOut(PacienteBase, ORM):
    id: int
    creado_en: datetime


class PacienteMini(ORM):
    id: int
    nombre: str
    apellido: str | None
    dni: str | None
    telefono: str | None


# ---------- Turnos ----------
class TurnoCreate(BaseModel):
    paciente_id: int
    fecha_hora: datetime
    duracion_min: int | None = None
    motivo: str | None = None
    estado: EstadoTurno = "confirmado"
    notas: str | None = None


class TurnoUpdate(BaseModel):
    fecha_hora: datetime | None = None
    duracion_min: int | None = None
    motivo: str | None = None
    estado: EstadoTurno | None = None
    notas: str | None = None


class TurnoOut(ORM):
    id: int
    fecha_hora: datetime
    duracion_min: int
    motivo: str | None
    estado: str
    origen: str
    notas: str | None
    paciente: PacienteMini


# ---------- Historia clínica ----------
class ConsultaBase(BaseModel):
    fecha: datetime | None = None
    motivo: str | None = None
    av_od: str | None = None
    av_oi: str | None = None
    pio_od: Decimal | None = None
    pio_oi: Decimal | None = None
    rx_od: str | None = None
    rx_oi: str | None = None
    adicion: str | None = None
    diagnostico: str | None = None
    indicaciones: str | None = None


class ConsultaCreate(ConsultaBase):
    paciente_id: int


class ConsultaUpdate(ConsultaBase):
    pass


class ConsultaOut(ConsultaBase, ORM):
    id: int
    paciente_id: int
    fecha: datetime


# ---------- Anteojos ----------
class PedidoBase(BaseModel):
    consulta_id: int | None = None
    tipo: str | None = None
    descripcion: str | None = None
    fecha_estimada: date | None = None
    fecha_entrega: date | None = None
    monto_total: Decimal | None = None
    sena: Decimal | None = None
    notas: str | None = None


class PedidoCreate(PedidoBase):
    paciente_id: int
    estado: EstadoPedido = "recibido"
    fecha_pedido: date | None = None


class PedidoUpdate(PedidoBase):
    estado: EstadoPedido | None = None
    fecha_pedido: date | None = None


class PedidoOut(PedidoBase, ORM):
    id: int
    estado: str
    fecha_pedido: date
    saldo: Decimal | None
    paciente: PacienteMini


# ---------- Campañas ----------
class CampaniaBase(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    descripcion: str = ""
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    activa: bool = True


class CampaniaUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    activa: bool | None = None


class CampaniaOut(CampaniaBase, ORM):
    id: int
    fecha_inicio: date


# ---------- Conversaciones / bot ----------
class MensajeOut(ORM):
    id: int
    telefono: str
    direccion: str
    texto: str
    creado_en: datetime


class ConversacionOut(BaseModel):
    telefono: str
    estado: str
    requiere_atencion: bool
    actualizado_en: datetime
    ultimo_mensaje: str | None = None
    paciente: str | None = None


class TextoIn(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)


class SimularIn(TextoIn):
    telefono: str = Field(min_length=6, max_length=30)


class SimularOut(BaseModel):
    respuesta: str | None


class HistorialOut(BaseModel):
    paciente: PacienteOut
    consultas: list[ConsultaOut]
    pedidos: list[PedidoOut]
    turnos: list[TurnoOut]


class LimiteTurnos(BaseModel):
    max_turnos_dia: int  # 0 = sin límite
