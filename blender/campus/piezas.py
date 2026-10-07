"""Piezas reutilizables a escala real: edificios, naves, árboles, vehículos y mobiliario urbano."""
import math
import random

import bpy

from . import geo

PISO = 3.6  # altura de entrepiso (m)


def parapeto(nombre, w, d, z, pos, mat, alto=0.9, grosor=0.3):
    x, y = pos[0], pos[1]
    geo.caja(f'{nombre} Parapeto N', (w, grosor, alto), (x, y + d / 2 - grosor / 2, z), mat)
    geo.caja(f'{nombre} Parapeto S', (w, grosor, alto), (x, y - d / 2 + grosor / 2, z), mat)
    geo.caja(f'{nombre} Parapeto E', (grosor, d - 2 * grosor, alto), (x + w / 2 - grosor / 2, y, z), mat)
    geo.caja(f'{nombre} Parapeto O', (grosor, d - 2 * grosor, alto), (x - w / 2 + grosor / 2, y, z), mat)


def equipos_azotea(nombre, w, d, z, pos, M, n=4, semilla=0):
    rnd = random.Random(semilla)
    for i in range(n):
        ex = pos[0] + rnd.uniform(-w / 2 + 3, w / 2 - 3)
        ey = pos[1] + rnd.uniform(-d / 2 + 3, d / 2 - 3)
        geo.caja(f'{nombre} HVAC {i}', (rnd.uniform(2.5, 4.5), rnd.uniform(1.8, 3.0), rnd.uniform(1.2, 1.8)), (ex, ey, z), M['gris'], bisel=0.04)
        geo.cilindro(f'{nombre} Ventilador {i}', 0.55, 0.15, (ex, ey, z + 1.6), M['gris_oscuro'], seg=16)


def oficina(nombre, w, d, pisos, pos, M, semilla=0, vidrio=None, azotea=True):
    """Edificio de concreto con ventanas corridas por piso, parapeto y equipos en azotea."""
    x, y, z = pos
    h = pisos * PISO + 0.6
    geo.caja(f'{nombre} Cuerpo', (w, d, h), pos, M['fachada'], bisel=0.05)
    for p in range(pisos):
        geo.caja(f'{nombre} Ventanas {p}', (w + 0.12, d + 0.12, 1.7), (x, y, z + p * PISO + 1.15), vidrio or M['vidrio_oscuro'])
    geo.caja(f'{nombre} Losa Azotea', (w - 0.6, d - 0.6, 0.05), (x, y, z + h), M['azotea'])
    parapeto(nombre, w, d, z + h, (x, y), M['fachada'])
    if azotea:
        equipos_azotea(nombre, w, d, z + h, (x, y), M, n=max(2, int(w * d / 180)), semilla=semilla)
    return h


def muro_cortina(nombre, w, d, h, pos, M):
    """Volumen de vidrio (atrio) con losa y parapeto."""
    x, y, z = pos
    geo.caja(f'{nombre} Vidrio', (w, d, h), pos, M['vidrio'])
    geo.caja(f'{nombre} Losa', (w + 0.6, d + 0.6, 0.6), (x, y, z + h), M['blanco'], bisel=0.05)


def nave(nombre, w, d, h, pos, M, muro=None, techo=None, andenes=0, lado_andenes=-1, claraboyas=True):
    """Nave industrial de lámina con techo a dos aguas bajo, claraboyas y andenes de carga."""
    x, y, z = pos
    geo.caja(f'{nombre} Muros', (w, d, h), pos, muro or M['lamina'], bisel=0.04)
    geo.caja(f'{nombre} Zoclo', (w + 0.1, d + 0.1, 1.2), pos, M['fachada'])
    # techo a dos aguas muy bajo (pendiente 5 %) con dos faldones
    for lado in (-1, 1):
        faldon = geo.caja(f'{nombre} Techo {lado}', (w + 0.8, d / 2 + 0.4, 0.25), (x, y + lado * d / 4, z + h), techo or M['lamina'])
        faldon.rotation_euler[0] = -lado * math.atan(0.05)
    if claraboyas:
        for i in range(int(w // 9)):
            cx = x - w / 2 + 6 + i * 9
            if cx > x + w / 2 - 4:
                break
            for lado in (-1, 1):
                geo.caja(f'{nombre} Claraboya {i}{lado}', (1.6, d / 2 - 4, 0.2), (cx, y + lado * d / 4, z + h + 0.3), M['blanco'])
    if andenes:
        cy = y + lado_andenes * (d / 2 + 0.05)
        paso = w / (andenes + 1)
        for i in range(andenes):
            ax = x - w / 2 + paso * (i + 1)
            geo.caja(f'{nombre} Anden Puerta {i}', (3.4, 0.2, 4.0), (ax, cy, z + 1.2), M['gris_oscuro'])
            geo.caja(f'{nombre} Anden Sello {i}', (4.0, 0.6, 0.5), (ax, cy + lado_andenes * 0.3, z + 5.2), M['gris_oscuro'])
            geo.caja(f'{nombre} Anden Rampa {i}', (3.6, 2.0, 1.2), (ax, cy + lado_andenes * 1.0, z), M['banqueta'])
    return h


def diente_sierra(nombre, w, d, h, dientes, pos, M):
    """Nave de manufactura con techo de diente de sierra (vidrio orientado al norte)."""
    x, y, z = pos
    geo.caja(f'{nombre} Muros', (w, d, h), pos, M['fachada'], bisel=0.04)
    geo.caja(f'{nombre} Ventanas', (w + 0.12, d + 0.12, 1.4), (x, y, z + 3.2), M['vidrio_oscuro'])
    paso = d / dientes
    for i in range(dientes):
        cy = y - d / 2 + paso * (i + 0.5)
        geo.prisma_triangular(f'{nombre} Diente {i}', w, paso, 3.0, (x, cy, z + h), M['lamina'])
        geo.caja(f'{nombre} Diente Vidrio {i}', (w - 0.4, 0.15, 2.8), (x, cy + paso / 2 - 0.1, z + h), M['vidrio'])


# ---------- Árboles (colecciones fuente para instanciar) ----------

def _arbol_fuente(nombre, M, alto, copa, capas, semilla):
    col = geo.coleccion(nombre, geo.coleccion('Fuentes'))
    rnd = random.Random(semilla)
    tronco = geo.cilindro(f'{nombre} Tronco', 0.22, alto * 0.55, (0, 0, 0), M['tronco'], seg=10, col=col)
    copas = []
    for i in range(capas):
        r = copa * rnd.uniform(0.65, 1.0)
        pos = (rnd.uniform(-copa * 0.35, copa * 0.35), rnd.uniform(-copa * 0.35, copa * 0.35), alto * 0.55 + r * 0.6 + i * copa * 0.25)
        e = geo.esfera(f'{nombre} Copa {i}', r, pos, M['follaje'], subdiv=3, escala=(1, 1, 0.85), col=col)
        mod = e.modifiers.new('Ramaje', 'DISPLACE')
        tex = bpy.data.textures.get('Ramaje') or bpy.data.textures.new('Ramaje', 'VORONOI')
        tex.noise_scale = 0.9
        mod.texture = tex
        mod.strength = 0.55
        mod.texture_coords = 'GLOBAL'
        copas.append(e)
    del tronco
    return col


def arboles_fuente(M):
    return [
        _arbol_fuente('Arbol A', M, 7.0, 3.2, 3, 1),
        _arbol_fuente('Arbol B', M, 9.0, 3.8, 4, 2),
        _arbol_fuente('Arbol C', M, 5.5, 2.6, 2, 3),
    ]


def auto_fuente(M):
    col = geo.coleccion('Auto', geo.coleccion('Fuentes'))
    geo.caja('Auto Carroceria', (4.5, 1.85, 0.75), (0, 0, 0.32), M['carroceria'], bisel=0.18, col=col)
    geo.caja('Auto Cabina', (2.5, 1.65, 0.6), (-0.2, 0, 1.0), M['vidrio_oscuro'], bisel=0.15, col=col)
    for sx in (-1.4, 1.4):
        for sy in (-0.85, 0.85):
            geo.cilindro('Auto Llanta', 0.34, 0.24, (sx, sy + (0.12 if sy < 0 else -0.12), 0.34), M['llanta'], seg=16, rot=(math.pi / 2, 0, 0), col=col)
    return col


def camion_fuente(M, nombre='Camion', color_caja=None):
    col = geo.coleccion(nombre, geo.coleccion('Fuentes'))
    geo.caja(f'{nombre} Caja', (13.6, 2.6, 2.9), (0, 0, 1.25), color_caja or M['blanco'], bisel=0.06, col=col)
    geo.caja(f'{nombre} Cabina', (2.6, 2.5, 2.8), (8.3, 0, 0.9), M['blanco'], bisel=0.2, col=col)
    geo.caja(f'{nombre} Parabrisas', (0.1, 2.2, 1.0), (9.62, 0, 2.3), M['vidrio_oscuro'], col=col)
    geo.caja(f'{nombre} Chasis', (16.5, 2.2, 0.5), (1.4, 0, 0.6), M['gris_oscuro'], col=col)
    for sx in (-5.5, -4.2, 6.0, 8.6):
        for sy in (-1.15, 1.15):
            geo.cilindro(f'{nombre} Llanta', 0.5, 0.35, (sx, sy, 0.5), M['llanta'], seg=16, rot=(math.pi / 2, 0, 0), col=col)
    return col


def estacionamiento(nombre, x, y, filas, columnas, M, auto_col, rot=0.0, semilla=0, ocupacion=0.75):
    """Cajones de 2.6 x 5.2 m con líneas pintadas y autos instanciados."""
    rnd = random.Random(semilla)
    c, s = math.cos(rot), math.sin(rot)
    for f in range(filas):
        for k in range(columnas):
            lx = (k - (columnas - 1) / 2) * 2.7
            ly = f * 11.5
            px, py = x + lx * c - ly * s, y + lx * s + ly * c
            linea_x = px + (1.35 * c)
            linea_y = py + (1.35 * s)
            geo.caja(f'{nombre} Linea', (0.12, 5.0, 0.02), (linea_x, linea_y, 0.16), M['pintura_vial'], rot_z=rot)
            if rnd.random() < ocupacion:
                geo.instancia(f'{nombre} Auto', auto_col, (px, py, 0.15), rot + math.pi / 2 + (math.pi if f % 2 else 0) + rnd.uniform(-0.04, 0.04))


# ---------- Mobiliario urbano e interactivos ----------

def poste_inteligente(nombre, pos, M, giro=0.0):
    x, y, z = pos
    geo.cilindro(f'{nombre} Mastil', 0.12, 9.0, (x, y, z), M['gris_oscuro'], seg=12)
    geo.cilindro(f'{nombre} Anillo Sensor', 0.16, 0.25, (x, y, z + 4.5), M['led'], seg=12)
    brazo = geo.caja(f'{nombre} Brazo', (2.2, 0.12, 0.12), (x + math.cos(giro), y + math.sin(giro), z + 8.9), M['gris_oscuro'], rot_z=giro)
    geo.caja(f'{nombre} Luminaria', (0.9, 0.35, 0.12), (x + 2.0 * math.cos(giro), y + 2.0 * math.sin(giro), z + 8.85), M['blanco'], rot_z=giro)
    geo.caja(f'{nombre} Panel Solar', (0.9, 0.6, 0.05), (x, y, z + 9.1), M['panel_solar'])
    return brazo


def camara_cctv(nombre, pos, M, giro=0.0):
    x, y, z = pos
    geo.cilindro(f'{nombre} Poste', 0.1, 6.5, (x, y, z), M['blanco'], seg=12)
    geo.caja(f'{nombre} Cuerpo', (0.7, 0.28, 0.28), (x + 0.35 * math.cos(giro), y + 0.35 * math.sin(giro), z + 6.2), M['blanco'], rot_z=giro, bisel=0.05)


def ancla(nombre, pos, tipo, titulo):
    """Empty que marca un punto interactivo: se exporta a JSON para los hotspots web."""
    obj = bpy.data.objects.new(nombre, None)
    obj.empty_display_type = 'SPHERE'
    obj.location = pos
    obj['tipo'] = tipo
    obj['titulo'] = titulo
    geo.coleccion('Interactivos').objects.link(obj)
    return obj
