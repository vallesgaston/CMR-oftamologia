import { computed, inject, Injectable, signal } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

const CLAVE = 'adminToken';

function leerToken(): string {
  try {
    return localStorage.getItem(CLAVE) ?? '';
  } catch {
    return '';
  }
}

@Injectable({ providedIn: 'root' })
export class Auth {
  readonly token = signal(leerToken());
  readonly logueado = computed(() => !!this.token());

  login(token: string): void {
    localStorage.setItem(CLAVE, token);
    this.token.set(token);
  }

  logout(): void {
    localStorage.removeItem(CLAVE);
    this.token.set('');
  }
}

export const authGuard: CanActivateFn = () =>
  inject(Auth).logueado() || inject(Router).createUrlTree(['/login']);
