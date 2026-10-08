"""Ruta de cámara del recorrido con scroll: aérea → alumbrado → vialidad → alcantarillado → parabuses →
CCTV → tinacos → plaza → aérea final.

Cada clave: (frame, posición de cámara, objetivo, focal mm, apertura f). Entre paradas la cámara viaja
por el eje de la avenida (y ≈ 0), que está libre de edificios, para no atravesar construcciones.
La web usa `paradas` (rango de frames de cada escena) para mostrar los textos.
"""
import bpy  # noqa: E402  (math se importa junto a las funciones de cámara)

import math


def _isometrica(azimut, elevacion=35.0, distancia=1650.0):
    """Posición de cámara para la vista casi isométrica (teleobjetivo largo, poca perspectiva)."""
    a, e = math.radians(azimut), math.radians(elevacion)
    return (math.sin(a) * math.cos(e) * distancia, -math.cos(a) * math.cos(e) * distancia, math.sin(e) * distancia)


CLAVES = [
    (1, _isometrica(-45), (0, 0, -20), 50, 22),
    (20, _isometrica(-41), (0, 0, -20), 50, 22),
    # bajada al alumbrado: alto sobre las torres de la avenida y luego por el arroyo vehicular (y = -6),
    # nunca sobre las manzanas a baja altura (antes la cámara atravesaba una casa entre los frames 71 y 76)
    (48, (-175, -40, 90), (-160, 0, 5), 40, 16),
    (60, (-150, -6, 40), (-160, 0, 5), 35, 16),
    # junto a la guarnición (y = -11.2): fuera de las copas de los árboles de banqueta (y ≈ -13.6)
    (90, (-122, -11.2, 2.0), (-162, 0, 5), 30, 5.6),
    (112, (-126, -11.0, 2.1), (-162, 0, 5), 30, 5.6),
    (150, (-72, 10.3, 1.4), (-87, 6.2, 0.0), 28, 4.0),
    (168, (-73, 10.1, 1.4), (-87, 6.2, 0.0), 28, 4.0),
    (195, (-71.5, 7.6, 1.0), (-77.5, 11.6, 0.0), 32, 3.5),
    (213, (-72.3, 7.4, 1.0), (-77.5, 11.6, 0.0), 32, 3.5),
    (250, (-31, 3.2, 1.9), (-41, 14.6, 1.3), 26, 5.6),
    (270, (-32.5, 3.0, 1.9), (-41, 14.6, 1.3), 26, 5.6),
    (308, (12.0, 9.0, 1.8), (8.6, 13.8, 8.6), 28, 5.6),
    (328, (12.6, 8.6, 1.8), (8.6, 13.8, 8.6), 28, 5.6),
    # tinacos: se sube por encima de las torres de la avenida y se baja sobre azoteas residenciales
    (350, (-40, 0, 55), (-120, 80, 10), 30, 16),
    (376, (-130, 84, 22), (-130, 112, 9), 30, 8),
    (396, (-126, 84, 22), (-130, 112, 9), 30, 8),
    (420, (-50, 50, 55), (40, 50, 5), 28, 16),
    (450, (18, 19, 5.5), (52, 58, 2.5), 24, 8),
    (470, (21, 21, 5.3), (52, 58, 2.5), 24, 8),
    (540, _isometrica(-30), (0, 0, -20), 50, 22),
]

# Fondo visible para la cámara: 1 = negro (como la página), 0 = cielo. La iluminación siempre es el cielo.
FONDO_NEGRO = [(1, 1.0), (24, 1.0), (75, 0.0), (480, 0.0), (530, 1.0)]

FRAME_FINAL = CLAVES[-1][0]

PARADAS = [
    {'id': 'ciudad', 'desde': 1, 'hasta': 35, 'titulo': 'Soluciones para toda la ciudad',
     'texto': 'Recorre cómo los productos AmUrb mejoran calles, plazas y servicios urbanos.'},
    {'id': 'alumbrado', 'desde': 80, 'hasta': 120, 'titulo': 'Alumbrado público y solar',
     'texto': 'Luminarias con panel solar, faroles de hierro y luminarias LED para avenidas y camellones.'},
    {'id': 'vialidad', 'desde': 140, 'hasta': 175, 'titulo': 'Seguridad vial',
     'texto': 'Bolardos divisores de carril trapezoidales 120-15-9.5 para confinar y ordenar el tránsito.'},
    {'id': 'alcantarillado', 'desde': 185, 'hasta': 220, 'titulo': 'Alcantarillado',
     'texto': 'Brocales con tapa para pozos de visita y coladeras pluviales de hierro.'},
    {'id': 'parabuses', 'desde': 240, 'hasta': 278, 'titulo': 'Parabuses',
     'texto': 'Parabuses Elle y Contempo, personalizables con celosía, logotipos y alumbrado.'},
    {'id': 'cctv', 'desde': 298, 'hasta': 335, 'titulo': 'Videovigilancia CCTV',
     'texto': 'Postes con cámaras, domo PTZ, botón de pánico y altavoz para cruces seguros.'},
    {'id': 'tinacos', 'desde': 368, 'hasta': 402, 'titulo': 'Hidráulicos: tinacos',
     'texto': 'Almacenamiento de agua para viviendas y edificios.'},
    {'id': 'plaza', 'desde': 440, 'hasta': 478, 'titulo': 'Espacio público',
     'texto': 'Faroles de hierro, bancas, botes y jardineras para plazas y jardines.'},
    {'id': 'final', 'desde': 505, 'hasta': FRAME_FINAL, 'titulo': 'Infraestructura que transforma ciudades',
     'texto': 'Ambiental y Urbanística de Michoacán.'},
]


def animar(cam):
    """Anima la cámara siguiendo un Empty objetivo (Track To) con enfoque automático al objetivo."""
    esc = bpy.context.scene
    objetivo = bpy.data.objects.new('Objetivo Camara', None)
    esc.collection.objects.link(objetivo)
    restr = cam.constraints.new('TRACK_TO')
    restr.target = objetivo
    restr.track_axis = 'TRACK_NEGATIVE_Z'
    restr.up_axis = 'UP_Y'
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = objetivo
    for frame, pos, obj, focal, apertura in CLAVES:
        cam.location = pos
        cam.keyframe_insert('location', frame=frame)
        objetivo.location = obj
        objetivo.keyframe_insert('location', frame=frame)
        cam.data.lens = focal
        cam.data.keyframe_insert('lens', frame=frame)
        cam.data.dof.aperture_fstop = apertura
        cam.data.dof.keyframe_insert('aperture_fstop', frame=frame)
    # curvas suaves sin rebases (auto clamped) para no salirse del corredor de la avenida
    for datos in (cam.animation_data, objetivo.animation_data, cam.data.animation_data):
        for curva in datos.action.fcurves if hasattr(datos.action, 'fcurves') else _curvas(datos.action):
            for k in curva.keyframe_points:
                k.interpolation = 'BEZIER'
                k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
    _fondo_negro_animado()
    esc.frame_start, esc.frame_end = 1, FRAME_FINAL
    return objetivo


def _fondo_negro_animado():
    """Inserta en el mundo un mezclador: la cámara ve negro (según FONDO_NEGRO) y la luz sigue siendo el cielo."""
    nt = bpy.context.scene.world.node_tree
    salida = nt.nodes.get('World Output')
    fondo_cielo = nt.nodes.get('Background')
    negro = nt.nodes.new('ShaderNodeBackground')
    negro.inputs['Color'].default_value = (0, 0, 0, 1)
    camino = nt.nodes.new('ShaderNodeLightPath')
    valor = nt.nodes.new('ShaderNodeValue')
    valor.name = 'Fondo Negro'
    mult = nt.nodes.new('ShaderNodeMath')
    mult.operation = 'MULTIPLY'
    nt.links.new(camino.outputs['Is Camera Ray'], mult.inputs[0])
    nt.links.new(valor.outputs['Value'], mult.inputs[1])
    mezcla = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mult.outputs['Value'], mezcla.inputs['Fac'])
    nt.links.new(fondo_cielo.outputs['Background'], mezcla.inputs[1])
    nt.links.new(negro.outputs['Background'], mezcla.inputs[2])
    nt.links.new(mezcla.outputs['Shader'], salida.inputs['Surface'])
    for frame, v in FONDO_NEGRO:
        valor.outputs['Value'].default_value = v
        valor.outputs['Value'].keyframe_insert('default_value', frame=frame)


def _curvas(accion):
    """Blender 5 guarda las curvas en capas/tiras/canales; esto las recorre todas."""
    for capa in accion.layers:
        for tira in capa.strips:
            for bolsa in tira.channelbags:
                yield from bolsa.fcurves
