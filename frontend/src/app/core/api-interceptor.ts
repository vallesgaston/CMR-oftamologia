import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { Auth } from './auth';

/** Agrega el token a cada request y muestra los errores de la API. */
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(Auth);
  const router = inject(Router);

  return next(req.clone({ setHeaders: { 'X-Admin-Token': auth.token() } })).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401) {
        auth.logout();
        router.navigate(['/login']);
      } else {
        const detalle = err.error?.detail;
        const texto = typeof detalle === 'string' ? detalle : detalle ? JSON.stringify(detalle) : err.message;
        alert('Error: ' + texto);
      }
      return throwError(() => err);
    }),
  );
};
