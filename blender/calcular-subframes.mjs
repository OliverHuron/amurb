// Detecta los tramos del recorrido donde la imagen cambia demasiado entre frames consecutivos y
// decide cuántos frames intermedios (subframes) renderizar ahí para que el scroll se sienta continuo.
// Uso: node blender/calcular-subframes.mjs  ->  blender/render/subframes.json  (lista de tiempos, p. ej. 71.5)
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const ORIGEN = path.join(RAIZ, 'blender/render/recorrido');
const TOTAL = 540;

const leer = (i) => sharp(path.join(ORIGEN, `frame_${String(i).padStart(4, '0')}.png`))
  .resize(240, 135).greyscale().raw().toBuffer();

const difs = [];
let anterior = await leer(1);
for (let i = 2; i <= TOTAL; i++) {
  const actual = await leer(i);
  let suma = 0;
  for (let k = 0; k < actual.length; k++) suma += Math.abs(actual[k] - anterior[k]);
  difs.push({ entre: i - 1, cambio: suma / actual.length });
  anterior = actual;
}

const ordenados = difs.map((d) => d.cambio).sort((a, b) => a - b);
const mediana = ordenados[Math.floor(ordenados.length / 2)];
const tiempos = [];
for (const { entre, cambio } of difs) {
  // cambio / mediana: ~1 es normal. Se divide el salto en partes de tamaño ~normal.
  const partes = cambio > mediana * 2.5 ? 4 : cambio > mediana * 1.6 ? 2 : 1;
  for (let k = 1; k < partes; k++) tiempos.push(+(entre + k / partes).toFixed(2));
}
await writeFile(path.join(RAIZ, 'blender/render/subframes.json'), JSON.stringify({ mediana, tiempos }, null, 1));
console.log(`Mediana de cambio: ${mediana.toFixed(1)} · subframes a renderizar: ${tiempos.length}`);
