import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../../core/api';
import { ESTADOS_PEDIDO, Pedido } from '../../core/models';
import { TablaPedidos } from '../../shared/tabla-pedidos';

@Component({
  selector: 'app-anteojos',
  imports: [FormsModule, TablaPedidos],
  template: `
    <div class="toolbar">
      <select [ngModel]="filtro()" (ngModelChange)="filtro.set($event); cargar()">
        <option value="">En curso</option>
        @for (e of estados; track e.valor) { <option [value]="e.valor">{{ e.texto }}</option> }
        <option value="todos">Todos</option>
      </select>
      <span class="hint">Al pasar un pedido a <b>Listo</b> se avisa al paciente por WhatsApp.
        Los pedidos nuevos se cargan desde la ficha del paciente.</span>
    </div>
    <app-tabla-pedidos [pedidos]="pedidos()" (cambiado)="cargar()" />
  `,
})
export class Anteojos implements OnInit {
  private readonly api = inject(Api);
  readonly estados = ESTADOS_PEDIDO;
  readonly filtro = signal('');
  readonly pedidos = signal<Pedido[]>([]);

  ngOnInit() {
    this.cargar();
  }

  async cargar() {
    this.pedidos.set(await this.api.pedidos(this.filtro()));
  }
}
