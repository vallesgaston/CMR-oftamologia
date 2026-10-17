export interface PacienteMini {
  id: number;
  nombre: string;
  apellido: string | null;
  dni: string | null;
  telefono: string | null;
}

export interface Paciente extends PacienteMini {
  email: string | null;
  fecha_nacimiento: string | null;
  obra_social: string | null;
  nro_afiliado: string | null;
  notas: string | null;
  creado_en: string;
}

export type EstadoTurno = 'pendiente' | 'confirmado' | 'cancelado' | 'atendido' | 'ausente';

export interface Turno {
  id: number;
  fecha_hora: string;
  duracion_min: number;
  motivo: string | null;
  estado: EstadoTurno;
  origen: 'manual' | 'bot';
  notas: string | null;
  paciente: PacienteMini;
}

export interface Consulta {
  id: number;
  paciente_id: number;
  fecha: string;
  motivo: string | null;
  av_od: string | null;
  av_oi: string | null;
  pio_od: string | null;
  pio_oi: string | null;
  rx_od: string | null;
  rx_oi: string | null;
  adicion: string | null;
  diagnostico: string | null;
  indicaciones: string | null;
}

export type EstadoPedido = 'recibido' | 'en_laboratorio' | 'listo' | 'entregado' | 'cancelado';

export interface Pedido {
  id: number;
  consulta_id: number | null;
  tipo: string | null;
  descripcion: string | null;
  estado: EstadoPedido;
  fecha_pedido: string;
  fecha_estimada: string | null;
  fecha_entrega: string | null;
  monto_total: string | null;
  sena: string | null;
  saldo: string | null;
  notas: string | null;
  paciente: PacienteMini;
}

export interface Campania {
  id: number;
  titulo: string;
  descripcion: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  activa: boolean;
}

export interface Conversacion {
  telefono: string;
  estado: string;
  requiere_atencion: boolean;
  actualizado_en: string;
  ultimo_mensaje: string | null;
  paciente: string | null;
}

export interface Mensaje {
  id: number;
  telefono: string;
  direccion: 'in' | 'out';
  texto: string;
  creado_en: string;
}

export interface Historial {
  paciente: Paciente;
  consultas: Consulta[];
  pedidos: Pedido[];
  turnos: Turno[];
}

export interface Resumen {
  turnos_hoy: number;
  anteojos_listos: number;
  anteojos_en_laboratorio: number;
  conversaciones_pendientes: number;
  campanias_activas: number;
  pacientes: number;
}

export const ESTADOS_TURNO: EstadoTurno[] = ['pendiente', 'confirmado', 'atendido', 'ausente', 'cancelado'];

export const ESTADOS_PEDIDO: { valor: EstadoPedido; texto: string }[] = [
  { valor: 'recibido', texto: 'Recibido' },
  { valor: 'en_laboratorio', texto: 'En laboratorio' },
  { valor: 'listo', texto: 'Listo p/ retirar' },
  { valor: 'entregado', texto: 'Entregado' },
  { valor: 'cancelado', texto: 'Cancelado' },
];

export const TIPOS_ANTEOJOS = ['Lejos', 'Cerca', 'Multifocal', 'Bifocal', 'Lentes de contacto', 'Otro'];
