// Genera los assets web a partir de los originales (que no se modifican):
//   desktop_frames/*.webp (5120x2880) -> public/frames/desktop (1920x1080) y public/frames/mobile (720x1280)
//   logo_ambiental.png                -> public/brand/logo-claro.webp (versión para fondos oscuros)
// Uso: node scripts/optimizar-assets.mjs            (logo + frames)
//      node scripts/optimizar-assets.mjs --solo-logo
import { mkdir, readdir } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const ORIGEN = path.join(RAIZ, 'desktop_frames');
const DESTINO_DESKTOP = path.join(RAIZ, 'public/frames/desktop');
const DESTINO_MOBILE = path.join(RAIZ, 'public/frames/mobile');
const DESTINO_MARCA = path.join(RAIZ, 'public/brand');

// Recorte central del 86 %: elimina la marca de agua de la esquina inferior derecha.
const RECORTE = 0.07;
// En móvil se usa uno de cada dos frames para reducir la descarga.
const PASO_MOBILE = 2;
const CONCURRENCIA = 4;

async function procesarFrame(archivo, indice) {
  const entrada = sharp(path.join(ORIGEN, archivo));
  const { width, height } = await entrada.metadata();
  const left = Math.round(width * RECORTE);
  const top = Math.round(height * RECORTE);
  const cw = width - left * 2;
  const ch = height - top * 2;

  await sharp(path.join(ORIGEN, archivo))
    .extract({ left, top, width: cw, height: ch })
    .resize(1920, 1080, { fit: 'cover' })
    .webp({ quality: 62, effort: 5 })
    .toFile(path.join(DESTINO_DESKTOP, archivo));

  if (indice % PASO_MOBILE === 0) {
    // Encuadre vertical 9:16 centrado dentro del recorte.
    const mw = Math.round(ch * (9 / 16));
    const salida = `frame_${String(indice / PASO_MOBILE + 1).padStart(4, '0')}.webp`;
    await sharp(path.join(ORIGEN, archivo))
      .extract({ left: left + Math.round((cw - mw) / 2), top, width: mw, height: ch })
      .resize(720, 1280, { fit: 'cover' })
      .webp({ quality: 60, effort: 5 })
      .toFile(path.join(DESTINO_MOBILE, salida));
  }
}

async function procesarFrames() {
  await mkdir(DESTINO_DESKTOP, { recursive: true });
  await mkdir(DESTINO_MOBILE, { recursive: true });
  const archivos = (await readdir(ORIGEN)).filter((f) => f.endsWith('.webp')).sort();
  for (let i = 0; i < archivos.length; i += CONCURRENCIA) {
    const lote = archivos.slice(i, i + CONCURRENCIA);
    await Promise.all(lote.map((archivo, j) => procesarFrame(archivo, i + j)));
    process.stdout.write(`\rFrames: ${Math.min(i + CONCURRENCIA, archivos.length)}/${archivos.length}`);
  }
  process.stdout.write('\n');
  return archivos.length;
}

// Versión para la barra de navegación sobre fondos oscuros: invierte a blanco los tonos
// oscuros/grises (conserva verdes y ámbar) y quita el subtítulo, ilegible a tamaño de navbar.
async function procesarLogo() {
  await mkdir(DESTINO_MARCA, { recursive: true });
  const { data, info } = await sharp(path.join(RAIZ, 'logo_ambiental.png'))
    .resize({ height: 240 })
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const inicioTexto = Math.round(info.width * 0.41);
  const inicioSubtitulo = Math.round(info.height * 0.66);
  for (let p = 0; p < data.length; p += 4) {
    const x = (p / 4) % info.width;
    const y = Math.floor(p / 4 / info.width);
    if (x > inicioTexto && y > inicioSubtitulo) {
      data[p + 3] = 0;
      continue;
    }
    const [r, g, b, a] = [data[p], data[p + 1], data[p + 2], data[p + 3]];
    if (a === 0) continue;
    const max = Math.max(r, g, b);
    const saturacion = max === 0 ? 0 : (max - Math.min(r, g, b)) / max;
    if (saturacion < 0.25) {
      const claro = 255 - Math.round(max * 0.25);
      data[p] = data[p + 1] = data[p + 2] = claro;
    }
  }
  const claro = await sharp(data, { raw: info }).trim().png().toBuffer();
  await sharp(claro).webp({ quality: 90 }).toFile(path.join(DESTINO_MARCA, 'logo-claro.webp'));
  await sharp(path.join(RAIZ, 'logo_ambiental.png'))
    .resize({ height: 240 })
    .webp({ quality: 90 })
    .toFile(path.join(DESTINO_MARCA, 'logo.webp'));

  await crearFavicon(claro);
}

// Favicon "AU": la A (verde) y la U (clara) recortadas del propio logotipo "AmUrb",
// para conservar la tipografía de la marca. Las letras se localizan por columnas con tinta.
async function crearFavicon(logo) {
  const { data, info } = await sharp(logo).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const conTinta = (x) => {
    for (let y = 0; y < info.height; y++) if (data[(y * info.width + x) * 4 + 3] > 60) return true;
    return false;
  };
  const bloques = [];
  let inicio = -1;
  for (let x = 0; x <= info.width; x++) {
    const tinta = x < info.width && conTinta(x);
    if (tinta && inicio < 0) inicio = x;
    if (!tinta && inicio >= 0) {
      if (x - inicio > 4) bloques.push([inicio, x]);
      inicio = -1;
    }
  }
  // Los últimos 5 bloques son "A", "m", "U", "r", "b" (la A va pegada al icono sin hueco).
  if (bloques.length < 6) throw new Error(`Se esperaban icono + 5 letras; se encontraron ${bloques.length} bloques`);
  const letras = bloques.slice(-5);

  const recortarLetra = async ([x0, x1]) => {
    const tira = await sharp(logo).extract({ left: x0, top: 0, width: x1 - x0, height: info.height }).png().toBuffer();
    return sharp(tira).trim().png().toBuffer();
  };
  const [a, u] = await Promise.all([recortarLetra(letras[0]), recortarLetra(letras[2])]);
  const ma = await sharp(a).metadata();
  const mu = await sharp(u).metadata();
  const separacion = Math.round(ma.height * 0.06);
  const altura = Math.max(ma.height, mu.height);
  const ancho = ma.width + separacion + mu.width;
  const monograma = await sharp({ create: { width: ancho, height: altura, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
    .composite([
      { input: a, left: 0, top: altura - ma.height },
      { input: u, left: ma.width + separacion, top: altura - mu.height },
    ])
    .png()
    .toBuffer();

  for (const [lado, archivo] of [[64, 'favicon.png'], [180, 'apple-touch-icon.png']]) {
    const interior = Math.round(lado * 0.84);
    const marca = await sharp(monograma)
      .resize(interior, interior, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .toBuffer();
    const borde = Math.round((lado - interior) / 2);
    await sharp({ create: { width: lado, height: lado, channels: 4, background: '#070b14' } })
      .composite([{ input: marca, left: borde, top: borde }])
      .png()
      .toFile(path.join(RAIZ, 'public', archivo));
  }
}

await procesarLogo();
console.log('Logo y favicon listos');
if (!process.argv.includes('--solo-logo')) {
  const total = await procesarFrames();
  console.log(`Listo: ${total} frames desktop, ${Math.ceil(total / PASO_MOBILE)} frames mobile`);
}
