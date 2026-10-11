// Logos de las marcas para el carrusel de "Marcas", a partir de las imágenes de cruba.com.mx
// (descargadas en assets-origen/marcas-cruba/, sin el redimensionado de Wix).
//  - quita el fondo blanco de los que no traen transparencia (Polycon, RayHunters);
//  - recorta márgenes vacíos y los ajusta a una caja común de 400×180 (2× del tamaño en pantalla);
//  - salida: public/brand/marcas/<id>.webp con transparencia.
// Uso: node scripts/procesar-marcas.mjs
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const ORIGEN = path.join(RAIZ, 'assets-origen/marcas-cruba');
const SALIDA = path.join(RAIZ, 'public/brand/marcas');

const LOGOS = [
  { id: 'rayhunters', archivo: '24b14c_b492168618344a299ef904fb970717da~mv2.png', quitarBlanco: true },
  { id: 'supralux', archivo: '24b14c_e3a9dae1f5e34faa8c0109c7b451c285~mv2.webp' },
  { id: 'lirvan', archivo: '24b14c_25602a82345346f3b1794b76e38ba576~mv2.png' },
  { id: 'polycon', archivo: '24b14c_969c987b747044d4be2d06a4068a8ed8~mv2.jpg', quitarBlanco: true },
  { id: 'poliedro-urbano', archivo: '24b14c_2ecb2d43ec714cce93eef469db2e7c8c~mv2.png' },
  { id: 'tp-link', archivo: '24b14c_0a77f59b6e0f4031bab146cd9e2704a2~mv2.png' },
  { id: 'biocup', archivo: '24b14c_8663e14ea86b4f60b846aadbae221446~mv2.avif' },
  { id: 'galga-hilaturas', archivo: '24b14c_57a8bf147cbe4a288f708245e193bb48~mv2.webp' },
  { id: 'sbetech', archivo: '24b14c_3c73aa8228c14baab7e070f7670a4e9a~mv2.webp' },
  { id: 'tinacon', archivo: '24b14c_301cd622f7da4e79afd3fb05aded67d1~mv2.png' },
  { id: 'di-central', archivo: '24b14c_b9862b7aebcb4be8906ea3c497913fc5~mv2.png' },
];

/** Blanco → transparente con borde suave: mínimo de canal ≥ 248 transparente, rampa desde 215. */
async function sinFondoBlanco(entrada) {
  const { data, info } = await sharp(entrada).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  for (let i = 0; i < data.length; i += 4) {
    const minimo = Math.min(data[i], data[i + 1], data[i + 2]);
    const opacidad = Math.max(0, Math.min(1, (248 - minimo) / (248 - 215)));
    data[i + 3] = Math.round(data[i + 3] * opacidad);
  }
  return sharp(data, { raw: info }).png().toBuffer();
}

await mkdir(SALIDA, { recursive: true });
for (const { id, archivo, quitarBlanco } of LOGOS) {
  let img = path.join(ORIGEN, archivo);
  if (quitarBlanco) img = await sinFondoBlanco(img);
  const recortado = await sharp(img).ensureAlpha().trim({ threshold: 1 }).toBuffer();
  const { width, height } = await sharp(recortado
  ).metadata();
  await sharp(recortado)
    .resize(400, 180, { fit: 'inside', withoutEnlargement: false })
    .webp({ quality: 90, alphaQuality: 100, effort: 6 })
    .toFile(path.join(SALIDA, `${id}.webp`));
  console.log(`${id}: ${width}×${height} recortado`);
}
