// Reproducción automática de una secuencia ligada al scroll: mueve la PÁGINA (no solo la imagen) a
// velocidad constante, para que el texto de cada escena, el índice y la barra sigan sincronizados y el
// usuario pueda retomar el control en cualquier momento con la rueda, el touch o el teclado.
//  - reproducir(): avanza hasta el final con pausas en cada escena de producto;
//  - irA(+1 | -1): avanza o retrocede a la misma velocidad hasta la escena vecina y se detiene ahí.

export type Estado = 'detenido' | 'reproduciendo' | 'navegando';

interface Opciones {
  total: number;
  /** Posición de scroll (px) para un índice de frame (0-based, puede ser fraccionario). */
  aScroll: (indice: number) => number;
  /** Índice de frame que muestra hoy el scroll. */
  indiceActual: () => number;
  /** Índices donde se detiene "adelante/atrás" (centro de cada escena), en orden. */
  escenas: number[];
  /** Índices donde la reproducción hace una pausa (escenas con productos). */
  pausas: number[];
  /** Tras mover el scroll, en el mismo cuadro (ScrollTrigger.update). */
  alMover: () => void;
  alCambiarEstado: (estado: Estado) => void;
  /**
   * Frames por segundo de avance; se consulta en cada cuadro, así puede subir en equipos rápidos y
   * bajar si las imágenes del tramo que viene aún no llegan (recibe la posición y el sentido).
   */
  velocidad?: (posicion: number, sentido: number) => number;
  /** Segundos de pausa en cada escena de producto. */
  pausa?: number;
}

export class Reproductor {
  estado: Estado = 'detenido';
  /** Velocidad máxima usada en el último cuadro (para el medidor ?fps). */
  ultimaMaxima = 0;
  private posicion = 0;
  private velocidadActual = 0;
  private destino = 0;
  private pausaHasta = 0;
  private pausadas = new Set<number>();
  private ultimoTick = 0;
  private ultimoScroll = -1;
  private readonly velocidad: (posicion: number, sentido: number) => number;
  private readonly pausa: number;

  constructor(private o: Opciones) {
    this.velocidad = o.velocidad ?? (() => 42);
    this.pausa = o.pausa ?? 3;
    // El usuario toma el control: rueda, touch o teclas de desplazamiento detienen la reproducción.
    const tomarControl = () => this.estado !== 'detenido' && this.detener();
    window.addEventListener('wheel', tomarControl, { passive: true, capture: true });
    window.addEventListener('touchstart', tomarControl, { passive: true });
    window.addEventListener('keydown', (e) => {
      if ((e.target as HTMLElement | null)?.closest?.('button, a, input, textarea')) return; // Espacio/Enter sobre los propios controles
      if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(e.key)) tomarControl();
    });
  }

  /** Reproduce desde donde está hasta el final, con pausas en las escenas de producto. */
  reproducir() {
    let desde = this.o.indiceActual();
    if (desde >= this.o.total - 1.5) desde = 0; // al final: vuelve a empezar
    // no repetir la pausa de la escena en la que ya está detenido
    this.pausadas = new Set(this.o.pausas.filter((p) => p <= desde + 0.5));
    this.iniciar('reproduciendo', desde, this.o.total - 1);
  }

  /** Avanza (+1) o retrocede (-1) a la escena vecina a la misma velocidad. */
  irA(sentido: 1 | -1) {
    // si ya iba hacia una escena en ese sentido, la siguiente se cuenta desde ese destino
    const base = this.estado === 'navegando' && Math.sign(this.destino - this.posicion) === sentido ? this.destino : this.o.indiceActual();
    const escena =
      sentido > 0 ? this.o.escenas.find((e) => e > base + 0.5) : [...this.o.escenas].reverse().find((e) => e < base - 0.5);
    if (escena === undefined) return;
    if (this.estado === 'navegando') this.destino = escena;
    else this.iniciar('navegando', this.o.indiceActual(), escena);
  }

  detener() {
    this.cambiar('detenido');
  }

  private iniciar(estado: Estado, desde: number, destino: number) {
    const enMarcha = this.estado !== 'detenido';
    this.posicion = desde;
    this.destino = destino;
    this.pausaHasta = 0;
    if (!enMarcha) this.velocidadActual = 0;
    this.cambiar(estado);
    if (Math.abs(window.scrollY - this.o.aScroll(desde)) > 2) this.moverScroll();
    this.ultimoScroll = window.scrollY;
    if (!enMarcha) {
      this.ultimoTick = performance.now();
      requestAnimationFrame((t) => this.tick(t));
    }
  }

  private cambiar(estado: Estado) {
    if (estado === this.estado) return;
    this.estado = estado;
    this.o.alCambiarEstado(estado);
  }

  private moverScroll() {
    // 'instant': el CSS global tiene scroll-behavior: smooth
    window.scrollTo({ top: this.o.aScroll(this.posicion), behavior: 'instant' });
    this.ultimoScroll = window.scrollY;
    this.o.alMover();
  }

  private tick(t: number) {
    if (this.estado === 'detenido') return;
    // Si la página se movió por otro medio (barra, enlace), el usuario tomó el control.
    if (this.ultimoScroll >= 0 && Math.abs(window.scrollY - this.ultimoScroll) > 2) return this.detener();
    const dt = Math.min(0.1, (t - this.ultimoTick) / 1000);
    this.ultimoTick = t;

    if (t < this.pausaHasta) {
      requestAnimationFrame((s) => this.tick(s));
      return;
    }

    // Próxima parada en el camino: la pausa de producto más cercana (al reproducir) o el destino.
    const sentido = Math.sign(this.destino - this.posicion) || 1;
    let parada = this.destino;
    if (this.estado === 'reproduciendo') {
      // ">= posición": al frenar se queda a centésimas de la parada y debe seguir contando como pendiente
      const p = this.o.pausas.find((x) => x >= this.posicion - 0.001 && x < this.destino && !this.pausadas.has(x));
      if (p !== undefined) parada = p;
    }
    const distancia = Math.abs(parada - this.posicion);
    // velocidad constante con arranque y frenado suaves (~0,45 s): v ≤ √(2·a·d) para llegar justo a la parada
    const maxima = this.velocidad(this.posicion, sentido);
    this.ultimaMaxima = maxima;
    const aceleracion = Math.max(maxima, 42) / 0.45;
    const frenando = this.velocidadActual > maxima;
    this.velocidadActual = Math.min(
      frenando ? Math.max(maxima, this.velocidadActual - aceleracion * dt) : Math.min(maxima, this.velocidadActual + aceleracion * dt),
      Math.sqrt(2 * aceleracion * distancia) + 0.5,
    );
    const paso = this.velocidadActual * dt;

    if (paso >= distancia) {
      this.posicion = parada;
      this.velocidadActual = 0;
      this.moverScroll();
      if (parada === this.destino) return this.detener();
      this.pausadas.add(parada);
      this.pausaHasta = t + this.pausa * 1000;
    } else {
      this.posicion += paso * sentido;
      this.moverScroll();
    }
    requestAnimationFrame((s) => this.tick(s));
  }
}
