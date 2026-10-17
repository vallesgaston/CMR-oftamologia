import { DatePipe } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../../core/api';
import { Campania } from '../../core/models';
import { hoyISO, limpiar } from '../../core/util';
import { Modal } from '../../shared/modal';

@Component({
  selector: 'app-campanias',
  imports: [DatePipe, FormsModule, Modal],
  template: `
    <div class="toolbar">
      <span class="hint">Las campañas activas y vigentes son las que informa el bot (opción 4).</span>
      <span class="spacer"></span>
      <button (click)="abrir()">+ Nueva campaña</button>
    </div>

    @if (campanias().length) {
      <table>
        <thead><tr><th>Campaña</th><th>Vigencia</th><th>Activa</th><th></th></tr></thead>
        <tbody>
          @for (c of campanias(); track c.id) {
            <tr>
              <td><b>{{ c.titulo }}</b><br><span class="hint">{{ c.descripcion }}</span></td>
              <td>{{ c.fecha_inicio | date: 'dd/MM/yyyy' }} → {{ c.fecha_fin ? (c.fecha_fin | date: 'dd/MM/yyyy') : 'sin fin' }}</td>
              <td><input type="checkbox" [checked]="c.activa" (change)="alternar(c)"></td>
              <td class="nowrap">
                <button class="ghost small" (click)="abrir(c)">Editar</button>
                <button class="danger small" (click)="eliminar(c)">Eliminar</button>
              </td>
            </tr>
          }
        </tbody>
      </table>
    } @else {
      <p class="vacio">No hay campañas.</p>
    }

    @if (editando()) {
      <app-modal [titulo]="modelo.id ? 'Editar campaña' : 'Nueva campaña'" (cerrar)="editando.set(false)">
        <form #f="ngForm" (ngSubmit)="guardar()">
          <label>Título <input name="titulo" [(ngModel)]="modelo.titulo" required></label>
          <label>Descripción (es lo que lee el paciente en WhatsApp)
            <textarea name="descripcion" [(ngModel)]="modelo.descripcion"></textarea>
          </label>
          <div class="grid2">
            <label>Desde <input type="date" name="fecha_inicio" [(ngModel)]="modelo.fecha_inicio" required></label>
            <label>Hasta <input type="date" name="fecha_fin" [(ngModel)]="modelo.fecha_fin"></label>
          </div>
          <label class="check"><input type="checkbox" name="activa" [(ngModel)]="modelo.activa"> Activa</label>
          <button [disabled]="f.invalid">Guardar</button>
        </form>
      </app-modal>
    }
  `,
})
export class Campanias implements OnInit {
  private readonly api = inject(Api);
  readonly campanias = signal<Campania[]>([]);
  readonly editando = signal(false);
  modelo: Partial<Campania> = {};

  ngOnInit() {
    this.cargar();
  }

  async cargar() {
    this.campanias.set(await this.api.campanias());
  }

  abrir(c?: Campania) {
    this.modelo = c ? { ...c } : { titulo: '', descripcion: '', fecha_inicio: hoyISO(), fecha_fin: null, activa: true };
    this.editando.set(true);
  }

  async guardar() {
    const { id, ...datos } = limpiar(this.modelo);
    datos.descripcion = datos.descripcion ?? '';
    await (id ? this.api.actualizarCampania(id, datos) : this.api.crearCampania(datos));
    this.editando.set(false);
    this.cargar();
  }

  async alternar(c: Campania) {
    await this.api.actualizarCampania(c.id, { activa: !c.activa });
    this.cargar();
  }

  async eliminar(c: Campania) {
    if (!confirm(`¿Eliminar la campaña "${c.titulo}"?`)) return;
    await this.api.eliminarCampania(c.id);
    this.cargar();
  }
}
