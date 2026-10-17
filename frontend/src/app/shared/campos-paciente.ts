import { Component, input } from '@angular/core';
import { ControlContainer, FormsModule, NgForm } from '@angular/forms';

import { Paciente } from '../core/models';

/** Campos de la ficha del paciente; se registran en el <form> del componente padre. */
@Component({
  selector: 'app-campos-paciente',
  imports: [FormsModule],
  viewProviders: [{ provide: ControlContainer, useExisting: NgForm }],
  host: { class: 'grid2' },
  template: `
    <label>Nombre <input name="nombre" [(ngModel)]="modelo().nombre" required></label>
    <label>Apellido <input name="apellido" [(ngModel)]="modelo().apellido"></label>
    <label>DNI <input name="dni" [(ngModel)]="modelo().dni"></label>
    <label>Teléfono / WhatsApp <input name="telefono" [(ngModel)]="modelo().telefono" placeholder="5491122334455"></label>
    <label>Email <input type="email" name="email" [(ngModel)]="modelo().email"></label>
    <label>Fecha de nacimiento <input type="date" name="fecha_nacimiento" [(ngModel)]="modelo().fecha_nacimiento"></label>
    <label>Obra social <input name="obra_social" [(ngModel)]="modelo().obra_social"></label>
    <label>N° de afiliado <input name="nro_afiliado" [(ngModel)]="modelo().nro_afiliado"></label>
    <label class="full">Notas <textarea name="notas" [(ngModel)]="modelo().notas"></textarea></label>
  `,
})
export class CamposPaciente {
  readonly modelo = input.required<Partial<Paciente>>();
}
