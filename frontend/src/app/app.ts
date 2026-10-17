import { Component, DestroyRef, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { Api } from './core/api';
import { Auth } from './core/auth';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    @if (auth.logueado()) {
      <header>
        <h1>👁️ Labatte Oftalmología</h1>
        <nav>
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }"
            >Inicio</a
          >
          <a routerLink="/agenda" routerLinkActive="active">Agenda</a>
          <a routerLink="/pacientes" routerLinkActive="active">Pacientes</a>
          <a routerLink="/anteojos" routerLinkActive="active">Anteojos</a>
          <a routerLink="/campanias" routerLinkActive="active">Campañas</a>
          <a routerLink="/conversaciones" routerLinkActive="active">
            Conversaciones
            @if (api.chatsPendientes()) {
              <span class="badge">{{ api.chatsPendientes() }}</span>
            }
          </a>
        </nav>
        <button class="ghost" (click)="salir()">Salir</button>
      </header>
    }
    <main>
      <router-outlet />
    </main>
  `,
})
export class App {
  protected readonly auth = inject(Auth);
  protected readonly api = inject(Api);
  private readonly router = inject(Router);

  constructor() {
    // Mantiene actualizado el contador de chats pendientes
    const intervalo = setInterval(() => {
      if (this.auth.logueado()) this.api.resumen().catch(() => {});
    }, 30000);
    inject(DestroyRef).onDestroy(() => clearInterval(intervalo));
  }

  salir() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
