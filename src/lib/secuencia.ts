// Secuencia de imágenes dibujada en canvas, con carga progresiva (para animaciones ligadas al scroll).

export type Ajuste = 'cover' | 'contain';

export class SecuenciaFrames {
  private frames: (HTMLImageElement | undefined)[];
  private ctx: CanvasRenderingContext2D;
  private actual = 0;
  private cargando = false;

  constructor(
    private canvas: HTMLCanvasElement,
    private urlFrame: (i: number) => string,
    readonly total: number,
    private ajuste: () => Ajuste = () => 'cover',
  ) {
    this.frames = new Array(total);
    this.ctx = canvas.getContext('2d')!;
    this.ajustarTamano();
    window.addEventListener('resize', () => this.ajustarTamano());
  }

  /** Frame cargado más cercano al pedido (para no dejar huecos mientras se descarga). */
  private disponible(i: number) {
    for (let d = 0; d < this.total; d++) {
      if (this.frames[i - d]) return this.frames[i - d];
      if (this.frames[i + d]) return this.frames[i + d];
    }
    return undefined;
  }

  /**
   * Dibuja la posición `i` (puede ser fraccionaria): si cae entre dos frames cargados,
   * los funde según la fracción para que el scroll lento no se vea escalonado.
   */
  dibujar(i: number) {
    this.actual = Math.max(0, Math.min(this.total - 1, i));
    const a = Math.floor(this.actual);
    const fraccion = this.actual - a;
    const imgA = this.frames[a];
    const imgB = this.frames[Math.min(a + 1, this.total - 1)];
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (imgA && imgB && fraccion > 0.02) {
      this.pintar(imgA, 1);
      this.pintar(imgB, fraccion);
    } else {
      const img = this.disponible(Math.round(this.actual));
      if (img) this.pintar(img, 1);
    }
  }

  private pintar(img: HTMLImageElement, opacidad: number) {
    const { width: cw, height: ch } = this.canvas;
    const escalaX = cw / img.naturalWidth;
    const escalaY = ch / img.naturalHeight;
    const escala = this.ajuste() === 'cover' ? Math.max(escalaX, escalaY) : Math.min(escalaX, escalaY);
    const w = img.naturalWidth * escala;
    const h = img.naturalHeight * escala;
    this.ctx.globalAlpha = opacidad;
    this.ctx.drawImage(img, (cw - w) / 2, (ch - h) / 2, w, h);
    this.ctx.globalAlpha = 1;
  }

  private ajustarTamano() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    this.canvas.width = Math.round(this.canvas.clientWidth * dpr);
    this.canvas.height = Math.round(this.canvas.clientHeight * dpr);
    this.ctx.imageSmoothingQuality = 'high';
    this.dibujar(this.actual);
  }

  private async cargarFrame(i: number) {
    if (this.frames[i]) return;
    const img = new Image();
    img.src = this.urlFrame(i);
    try {
      await img.decode();
      this.frames[i] = img;
      if (Math.abs(i - this.actual) < 3) this.dibujar(this.actual);
    } catch {
      /* frame faltante: se usa el más cercano disponible */
    }
  }

  /** Carga el primer frame y luego uno de cada `salto` (cobertura rápida) y el resto, en paralelo. */
  async cargar(salto = 10, concurrencia = 6, alPrimerFrame?: () => void) {
    if (this.cargando) return;
    this.cargando = true;
    await this.cargarFrame(0);
    this.dibujar(this.actual);
    alPrimerFrame?.();
    const orden: number[] = [];
    for (let i = salto; i < this.total; i += salto) orden.push(i);
    for (let i = 1; i < this.total; i++) if (i % salto !== 0) orden.push(i);
    let siguiente = 0;
    const trabajador = async () => {
      while (siguiente < orden.length) await this.cargarFrame(orden[siguiente++]);
    };
    await Promise.all(Array.from({ length: concurrencia }, trabajador));
  }
}
