import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { Api } from '../core/api';
import { ESTADOS_PEDIDO, EstadoPedido, Pedido } from '../core/models';
import { NombrePacPipe } from '../core/util';
import { Modal } from './modal';

@Component({
  selector: 'app-tabla-pedidos',
  imports: [DatePipe, DecimalPipe, FormsModule, RouterLink, NombrePacPipe, Modal],
  template: `
    @if (pedidos().length) {
      <table>
        <thead>
          <tr>
            @if (conPaciente()) { <th>Paciente</th><th>Teléfono</th> }
            <th>Pedido</th><th>Tipo</th><th>Descripción</th><th>Entrega</th><th>Saldo</th><th>Estado</th>
          </tr>
        </thead>
        <tbody>
          @for (p of pedidos(); track p.id) {
            <tr class="click" (click)="detalle.set(p)">
              @if (conPaciente()) {
                <td (click)="$event.stopPropagation()"><a [routerLink]="['/pacientes', p.paciente.id]">{{ p.paciente | nombrePac }}</a></td>
                <td>{{ p.paciente.telefono }}</td>
              }
              <td>{{ p.fecha_pedido | date: 'dd/MM/yyyy' }}</td>
              <td>{{ p.tipo }}</td>
              <td>
                {{ p.descripcion }}
                @if (p.notas) { <span title="Tiene notas">📝</span> }
              </td>
              <td>
                @if (p.estado === 'entregado') { Entregado {{ p.fecha_entrega | date: 'dd/MM' }} }
                @else { {{ p.fecha_estimada | date: 'dd/MM/yyyy' }} }
              </td>
              <td>@if (p.saldo !== null) { $ {{ +p.saldo | number: '1.0-0' }} }</td>
              <td (click)="$event.stopPropagation()">
                <select [class]="'estado-' + p.estado" [ngModel]="p.estado" (ngModelChange)="cambiarEstado(p, $event)">
                  @for (e of estados; track e.valor) { <option [value]="e.valor">{{ e.texto }}</option> }
                </select>
              </td>
            </tr>
          }
        </tbody>
      </table>
    } @else {
      <p class="vacio">Sin pedidos.</p>
    }

    @if (detalle(); as p) {
      <app-modal titulo="Pedido de anteojos" (cerrar)="detalle.set(null)">
        <dl class="detalle">
          <dt>Paciente</dt><dd>{{ p.paciente | nombrePac }}</dd>
          <dt>Estado</dt><dd [class]="'estado-' + p.estado">{{ textoEstado(p.estado) }}</dd>
          <dt>Tipo</dt><dd>{{ p.tipo || '—' }}</dd>
          <dt>Descripción</dt><dd>{{ p.descripcion || '—' }}</dd>
          <dt>Fecha de pedido</dt><dd>{{ p.fecha_pedido | date: 'dd/MM/yyyy' }}</dd>
          <dt>Entrega estimada</dt><dd>{{ p.fecha_estimada ? (p.fecha_estimada | date: 'dd/MM/yyyy') : '—' }}</dd>
          @if (p.fecha_entrega) {
            <dt>Entregado</dt><dd>{{ p.fecha_entrega | date: 'dd/MM/yyyy' }}</dd>
          }
          <dt>Monto total</dt><dd>{{ p.monto_total !== null ? '$ ' + (+p.monto_total | number: '1.0-0') : '—' }}</dd>
          <dt>Seña</dt><dd>{{ p.sena !== null ? '$ ' + (+p.sena | number: '1.0-0') : '—' }}</dd>
          <dt>Saldo</dt><dd><b>{{ p.saldo !== null ? '$ ' + (+p.saldo | number: '1.0-0') : '—' }}</b></dd>
          <dt>Notas</dt><dd class="notas">{{ p.notas || '—' }}</dd>
        </dl>
      </app-modal>
    }
  `,
})
export class TablaPedidos {
  private readonly api = inject(Api);
  readonly pedidos = input.required<Pedido[]>();
  readonly conPaciente = input(true);
  readonly cambiado = output<void>();
  readonly estados = ESTADOS_PEDIDO;
  readonly detalle = signal<Pedido | null>(null);

  textoEstado(estado: EstadoPedido) {
    return this.estados.find((e) => e.valor === estado)?.texto ?? estado;
  }

  async cambiarEstado(p: Pedido, estado: EstadoPedido) {
    await this.api.actualizarPedido(p.id, { estado });
    this.cambiado.emit();
  }
}
