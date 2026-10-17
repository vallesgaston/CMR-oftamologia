import { DatePipe } from '@angular/common';
import { Component, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { Api } from '../../core/api';
import { Consulta, Historial, TIPOS_ANTEOJOS } from '../../core/models';
import { ahoraLocalISO, limpiar, NombrePacPipe } from '../../core/util';
import { FormPaciente } from '../../shared/form-paciente';
import { FormTurno } from '../../shared/form-turno';
import { Modal } from '../../shared/modal';
import { TablaPedidos } from '../../shared/tabla-pedidos';

type ModalAbierto = 'editar' | 'turno' | 'consulta' | 'pedido' | null;

@Component({
  selector: 'app-paciente-detalle',
  imports: [DatePipe, FormsModule, RouterLink, NombrePacPipe, Modal, FormPaciente, FormTurno, TablaPedidos],
  templateUrl: './paciente-detalle.html',
})
export class PacienteDetalle {
  private readonly api = inject(Api);
  private readonly router = inject(Router);

  /** Viene del parámetro :id de la ruta. */
  readonly id = input.required<string>();
  readonly h = signal<Historial | null>(null);
  readonly modal = signal<ModalAbierto>(null);
  readonly consultaDetalle = signal<Consulta | null>(null);
  readonly tipos = TIPOS_ANTEOJOS;

  consulta: Partial<Consulta> = {};
  pedido: Record<string, string | number | null> = {};

  constructor() {
    effect(() => {
      this.id();
      this.cargar();
    });
  }

  async cargar() {
    this.h.set(await this.api.historial(+this.id()));
  }

  pedidosDeConsulta(consultaId: number) {
    return this.h()?.pedidos.filter((p) => p.consulta_id === consultaId) ?? [];
  }

  abrirConsulta() {
    this.consulta = { fecha: ahoraLocalISO() };
    this.modal.set('consulta');
  }

  abrirPedido() {
    this.pedido = { tipo: 'Lejos', consulta_id: this.h()?.consultas[0]?.id ?? null };
    this.modal.set('pedido');
  }

  async guardarConsulta() {
    await this.api.crearConsulta({ ...limpiar(this.consulta), paciente_id: +this.id() });
    this.cerrarYRecargar();
  }

  async guardarPedido() {
    await this.api.crearPedido({ ...limpiar(this.pedido), paciente_id: +this.id() });
    this.cerrarYRecargar();
  }

  async eliminar() {
    if (!confirm('¿Eliminar el paciente y toda su historia clínica? No se puede deshacer.')) return;
    await this.api.eliminarPaciente(+this.id());
    this.router.navigate(['/pacientes']);
  }

  cerrarYRecargar() {
    this.modal.set(null);
    this.cargar();
  }
}
