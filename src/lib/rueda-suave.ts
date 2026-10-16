// Rueda del mouse "como las flechas del teclado" dentro de un tramo de la página.
// Cada clic de rueda salta ~100 px de golpe; en una secuencia larga eso son muchas imágenes por clic y se
// ve como arrancón-frenón. Aquí, dentro del tramo, la rueda avanza menos por clic y el desplazamiento se
// reparte en el tiempo (suavizado exponencial), como el scroll continuo de las flechas.
// Fuera del tramo y con pellizco de trackpad (ctrlKey), la rueda es la nativa.
// Se aplica también con "reducir movimiento" (Windows lo activa al apagar los efectos de animación): no
// agrega movimiento, solo reparte el que pide el usuario; sin esto cada clic brincaba ~15 imágenes de golpe.

interface Opciones {
  /** Rango de scroll (px) donde actúa; se consulta en cada evento (cambia al redimensionar). */
  rango: () => { inicio: number; fin: number };
  /** Fracción de la distancia nativa por clic (las flechas mueven ~40 px; un clic de rueda ~100 px). */
  factor?: number;
  /** Segundos para recorrer ~63 % de lo pendiente. */
  suavizado?: number;
  /** Se llama en el mismo cuadro tras mover el scroll (p. ej. ScrollTrigger.update) para no ir un cuadro atrás. */
  alMover?: () => void;
}

export function ruedaSuave({ rango, factor = 0.55, suavizado = 0.32, alMover }: Opciones) {
  let objetivo = 0;
  let actual = 0;
  let ultimoAsignado = -1;
  let animando = false;
  let ultimoTick = 0;

  const maximo = () => document.documentElement.scrollHeight - window.innerHeight;

  function tick(t: number) {
    // Si el usuario movió la página por otro medio (barra, teclado, enlace), se cede el control.
    if (Math.abs(window.scrollY - ultimoAsignado) > 2) {
      animando = false;
      return;
    }
    const dt = Math.min(0.1, (t - ultimoTick) / 1000);
    ultimoTick = t;
    const restante = objetivo - actual;
    actual = Math.abs(restante) < 0.5 ? objetivo : actual + restante * (1 - Math.exp(-dt / suavizado));
    // 'instant': el CSS global tiene scroll-behavior: smooth y convertiría esto en otra animación encima
    window.scrollTo({ top: actual, behavior: 'instant' });
    ultimoAsignado = window.scrollY;
    alMover?.();
    if (actual !== objetivo) requestAnimationFrame(tick);
    else animando = false;
  }

  window.addEventListener(
    'wheel',
    (e) => {
      if (e.ctrlKey || e.deltaY === 0) return;
      const { inicio, fin } = rango();
      const base = animando ? objetivo : window.scrollY;
      // Solo dentro del tramo (o entrando a él): al salir, la rueda vuelve a ser la nativa.
      if (base < inicio - 1 || base > fin + 1) return;
      if (base <= inicio + 1 && e.deltaY < 0) return;
      if (base >= fin - 1 && e.deltaY > 0) return;
      e.preventDefault();
      const px = e.deltaMode === 1 ? e.deltaY * 40 : e.deltaMode === 2 ? e.deltaY * window.innerHeight : e.deltaY;
      if (!animando) {
        actual = window.scrollY;
        objetivo = actual;
        ultimoAsignado = actual;
      }
      objetivo = Math.max(0, Math.min(maximo(), objetivo + px * factor));
      if (!animando) {
        animando = true;
        ultimoTick = performance.now();
        requestAnimationFrame(tick);
      }
    },
    { passive: false },
  );
}
