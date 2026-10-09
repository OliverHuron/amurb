// Detecta los tramos del recorrido donde la imagen cambia demasiado entre frames consecutivos y
// decide cuántos frames intermedios (subframes) renderizar ahí para que el scroll se sienta continuo.
// Mide la secuencia completa (normales + intermedios ya renderizados) y solo pide los que faltan.
// Uso: node blender/calcular-subframes.mjs [objetivo=12]  ->  blender/render/subframes.json
//   objetivo: cambio medio máximo entre dos frames vecinos (0–255 por píxel, en gris a 240x135).
//   Referencia: el hero tiene mediana 4,6; el recorrido tenía 23 antes de este paso.
import { readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const RENDER = path.join(RAIZ, 'blender/render');
const OBJETIVO = Number(process.argv[2] ?? 12);

async function listar(carpeta, patron, aTiempo) {
  const archivos = await readdir(carpeta).catch(() => []);
  return archivos.filter((f) => patron.test(f)).map((f) => ({ ruta: path.join(carpeta, f), t: aTiempo(f) }));
}
const frames = [
  ...(await listar(path.join(RENDER, 'recorrido'), /^frame_\d{4}\.png$/, (f) => +f.slice(6, 10))),
  ...(await listar(path.join(RENDER, 'recorrido-sub'), /^frame_\d{4}_\d{2}\.png$/, (f) => +f.slice(6, 10) + +f.slice(11, 13) / 100)),
].sort((a, b) => a.t - b.t);

const leer = (r) => sharp(r).resize(240, 135, { fit: 'fill' }).greyscale().raw().toBuffer();
const existentes = new Set(frames.map((f) => f.t.toFixed(2)));
const tiempos = [];
let anterior = await leer(frames[0].ruta);
let max = 0;
for (let i = 1; i < frames.length; i++) {
  const actual = await leer(frames[i].ruta);
  let suma = 0;
  for (let k = 0; k < actual.length; k++) suma += Math.abs(actual[k] - anterior[k]);
  const cambio = suma / actual.length;
  max = Math.max(max, cambio);
  anterior = actual;
  // Se divide el salto en partes de tamaño <= objetivo (resolución de tiempo: centésimas).
  const t0 = frames[i - 1].t, t1 = frames[i].t;
  const partes = Math.ceil(cambio / OBJETIVO);
  for (let k = 1; k < partes; k++) {
    const t = +(t0 + ((t1 - t0) * k) / partes).toFixed(2);
    if (t > t0 && t < t1 && !Number.isInteger(t) && !existentes.has(t.toFixed(2))) {
      existentes.add(t.toFixed(2));
      tiempos.push(t);
    }
  }
  if (i % 100 === 0) process.stdout.write(`\rMidiendo ${i}/${frames.length - 1}`);
}
await writeFile(path.join(RENDER, 'subframes.json'), JSON.stringify({ objetivo: OBJETIVO, tiempos }, null, 1));
console.log(`\nFrames actuales: ${frames.length} · cambio máximo ${max.toFixed(1)} · intermedios nuevos: ${tiempos.length}`);
