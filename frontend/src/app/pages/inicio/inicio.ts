import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Api } from '../../core/api';
import { Resumen, Turno } from '../../core/models';
import { hoyISO } from '../../core/util';
import { TablaTurnos } from '../../shared/tabla-turnos';

@Component({
  selector: 'app-inicio',
  imports: [RouterLink, TablaTurnos],
  template: `
    @if (resumen(); as r) {
      <div class="cards">
        <a class="card" routerLink="/agenda"><div class="num">{{ r.turnos_hoy }}</div>Turnos hoy</a>
        <a class="card" routerLink="/anteojos"><div class="num">{{ r.anteojos_listos }}</div>Anteojos listos p/ retirar</a>
        <a class="card" routerLink="/anteojos"><div class="num">{{ r.anteojos_en_laboratorio }}</div>Anteojos en laboratorio</a>
        <a class="card" routerLink="/conversaciones"><div class="num">{{ r.conversaciones_pendientes }}</div>Chats esperando respuesta</a>
        <a class="card" routerLink="/campanias"><div class="num">{{ r.campanias_activas }}</div>Campañas activas</a>
        <a class="card" routerLink="/pacientes"><div class="num">{{ r.pacientes }}</div>Pacientes</a>
      </div>
    }
    <h2>Turnos de hoy</h2>
    <app-tabla-turnos [turnos]="turnos()" (cambiado)="cargar()" />
  `,
})
export class Inicio implements OnInit {
  private readonly api = inject(Api);
  readonly resumen = signal<Resumen | null>(null);
  readonly turnos = signal<Turno[]>([]);

  ngOnInit() {
    this.cargar();
  }

  async cargar() {
    const [r, t] = await Promise.all([this.api.resumen(), this.api.turnos(hoyISO())]);
    this.resumen.set(r);
    this.turnos.set(t);
  }
}
