// Frames del hero a partir del video de dron (toma10.MP4, 4K a 59,94 cps, fuera de git):
//  1. Usa del segundo 4 al 15 (en los primeros 4 s el dron aún se estabiliza).
//  2. Elige los cuadros según cuánto cambia la imagen (como los intermedios del recorrido de la ciudad):
//     se toma un cuadro cada vez que el cambio medio respecto al anterior elegido llega a OBJETIVO.
//     Así cada paso del scroll mueve lo mismo, vaya el dron lento o rápido.
//  3. Escritorio 1600×900 AVIF; celular encuadre vertical 9:16 centrado, 720×1280, uno de cada dos.
// Salida: public/hero/{desktop,mobile}/frame_####.avif (fuera de git; se suben aparte al servidor)
//         src/data/hero.json (número de frames por versión)
// Uso: node scripts/optimizar-hero.mjs [video] [objetivo=4]
import { execFileSync } from 'node:child_process';
import { mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import sharp from 'sharp';

const RAIZ = path.resolve(import.meta.dirname, '..');
const VIDEO = path.resolve(RAIZ, process.argv[2] ?? 'toma10.MP4');
const OBJETIVO = Number(process.argv[3] ?? 4);
const DESDE = 4;
const HASTA = 15;
const TMP = path.join(os.tmpdir(), 'amurb-hero');
const SALIDA = {
  desktop: path.join(RAIZ, 'public/hero/desktop'),
  mobile: path.join(RAIZ, 'public/hero/mobile'),
};

const ffmpeg = (...args) => execFileSync('ffmpeg', ['-v', 'error', '-y', ...args], { stdio: 'inherit' });
const listar = async (d) => (await readdir(d)).filter((f) => !f.startsWith('.')).sort();

for (const d of ['analisis', 'desktop', 'mobile']) {
  await rm(path.join(TMP, d), { recursive: true, force: true });
  await mkdir(path.join(TMP, d), { recursive: true });
}

// 1) Todos los cuadros del tramo: miniaturas en gris para medir, y en alta calidad para cada versión
console.log('Extrayendo cuadros del video…');
const tramo = ['-ss', String(DESDE), '-to', String(HASTA), '-i', VIDEO];
ffmpeg(...tramo, '-vf', 'scale=240:135,format=gray', path.join(TMP, 'analisis/f_%04d.png'));
ffmpeg(...tramo, '-vf', 'scale=1600:900:flags=lanczos', '-q:v', '2', path.join(TMP, 'desktop/f_%04d.jpg'));
ffmpeg(...tramo, '-vf', 'crop=ih*9/16:ih,scale=720:1280:flags=lanczos', '-q:v', '2', path.join(TMP, 'mobile/f_%04d.jpg'));

// 2) Selección por cambio de imagen
const analisis = await listar(path.join(TMP, 'analisis'));
const grises = [];
for (const f of analisis) grises.push(await sharp(path.join(TMP, 'analisis', f)).greyscale().raw().toBuffer());
const cambio = (a, b) => {
  let s = 0;
  for (let k = 0; k < a.length; k++) s += Math.abs(a[k] - b[k]);
  return s / a.length;
};
const elegidos = [0];
for (let i = 1; i < grises.length; i++) {
  if (cambio(grises[elegidos.at(-1)], grises[i]) >= OBJETIVO || i === grises.length - 1) elegidos.push(i);
}
console.log(`${analisis.length} cuadros en el tramo → ${elegidos.length} elegidos (objetivo de cambio ${OBJETIVO})`);

// 3) AVIF
const versiones = [
  { clave: 'desktop', indices: elegidos, calidad: 48 },
  { clave: 'mobile', indices: elegidos.filter((_, k) => k % 2 === 0), calidad: 46 },
];
const totales = {};
for (const { clave, indices, calidad } of versiones) {
  await rm(SALIDA[clave], { recursive: true, force: true });
  await mkdir(SALIDA[clave], { recursive: true });
  const fuentes = await listar(path.join(TMP, clave));
  for (let k = 0; k < indices.length; k += 4) {
    await Promise.all(
      indices.slice(k, k + 4).map((i, j) =>
        sharp(path.join(TMP, clave, fuentes[i]))
          .avif({ quality: calidad, effort: 4 })
          .toFile(path.join(SALIDA[clave], `frame_${String(k + j + 1).padStart(4, '0')}.avif`)),
      ),
    );
    process.stdout.write(`\r${clave}: ${Math.min(k + 4, indices.length)}/${indices.length}`);
  }
  totales[clave] = indices.length;
  console.log();
}

await writeFile(path.join(RAIZ, 'src/data/hero.json'), JSON.stringify({ ...totales, extension: 'avif' }, null, 2) + '\n');
await rm(TMP, { recursive: true, force: true });
console.log('Hero listo:', totales);
