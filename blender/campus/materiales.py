"""Materiales PBR: texturas fotográficas de Poly Haven + shaders procedurales (vidrio, follaje, autos)."""
import os

import bpy

TEXTURAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'texturas')
_cache = {}


def _hex(color):
    color = color.lstrip('#')
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)


def _nuevo(nombre):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    return mat, nt, bsdf


def _socket(nodo, nombre, tipo=None, salida=False):
    lista = nodo.outputs if salida else nodo.inputs
    for s in lista:
        if s.name == nombre and (tipo is None or s.type == tipo):
            return s
    raise KeyError(f'{nodo.name}: socket {nombre} ({tipo})')


def _mezcla(nt, factor, a, b):
    """Mezcla de colores con el nodo Mix moderno. a/b/factor pueden ser sockets o valores."""
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    for destino, valor in ((_socket(mix, 'Factor', 'VALUE'), factor), (_socket(mix, 'A', 'RGBA'), a), (_socket(mix, 'B', 'RGBA'), b)):
        if hasattr(valor, 'is_output'):
            nt.links.new(valor, destino)
        else:
            destino.default_value = valor
    return _socket(mix, 'Result', 'RGBA', salida=True)


def _coordenadas(nt, escala_m):
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapeo = nt.nodes.new('ShaderNodeMapping')
    s = 1.0 / escala_m
    mapeo.inputs['Scale'].default_value = (s, s, s)
    nt.links.new(coord.outputs['Object'], mapeo.inputs['Vector'])
    return mapeo.outputs['Vector']


def _imagen(nt, ruta, vector, color=True):
    nodo = nt.nodes.new('ShaderNodeTexImage')
    nodo.image = bpy.data.images.load(ruta, check_existing=True)
    if not color:
        nodo.image.colorspace_settings.name = 'Non-Color'
    nodo.projection = 'BOX'
    nodo.projection_blend = 0.25
    nt.links.new(vector, nodo.inputs['Vector'])
    return nodo


def _variar_por_objeto(nt, color, rango_valor=(0.8, 1.12), rango_tono=0.025):
    """Cada objeto recibe un brillo y un matiz ligeramente distintos (Object Info > Random)."""
    info = nt.nodes.new('ShaderNodeObjectInfo')
    valor = nt.nodes.new('ShaderNodeMapRange')
    valor.inputs['To Min'].default_value, valor.inputs['To Max'].default_value = rango_valor
    nt.links.new(info.outputs['Random'], valor.inputs['Value'])
    tono = nt.nodes.new('ShaderNodeMapRange')
    tono.inputs['To Min'].default_value = 0.5 - rango_tono
    tono.inputs['To Max'].default_value = 0.5 + rango_tono
    nt.links.new(info.outputs['Random'], tono.inputs['Value'])
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    nt.links.new(color, hsv.inputs['Color'])
    nt.links.new(valor.outputs['Result'], hsv.inputs['Value'])
    nt.links.new(tono.outputs['Result'], hsv.inputs['Hue'])
    return hsv.outputs['Color']


def textura(nombre, tex_id, escala_m, tinte=None, rugosidad=1.0, normal=0.6, variacion=0.15, metal=0.0, mezcla=0.35, por_objeto=False):
    """Material fotográfico con proyección box en coordenadas de objeto (metros reales).

    escala_m: metros que abarca un mosaico de la textura. variacion: manchas grandes de
    tono para que el mosaico no se note desde la vista aérea. mezcla: cuánto pesa el tinte."""
    clave = (nombre,)
    if clave in _cache:
        return _cache[clave]
    mat, nt, bsdf = _nuevo(nombre)
    carpeta = os.path.join(TEXTURAS, tex_id)
    vec = _coordenadas(nt, escala_m)

    diff = _imagen(nt, os.path.join(carpeta, 'diff.jpg'), vec)
    color = diff.outputs['Color']
    if tinte:
        # mezcla parcial con el tinte: unifica la paleta sin perder el detalle fotográfico
        color = _mezcla(nt, mezcla, color, _hex(tinte))
    if variacion > 0:
        # manchas de ~50 m que oscurecen hasta `variacion`: rompen la repetición del mosaico
        ruido = nt.nodes.new('ShaderNodeTexNoise')
        coord = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(coord.outputs['Object'], ruido.inputs['Vector'])
        ruido.inputs['Scale'].default_value = 0.02
        rampa = nt.nodes.new('ShaderNodeMapRange')
        rampa.inputs['From Min'].default_value = 0.35
        rampa.inputs['From Max'].default_value = 0.65
        rampa.inputs['To Min'].default_value = 0.0
        rampa.inputs['To Max'].default_value = variacion
        nt.links.new(ruido.outputs['Fac'], rampa.inputs['Value'])
        color = _mezcla(nt, rampa.outputs['Result'], color, (0.0, 0.0, 0.0, 1.0))
    if por_objeto:
        color = _variar_por_objeto(nt, color)
    nt.links.new(color, bsdf.inputs['Base Color'])

    ruta_rough = os.path.join(carpeta, 'rough.jpg')
    if os.path.exists(ruta_rough):
        rough = _imagen(nt, ruta_rough, vec, color=False)
        mult = nt.nodes.new('ShaderNodeMath')
        mult.operation = 'MULTIPLY'
        mult.inputs[1].default_value = rugosidad
        nt.links.new(rough.outputs['Color'], mult.inputs[0])
        nt.links.new(mult.outputs['Value'], bsdf.inputs['Roughness'])
    ruta_nor = os.path.join(carpeta, 'nor.jpg')
    if os.path.exists(ruta_nor) and normal > 0:
        nor = _imagen(nt, ruta_nor, vec, color=False)
        mapa = nt.nodes.new('ShaderNodeNormalMap')
        mapa.inputs['Strength'].default_value = normal
        nt.links.new(nor.outputs['Color'], mapa.inputs['Color'])
        nt.links.new(mapa.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = metal
    _cache[clave] = mat
    return mat


def pintura(nombre, color, rugosidad=0.5, metal=0.0, emision=None, fuerza=0.0):
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    bsdf.inputs['Base Color'].default_value = _hex(color)
    bsdf.inputs['Roughness'].default_value = rugosidad
    bsdf.inputs['Metallic'].default_value = metal
    if emision:
        bsdf.inputs['Emission Color'].default_value = _hex(emision)
        bsdf.inputs['Emission Strength'].default_value = fuerza
    _cache[nombre] = mat
    return mat


def _rejilla(nt, eje, paso, grosor):
    """Máscara 1 en líneas periódicas a lo largo de un eje de coordenadas de objeto."""
    coord = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(coord.outputs['Object'], sep.inputs['Vector'])
    div = nt.nodes.new('ShaderNodeMath')
    div.operation = 'DIVIDE'
    div.inputs[1].default_value = paso
    nt.links.new(sep.outputs[eje], div.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath')
    fr.operation = 'FRACT'
    nt.links.new(div.outputs['Value'], fr.inputs[0])
    menor = nt.nodes.new('ShaderNodeMath')
    menor.operation = 'LESS_THAN'
    menor.inputs[1].default_value = grosor / paso
    nt.links.new(fr.outputs['Value'], menor.inputs[0])
    return menor.outputs['Value']


def _maximo(nt, a, b):
    m = nt.nodes.new('ShaderNodeMath')
    m.operation = 'MAXIMUM'
    nt.links.new(a, m.inputs[0])
    nt.links.new(b, m.inputs[1])
    return m.outputs['Value']


def vidrio_fachada(nombre='Vidrio Fachada', tono='#2b3a4a', marco='#c9ccd0', modulo=1.6, piso=3.6, faja=0.9):
    """Muro cortina: vidrio reflejante con parteluces verticales y fajas de entrepiso."""
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    lineas = _maximo(nt, _rejilla(nt, 'X', modulo, 0.12), _rejilla(nt, 'Y', modulo, 0.12))
    lineas = _maximo(nt, lineas, _rejilla(nt, 'Z', piso, faja))
    nt.links.new(_mezcla(nt, lineas, _hex(tono), _hex(marco)), bsdf.inputs['Base Color'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = 0.04
    rough.inputs['To Max'].default_value = 0.45
    nt.links.new(lineas, rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'], bsdf.inputs['Roughness'])
    metal = nt.nodes.new('ShaderNodeMapRange')
    metal.inputs['To Min'].default_value = 0.55
    metal.inputs['To Max'].default_value = 0.2
    nt.links.new(lineas, metal.inputs['Value'])
    nt.links.new(metal.outputs['Result'], bsdf.inputs['Metallic'])
    _cache[nombre] = mat
    return mat


def follaje(nombre='Follaje'):
    """Copas de árbol: verde con variación por instancia (Object Info > Random) y relieve."""
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    info = nt.nodes.new('ShaderNodeObjectInfo')
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    els = rampa.color_ramp.elements
    els[0].position, els[0].color = 0.0, _hex('#2f4a22')
    els[1].position, els[1].color = 1.0, _hex('#5b7a34')
    medio = els.new(0.55)
    medio.color = _hex('#40602a')
    nt.links.new(info.outputs['Random'], rampa.inputs['Fac'])
    ruido = nt.nodes.new('ShaderNodeTexNoise')
    ruido.inputs['Scale'].default_value = 2.5
    ruido.inputs['Detail'].default_value = 8
    color = _mezcla(nt, ruido.outputs['Fac'], rampa.outputs['Color'], _hex('#6f8f3e'))
    nt.links.new(color, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Subsurface Weight'].default_value = 0.08
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    nt.links.new(ruido.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    _cache[nombre] = mat
    return mat


def carroceria(nombre='Carroceria'):
    """Colores reales de autos (blanco, plata, gris, negro, azul, rojo) por instancia."""
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    info = nt.nodes.new('ShaderNodeObjectInfo')
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    rampa.color_ramp.interpolation = 'CONSTANT'
    colores = ['#f2f2f0', '#f2f2f0', '#b8bcc2', '#6e7378', '#1d1f22', '#24406e', '#8a1e1e', '#dcdcd8']
    els = rampa.color_ramp.elements
    els[0].position, els[0].color = 0.0, _hex(colores[0])
    els[1].position, els[1].color = 1.0, _hex(colores[-1])
    for i, c in enumerate(colores[1:-1], start=1):
        e = els.new(i / len(colores))
        e.color = _hex(c)
    nt.links.new(info.outputs['Random'], rampa.inputs['Fac'])
    nt.links.new(rampa.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.25
    bsdf.inputs['Metallic'].default_value = 0.4
    bsdf.inputs['Coat Weight'].default_value = 0.8
    _cache[nombre] = mat
    return mat


def agua(nombre='Agua'):
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    bsdf.inputs['Base Color'].default_value = _hex('#1f5f7a')
    bsdf.inputs['Roughness'].default_value = 0.03
    bsdf.inputs['Metallic'].default_value = 0.3
    ruido = nt.nodes.new('ShaderNodeTexNoise')
    ruido.inputs['Scale'].default_value = 1.5
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    nt.links.new(ruido.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    _cache[nombre] = mat
    return mat


def imagen_alfa(nombre, ruta):
    """Logo u otra imagen con transparencia sobre un plano."""
    if nombre in _cache:
        return _cache[nombre]
    mat, nt, bsdf = _nuevo(nombre)
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(ruta, check_existing=True)
    coord = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(coord.outputs['UV'], img.inputs['Vector'])
    nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(img.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.4
    _cache[nombre] = mat
    return mat


def paleta():
    """Materiales compartidos de la escena."""
    return {
        'asfalto': textura('Asfalto', 'asphalt_02', 6.0, tinte='#3f4247', variacion=0.25, mezcla=0.5),
        'banqueta': textura('Concreto Banqueta', 'concrete_pavement_02', 3.0, tinte='#a9aaa6', variacion=0.12, mezcla=0.5),
        'plaza': textura('Plaza Adoquin', 'brick_pavement_02', 2.5, tinte='#b9b2a6', variacion=0.1),
        'cesped': textura('Cesped', 'leafy_grass', 4.0, tinte='#3f6b2a', variacion=0.3, normal=0.3, mezcla=0.75),
        'grava': textura('Grava', 'bicolour_gravel', 3.0, tinte='#9a958c', variacion=0.2, mezcla=0.3),
        'fachada': textura('Fachada Concreto', 'precast_concrete_wall', 6.0, tinte='#d8d6d0', variacion=0.08, por_objeto=True),
        'lamina': textura('Lamina Industrial', 'box_profile_metal_sheet', 3.0, tinte='#b8bdc3', metal=0.5, variacion=0.1, mezcla=0.75, por_objeto=True),
        'lamina_azul': textura('Lamina Azul', 'box_profile_metal_sheet', 3.0, tinte='#2d4d78', metal=0.4, variacion=0.1, mezcla=0.75),
        'azotea': textura('Azotea', 'concrete_floor_worn_001', 5.0, tinte='#bdbcb8', variacion=0.15, por_objeto=True),
        'terreno': textura('Terreno', 'aerial_grass_rock', 25.0, tinte='#4a6b32', variacion=0.3, normal=0.4, mezcla=0.55),
        'vidrio': vidrio_fachada(),
        'vidrio_oscuro': pintura('Vidrio Oscuro', '#1b2430', 0.06, 0.6),
        'blanco': pintura('Pintura Blanca', '#e8e8e4', 0.6),
        'gris': pintura('Gris Metal', '#8f959c', 0.45, 0.7),
        'gris_oscuro': pintura('Gris Oscuro', '#3a3e44', 0.6, 0.3),
        'amarillo': pintura('Amarillo Seguridad', '#e3b322', 0.45, 0.2),
        'azul_tanque': pintura('Azul Tanque', '#1f6fd1', 0.35),
        'oxido': pintura('Acero Oxidado', '#6b3f27', 0.75, 0.5),
        'acero': pintura('Acero Galvanizado', '#9aa1a8', 0.35, 0.9),
        'panel_solar': vidrio_fachada('Panel Solar', tono='#14233f', marco='#9aa6b5', modulo=1.0, piso=1.7, faja=0.05),
        'pintura_vial': pintura('Pintura Vial', '#f2f0e8', 0.6),
        'amarillo_vial': pintura('Pintura Vial Amarilla', '#e9c23a', 0.6),
        'tronco': pintura('Tronco', '#4a3a2c', 0.9),
        'follaje': follaje(),
        'carroceria': carroceria(),
        'llanta': pintura('Llanta', '#151618', 0.8),
        'agua': agua(),
        'tierra': pintura('Agregado', '#a39a8a', 0.95),
        'madera': pintura('Madera', '#8b6a42', 0.7),
        'carton': pintura('Carton', '#b88a52', 0.85),
        'led': pintura('LED', '#ffffff', 0.3, emision='#fff4d6', fuerza=2.0),
        'baliza': pintura('Baliza', '#ff2a2a', 0.3, emision='#ff2a2a', fuerza=8.0),
        'verde_techo': textura('Techo Verde', 'leafy_grass', 2.0, tinte='#4f7a33', variacion=0.2),
    }
