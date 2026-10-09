// Secuencia de imágenes dibujada en canvas para animaciones ligadas al scroll, optimizada para equipos
// modestos (sin tarjeta gráfica) y móviles:
//  - el canvas nunca es más grande que el frame original (el CSS escala; dibujar de más es CPU perdida);
//  - los frames se guardan comprimidos (Blob, ~100 KB) y solo una VENTANA alrededor de la posición
//    actual se decodifica como ImageBitmap ya escalado al tamaño de dibujo (drawImage sin reescalar);
//  - un único ciclo de dibujo (requestAnimationFrame) acerca suavemente el frame mostrado al que pide
//    el scroll y pinta en ese mismo cuadro: la rueda del mouse, la barra y el touch se ven igual de
//    fluidos (antes, con Lenis, la rueda congelaba ~47 % de los cuadros por un desfase de un cuadro).

export type Ajuste = 'cover' | 'contain';

interface Opciones {
  /** Frames decodificados hacia adelante en el sentido del scroll. */
  adelante?: number;
  /** Frames decodificados hacia atrás. */
  atras?: number;
  /**
   * Suavizado de la animación hacia el frame pedido (segundos para recorrer ~63 % de la distancia).
   * 0 = sin suavizado (cuando quien llama ya suaviza, p. ej. un scrub de GSAP).
   */
  suavizado?: number;
}

export class SecuenciaFrames {
  private blobs: (Blob | undefined)[];
  private bitmaps = new Map<number, ImageBitmap>();
  private decodificando = new Set<number>();
  private descargando = new Set<number>();
  private ctx: CanvasRenderingContext2D;
  private posicion = 0;
  private objetivo = 0;
  private dibujada = -1;
  private sentido = 1;
  private enCiclo = false;
  private ultimoTick = 0;
  private readonly suavizado: number;
  private cargando = false;
  private anchoFrame = 0;
  private altoFrame = 0;
  private generacion = 0; // cambia al redimensionar: invalida bitmaps escalados al tamaño anterior
  private readonly adelante: number;
  private readonly atras: number;
  /** Estadísticas para pruebas (/?fps): cuadros pintados con el frame exacto vs. con uno aproximado. */
  readonly estadisticas = { exactos: 0, aproximados: 0, ultimoPintado: 0 };

  constructor(
    private canvas: HTMLCanvasElement,
    private urlFrame: (i: number) => string,
    readonly total: number,
    private ajuste: () => Ajuste = () => 'cover',
    opciones: Opciones = {},
  ) {
    this.blobs = new Array(total);
    this.ctx = canvas.getContext('2d', { alpha: false })!;
    const movil = window.matchMedia('(max-width: 900px)').matches;
    this.adelante = opciones.adelante ?? (movil ? 16 : 28);
    this.atras = opciones.atras ?? (movil ? 6 : 10);
    // Sin excepción por "reducir movimiento": solo interpola el movimiento que pide el propio scroll.
    this.suavizado = opciones.suavizado ?? 0.12;
    window.addEventListener('resize', () => this.ajustarTamano());
  }

  /** Pide ir a la posición `i` (puede ser fraccionaria). El ciclo de dibujo llega a ella suavemente. */
  dibujar(i: number) {
    const nuevo = Math.max(0, Math.min(this.total - 1, i));
    if (nuevo !== this.objetivo) this.sentido = nuevo > this.objetivo ? 1 : -1;
    this.objetivo = nuevo;
    this.decodificarVentana();
    if (!this.enCiclo) {
      this.enCiclo = true;
      this.ultimoTick = performance.now();
      requestAnimationFrame((t) => this.tick(t));
    }
  }

  /** Vuelve a pintar la posición actual (p. ej. al llegar un frame decodificado) sin tocar el objetivo. */
  private repintar() {
    this.dibujada = -1;
    if (!this.enCiclo) {
      this.enCiclo = true;
      this.ultimoTick = performance.now();
      requestAnimationFrame((t) => this.tick(t));
    }
  }

  /** Un cuadro del ciclo: acerca la posición al objetivo (independiente de los fps) y pinta ya. */
  private tick(t: number) {
    const dt = Math.min(0.1, (t - this.ultimoTick) / 1000);
    this.ultimoTick = t;
    const restante = this.objetivo - this.posicion;
    if (this.suavizado > 0 && Math.abs(restante) > 0.004) {
      this.posicion += restante * (1 - Math.exp(-dt / this.suavizado));
    } else {
      this.posicion = this.objetivo;
    }
    this.decodificarVentana();
    this.pintarCuadro();
    if (this.posicion !== this.objetivo) requestAnimationFrame((s) => this.tick(s));
    else this.enCiclo = false;
  }

  // ---------------------------------------------------------------- dibujo

  private pintarCuadro() {
    if (Math.abs(this.posicion - this.dibujada) < 0.002) return;
    const a = Math.floor(this.posicion);
    const fraccion = this.posicion - a;
    const bmpA = this.bitmaps.get(a);
    const bmpB = this.bitmaps.get(Math.min(a + 1, this.total - 1));
    const cercano = bmpA ?? this.masCercano(Math.round(this.posicion));
    if (!cercano) return;
    const { width: cw, height: ch } = this.canvas;
    if (this.ajuste() === 'contain') {
      this.ctx.fillStyle = '#000';
      this.ctx.fillRect(0, 0, cw, ch);
    }
    this.ctx.drawImage(cercano, (cw - cercano.width) / 2, (ch - cercano.height) / 2);
    if (bmpA && bmpB && fraccion > 0.02) {
      this.ctx.globalAlpha = fraccion;
      this.ctx.drawImage(bmpB, (cw - bmpB.width) / 2, (ch - bmpB.height) / 2);
      this.ctx.globalAlpha = 1;
    }
    this.dibujada = bmpA ? this.posicion : -1;
    if (bmpA) this.estadisticas.exactos++;
    else this.estadisticas.aproximados++;
    this.estadisticas.ultimoPintado = this.posicion;
  }

  private masCercano(i: number) {
    for (let d = 1; d < this.total; d++) {
      const b = this.bitmaps.get(i - d) ?? this.bitmaps.get(i + d);
      if (b) return b;
    }
    return undefined;
  }

  // ---------------------------------------------------------------- tamaño

  /**
   * Canvas al tamaño en pantalla × DPR, reducido si así el frame se dibujaría ampliado: nunca se dibujan
   * más píxeles de los que trae la imagen (el CSS escala el canvas al tamaño en pantalla).
   */
  private ajustarTamano() {
    if (!this.anchoFrame) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const cw = this.canvas.clientWidth * dpr;
    const ch = this.canvas.clientHeight * dpr;
    const sx = cw / this.anchoFrame;
    const sy = ch / this.altoFrame;
    const ampliacion = this.ajuste() === 'cover' ? Math.max(sx, sy) : Math.min(sx, sy);
    const escala = Math.min(1, 1 / ampliacion);
    const w = Math.round(cw * escala);
    const h = Math.round(ch * escala);
    if (w === this.canvas.width && h === this.canvas.height && this.generacion > 0) return;
    this.canvas.width = w;
    this.canvas.height = h;
    this.ctx.imageSmoothingQuality = 'high';
    this.generacion++;
    for (const b of this.bitmaps.values()) b.close();
    this.bitmaps.clear();
    this.dibujada = -1;
    this.decodificarVentana();
  }

  /** Tamaño al que se dibuja el frame en el canvas actual (cover o contain). */
  private tamanoDibujo() {
    const { width: cw, height: ch } = this.canvas;
    const sx = cw / this.anchoFrame;
    const sy = ch / this.altoFrame;
    const s = this.ajuste() === 'cover' ? Math.max(sx, sy) : Math.min(sx, sy);
    return { w: Math.round(this.anchoFrame * s), h: Math.round(this.altoFrame * s) };
  }

  // ---------------------------------------------------------------- decodificación por ventana

  private decodificarVentana() {
    if (!this.anchoFrame) return;
    const centro = Math.round(this.posicion);
    const desde = this.sentido > 0 ? centro - this.atras : centro - this.adelante;
    const hasta = this.sentido > 0 ? centro + this.adelante : centro + this.atras;
    // liberar lo que quedó fuera de la ventana (con margen para no oscilar)
    for (const [i, b] of this.bitmaps) {
      if (i < desde - 8 || i > hasta + 8) {
        b.close();
        this.bitmaps.delete(i);
      }
    }
    // pedir primero los más cercanos, en el sentido del scroll
    const orden: number[] = [];
    for (let d = 0; d <= Math.max(this.adelante, this.atras); d++) {
      for (const i of this.sentido > 0 ? [centro + d, centro - d] : [centro - d, centro + d]) {
        if (i >= Math.max(0, desde) && i <= Math.min(this.total - 1, hasta)) orden.push(i);
      }
    }
    for (const i of orden) {
      // frames de la ventana aún sin descargar (p. ej. tras un salto): se piden con prioridad
      if (!this.blobs[i] && this.descargando.size < 8) this.descargar(i);
      if (this.decodificando.size >= 3) continue;
      if (!this.bitmaps.has(i) && !this.decodificando.has(i) && this.blobs[i]) this.decodificar(i);
    }
  }

  private async decodificar(i: number) {
    const blob = this.blobs[i];
    if (!blob) return;
    this.decodificando.add(i);
    const generacion = this.generacion;
    try {
      const { w, h } = this.tamanoDibujo();
      const bmp = await createImageBitmap(blob, { resizeWidth: w, resizeHeight: h, resizeQuality: 'high' });
      if (generacion !== this.generacion) bmp.close();
      else {
        this.bitmaps.set(i, bmp);
        if (Math.abs(i - this.posicion) < 2) this.repintar();
      }
    } catch {
      /* frame dañado o no soportado: se usa el más cercano */
    } finally {
      this.decodificando.delete(i);
      this.decodificarVentana();
    }
  }

  // ---------------------------------------------------------------- descarga (comprimida)

  private async descargar(i: number) {
    if (this.blobs[i] || this.descargando.has(i)) return;
    this.descargando.add(i);
    try {
      const r = await fetch(this.urlFrame(i));
      if (!r.ok) return;
      this.blobs[i] = await r.blob();
      if (!this.anchoFrame) {
        const bmp = await createImageBitmap(this.blobs[i]!);
        this.anchoFrame = bmp.width;
        this.altoFrame = bmp.height;
        bmp.close();
        this.ajustarTamano();
      }
      const centro = Math.round(this.posicion);
      if (i >= centro - this.atras - 2 && i <= centro + this.adelante + 2) this.decodificarVentana();
    } catch {
      /* sin red: se reintenta en la siguiente carga */
    } finally {
      this.descargando.delete(i);
    }
  }

  /** Descarga el primer frame y luego uno de cada `salto` (cobertura rápida) y el resto, en paralelo. */
  async cargar(salto = 10, concurrencia = 4, alPrimerFrame?: () => void) {
    if (this.cargando) return;
    this.cargando = true;
    await this.descargar(0);
    await this.decodificar(0);
    this.repintar();
    alPrimerFrame?.();
    const orden: number[] = [];
    for (let i = salto; i < this.total; i += salto) orden.push(i);
    for (let i = 1; i < this.total; i++) if (i % salto !== 0) orden.push(i);
    let siguiente = 0;
    const trabajador = async () => {
      while (siguiente < orden.length) await this.descargar(orden[siguiente++]);
    };
    await Promise.all(Array.from({ length: concurrencia }, trabajador));
  }
}
