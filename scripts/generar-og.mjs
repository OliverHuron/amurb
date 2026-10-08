// Imagen para compartir en redes (Open Graph / Twitter): 1200x630 con el render de la ciudad, logo y lema.
// Uso: node scripts/generar-og.mjs  ->  public/og.jpg
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const FONDO = path.join(RAIZ, 'blender/render/ciudad_parabus.png');
const LOGO = path.join(RAIZ, 'public/brand/logo-claro.webp');
const W = 1200;
const H = 630;

const degradado = Buffer.from(`<svg width="${W}" height="${H}">
  <defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="#070b14" stop-opacity="0.92"/>
    <stop offset="0.55" stop-color="#070b14" stop-opacity="0.55"/>
    <stop offset="1" stop-color="#070b14" stop-opacity="0.05"/>
  </linearGradient></defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
  <text x="64" y="330" font-family="Montserrat, Arial, sans-serif" font-size="64" font-weight="800" fill="#ffffff">Soluciones</text>
  <text x="64" y="404" font-family="Montserrat, Arial, sans-serif" font-size="64" font-weight="800" fill="#ffc46b">innovadoras</text>
  <text x="64" y="468" font-family="Inter, Arial, sans-serif" font-size="26" fill="#d9dde3">Alumbrado, mobiliario urbano, vialidad y CCTV</text>
  <text x="64" y="504" font-family="Inter, Arial, sans-serif" font-size="26" fill="#d9dde3">para ciudades de México.</text>
  <text x="64" y="580" font-family="Inter, Arial, sans-serif" font-size="22" fill="#9fd36b">amurb.com.mx</text>
</svg>`);

const logo = await sharp(LOGO).resize({ height: 110 }).toBuffer();
await sharp(FONDO)
  .resize(W, H, { fit: 'cover', position: 'right' })
  .composite([{ input: degradado }, { input: logo, left: 64, top: 90 }])
  .jpeg({ quality: 82, mozjpeg: true })
  .toFile(path.join(RAIZ, 'public/og.jpg'));
console.log('public/og.jpg listo');
