import { DatePipe } from '@angular/common';
import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../core/api';
import { Paciente, PacienteMini } from '../core/models';
import { hoyISO, limpiar, NombrePacPipe } from '../core/util';
import { CamposPaciente } from './campos-paciente';
import { Modal } from './modal';

@Component({
  selector: 'app-form-turno',
  imports: [DatePipe, FormsModule, Modal, NombrePacPipe, CamposPaciente],
  template: `
    <app-modal titulo="Nuevo turno" (cerrar)="cerrar.emit()">
      <form #f="ngForm" (ngSubmit)="guardar()">
        @if (!paciente()) {
          <div class="acciones selector-paciente">
            <button type="button" [class.ghost]="!creandoPaciente()" (click)="creandoPaciente.set(true)">
              Paciente nuevo
            </button>
            <button type="button" [class.ghost]="creandoPaciente()" (click)="creandoPaciente.set(false)">
              Paciente existente
            </button>
          </div>

          @if (creandoPaciente()) {
            <app-campos-paciente [modelo]="nuevoPaciente" />
          } @else {
            <label>
              Buscar paciente
              <input
                name="busqueda"
                [ngModel]="busqueda()"
                (ngModelChange)="buscar($event)"
                placeholder="Nombre, apellido o DNI"
              />
            </label>
            <label>
              Paciente
              <select name="paciente_id" [(ngModel)]="pacienteId" required>
                @for (p of candidatos(); track p.id) {
                  <option [ngValue]="p.id">
                    {{ p | nombrePac }}{{ p.dni ? ' — DNI ' + p.dni : '' }}
                  </option>
                } @empty {
                  <option [ngValue]="null">— buscá arriba —</option>
                }
              </select>
            </label>
          }
        }

        <div class="grid2">
          <label>
            Fecha
            <input
              type="date"
              name="fecha"
              [ngModel]="fecha"
              (ngModelChange)="fecha = $event; cargarHorarios()"
              required
            />
          </label>
          <label>
            Horario
            <select name="fecha_hora" [(ngModel)]="fechaHora" required>
              @for (h of horarios; track h) {
                <option [value]="h">{{ h | date: 'HH:mm' }}</option>
              } @empty {
                <option value="">Sin horarios libres</option>
              }
            </select>
          </label>
        </div>
        <label>
          Motivo
          <input name="motivo" [(ngModel)]="motivo" placeholder="Control, fondo de ojo, receta…" />
        </label>
        <button type="submit" [disabled]="f.invalid || guardando() || (!creandoPaciente() && !pacienteId)">
          {{ creandoPaciente() ? 'Guardar paciente y turno' : 'Guardar turno' }}
        </button>
      </form>
    </app-modal>
  `,
})
export class FormTurno implements OnInit {
  private readonly api = inject(Api);
  readonly paciente = input<PacienteMini | null>(null);
  readonly fechaInicial = input(hoyISO());
  /** Si arranca mostrando el alta de paciente (desde la agenda) o el buscador. */
  readonly pacienteNuevo = input(false);
  readonly guardado = output<void>();
  readonly cerrar = output<void>();

  readonly busqueda = signal('');
  readonly candidatos = signal<PacienteMini[]>([]);
  readonly creandoPaciente = signal(false);
  pacienteId: number | null = null;
  fecha = hoyISO();
  horarios: string[] = [];
  fechaHora = '';
  motivo = '';
  nuevoPaciente: Partial<Paciente> = {};
  /** Paciente ya creado en un intento anterior cuyo turno falló: no se vuelve a crear. */
  private pacienteCreado: Paciente | null = null;
  readonly guardando = signal(false);
  private timer?: ReturnType<typeof setTimeout>;

  ngOnInit() {
    const p = this.paciente();
    if (p) {
      this.candidatos.set([p]);
      this.pacienteId = p.id;
    } else {
      this.creandoPaciente.set(this.pacienteNuevo());
    }
    this.fecha = this.fechaInicial();
    this.cargarHorarios();
  }

  buscar(q: string) {
    this.busqueda.set(q);
    clearTimeout(this.timer);
    this.timer = setTimeout(async () => {
      const ps = await this.api.pacientes(q);
      this.candidatos.set(ps);
      this.pacienteId = ps[0]?.id ?? null;
    }, 250);
  }

  async cargarHorarios() {
    const hs = await this.api.horariosDisponibles(this.fecha);
    this.horarios = hs;
    this.fechaHora = hs[0] ?? '';
  }

  async guardar() {
    if (!this.fechaHora) return;
    this.guardando.set(true);
    try {
      let pacienteId = this.pacienteId;
      if (this.creandoPaciente()) {
        this.pacienteCreado ??= await this.api.crearPaciente(limpiar(this.nuevoPaciente));
        pacienteId = this.pacienteCreado.id;
      }
      if (!pacienteId) return;
      await this.api.crearTurno({
        paciente_id: pacienteId,
        fecha_hora: this.fechaHora,
        motivo: this.motivo || null,
      });
      this.guardado.emit();
    } finally {
      this.guardando.set(false);
    }
  }
}
