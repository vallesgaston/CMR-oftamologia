import { DatePipe } from '@angular/common';
import { Component, DestroyRef, ElementRef, inject, OnInit, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Api } from '../../core/api';
import { Conversacion, Mensaje } from '../../core/models';
import { WhatsappPipe } from '../../core/util';

@Component({
  selector: 'app-conversaciones',
  imports: [DatePipe, FormsModule, WhatsappPipe],
  templateUrl: './conversaciones.html',
})
export class Conversaciones implements OnInit {
  private readonly api = inject(Api);

  readonly lista = signal<Conversacion[]>([]);
  readonly actual = signal<string | null>(null);
  readonly mensajes = signal<Mensaje[]>([]);
  readonly respuesta = signal('');

  readonly simTel = signal('5491100000001');
  readonly simMensajes = signal<Mensaje[]>([]);
  readonly simTexto = signal('');

  private readonly chatBox = viewChild<ElementRef<HTMLElement>>('chatBox');
  private readonly simBox = viewChild<ElementRef<HTMLElement>>('simBox');

  constructor() {
    const intervalo = setInterval(() => this.cargarLista(), 10000);
    inject(DestroyRef).onDestroy(() => clearInterval(intervalo));
  }

  ngOnInit() {
    this.cargarLista();
    this.refrescarSimulador();
  }

  async cargarLista() {
    this.lista.set(await this.api.conversaciones());
    const tel = this.actual();
    if (tel) this.mostrar(this.chatBox, this.mensajes, await this.api.mensajes(tel));
  }

  async abrir(tel: string) {
    this.actual.set(tel);
    this.mostrar(this.chatBox, this.mensajes, await this.api.mensajes(tel));
  }

  async responder() {
    const tel = this.actual();
    const texto = this.respuesta().trim();
    if (!tel || !texto) return;
    await this.api.responder(tel, texto);
    this.respuesta.set('');
    await this.cargarLista();
    this.refrescarSimulador();
  }

  async liberar() {
    const tel = this.actual();
    if (!tel) return;
    await this.api.liberar(tel);
    this.cargarLista();
  }

  // ---- simulador ----
  private telSimulado = () => this.simTel().replace(/\D/g, '');

  async refrescarSimulador() {
    const tel = this.telSimulado();
    if (tel.length >= 6) this.mostrar(this.simBox, this.simMensajes, await this.api.mensajes(tel));
  }

  async enviarSimulado() {
    const texto = this.simTexto().trim();
    if (!texto) return;
    this.simTexto.set('');
    await this.api.simular(this.telSimulado(), texto);
    await this.refrescarSimulador();
    this.cargarLista();
  }

  private mostrar(caja: () => ElementRef<HTMLElement> | undefined, destino: { set(v: Mensaje[]): void }, ms: Mensaje[]) {
    destino.set(ms);
    // bajar el scroll cuando se renderizaron los mensajes nuevos
    setTimeout(() => {
      const el = caja()?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
}
