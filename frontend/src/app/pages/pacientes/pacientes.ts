import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { Api } from '../../core/api';
import { Paciente } from '../../core/models';
import { NombrePacPipe } from '../../core/util';
import { FormPaciente } from '../../shared/form-paciente';

@Component({
  selector: 'app-pacientes',
  imports: [FormsModule, NombrePacPipe, FormPaciente],
  template: `
    <div class="toolbar">
      <input class="grow" placeholder="Buscar por nombre, DNI o teléfono" [ngModel]="q()" (ngModelChange)="buscar($event)">
      <button (click)="nuevo.set(true)">+ Nuevo paciente</button>
    </div>

    @if (pacientes().length) {
      <table>
        <thead><tr><th>Paciente</th><th>DNI</th><th>Teléfono</th><th>Obra social</th></tr></thead>
        <tbody>
          @for (p of pacientes(); track p.id) {
            <tr class="click" (click)="abrir(p)">
              <td>{{ p | nombrePac }}</td><td>{{ p.dni }}</td><td>{{ p.telefono }}</td><td>{{ p.obra_social }}</td>
            </tr>
          }
        </tbody>
      </table>
    } @else {
      <p class="vacio">Sin resultados.</p>
    }

    @if (nuevo()) {
      <app-form-paciente (cerrar)="nuevo.set(false)" (guardado)="abrir($event)" />
    }
  `,
})
export class Pacientes implements OnInit {
  private readonly api = inject(Api);
  private readonly router = inject(Router);
  readonly q = signal('');
  readonly pacientes = signal<Paciente[]>([]);
  readonly nuevo = signal(false);
  private timer?: ReturnType<typeof setTimeout>;

  ngOnInit() {
    this.cargar();
  }

  buscar(q: string) {
    this.q.set(q);
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.cargar(), 250);
  }

  async cargar() {
    this.pacientes.set(await this.api.pacientes(this.q()));
  }

  abrir(p: Paciente) {
    this.router.navigate(['/pacientes', p.id]);
  }
}
