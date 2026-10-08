// Contenido corporativo de AmUrb (Ambiental y Urbanística de Michoacán).
// AmUrb es el nuevo nombre de Grupo CRUBA: los textos provienen de cruba.com.mx (2026-10-06)
// y siguen vigentes con la marca actualizada.

export const empresa = {
  nombre: 'AmUrb',
  nombreCompleto: 'Ambiental y Urbanística de Michoacán',
  lema: 'Soluciones innovadoras',
  bajada:
    'Descubre nuestra infraestructura inteligente diseñada para ciudades y empresas que buscan un futuro sostenible.',
  quienesSomos:
    'AmUrb es una empresa mexicana comprometida con el fortalecimiento de la infraestructura y el suministro estratégico para dependencias federales.',
  mision:
    'Proveer al Estado mexicano y sus instituciones soluciones técnicas, materiales y logística de alta calidad, garantizando seguridad, eficiencia y cumplimiento en cada entrega, bajo los principios de responsabilidad, ética y compromiso nacional.',
  vision:
    'Consolidarnos como un proveedor integral de referencia nacional para la SEDENA y demás instituciones públicas, distinguiéndonos por nuestra confiabilidad, calidad e innovación aplicada.',
};

export const valores = [
  { nombre: 'Compromiso', texto: 'Cumplimos con la palabra dada y respetamos cada acuerdo.' },
  { nombre: 'Lealtad', texto: 'Operamos con apego a los intereses nacionales.' },
  { nombre: 'Eficiencia', texto: 'Optimizamos recursos y tiempos de ejecución.' },
  { nombre: 'Honestidad', texto: 'Actuamos con transparencia en cada proceso.' },
  { nombre: 'Excelencia', texto: 'Buscamos superar los estándares en todos los ámbitos.' },
];

// Áreas de suministro (coinciden con las zonas del campus 3D en Spline).
export const areas = [
  'Materiales de construcción',
  'Acero y derivados',
  'Hidráulicos y sanitarios',
  'Eléctrico',
  'CCTV y tecnología',
  'Textiles y equipo técnico',
];

export const sectores = [
  'Secretaría de la Defensa Nacional (SEDENA)',
  'Dependencias del gobierno federal',
  'Proyectos estratégicos nacionales',
  'Desarrollo de infraestructura',
  'Ciudades inteligentes',
];

// Revisar: en el sitio de origen, Biocup apuntaba a un CDN de Shopify y SBETech a la
// misma URL que Galga Hilaturas (probables errores); se dejan sin enlace.
export const marcas = [
  { nombre: 'Rayhunters', url: 'https://rayhunters.com.mx/' },
  { nombre: 'Supralux', url: 'https://supralux.mx/' },
  { nombre: 'Lirvan', url: 'https://lirvan.com/' },
  { nombre: 'Polycon', url: 'https://polycon.mx/' },
  { nombre: 'Poliedro Urbano', url: 'https://poliedrourbano.com/' },
  { nombre: 'TP-Link', url: null },
  { nombre: 'Biocup', url: null },
  { nombre: 'Galga Hilaturas', url: 'https://galgahilaturas.com/' },
  { nombre: 'SBETech', url: null },
  { nombre: 'Tinacón', url: 'https://tinacon.com/' },
];

export const contacto = {
  direccion: 'Calle Valle de Carácuaro #79, Col. Valle Quieto, C.P. 58066, Morelia, Michoacán',
  telefono: '(443) 523 6446',
  telefonoHref: 'tel:+524435236446',
};

export const navegacion = [
  { href: '#nosotros', texto: 'Nosotros' },
  { href: '#soluciones', texto: 'Soluciones' },
  { href: '#marcas', texto: 'Marcas' },
];
