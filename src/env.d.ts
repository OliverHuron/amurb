import type Lenis from 'lenis';

declare global {
  interface Window {
    /** Instancia de scroll suave (ausente con movimiento reducido). `window.lenis` lo usa la propia librería. */
    scrollSuave?: Lenis;
  }
}

export {};
