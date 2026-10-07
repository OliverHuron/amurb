"""Mundo (cielo físico), cámara isométrica ortográfica, ajustes de Cycles y exportación de hotspots."""
import json
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view

from . import geo


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def cielo(elevacion_sol=42.0, rotacion_sol=-35.0, fuerza=0.12):
    mundo = bpy.data.worlds.new('Cielo')
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    nt = mundo.node_tree
    fondo = nt.nodes.get('Background')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(elevacion_sol)
    sky.sun_rotation = math.radians(rotacion_sol)
    sky.altitude = 400
    sky.air_density = 1.0
    sky.aerosol_density = 1.3
    sky.sun_size = math.radians(0.6)
    nt.links.new(sky.outputs['Color'], fondo.inputs['Color'])
    fondo.inputs['Strength'].default_value = fuerza


def camara(azimut=-30.0, elevacion=35.0, escala=370.0, objetivo=(0, -4, 0), distancia=900.0):
    """Cámara ortográfica (isométrica real) montada en un pivote que gira para la órbita 360°."""
    pivote = bpy.data.objects.new('Pivote Camara', None)
    pivote.location = objetivo
    bpy.context.scene.collection.objects.link(pivote)
    datos = bpy.data.cameras.new('Camara Isometrica')
    datos.type = 'ORTHO'
    datos.ortho_scale = escala
    datos.clip_start = 1
    datos.clip_end = 5000
    cam = bpy.data.objects.new('Camara Isometrica', datos)
    bpy.context.scene.collection.objects.link(cam)
    el, az = math.radians(elevacion), math.radians(azimut)
    cam.location = (math.sin(az) * math.cos(el) * distancia, -math.cos(az) * math.cos(el) * distancia, math.sin(el) * distancia)
    cam.rotation_euler = (math.pi / 2 - el, 0, az)
    cam.parent = pivote
    bpy.context.scene.camera = cam
    return cam, pivote


def ajustes(ancho=1920, alto=1080, muestras=128):
    esc = bpy.context.scene
    esc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    esc.cycles.device = 'GPU'
    esc.cycles.samples = muestras
    esc.cycles.use_adaptive_sampling = True
    esc.cycles.adaptive_threshold = 0.02
    esc.cycles.use_denoising = True
    esc.cycles.denoiser = 'OPENIMAGEDENOISE'
    esc.cycles.max_bounces = 6
    esc.render.resolution_x, esc.render.resolution_y = ancho, alto
    esc.render.resolution_percentage = 100
    esc.render.film_transparent = False
    esc.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            esc.view_settings.look = look
            break
        except TypeError:
            continue
    esc.view_settings.exposure = 0.0
    esc.render.image_settings.file_format = 'PNG'


def anclas():
    col = bpy.data.collections.get('Interactivos')
    return [] if col is None else list(col.objects)


def proyectar_hotspots(cam):
    """Posición 2D normalizada (0..1, origen arriba-izquierda) de cada ancla en el frame actual."""
    esc = bpy.context.scene
    puntos = {}
    for obj in anclas():
        v = world_to_camera_view(esc, cam, obj.matrix_world.translation)
        puntos[obj.name] = [round(v.x, 4), round(1 - v.y, 4)]
    return puntos


def metadatos_hotspots():
    return {o.name: {'tipo': o.get('tipo'), 'titulo': o.get('titulo')} for o in anclas()}


def guardar_json(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)


__all__ = ['limpiar', 'cielo', 'camara', 'ajustes', 'proyectar_hotspots', 'metadatos_hotspots', 'guardar_json', 'geo']
