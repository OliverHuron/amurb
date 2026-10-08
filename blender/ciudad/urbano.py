"""Ciudad mexicana procedural (metros): avenida con camellón, manzanas, casas, torres y viñetas de producto.

Avenida principal a lo largo de X en y = 0. Escaparates de producto (paradas del recorrido):
  alumbrado  -> camellón x∈[-190,-110]: luminarias solares
  vialidad   -> cruce x = -100: bolardos, brocales y coladeras
  parabuses  -> x ≈ -40: parabús Elle (norte) y Contempo (sur)
  plaza      -> manzana x∈[10,90] norte: faroles de hierro, bancas, jardineras, botes
"""
import math
import os
import random

import bpy

from campus import geo
from campus import materiales as mt
from . import productos as P

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELOS = os.path.join(AQUI, 'modelos')

CAMELLON = 2.5        # medio ancho del camellón
CALZADA = 9.9         # 3 carriles de 3.3 m por sentido
BANQUETA = 4.5
BORDE_AV = CAMELLON + CALZADA          # 12.4: guarnición de la avenida
FRENTE_AV = BORDE_AV + BANQUETA        # 16.9: paramento de los edificios
CALLES_X = (-300, -200, -100, 0, 100, 200, 300)   # calles transversales
CALLES_Y = (-230, -160, -90, 90, 160, 230)         # calles paralelas a la avenida
ANCHO_CALLE = 14.0
LIMITE = (-300, 300, -300, 300)                    # mapa cuadrado (se ve como maqueta sobre fondo negro)
ESPESOR_BASE = 8.0


# ---------------------------------------------------------------- materiales de ciudad

def _muro_mexicano():
    """Aplanado pintado: textura de yeso + color por casa de una paleta mexicana."""
    nombre = 'Muro Aplanado'
    if nombre in mt._cache:
        return mt._cache[nombre]
    mat, nt, bsdf = mt._nuevo(nombre)
    vec = mt._coordenadas(nt, 3.0)
    yeso = mt._imagen(nt, os.path.join(mt.TEXTURAS, 'acg', 'PaintedPlaster006', 'diff.jpg'), vec)
    info = nt.nodes.new('ShaderNodeObjectInfo')
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    rampa.color_ramp.interpolation = 'CONSTANT'
    paleta = ['#e8e2d6', '#d9c6a1', '#e3b778', '#c96f4a', '#b8463a', '#f0d9a8', '#8fa6a3', '#d79b6a', '#efe9df', '#a64b3c', '#e1cfa9', '#cfd6cf']
    els = rampa.color_ramp.elements
    els[0].color = mt._hex(paleta[0])
    els[1].position, els[1].color = 1.0, mt._hex(paleta[-1])
    for i, c in enumerate(paleta[1:-1], start=1):
        els.new(i / len(paleta)).color = mt._hex(c)
    nt.links.new(info.outputs['Random'], rampa.inputs['Fac'])
    mult = nt.nodes.new('ShaderNodeMix')
    mult.data_type = 'RGBA'
    mult.blend_type = 'MULTIPLY'
    mt._socket(mult, 'Factor', 'VALUE').default_value = 0.85
    nt.links.new(rampa.outputs['Color'], mt._socket(mult, 'A', 'RGBA'))
    nt.links.new(yeso.outputs['Color'], mt._socket(mult, 'B', 'RGBA'))
    color = mt._mezcla(nt, 0.55, mt._socket(mult, 'Result', 'RGBA', salida=True), rampa.outputs['Color'])
    nt.links.new(color, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.85
    mt._cache[nombre] = mat
    return mat


def _azotea_mexicana():
    """Azoteas: impermeabilizante rojo, blanco o concreto gris según la casa."""
    nombre = 'Azotea Impermeabilizada'
    if nombre in mt._cache:
        return mt._cache[nombre]
    mat, nt, bsdf = mt._nuevo(nombre)
    vec = mt._coordenadas(nt, 5.0)
    base = mt._imagen(nt, os.path.join(mt.TEXTURAS, 'concrete_floor_worn_001', 'diff.jpg'), vec)
    info = nt.nodes.new('ShaderNodeObjectInfo')
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    rampa.color_ramp.interpolation = 'CONSTANT'
    els = rampa.color_ramp.elements
    els[0].color = mt._hex('#9a3d2c')
    els[1].position, els[1].color = 0.75, mt._hex('#8d8a84')
    els.new(0.45).color = mt._hex('#dcdad4')
    nt.links.new(info.outputs['Random'], rampa.inputs['Fac'])
    color = mt._mezcla(nt, 0.6, base.outputs['Color'], rampa.outputs['Color'])
    nt.links.new(color, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.8
    mt._cache[nombre] = mat
    return mat


def paleta_ciudad(M):
    M = P.materiales_productos(M)
    M['muro_mx'] = _muro_mexicano()
    M['azotea_mx'] = _azotea_mexicana()
    M['adoquin'] = mt.textura('Adoquin Plaza', 'acg/PavingStones128', 3.0, variacion=0.12)
    M['asfalto_av'] = mt.textura('Asfalto Avenida', 'acg/Asphalt026B', 7.0, tinte='#45484c', mezcla=0.3, variacion=0.25)
    M['guarnicion'] = mt.pintura('Guarnicion', '#c9c6be', 0.8)
    M['guarnicion_amarilla'] = mt.pintura('Guarnicion Amarilla', '#e2b43a', 0.7)
    M['ventana'] = mt.pintura('Vidrio Ventana', '#2a333c', 0.08, 0.5)
    M['marco_ventana'] = mt.pintura('Marco Ventana', '#e9e7e1', 0.5)
    M['herreria'] = mt.pintura('Herreria', '#1c1c1c', 0.5, 0.6)
    for fid, escala in (('Facade018A', 20), ('Facade019A', 20), ('Facade020A', 20), ('Facade006', 30),
                        ('Facade001', 34), ('Facade002', 34), ('Facade003', 34), ('Facade005', 34)):
        M[f'fachada_{fid}'] = mt.textura(f'Fachada {fid}', f'acg/{fid}', escala, variacion=0.05, normal=0.4)
    return M


# ---------------------------------------------------------------- modelos de Poly Haven

_fuentes = {}


def modelo(id_modelo, escala=1.0):
    """Importa un glTF de Poly Haven una sola vez en una colección fuente (excluida) para instanciar."""
    if id_modelo in _fuentes:
        return _fuentes[id_modelo]
    ruta = os.path.join(MODELOS, id_modelo, f'{id_modelo}.gltf')
    padre = geo.coleccion('Fuentes')
    col = geo.coleccion(f'Fuente {id_modelo}', padre)
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ruta)
    nuevos = [o for o in bpy.data.objects if o not in antes]
    for o in nuevos:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None:
            o.scale = (o.scale[0] * escala, o.scale[1] * escala, o.scale[2] * escala)
    capa = bpy.context.view_layer.layer_collection.children.get('Fuentes')
    if capa:
        capa.exclude = True
    _fuentes[id_modelo] = col
    return col


# ---------------------------------------------------------------- vialidades

def vialidades(M):
    piezas_linea = []
    x0, x1, y0, y1 = LIMITE
    lado = x1 - x0 + ANCHO_CALLE
    # base del mapa: losa con espesor (se ve el canto en la vista isométrica) y asfalto encima
    geo.caja('Base Mapa', (lado, lado, ESPESOR_BASE), (0, 0, -ESPESOR_BASE - 0.01), M['concreto_oscuro'])
    geo.plano('Asfalto Ciudad', lado, lado, (0, 0, 0.0), M['asfalto_av'])
    # camellón con césped y guarnición
    geo.caja('Camellon Guarnicion', (x1 - x0, CAMELLON * 2, 0.2), (0, 0, 0), M['guarnicion'])
    geo.caja('Camellon Cesped', (x1 - x0, CAMELLON * 2 - 0.4, 0.02), (0, 0, 0.2), M['cesped'])
    # líneas de carril de la avenida (discontinuas) y orilla
    for lado in (-1, 1):
        for k in (1, 2):
            yl = lado * (CAMELLON + 3.3 * k)
            x = x0
            while x < x1:
                if not any(abs(x - cx) < ANCHO_CALLE / 2 + 6 for cx in CALLES_X):
                    piezas_linea.append(geo.caja('Linea Carril', (3.0, 0.14, 0.012), (x + 1.5, yl, 0.0), M['pintura_vial']))
                x += 9
        piezas_linea.append(geo.caja('Linea Orilla', (x1 - x0, 0.14, 0.012), (0, lado * (BORDE_AV - 0.4), 0.0), M['pintura_vial']))
    # pasos peatonales en cada cruce de la avenida
    for cx in CALLES_X:
        for lado in (-1, 1):
            for i in range(int(CALZADA / 0.9)):
                yy = lado * (CAMELLON + 0.45 + i * 0.9)
                for off in (-ANCHO_CALLE / 2 - 3.2, ANCHO_CALLE / 2 + 3.2):
                    piezas_linea.append(geo.caja('Cebra', (4.0, 0.5, 0.012), (cx + off, yy, 0.0), M['pintura_vial']))
            piezas_linea.append(geo.caja('Alto', (0.4, CALZADA - 0.6, 0.012), (cx - lado * (ANCHO_CALLE / 2 + 5.8), lado * (CAMELLON + CALZADA / 2), 0.0), M['pintura_vial']))
    geo.unir('Pintura Vial', piezas_linea)


def manzanas():
    """Rectángulos de manzana (x0, x1, y0, y1) delimitados por avenida y calles."""
    xs = sorted(CALLES_X)
    ys = [-LIMITE[3], *sorted(CALLES_Y), LIMITE[3]]
    resultado = []
    for i in range(len(xs) - 1):
        ax0, ax1 = xs[i] + ANCHO_CALLE / 2, xs[i + 1] - ANCHO_CALLE / 2
        for j in range(len(ys) - 1):
            ay0, ay1 = ys[j] + ANCHO_CALLE / 2, ys[j + 1] - ANCHO_CALLE / 2
            if ay0 < 0 < ay1:
                # la avenida parte la franja central en dos manzanas
                resultado.append((ax0, ax1, ay0, -BORDE_AV))
                resultado.append((ax0, ax1, BORDE_AV, ay1))
            else:
                resultado.append((ax0, ax1, ay0, ay1))
    return resultado


def banqueta_manzana(nombre, x0, x1, y0, y1, M, ancho=3.0):
    """Guarnición y banqueta perimetral; devuelve el rectángulo construible."""
    geo.caja(f'{nombre} Banqueta', (x1 - x0, y1 - y0, 0.16), ((x0 + x1) / 2, (y0 + y1) / 2, 0), M['banqueta'])
    return x0 + ancho, x1 - ancho, y0 + ancho, y1 - ancho


# ---------------------------------------------------------------- edificaciones

def casa(nombre, x, y, w, d, pisos, frente, M, rnd):
    """Casa o edificio bajo mexicano: aplanado de color, ventanas con marco, pretil, tinaco y cuarto de azotea.

    frente: +1 si la fachada mira a +Y, -1 si mira a -Y."""
    h = pisos * 3.1 + 0.4
    z = 0.16
    geo.caja(f'{nombre} Muros', (w, d, h), (x, y, z), M['muro_mx'], bisel=0.02)
    geo.caja(f'{nombre} Azotea', (w - 0.3, d - 0.3, 0.04), (x, y, z + h), M['azotea_mx'])
    for lado, (lw, ld, ox, oy) in enumerate(((w, 0.2, 0, d / 2 - 0.1), (w, 0.2, 0, -d / 2 + 0.1), (0.2, d, w / 2 - 0.1, 0), (0.2, d, -w / 2 + 0.1, 0))):
        geo.caja(f'{nombre} Pretil {lado}', (lw, ld, 0.6), (x + ox, y + oy, z + h), M['muro_mx'])
    yf = y + frente * (d / 2 + 0.03)
    n_vent = max(1, int((w - 1.5) // 3.2))
    for p in range(pisos):
        for k in range(n_vent):
            vx = x - (n_vent - 1) * 1.6 + k * 3.2
            if p == 0 and k == 0:
                geo.caja(f'{nombre} Puerta', (1.1, 0.08, 2.2), (vx, yf, z), M['herreria'])
                continue
            geo.caja(f'{nombre} Marco', (1.5, 0.1, 1.45), (vx, yf, z + p * 3.1 + 0.95), M['marco_ventana'])
            geo.caja(f'{nombre} Ventana', (1.3, 0.12, 1.25), (vx, yf, z + p * 3.1 + 1.05), M['ventana'])
            if p == 0 and rnd.random() < 0.6:
                for b in range(5):
                    geo.caja(f'{nombre} Proteccion', (0.03, 0.14, 1.25), (vx - 0.55 + b * 0.275, yf + frente * 0.02, z + 1.05), M['herreria'])
    zt = z + h
    for t in range(rnd.choice((1, 1, 2))):
        P.tinaco(f'{nombre} Tinaco {t}', (x + rnd.uniform(-w / 2 + 1, w / 2 - 1), y - frente * (d / 2 - 1.5 - t * 1.3), zt), M,
                 capacidad=rnd.choice((1100, 1100, 2500)))
    if rnd.random() < 0.45:
        geo.caja(f'{nombre} Cuarto Azotea', (min(4, w - 1), 3, 2.4), (x + rnd.uniform(-1, 1), y - frente * (d / 2 - 2.0), zt), M['muro_mx'], bisel=0.02)
    if rnd.random() < 0.3:
        geo.caja(f'{nombre} Tendedero', (3.0, 0.02, 0.02), (x, y, zt + 1.6), M['acero'])


def torre(nombre, x, y, w, d, pisos, M, fachada, rnd):
    h = pisos * 3.5
    z = 0.16
    geo.caja(f'{nombre} Torre', (w, d, h), (x, y, z), M[fachada], bisel=0.03)
    geo.caja(f'{nombre} Remate', (w + 0.3, d + 0.3, 0.8), (x, y, z + h), M['fachada'], bisel=0.02)
    geo.caja(f'{nombre} Azotea', (w - 0.4, d - 0.4, 0.05), (x, y, z + h + 0.8), M['azotea'])
    for i in range(rnd.randint(2, 4)):
        geo.caja(f'{nombre} Equipo {i}', (rnd.uniform(2, 4), rnd.uniform(1.5, 3), 1.6),
                 (x + rnd.uniform(-w / 3, w / 3), y + rnd.uniform(-d / 3, d / 3), z + h + 0.85), M['gris'], bisel=0.04)


def poblar_manzana(nombre, rect, M, rnd, sobre_avenida=False, excluir=None):
    """Lotes angostos (8-14 m) en los dos frentes largos de la manzana; torres en esquinas de avenida."""
    x0, x1, y0, y1 = rect
    fondo = min(18.0, (y1 - y0) / 2 - 1)
    for frente, yb in ((-1, y0 + fondo / 2), (1, y1 - fondo / 2)):
        x = x0
        while x < x1 - 6:
            w = min(rnd.uniform(8, 14), x1 - x)
            cx = x + w / 2
            if excluir and excluir[0] <= cx <= excluir[1]:
                x += w
                continue
            frente_avenida = sobre_avenida and ((frente == -1 and yb > 0) or (frente == 1 and yb < 0))
            if frente_avenida and rnd.random() < 0.35:
                fid = rnd.choice(('fachada_Facade018A', 'fachada_Facade019A', 'fachada_Facade020A', 'fachada_Facade006'))
                torre(f'{nombre} Torre', cx, yb, w + 6, fondo, rnd.randint(5, 12), M, fid, rnd)
                x += w + 6
                continue
            pisos = rnd.choice((1, 2, 2, 2, 3, 3, 4)) + (1 if frente_avenida else 0)
            casa(f'{nombre} Casa', cx, yb, w - 0.05, fondo, pisos, frente, M, rnd)
            x += w


def arboles_banqueta(rect, F, rnd, paso=11):
    x0, x1, y0, y1 = rect
    for yb in (y0 + 1.2, y1 - 1.2):
        x = x0 + 4
        while x < x1 - 4:
            geo.instancia('Arbol Banqueta', rnd.choice(F), (x + rnd.uniform(-1, 1), yb, 0.16), rnd.uniform(0, 6.28), rnd.uniform(1.3, 1.8))
            x += paso + rnd.uniform(-2, 3)


# ---------------------------------------------------------------- viñetas de producto

def vineta_alumbrado(M, arbusto):
    """Camellón despejado con luminarias solares alternadas (una hacia cada sentido) y arbustos bajos."""
    for i, x in enumerate(range(-190, -108, 16)):
        P.luminaria_solar(f'Luminaria Solar {i + 1:02d}', (x, 0, 0.22), M, rot_z=math.pi / 2 if i % 2 else -math.pi / 2)
        geo.instancia('Arbusto Camellon', arbusto, (x + 8, 0, 0.22), i * 1.3, 0.55)
    # faroles de hierro en la banqueta sur de la misma cuadra
    farol = modelo('street_lamp_01')
    for i, x in enumerate(range(-186, -110, 14)):
        geo.instancia(f'Farol Banqueta {i + 1:02d}', farol, (x, -BORDE_AV - 0.8, 0.16), math.pi / 2, 1.15)


def vineta_vialidad(M):
    """Cruce x = -100: bolardos dividiendo carriles, brocales en banqueta y coladeras junto a la guarnición."""
    for k in range(10):
        P.bolardo_trapezoidal(f'Bolardo {k + 1:02d}', (-88 + k * 1.9, CAMELLON + 3.3, 0.0), M)
        P.bolardo_trapezoidal(f'Bolardo S {k + 1:02d}', (-88 + k * 1.9, -(CAMELLON + 3.3), 0.0), M)
    for i, (x, y) in enumerate(((-96, BORDE_AV + 2.2), (-82, BORDE_AV + 2.4), (-104, -BORDE_AV - 2.3))):
        P.brocal_con_tapa(f'Brocal {i + 1}', (x, y, 0.16), M)
    # pozos de visita también sobre el arroyo vehicular
    for i, (x, y) in enumerate(((-80, 8.6), (-66, 4.2))):
        P.brocal_con_tapa(f'Brocal Arroyo {i + 1}', (x, y, 0.0), M)
    for i, x in enumerate((-90, -76, -110)):
        P.coladera(f'Coladera {i + 1}', (x, BORDE_AV - 0.35, 0.0), M)
        P.coladera(f'Coladera S {i + 1}', (x, -BORDE_AV + 0.35, 0.0), M)


def vineta_parabuses(M, logo_mat):
    P.parabus_elle('Parabus Elle', (-40, BORDE_AV + 2.4, 0.16), M, rot_z=0.0, logo_mat=logo_mat)
    P.parabus_contempo('Parabus Contempo', (-46, -BORDE_AV - 2.2, 0.16), M, rot_z=math.pi)


def vineta_cctv(M):
    """Cruce x = 0: postes de videovigilancia en las cuatro esquinas y uno frente a la plaza."""
    esquina_x = ANCHO_CALLE / 2 + 1.6
    esquina_y = BORDE_AV + 1.4
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1)), start=1):
        P.poste_videovigilancia(f'Poste CCTV {i:02d}', (sx * esquina_x, sy * esquina_y, 0.16), M, rot_z=math.atan2(-sy, -sx) + math.pi / 2)
    P.poste_videovigilancia('Poste CCTV 05', (88, FRENTE_AV + 1.0, 0.18), M, rot_z=math.pi)


def vineta_plaza(M, rnd):
    """Jardín público: adoquín, faroles de hierro, bancas, jardineras, botes y jacarandas."""
    x0, x1, y0, y1 = 10, 90, FRENTE_AV, 82
    geo.caja('Plaza Piso', (x1 - x0, y1 - y0, 0.18), ((x0 + x1) / 2, (y0 + y1) / 2, 0), M['adoquin'])
    for i, (ax, ay) in enumerate(((30, 42), (70, 42), (30, 68), (70, 68))):
        geo.caja(f'Plaza Arriate {i}', (16, 12, 0.45), (ax, ay, 0.18), M['guarnicion'])
        geo.caja(f'Plaza Arriate Pasto {i}', (15.4, 11.4, 0.05), (ax, ay, 0.63), M['cesped'])
        geo.instancia('Plaza Jacaranda', modelo('jacaranda_tree'), (ax, ay, 0.63), rnd.uniform(0, 6.28), rnd.uniform(0.5, 0.6))
    farol = modelo('street_lamp_01')
    banca = modelo('modular_street_seating')
    bote = modelo('metal_trash_can')
    jardinera = modelo('planter_box_01')
    k = 0
    # faroles de hierro a lo largo de los andadores en cruz y del perímetro
    for fx, fy in [(50, y) for y in range(26, 86, 10)] + [(x, 55) for x in range(16, 88, 10) if abs(x - 50) > 4] + \
                  [(x, 21) for x in range(14, 90, 12)]:
        k += 1
        geo.instancia(f'Farol Hierro {k:02d}', farol, (fx + 2.2, fy + 2.2, 0.18), 0.0, 1.1)
    for i, (bx, by, r) in enumerate(((44, 34, math.pi / 2), (56, 34, -math.pi / 2), (44, 76, math.pi / 2), (56, 76, -math.pi / 2),
                                     (36, 49, 0), (64, 49, 0), (36, 61, math.pi), (64, 61, math.pi))):
        geo.instancia(f'Plaza Banca {i}', banca, (bx, by, 0.18), r)
    for i, (bx, by) in enumerate(((47, 30), (53, 80), (32, 52), (68, 58))):
        geo.instancia(f'Plaza Bote {i}', bote, (bx, by, 0.18), 0.0)
    for i in range(14):
        geo.instancia(f'Plaza Jardinera {i}', jardinera, (16 + i * 5.2, 19.5, 0.18), 0.0, 1.8)


def anclas_paradas():
    """Puntos de interés del recorrido (la web los usa para los textos de cada escena)."""
    datos = {
        'alumbrado': ((-150, 0, 4), 'Alumbrado público y luminarias solares'),
        'vialidad': ((-80, 8, 0.5), 'Seguridad vial: bolardos, brocales y coladeras'),
        'parabuses': ((-43, 0, 1.5), 'Mobiliario urbano: parabuses'),
        'plaza': ((50, 52, 3), 'Espacio público: faroles de hierro, bancas y jardineras'),
    }
    for clave, (pos, titulo) in datos.items():
        obj = bpy.data.objects.new(f'Parada {clave}', None)
        obj.location = pos
        obj['titulo'] = titulo
        geo.coleccion('Paradas').objects.link(obj)
