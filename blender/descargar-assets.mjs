// Descarga assets CC0 (gratis, sin cuenta ni API key) para la ciudad fotorrealista:
//   - Fachadas y techos fotográficos de ambientCG  -> blender/texturas/acg/<id>/
//   - Modelos 3D de Poly Haven (glTF 2k)            -> blender/modelos/<id>/
// Uso: node blender/descargar-assets.mjs
import { mkdir, writeFile, access, readdir, rename, rm } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const AQUI = import.meta.dirname;
const existe = (p) => access(p).then(() => true, () => false);
const bajar = async (url) => Buffer.from(await (await fetch(url)).arrayBuffer());

// ---------- ambientCG: materiales en zip 2K-JPG ----------
const ACG = [
  'Facade001', 'Facade002', 'Facade003', 'Facade004', 'Facade005', 'Facade006', 'Facade007', 'Facade008',
  'Facade009', 'Facade010', 'Facade011', 'Facade018A', 'Facade019A', 'Facade020A',
  'PaintedPlaster006', 'RoofingTiles013A', 'RoofingTiles006', 'Tiles074', 'PavingStones128', 'Asphalt026B',
];

// Normaliza los nombres de ambientCG a diff/rough/nor/disp para que el código de Blender no dependa de ellos.
const MAPA_ACG = [
  [/_Color\.jpg$/i, 'diff.jpg'], [/_Roughness\.jpg$/i, 'rough.jpg'], [/_NormalGL\.jpg$/i, 'nor.jpg'],
  [/_Displacement\.jpg$/i, 'disp.jpg'], [/_Metalness\.jpg$/i, 'metal.jpg'], [/_Opacity\.jpg$/i, 'alpha.jpg'],
];

for (const id of ACG) {
  const carpeta = path.join(AQUI, 'texturas', 'acg', id);
  if (await existe(path.join(carpeta, 'diff.jpg'))) continue;
  await mkdir(carpeta, { recursive: true });
  const zip = path.join(carpeta, 'x.zip');
  await writeFile(zip, await bajar(`https://ambientcg.com/get?file=${id}_2K-JPG.zip`));
  execFileSync('tar', ['-xf', zip, '-C', carpeta]);
  await rm(zip);
  for (const f of await readdir(carpeta)) {
    const destino = MAPA_ACG.find(([re]) => re.test(f));
    if (destino) await rename(path.join(carpeta, f), path.join(carpeta, destino[1]));
    else if (!/\.jpg$/i.test(f) || /NormalDX|AmbientOcclusion/i.test(f)) await rm(path.join(carpeta, f), { force: true });
  }
  console.log(`✓ ambientCG ${id}`);
}

// ---------- Poly Haven: modelos glTF ----------
const MODELOS = [
  'street_lamp_01', 'street_lamp_02', 'water_manhole_cover', 'modular_street_seating', 'metal_trash_can',
  'planter_box_01', 'fire_hydrant', 'jacaranda_tree', 'tree_small_02', 'island_tree_01', 'concrete_road_barrier',
];

for (const id of MODELOS) {
  const carpeta = path.join(AQUI, 'modelos', id);
  if (await existe(path.join(carpeta, `${id}.gltf`))) continue;
  await mkdir(carpeta, { recursive: true });
  const info = await (await fetch(`https://api.polyhaven.com/files/${id}`)).json();
  const gltf = info.gltf?.['2k']?.gltf ?? info.gltf?.['1k']?.gltf;
  if (!gltf) {
    console.warn(`  ${id}: sin glTF`);
    continue;
  }
  await writeFile(path.join(carpeta, `${id}.gltf`), await bajar(gltf.url));
  for (const [rel, extra] of Object.entries(gltf.include ?? {})) {
    const destino = path.join(carpeta, rel);
    await mkdir(path.dirname(destino), { recursive: true });
    await writeFile(destino, await bajar(extra.url));
  }
  console.log(`✓ Poly Haven ${id}`);
}
console.log('Assets listos (licencia CC0: ambientcg.com y polyhaven.com)');
