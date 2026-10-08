// Escenas del recorrido por la ciudad (sección "Soluciones").
// `desde`/`hasta` están en frames de Blender (como PARADAS en blender/ciudad/recorrido.py); se convierten
// a índices web con recorrido-tiempos.json, que incluye los frames intermedios de los tramos rápidos.
import tiempos from './recorrido-tiempos.json';

export const RECORRIDO = {
  frames: tiempos.length,
  rutaDesktop: '/recorrido/desktop/',
  rutaMobile: '/recorrido/mobile/',
};

export interface Parada {
  id: string;
  desde: number;
  hasta: number;
  etiqueta: string;
  titulo: string;
  texto: string;
  productos: string[];
}

/** Primer y último frame web (base 1) cuyos tiempos de Blender caen dentro del rango. */
function aIndices(desde: number, hasta: number) {
  const primero = tiempos.findIndex((t) => t >= desde);
  let ultimo = primero;
  while (ultimo + 1 < tiempos.length && tiempos[ultimo + 1] <= hasta) ultimo++;
  return { desde: primero + 1, hasta: ultimo + 1 };
}

const definiciones: (Omit<Parada, 'desde' | 'hasta'> & { rango: [number, number] })[] = [
  {
    id: 'ciudad', rango: [1, 35], etiqueta: 'Soluciones',
    titulo: 'Todo lo que una ciudad necesita',
    texto: 'Recorre cómo nuestros productos mejoran calles, plazas y servicios urbanos.',
    productos: [],
  },
  {
    id: 'alumbrado', rango: [80, 120], etiqueta: 'Alumbrado',
    titulo: 'Alumbrado público y solar',
    texto: 'Iluminación eficiente para avenidas, camellones y banquetas.',
    productos: ['Luminarias con panel solar', 'Faroles de hierro', 'Luminarias LED'],
  },
  {
    id: 'vialidad', rango: [140, 175], etiqueta: 'Vialidad',
    titulo: 'Seguridad vial',
    texto: 'Confinamiento y orden del tránsito en cruces y carriles.',
    productos: ['Bolardo divisor trapezoidal 120-15-9.5', 'Señalamiento horizontal'],
  },
  {
    id: 'alcantarillado', rango: [185, 220], etiqueta: 'Alcantarillado',
    titulo: 'Alcantarillado',
    texto: 'Registro y drenaje pluvial resistentes al tráfico urbano.',
    productos: ['Brocal con tapa para pozo de visita', 'Coladeras pluviales de hierro'],
  },
  {
    id: 'parabuses', rango: [240, 278], etiqueta: 'Parabuses',
    titulo: 'Parabuses',
    texto: 'Personalizables con celosía, logotipos y alumbrado. Diseños inclusivos.',
    productos: ['Parabús Elle', 'Parabús Contempo', 'Bancas y botes'],
  },
  {
    id: 'cctv', rango: [298, 335], etiqueta: 'CCTV',
    titulo: 'Videovigilancia',
    texto: 'Cruces y espacios públicos más seguros, conectados a centros de monitoreo.',
    productos: ['Postes de videovigilancia', 'Domo PTZ y cámaras bala', 'Botón de pánico y altavoz'],
  },
  {
    id: 'tinacos', rango: [368, 402], etiqueta: 'Hidráulicos',
    titulo: 'Almacenamiento de agua',
    texto: 'Soluciones hidráulicas y sanitarias para viviendas y edificios.',
    productos: ['Tinacos', 'Hidráulicos y sanitarios'],
  },
  {
    id: 'plaza', rango: [440, 478], etiqueta: 'Espacio público',
    titulo: 'Plazas y jardines',
    texto: 'Mobiliario urbano que hace los espacios públicos más habitables.',
    productos: ['Faroles de hierro', 'Bancas urbanas', 'Botes y jardineras'],
  },
  {
    id: 'final', rango: [505, 540], etiqueta: 'AmUrb',
    titulo: 'Infraestructura que transforma ciudades',
    texto: 'Ambiental y Urbanística de Michoacán: suministro integral para gobierno, defensa e iniciativa privada.',
    productos: [],
  },
];

export const paradas: Parada[] = definiciones.map(({ rango, ...resto }) => ({ ...resto, ...aIndices(rango[0], rango[1]) }));
