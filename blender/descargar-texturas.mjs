// Descarga texturas PBR CC0 de Poly Haven (gratis, sin cuenta ni API key) para la escena de Blender.
// Uso: node blender/descargar-texturas.mjs
import { mkdir, writeFile, access } from 'node:fs/promises';
import path from 'node:path';

const DESTINO = path.join(import.meta.dirname, 'texturas');
const RESOLUCION = '2k';

// id de Poly Haven -> uso en la escena
const TEXTURAS = {
  asphalt_02: 'calles',
  concrete_pavement_02: 'patios y banquetas',
  brick_pavement_02: 'plazas',
  leafy_grass: 'césped',
  bicolour_gravel: 'patio de construcción',
  precast_concrete_wall: 'fachadas de concreto',
  box_profile_metal_sheet: 'naves industriales (muros y techos)',
  concrete_floor_worn_001: 'azoteas',
  aerial_grass_rock: 'terreno exterior',
};

// Mapas por textura: nombre en la API -> sufijo de archivo local
const MAPAS = { Diffuse: 'diff', Rough: 'rough', nor_gl: 'nor' };

const existe = (p) => access(p).then(() => true, () => false);

for (const [id, uso] of Object.entries(TEXTURAS)) {
  const carpeta = path.join(DESTINO, id);
  await mkdir(carpeta, { recursive: true });
  const archivos = await (await fetch(`https://api.polyhaven.com/files/${id}`)).json();
  for (const [mapa, sufijo] of Object.entries(MAPAS)) {
    const info = archivos[mapa]?.[RESOLUCION]?.jpg;
    if (!info) {
      console.warn(`  ${id}: sin mapa ${mapa}`);
      continue;
    }
    const salida = path.join(carpeta, `${sufijo}.jpg`);
    if (await existe(salida)) continue;
    const datos = Buffer.from(await (await fetch(info.url)).arrayBuffer());
    await writeFile(salida, datos);
  }
  console.log(`✓ ${id} (${uso})`);
}
console.log('Texturas listas en blender/texturas (licencia CC0, polyhaven.com)');
