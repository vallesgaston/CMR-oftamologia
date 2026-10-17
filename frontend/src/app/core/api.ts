import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  Campania,
  Consulta,
  Conversacion,
  Historial,
  Mensaje,
  Paciente,
  Pedido,
  Resumen,
  Turno,
} from './models';

type Params = Record<string, string | number | boolean | null | undefined>;

@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);

  /** Chats esperando respuesta de la secretaría (se muestra como badge en el menú). */
  readonly chatsPendientes = signal(0);

  private get<T>(url: string, params: Params = {}): Promise<T> {
    let p = new HttpParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== null && v !== undefined && v !== '') p = p.set(k, String(v));
    }
    return firstValueFrom(this.http.get<T>(url, { params: p }));
  }

  private post<T>(url: string, body: unknown = {}): Promise<T> {
    return firstValueFrom(this.http.post<T>(url, body));
  }

  private patch<T>(url: string, body: unknown): Promise<T> {
    return firstValueFrom(this.http.patch<T>(url, body));
  }

  private delete(url: string): Promise<void> {
    return firstValueFrom(this.http.delete<void>(url));
  }

  // ---- resumen ----
  async resumen(): Promise<Resumen> {
    const r = await this.get<Resumen>('/api/resumen');
    this.chatsPendientes.set(r.conversaciones_pendientes);
    return r;
  }

  // ---- pacientes ----
  pacientes(q = '') {
    return this.get<Paciente[]>('/api/pacientes', { q });
  }
  historial(id: number) {
    return this.get<Historial>(`/api/pacientes/${id}/historial`);
  }
  crearPaciente(d: Partial<Paciente>) {
    return this.post<Paciente>('/api/pacientes', d);
  }
  actualizarPaciente(id: number, d: Partial<Paciente>) {
    return this.patch<Paciente>(`/api/pacientes/${id}`, d);
  }
  eliminarPaciente(id: number) {
    return this.delete(`/api/pacientes/${id}`);
  }

  // ---- turnos ----
  turnos(desde: string, incluirCancelados = false, hasta?: string) {
    return this.get<Turno[]>('/api/turnos', {
      desde,
      hasta,
      incluir_cancelados: incluirCancelados,
    });
  }
  horariosDisponibles(fecha: string) {
    return this.get<string[]>('/api/turnos/disponibles', { fecha });
  }
  limiteTurnos() {
    return this.get<{ max_turnos_dia: number }>('/api/turnos/limite');
  }
  crearTurno(d: { paciente_id: number; fecha_hora: string; motivo?: string | null }) {
    return this.post<Turno>('/api/turnos', d);
  }
  actualizarTurno(id: number, d: Partial<Turno>) {
    return this.patch<Turno>(`/api/turnos/${id}`, d);
  }

  // ---- historia clínica ----
  crearConsulta(d: Partial<Consulta>) {
    return this.post<Consulta>('/api/consultas', d);
  }

  // ---- anteojos ----
  pedidos(estado = '') {
    return this.get<Pedido[]>('/api/anteojos', { estado });
  }
  crearPedido(d: Record<string, unknown>) {
    return this.post<Pedido>('/api/anteojos', d);
  }
  actualizarPedido(id: number, d: Record<string, unknown>) {
    return this.patch<Pedido>(`/api/anteojos/${id}`, d);
  }

  // ---- campañas ----
  campanias() {
    return this.get<Campania[]>('/api/campanias');
  }
  crearCampania(d: Partial<Campania>) {
    return this.post<Campania>('/api/campanias', d);
  }
  actualizarCampania(id: number, d: Partial<Campania>) {
    return this.patch<Campania>(`/api/campanias/${id}`, d);
  }
  eliminarCampania(id: number) {
    return this.delete(`/api/campanias/${id}`);
  }

  // ---- conversaciones / bot ----
  async conversaciones(): Promise<Conversacion[]> {
    const cs = await this.get<Conversacion[]>('/api/conversaciones');
    this.chatsPendientes.set(cs.filter((c) => c.requiere_atencion).length);
    return cs;
  }
  mensajes(tel: string) {
    return this.get<Mensaje[]>(`/api/conversaciones/${tel}/mensajes`);
  }
  responder(tel: string, texto: string) {
    return this.post<Mensaje>(`/api/conversaciones/${tel}/responder`, { texto });
  }
  liberar(tel: string) {
    return this.post<void>(`/api/conversaciones/${tel}/liberar`);
  }
  simular(telefono: string, texto: string) {
    return this.post<{ respuesta: string | null }>('/api/bot/simular', { telefono, texto });
  }
}
