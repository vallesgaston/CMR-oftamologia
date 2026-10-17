import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../core/api';
import { Paciente } from '../core/models';
import { limpiar } from '../core/util';
import { CamposPaciente } from './campos-paciente';
import { Modal } from './modal';

@Component({
  selector: 'app-form-paciente',
  imports: [FormsModule, Modal, CamposPaciente],
  template: `
    <app-modal [titulo]="paciente() ? 'Editar paciente' : 'Nuevo paciente'" (cerrar)="cerrar.emit()">
      <form #f="ngForm" (ngSubmit)="guardar()">
        <app-campos-paciente [modelo]="modelo" />
        <button [disabled]="f.invalid || guardando()">Guardar</button>
      </form>
    </app-modal>
  `,
})
export class FormPaciente implements OnInit {
  private readonly api = inject(Api);
  readonly paciente = input<Paciente | null>(null);
  readonly guardado = output<Paciente>();
  readonly cerrar = output<void>();
  readonly guardando = signal(false);
  modelo: Partial<Paciente> = {};

  ngOnInit() {
    const p = this.paciente();
    if (p) {
      const { nombre, apellido, dni, telefono, email, fecha_nacimiento, obra_social, nro_afiliado, notas } = p;
      this.modelo = { nombre, apellido, dni, telefono, email, fecha_nacimiento, obra_social, nro_afiliado, notas };
    }
  }

  async guardar() {
    this.guardando.set(true);
    try {
      const datos = limpiar(this.modelo);
      const p = this.paciente();
      this.guardado.emit(p ? await this.api.actualizarPaciente(p.id, datos) : await this.api.crearPaciente(datos));
    } finally {
      this.guardando.set(false);
    }
  }
}
