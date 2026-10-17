import { Component, ElementRef, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { Api } from '../../core/api';
import { Auth } from '../../core/auth';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  template: `
    <div class="login">
      <form (ngSubmit)="entrar()">
        <h1>👁️ Labatte Oftalmología</h1>
        <label>
          Token de administrador
          <div class="password-wrap">
            <input
              #tokenInput
              [type]="mostrarPassword() ? 'text' : 'password'"
              name="token"
              [ngModel]="token()"
              (ngModelChange)="token.set($event)"
              required
              autofocus
            />
            <button
              type="button"
              class="toggle-password"
              (mousedown)="$event.preventDefault()"
              (click)="togglePassword()"
              aria-label="Mostrar u ocultar contraseña"
            >
              @if (mostrarPassword()) {
                <svg class="toggle-password-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M3.5 12.5c2.7-4.2 6.2-6.3 10.5-6.3s7.8 2.1 10.5 6.3c-2.7 4.2-6.2 6.3-10.5 6.3S6.2 16.7 3.5 12.5Zm10.5 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"
                  />
                  <path d="M3 3l18 18" />
                </svg>
              } @else {
                <svg class="toggle-password-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M2 12c2.7-4.2 6.2-6.3 10.5-6.3S21.3 7.8 24 12c-2.7 4.2-6.2 6.3-10.5 6.3S4.7 16.2 2 12Z"
                  />
                  <circle cx="12" cy="12" r="3.3" />
                </svg>
              }
            </button>
          </div>
        </label>
        <p class="hint">Es el valor de <code>ADMIN_TOKEN</code> en el archivo <code>.env</code>.</p>
        @if (error()) {
          <p class="error">{{ error() }}</p>
        }
        <button [disabled]="!token() || cargando()">Entrar</button>
      </form>
    </div>
  `,
})
export class Login {
  private readonly auth = inject(Auth);
  private readonly api = inject(Api);
  private readonly router = inject(Router);
  readonly token = signal('');
  readonly error = signal('');
  readonly cargando = signal(false);
  readonly mostrarPassword = signal(false);
  readonly tokenInput = viewChild<ElementRef<HTMLInputElement>>('tokenInput');

  togglePassword() {
    this.mostrarPassword.set(!this.mostrarPassword());
    queueMicrotask(() => this.tokenInput()?.nativeElement?.focus());
  }

  async entrar() {
    this.cargando.set(true);
    this.error.set('');
    this.auth.login(this.token());
    try {
      await this.api.resumen();
      this.router.navigate(['/']);
    } catch {
      this.error.set('Token inválido o la API no responde (¿está levantado Docker?).');
    } finally {
      this.cargando.set(false);
    }
  }
}
