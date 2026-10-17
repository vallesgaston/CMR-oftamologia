import { DatePipe } from '@angular/common';
import { Component, inject, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { Api } from '../core/api';
import { ESTADOS_TURNO, EstadoTurno, Turno } from '../core/models';
import { NombrePacPipe } from '../core/util';

@Component({
  selector: 'app-tabla-turnos',
  imports: [DatePipe, FormsModule, RouterLink, NombrePacPipe],
  template: `
    @if (turnos().length) {
      <table>
        <thead>
          <tr><th>Hora</th><th>Paciente</th><th>Teléfono</th><th>Motivo</th><th>Origen</th><th>Estado</th></tr>
        </thead>
        <tbody>
          @for (t of turnos(); track t.id) {
            <tr class="click" (click)="abrir(t)">
              <td><b>{{ t.fecha_hora | date: 'HH:mm' }}</b></td>
              <td><a [routerLink]="['/pacientes', t.paciente.id]">{{ t.paciente | nombrePac }}</a></td>
              <td>{{ t.paciente.telefono }}</td>
              <td>{{ t.motivo }}</td>
              <td>{{ t.origen === 'bot' ? '🤖 WhatsApp' : '✍️ Manual' }}</td>
              <td (click)="$event.stopPropagation()">
                <select [class]="'estado-' + t.estado" [ngModel]="t.estado" (ngModelChange)="cambiarEstado(t, $event)">
                  @for (e of estados; track e) { <option [value]="e">{{ e }}</option> }
                </select>
              </td>
            </tr>
          }
        </tbody>
      </table>
    } @else {
      <p class="vacio">No hay turnos.</p>
    }
  `,
})
export class TablaTurnos {
  private readonly api = inject(Api);
  private readonly router = inject(Router);
  readonly turnos = input.required<Turno[]>();
  readonly cambiado = output<void>();
  readonly estados = ESTADOS_TURNO;

  abrir(t: Turno) {
    this.router.navigate(['/pacientes', t.paciente.id]);
  }

  async cambiarEstado(t: Turno, estado: EstadoTurno) {
    await this.api.actualizarTurno(t.id, { estado });
    this.cambiado.emit();
  }
}
