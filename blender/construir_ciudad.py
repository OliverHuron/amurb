"""Ciudad fotorrealista con los productos AmUrb aplicados, para el recorrido con scroll.

Uso (desde la raíz del proyecto):
  blender -b --factory-startup --python blender/construir_ciudad.py -- --tomas aereo,parabus
  blender -b --factory-startup --python blender/construir_ciudad.py -- --modo solo-escena

Tomas: aereo, alumbrado, vialidad, parabus, plaza (o "todas").
Salidas: blender/ciudad.blend y blender/render/ciudad_<toma>.png
"""
import argparse
import math
import os
import random
import sys
import time

import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

from campus import escena, geo, materiales, piezas  # noqa: E402
from ciudad import recorrido as R  # noqa: E402
from ciudad import urbano as U  # noqa: E402

# toma -> (posición de cámara, objetivo, focal mm, apertura f o None)
TOMAS = {
    'aereo': ((-330, -430, 330), (-40, 10, 0), 50, None),
    'alumbrado': ((-122, -17.0, 2.2), (-162, 0.0, 5.0), 30, 5.6),
    'vialidad': ((-72, 10.3, 1.4), (-87, 6.2, 0.0), 28, 4.0),
    'parabus': ((-31, 3.2, 1.9), (-41, 14.6, 1.3), 26, 5.6),
    'plaza': ((18, 19, 5.5), (52, 58, 2.5), 24, 8.0),
}


def argumentos():
    p = argparse.ArgumentParser()
    p.add_argument('--modo', choices=('tomas', 'solo-escena', 'recorrido'), default='tomas')
    p.add_argument('--previa', action='store_true', help='recorrido: solo un frame por parada, a baja resolución')
    p.add_argument('--desde', type=int, default=1)
    p.add_argument('--hasta', type=int, default=0)
    p.add_argument('--solo-frames', default='', help='recorrido: frames sueltos de prueba, p. ej. 1,318 (a media resolución)')
    p.add_argument('--subframes', action='store_true', help='recorrido: renderiza los tiempos de render/subframes.json')
    p.add_argument('--tomas', default='aereo,parabus')
    p.add_argument('--muestras', type=int, default=160)
    p.add_argument('--ancho', type=int, default=1920)
    p.add_argument('--alto', type=int, default=1080)
    p.add_argument('--cielo', type=float, default=0.06)
    p.add_argument('--semilla', type=int, default=7)
    return p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def camara_perspectiva():
    datos = bpy.data.cameras.new('Camara Recorrido')
    datos.clip_start = 0.1
    datos.clip_end = 6000
    cam = bpy.data.objects.new('Camara Recorrido', datos)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def apuntar(cam, pos, objetivo, focal, apertura):
    cam.location = pos
    direccion = Vector(objetivo) - Vector(pos)
    cam.rotation_euler = direccion.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = focal
    cam.data.dof.use_dof = apertura is not None
    if apertura:
        cam.data.dof.aperture_fstop = apertura
        cam.data.dof.focus_distance = direccion.length


def construir(args):
    t0 = time.time()
    escena.limpiar()
    rnd = random.Random(args.semilla)
    M = U.paleta_ciudad(materiales.paleta())
    # árboles reales de Poly Haven (los procedurales del campus se ven de juguete junto a ellos)
    jacaranda = U.modelo('jacaranda_tree')
    arbol_chico = U.modelo('tree_small_02')
    arbol_isla = U.modelo('island_tree_01')
    arboles = [arbol_chico, arbol_isla]
    logo = os.path.join(RAIZ, 'public', 'brand', 'logo.webp')
    logo_mat = materiales.imagen_alfa('Logo AmUrb', logo) if os.path.exists(logo) else None

    geo.usar_coleccion(geo.coleccion('Ciudad'))
    U.vialidades(M)
    for i, rect in enumerate(U.manzanas()):
        sobre_av = rect[2] == U.BORDE_AV or rect[3] == -U.BORDE_AV
        construible = U.banqueta_manzana(f'Manzana {i}', *rect, M, ancho=U.BANQUETA if sobre_av else 3.0)
        es_plaza = sobre_av and rect[0] < 50 < rect[1] and rect[2] > 0
        if es_plaza:
            continue
        U.poblar_manzana(f'Manzana {i}', construible, M, rnd, sobre_avenida=sobre_av)
        U.arboles_banqueta(rect, arboles, rnd, paso=12 if sobre_av else 16)

    geo.usar_coleccion(geo.coleccion('Productos'))
    U.vineta_alumbrado(M, arbol_isla)
    U.vineta_vialidad(M)
    U.vineta_parabuses(M, logo_mat)
    U.vineta_plaza(M, rnd)
    U.vineta_cctv(M)
    # jacarandas en el resto del camellón
    for x in range(-320, 330, 18):
        if not (-195 < x < -105) and not any(abs(x - cx) < 14 for cx in U.CALLES_X):
            geo.instancia('Jacaranda Camellon', jacaranda, (x, 0, 0.22), rnd.uniform(0, 6.28), rnd.uniform(0.38, 0.48))
    U.anclas_paradas()

    # sol del sur-suroeste (latitud de México): ilumina las fachadas que miran a la cámara
    escena.cielo(elevacion_sol=48, rotacion_sol=140, fuerza=args.cielo)
    escena.ajustes(args.ancho, args.alto, args.muestras)
    cam = camara_perspectiva()
    print(f'[ciudad] escena construida en {time.time() - t0:.1f}s: {len(bpy.data.objects)} objetos')
    return cam


def recorrido(args, cam, salida):
    """Renderiza la animación de cámara frame por frame (reanudable con --desde/--hasta)."""
    import json
    R.animar(cam)
    esc = bpy.context.scene
    carpeta = os.path.join(salida, 'recorrido-previa' if (args.previa or args.solo_frames) else 'recorrido')
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(salida, 'recorrido.json'), 'w', encoding='utf-8') as f:
        json.dump({'frames': R.FRAME_FINAL, 'paradas': R.PARADAS}, f, ensure_ascii=False, indent=1)
    if args.subframes:
        # frames intermedios (tiempos fraccionarios) en los tramos donde la cámara se mueve rápido
        with open(os.path.join(salida, 'subframes.json'), encoding='utf-8') as f:
            tiempos = json.load(f)['tiempos']
        carpeta_sub = os.path.join(salida, 'recorrido-sub')
        os.makedirs(carpeta_sub, exist_ok=True)
        for n, t in enumerate(tiempos, start=1):
            entero = int(t)
            fraccion = round(t - entero, 2)
            ruta = os.path.join(carpeta_sub, f'frame_{entero:04d}_{int(fraccion * 100):02d}.png')
            if os.path.exists(ruta):
                continue
            esc.frame_set(entero, subframe=fraccion)
            esc.render.filepath = ruta
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'[ciudad] subframe {n}/{len(tiempos)} ({t}) en {time.time() - t0:.1f}s', flush=True)
        return
    if args.previa or args.solo_frames:
        frames = [int(f) for f in args.solo_frames.split(',')] if args.solo_frames else \
            sorted({(p['desde'] + p['hasta']) // 2 for p in R.PARADAS})
        esc.render.resolution_percentage = 50
    else:
        frames = range(args.desde, (args.hasta or R.FRAME_FINAL) + 1)
    for f in frames:
        ruta = os.path.join(carpeta, f'frame_{f:04d}.png')
        if not (args.previa or args.solo_frames) and os.path.exists(ruta):
            continue  # reanudar sin repetir frames ya renderizados
        esc.frame_set(f)
        esc.render.filepath = ruta
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[ciudad] frame {f}/{R.FRAME_FINAL} en {time.time() - t0:.1f}s', flush=True)


def main():
    args = argumentos()
    cam = construir(args)
    salida = os.path.join(AQUI, 'render')
    os.makedirs(salida, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, 'ciudad.blend'))
    if args.modo == 'solo-escena':
        return
    if args.modo == 'recorrido':
        recorrido(args, cam, salida)
        return
    nombres = list(TOMAS) if args.tomas == 'todas' else args.tomas.split(',')
    for nombre in nombres:
        pos, objetivo, focal, apertura = TOMAS[nombre]
        apuntar(cam, pos, objetivo, focal, apertura)
        bpy.context.scene.render.filepath = os.path.join(salida, f'ciudad_{nombre}.png')
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[ciudad] toma {nombre} en {time.time() - t0:.1f}s', flush=True)


main()
