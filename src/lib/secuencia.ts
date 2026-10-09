// Secuencia de imágenes dibujada en canvas para animaciones ligadas al scroll, optimizada para equipos
// modestos (sin tarjeta gráfica) y móviles:
//  - el canvas nunca es más grande que el frame original (el CSS escala; dibujar de más es CPU perdida);
//  - los frames se guardan comprimidos (Blob, ~100 KB) y solo una VENTANA alrededor de la posición
//    actual se decodifica como ImageBitmap ya escalado al tamaño de dibujo (drawImage sin reescalar);
//  - se dibuja en requestAnimationFrame y solo cuando cambia la posición.

export type Ajuste = 'cover' | 'contain';

interface Opciones {
  /** Frames decodificados hacia adelante en el sentido del scroll. */
  adelante?: number;
  /** Frames decodificados hacia atrás. */
  atras?: number;
}

export class SecuenciaFrames {
  private blobs: (Blob | undefined)[];
  private bitmaps = new Map<number, ImageBitmap>();
  private decodificando = new Set<number>();
  private descargando = new Set<number>();
  private ctx: CanvasRenderingContext2D;
  private posicion = 0;
  private dibujada = -1;
  private sentido = 1;
  private pendiente = false;
  private cargando = false;
  private anchoFrame = 0;
  private altoFrame = 0;
  private generacion = 0; // cambia al redimensionar: invalida bitmaps escalados al tamaño anterior
  private readonly adelante: number;
  private readonly atras: number;

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
    window.addEventListener('resize', () => this.ajustarTamano());
  }

  /** Fija la posición (puede ser fraccionaria: se funden los dos frames vecinos) y agenda el dibujo. */
  dibujar(i: number) {
    const nueva = Math.max(0, Math.min(this.total - 1, i));
    if (nueva !== this.posicion) this.sentido = nueva > this.posicion ? 1 : -1;
    this.posicion = nueva;
    this.decodificarVentana();
    if (!this.pendiente) {
      this.pendiente = true;
      requestAnimationFrame(() => {
        this.pendiente = false;
        this.pintarCuadro();
      });
    }
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
        if (Math.abs(i - this.posicion) < 2) {
          this.dibujada = -1;
          this.dibujar(this.posicion);
        }
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
    this.dibujada = -1;
    this.dibujar(this.posicion);
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
