// Convierte el recorrido de Blender a WebP para la web, uniendo los frames normales con los intermedios:
//   blender/render/recorrido/frame_####.png        (t = ####)
//   blender/render/recorrido-sub/frame_####_ff.png  (t = ####.ff, tramos donde la cámara va rápido)
// Salida: public/recorrido/{desktop 1600x900, mobile 960x540}/frame_0001.webp… (numeración consecutiva)
//         src/data/recorrido-tiempos.json  (tiempo de Blender de cada frame web, para ubicar las escenas)
// Uso: node scripts/optimizar-recorrido.mjs
import { mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const RENDER = path.join(RAIZ, 'blender/render');
const SALIDAS = [
  { carpeta: path.join(RAIZ, 'public/recorrido/desktop'), ancho: 1600, alto: 900, calidad: 62 },
  { carpeta: path.join(RAIZ, 'public/recorrido/mobile'), ancho: 960, alto: 540, calidad: 58 },
];

async function listar(carpeta, patron, aTiempo) {
  const archivos = await readdir(carpeta).catch(() => []);
  return archivos.filter((f) => patron.test(f)).map((f) => ({ ruta: path.join(carpeta, f), t: aTiempo(f) }));
}

const frames = [
  ...(await listar(path.join(RENDER, 'recorrido'), /^frame_\d{4}\.png$/, (f) => +f.slice(6, 10))),
  ...(await listar(path.join(RENDER, 'recorrido-sub'), /^frame_\d{4}_\d{2}\.png$/, (f) => +f.slice(6, 10) + +f.slice(11, 13) / 100)),
].sort((a, b) => a.t - b.t);

// La numeración cambia al insertar intermedios: se regenera todo para no mezclar secuencias.
for (const s of SALIDAS) {
  await rm(s.carpeta, { recursive: true, force: true });
  await mkdir(s.carpeta, { recursive: true });
}
for (let i = 0; i < frames.length; i += 4) {
  await Promise.all(frames.slice(i, i + 4).map(async ({ ruta }, k) => {
    const nombre = `frame_${String(i + k + 1).padStart(4, '0')}.webp`;
    for (const s of SALIDAS) {
      await sharp(ruta).resize(s.ancho, s.alto).webp({ quality: s.calidad, effort: 5 }).toFile(path.join(s.carpeta, nombre));
    }
  }));
  process.stdout.write(`\rWebP: ${Math.min(i + 4, frames.length)}/${frames.length}`);
}
await writeFile(path.join(RAIZ, 'src/data/recorrido-tiempos.json'), JSON.stringify(frames.map((f) => f.t)));
console.log(`\nRecorrido: ${frames.length} frames web (${frames.filter((f) => !Number.isInteger(f.t)).length} intermedios)`);
