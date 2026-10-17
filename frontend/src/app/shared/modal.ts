import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-modal',
  host: { '(document:keydown.escape)': 'cerrar.emit()' },
  template: `
    <div class="overlay">
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          <h2>{{ titulo() }}</h2>
          <button type="button" class="ghost" (click)="cerrar.emit()" aria-label="Cerrar">✕</button>
        </div>
        <ng-content />
      </div>
    </div>
  `,
})
export class Modal {
  readonly titulo = input.required<string>();
  readonly cerrar = output<void>();
}
