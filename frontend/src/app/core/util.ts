import { Pipe, PipeTransform } from '@angular/core';

import { PacienteMini } from './models';

const local = (d = new Date()) => {
  const copia = new Date(d);
  copia.setMinutes(copia.getMinutes() - copia.getTimezoneOffset());
  return copia.toISOString();
};

export const hoyISO = () => local().slice(0, 10);
export const ahoraLocalISO = () => local().slice(0, 16);

export function sumarDias(fechaISO: string, dias: number): string {
  const d = new Date(fechaISO + 'T12:00');
  d.setDate(d.getDate() + dias);
  return local(d).slice(0, 10);
}

/** Convierte los strings vacíos de un formulario en null (la API los espera así). */
export function limpiar<T extends object>(obj: T): T {
  const salida: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(obj)) salida[k] = v === '' || v === undefined ? null : v;
  return salida as T;
}

export const nombrePac = (p: PacienteMini | null | undefined) =>
  p ? (p.apellido ? `${p.apellido}, ${p.nombre}` : p.nombre) : '';

@Pipe({ name: 'nombrePac' })
export class NombrePacPipe implements PipeTransform {
  transform(p: PacienteMini | null | undefined): string {
    return nombrePac(p);
  }
}

/** Formato de WhatsApp (*negrita* y saltos de línea) a HTML seguro. */
@Pipe({ name: 'whatsapp' })
export class WhatsappPipe implements PipeTransform {
  transform(texto: string): string {
    const escapado = texto.replace(/[&<>"']/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!,
    );
    return escapado.replace(/\*(.+?)\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
  }
}
