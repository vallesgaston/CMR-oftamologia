import { Routes } from '@angular/router';

import { authGuard } from './core/auth';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./pages/login/login').then((m) => m.Login) },
  {
    path: '',
    canActivate: [authGuard],
    children: [
      { path: '', loadComponent: () => import('./pages/inicio/inicio').then((m) => m.Inicio) },
      { path: 'agenda', loadComponent: () => import('./pages/agenda/agenda').then((m) => m.Agenda) },
      { path: 'pacientes', loadComponent: () => import('./pages/pacientes/pacientes').then((m) => m.Pacientes) },
      {
        path: 'pacientes/:id',
        loadComponent: () => import('./pages/paciente-detalle/paciente-detalle').then((m) => m.PacienteDetalle),
      },
      { path: 'anteojos', loadComponent: () => import('./pages/anteojos/anteojos').then((m) => m.Anteojos) },
      { path: 'campanias', loadComponent: () => import('./pages/campanias/campanias').then((m) => m.Campanias) },
      {
        path: 'conversaciones',
        loadComponent: () => import('./pages/conversaciones/conversaciones').then((m) => m.Conversaciones),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
