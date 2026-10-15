// Scroll controlado dentro de un tramo de la página (las secuencias de imágenes del hero y del recorrido).
//
// Rueda del mouse "como las flechas del teclado": cada clic de rueda salta ~100 px de golpe; en una
// secuencia larga eso son muchas imágenes por clic y se ve como arrancón-frenón. Aquí, dentro del tramo,
// la rueda avanza menos por clic y el desplazamiento se reparte en el tiempo (suavizado exponencial).
//
// Dedo (celulares): el scroll táctil nativo tiene inercia sin límite y un deslizón cruzaba media secuencia.
// Dentro del tramo, el arrastre sigue al dedo con menos recorrido y la inercia al soltar se limita a una
// fracción de pantalla por gesto. Un gesto que empieza en el borde del tramo hacia afuera es nativo.
//
// Fuera del tramo y con pellizco (ctrlKey / dos dedos), el scroll es el nativo.
// Se aplica también con "reducir movimiento" (Windows lo activa al apagar los efectos de animación): no
// agrega movimiento, solo reparte el que pide el usuario; sin esto cada clic brincaba ~15 imágenes de golpe.

interface Opciones {
  /** Rango de scroll (px) donde actúa; se consulta en cada evento (cambia al redimensionar). */
  rango: () => { inicio: number; fin: number };
  /** Fracción de la distancia nativa por clic (las flechas mueven ~40 px; un clic de rueda ~100 px). */
  factor?: number;
  /** Segundos para recorrer ~63 % de lo pendiente (rueda e inercia del dedo). */
  suavizado?: number;
  /** Fracción del movimiento del dedo que se aplica al arrastrar. */
  factorDedo?: number;
  /** Inercia máxima al soltar el dedo, en pantallas. */
  inerciaMaxima?: number;
  /** Se llama en el mismo cuadro tras mover el scroll (p. ej. ScrollTrigger.update) para no ir un cuadro atrás. */
  alMover?: () => void;
}

export function ruedaSuave({ rango, factor = 0.55, suavizado = 0.32, factorDedo = 0.55, inerciaMaxima = 0.3, alMover }: Opciones) {
  let objetivo = 0;
  let actual = 0;
  let ultimoAsignado = -1;
  let animando = false;
  let ultimoTick = 0;
  let tau = suavizado;

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
    actual = Math.abs(restante) < 0.5 ? objetivo : actual + restante * (1 - Math.exp(-dt / tau));
    // 'instant': el CSS global tiene scroll-behavior: smooth y convertiría esto en otra animación encima
    window.scrollTo({ top: actual, behavior: 'instant' });
    ultimoAsignado = window.scrollY;
    alMover?.();
    if (actual !== objetivo) requestAnimationFrame(tick);
    else animando = false;
  }

  /** Mueve el objetivo `px` y arranca la animación si hace falta. */
  function empujar(px: number, nuevoTau: number) {
    if (!animando) {
      actual = window.scrollY;
      objetivo = actual;
      ultimoAsignado = actual;
    }
    tau = nuevoTau;
    objetivo = Math.max(0, Math.min(maximo(), objetivo + px));
    if (!animando) {
      animando = true;
      ultimoTick = performance.now();
      requestAnimationFrame(tick);
    }
  }

  /** ¿Este gesto (en `sentido`) le toca al tramo? No si empieza fuera o en un borde hacia afuera. */
  function controla(sentido: number) {
    const { inicio, fin } = rango();
    const base = animando ? objetivo : window.scrollY;
    if (base < inicio - 1 || base > fin + 1) return false;
    if (base <= inicio + 1 && sentido < 0) return false;
    if (base >= fin - 1 && sentido > 0) return false;
    return true;
  }

  // ---------------------------------------------------------------- rueda
  window.addEventListener(
    'wheel',
    (e) => {
      if (e.ctrlKey || e.deltaY === 0 || !controla(Math.sign(e.deltaY))) return;
      e.preventDefault();
      const px = e.deltaMode === 1 ? e.deltaY * 40 : e.deltaMode === 2 ? e.deltaY * window.innerHeight : e.deltaY;
      empujar(px * factor, suavizado);
    },
    { passive: false },
  );

  // ---------------------------------------------------------------- dedo
  // estado del gesto: null = sin decidir aún (se decide en el primer movimiento), true/false = lo controla o no
  let gesto: boolean | null = null;
  let previo = { x: 0, y: 0, t: 0 };
  let velocidad = 0; // px de dedo por ms (positivo = avanzar hacia abajo de la página)

  window.addEventListener(
    'touchstart',
    (e) => {
      if (e.touches.length !== 1) {
        gesto = false;
        return;
      }
      const p = e.touches[0];
      previo = { x: p.clientX, y: p.clientY, t: e.timeStamp };
      velocidad = 0;
      // Dentro del tramo (lejos de sus bordes) el gesto se toma desde ya: en iPhone, si el primer
      // touchmove no se cancela, Safari arranca su scroll nativo y ya no deja cancelar el resto.
      // En un borde se decide con el primer movimiento (puede ser un gesto para salir).
      const { inicio, fin } = rango();
      const base = animando ? objetivo : window.scrollY;
      gesto = base > inicio + 2 && base < fin - 2 ? true : base >= inicio - 1 && base <= fin + 1 ? null : false;
    },
    { passive: true },
  );

  window.addEventListener(
    'touchmove',
    (e) => {
      if (gesto === false || e.touches.length !== 1) return;
      const p = e.touches[0];
      const dy = previo.y - p.clientY; // arrastrar hacia arriba = avanzar
      const dx = previo.x - p.clientX;
      if (gesto === null) {
        // en un borde del tramo: si va hacia afuera (o es horizontal), scroll nativo
        if (dy === 0 && dx === 0) return;
        gesto = Math.abs(dy) >= Math.abs(dx) && controla(Math.sign(dy) || 1);
        if (!gesto) return;
      }
      if (!e.cancelable) return;
      e.preventDefault();
      const dt = Math.max(1, e.timeStamp - previo.t);
      velocidad = 0.7 * (dy / dt) + 0.3 * velocidad;
      previo = { x: p.clientX, y: p.clientY, t: e.timeStamp };
      empujar(dy * factorDedo, 0.06); // el arrastre sigue al dedo casi sin retraso
    },
    { passive: false },
  );

  window.addEventListener(
    'touchend',
    (e) => {
      if (gesto) {
        // inercia al soltar: limitada a una fracción de pantalla por gesto; si el dedo se detuvo, no hay
        const quieto = e.timeStamp - previo.t > 80;
        const tope = window.innerHeight * inerciaMaxima;
        const inercia = quieto ? 0 : Math.max(-tope, Math.min(tope, velocidad * 280 * factorDedo));
        if (Math.abs(inercia) > 1) empujar(inercia, suavizado);
      }
      gesto = null;
    },
    { passive: true },
  );
}
