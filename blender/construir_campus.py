"""Genera el campus fotorrealista de AmUrb en Blender y lo renderiza con Cycles.

Uso (desde la raíz del proyecto):
  blender -b --factory-startup --python blender/construir_campus.py -- --modo still
  blender -b --factory-startup --python blender/construir_campus.py -- --modo orbita --frames 120

Opciones: --muestras N, --ancho W, --alto H, --azimut grados, --sin-contexto
Salidas: blender/campus.blend, blender/render/still.png o blender/render/orbita/frame_0001.png…,
         blender/render/hotspots.json (posición 2D de cada interactivo por frame).
"""
import argparse
import math
import os
import sys
import time

import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

from campus import entorno, escena, geo, materiales, piezas, zonas  # noqa: E402


def argumentos():
    p = argparse.ArgumentParser()
    p.add_argument('--modo', choices=('still', 'orbita', 'solo-escena'), default='still')
    p.add_argument('--frames', type=int, default=120)
    p.add_argument('--muestras', type=int, default=128)
    p.add_argument('--ancho', type=int, default=1920)
    p.add_argument('--alto', type=int, default=1080)
    p.add_argument('--azimut', type=float, default=-30.0)
    p.add_argument('--sin-contexto', action='store_true')
    p.add_argument('--cielo', type=float, default=0.12, help='intensidad del cielo físico')
    p.add_argument('--salida', default='still.png')
    return p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def construir(args):
    t0 = time.time()
    escena.limpiar()
    M = materiales.paleta()

    fuentes = geo.coleccion('Fuentes')
    F = {
        'arboles': piezas.arboles_fuente(M),
        'auto': piezas.auto_fuente(M),
        'camion': piezas.camion_fuente(M),
    }
    bpy.context.view_layer.layer_collection.children['Fuentes'].exclude = True
    del fuentes

    geo.usar_coleccion(geo.coleccion('Campus'))
    entorno.suelo(M)
    entorno.senalizacion(M)
    zonas.sede(M, F, RAIZ)
    zonas.cctv(M, F)
    zonas.textiles(M, F)
    zonas.logistica(M, F)
    zonas.ingenieria(M, F)
    zonas.calidad(M, F)
    zonas.construccion(M, F)
    zonas.acero(M, F)
    zonas.hidraulicos(M, F)
    zonas.electrico(M, F)
    entorno.muro_y_acceso(M, F)
    entorno.interactivos(M)
    if not args.sin_contexto:
        geo.usar_coleccion(geo.coleccion('Contexto'))
        entorno.ciudad_contexto(M, F)

    escena.cielo(fuerza=args.cielo)
    cam, pivote = escena.camara(azimut=args.azimut)
    escena.ajustes(args.ancho, args.alto, args.muestras)
    print(f'[campus] escena construida en {time.time() - t0:.1f}s: {len(bpy.data.objects)} objetos')
    return cam, pivote


def main():
    args = argumentos()
    cam, pivote = construir(args)
    salida = os.path.join(AQUI, 'render')
    os.makedirs(salida, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(AQUI, 'campus.blend'))
    esc = bpy.context.scene

    if args.modo == 'still':
        t0 = time.time()
        esc.render.filepath = os.path.join(salida, args.salida)
        bpy.ops.render.render(write_still=True)
        print(f'[campus] render en {time.time() - t0:.1f}s -> {esc.render.filepath}')
        escena.guardar_json(os.path.join(salida, 'hotspots-still.json'), {
            'meta': escena.metadatos_hotspots(), 'frames': [escena.proyectar_hotspots(cam)]})

    elif args.modo == 'orbita':
        carpeta = os.path.join(salida, 'orbita')
        os.makedirs(carpeta, exist_ok=True)
        frames = []
        for f in range(args.frames):
            pivote.rotation_euler[2] = 2 * math.pi * f / args.frames
            bpy.context.view_layer.update()
            frames.append(escena.proyectar_hotspots(cam))
            esc.render.filepath = os.path.join(carpeta, f'frame_{f + 1:04d}.png')
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'[campus] frame {f + 1}/{args.frames} en {time.time() - t0:.1f}s', flush=True)
        escena.guardar_json(os.path.join(salida, 'hotspots.json'), {
            'meta': escena.metadatos_hotspots(), 'frames': frames})


main()
