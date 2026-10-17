import { DatePipe } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../../core/api';
import { Campania, Turno } from '../../core/models';
import { hoyISO, sumarDias } from '../../core/util';
import { FormTurno } from '../../shared/form-turno';
import { TablaTurnos } from '../../shared/tabla-turnos';

@Component({
  selector: 'app-agenda',
  imports: [DatePipe, FormsModule, TablaTurnos, FormTurno],
  template: `
    <div class="toolbar">
      <button class="ghost" (click)="mover(-1)">◀</button>
      <input type="date" [ngModel]="fecha()" (ngModelChange)="fecha.set($event); cargar()" />
      <button class="ghost" (click)="mover(1)">▶</button>
      <button class="ghost" (click)="fecha.set(hoy()); cargar()">Hoy</button>
      <span class="spacer"></span>
      @if (diaCompleto()) {
        <span class="error">Día completo ({{ limite() }} turnos)</span>
      }
      <button [disabled]="diaCompleto()" (click)="nuevo.set(true)">
        + Nuevo turno
      </button>
    </div>

    <div class="agenda-layout">
      <div class="agenda-calendar">
        <div class="calendar-legend">
          <span class="legend-item"><span class="legend-swatch disponible"></span>Disponible (campaña)</span>
          <span class="legend-item"><span class="legend-swatch has-turno"></span>Con turno</span>
          <span class="legend-item"><span class="legend-swatch completo"></span>Completo</span>
        </div>
        <div class="calendar-header">
          <span>L</span>
          <span>M</span>
          <span>M</span>
          <span>J</span>
          <span>V</span>
          <span>S</span>
          <span>D</span>
        </div>
        <div class="calendar-grid">
          @for (d of diasDelMes(); track d.key) {
            <button
              type="button"
              class="calendar-day"
              [class.empty]="d.empty"
              [class.disponible]="d.campanias.length > 0"
              [class.has-turno]="d.hasTurno"
              [class.completo]="d.completo"
              [title]="d.campanias.join(', ')"
              [class.is-selected]="d.iso === fecha()"
              [disabled]="d.empty"
              (click)="seleccionarDia(d.iso)"
            >
              <span>{{ d.label }}</span>
            </button>
          }
        </div>
      </div>

      <section class="agenda-dia">
        <h2>Turnos del {{ fecha() | date: "EEEE d 'de' MMMM" }} <span class="hint">({{ activosDelDia() }}{{ limite() ? ' de ' + limite() : '' }})</span></h2>
        <app-tabla-turnos [turnos]="turnos()" (cambiado)="cargar()" />
      </section>
    </div>

    @if (nuevo()) {
      <app-form-turno
        [fechaInicial]="fecha()"
        [pacienteNuevo]="true"
        (cerrar)="nuevo.set(false)"
        (guardado)="nuevo.set(false); cargar()"
      />
    }
  `,
})
export class Agenda implements OnInit {
  private readonly api = inject(Api);
  readonly hoy = hoyISO;
  readonly fecha = signal(hoyISO());
  readonly turnos = signal<Turno[]>([]);
  readonly turnosMes = signal<Turno[]>([]);
  readonly campanias = signal<Campania[]>([]);
  readonly nuevo = signal(false);
  readonly limite = signal(0);
  readonly diasConTurnos = computed(() => {
    const set = new Set<string>();
    for (const turno of this.turnosMes()) {
      const fecha = new Date(turno.fecha_hora);
      const iso = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}-${String(fecha.getDate()).padStart(2, '0')}`;
      set.add(iso);
    }
    return set;
  });
  /** Turnos no cancelados por día: son los que ocupan cupo. */
  readonly activosPorDia = computed(() => {
    const cuenta = new Map<string, number>();
    for (const turno of this.turnosMes()) {
      if (turno.estado === 'cancelado') continue;
      const iso = turno.fecha_hora.slice(0, 10);
      cuenta.set(iso, (cuenta.get(iso) ?? 0) + 1);
    }
    return cuenta;
  });
  readonly activosDelDia = computed(() => this.turnos().filter((t) => t.estado !== 'cancelado').length);
  /** Con el día lleno no se deja abrir la carga (los cancelados no ocupan cupo). */
  readonly diaCompleto = computed(() => this.limite() > 0 && this.activosDelDia() >= this.limite());

  ngOnInit() {
    this.cargar();
    this.cargarCampanias();
    this.api.limiteTurnos().then((r) => this.limite.set(r.max_turnos_dia));
  }

  async cargarCampanias() {
    this.campanias.set((await this.api.campanias()).filter((c) => c.activa));
  }

  /** Títulos de las campañas activas que cubren ese día (sin fecha de fin = abierta). */
  private campaniasDelDia(iso: string) {
    return this.campanias()
      .filter((c) => c.fecha_inicio <= iso && (!c.fecha_fin || iso <= c.fecha_fin))
      .map((c) => c.titulo);
  }

  mover(dias: number) {
    this.fecha.set(sumarDias(this.fecha(), dias));
    this.cargar();
  }

  seleccionarDia(iso: string | null) {
    if (!iso) return;
    this.fecha.set(iso);
    this.cargar();
  }

  diasDelMes() {
    const base = new Date(this.fecha() + 'T12:00');
    const year = base.getFullYear();
    const month = base.getMonth();
    const primerDia = new Date(year, month, 1);
    const ultimoDia = new Date(year, month + 1, 0);
    const inicioOffset = (primerDia.getDay() + 6) % 7;
    const cells: Array<{
      key: string;
      iso: string | null;
      label: string;
      hasTurno: boolean;
      completo: boolean;
      campanias: string[];
      empty: boolean;
    }> = [];

    for (let i = 0; i < inicioOffset; i++) {
      cells.push({
        key: `empty-${i}`,
        iso: null,
        label: '',
        hasTurno: false,
        completo: false,
        campanias: [],
        empty: true,
      });
    }

    for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
      const d = new Date(year, month, dia);
      const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      cells.push({
        key: iso,
        iso,
        label: String(dia),
        hasTurno: this.diasConTurnos().has(iso),
        completo: this.limite() > 0 && (this.activosPorDia().get(iso) ?? 0) >= this.limite(),
        campanias: this.campaniasDelDia(iso),
        empty: false,
      });
    }

    while (cells.length % 7 !== 0) {
      cells.push({
        key: `after-${cells.length}`,
        iso: null,
        label: '',
        hasTurno: false,
        completo: false,
        campanias: [],
        empty: true,
      });
    }

    return cells;
  }

  async cargar() {
    const base = new Date(this.fecha() + 'T12:00');
    const year = base.getFullYear();
    const month = base.getMonth();
    const desdeMes = new Date(year, month, 1);
    const hastaMes = new Date(year, month + 1, 0);
    const [mes, dia] = await Promise.all([
      this.api.turnos(this.toISODate(desdeMes), true, this.toISODate(hastaMes)),
      this.api.turnos(this.fecha(), true),
    ]);
    this.turnosMes.set(mes);
    this.turnos.set(dia);
  }

  private toISODate(date: Date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }
}
