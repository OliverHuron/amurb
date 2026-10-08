"""Productos AmUrb modelados a escala real (metros), a partir de las fichas del catálogo.

- Luminaria solar (línea solar): poste galvanizado, brazo con cabeza LED y panel inclinado.
- Bolardo divisor de carril trapezoidal 120-15-9.5 (cm).
- Brocal con tapa para pozo de visita.
- Coladera pluvial con rejilla de hierro.
- Parabús Elle (techo translúcido, bancas de madera) y Parabús Contempo (L de madera y acero).
"""
import math

import bmesh
import bpy

from campus import geo


def _malla(nombre, verts, caras, mat, pos, rot_z=0.0):
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(verts, [], caras)
    malla.update()
    obj = bpy.data.objects.new(nombre, malla)
    obj.location = pos
    obj.rotation_euler = (0, 0, rot_z)
    malla.materials.append(mat)
    geo._vincular(obj)
    return obj


def _suavizar_bordes(obj, ancho=0.004):
    mod = obj.modifiers.new('Bisel', 'BEVEL')
    mod.width = ancho
    mod.segments = 2
    mod.limit_method = 'ANGLE'


# ---------------------------------------------------------------- luminaria solar

def luminaria_solar(nombre, pos, M, rot_z=0.0, alto=7.0):
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    geo.caja(f'{nombre} Base', (0.45, 0.45, 0.12), (x, y, z), M['concreto'], rot_z=rot_z, bisel=0.01)
    geo.cilindro(f'{nombre} Poste', 0.085, alto, (x, y, z + 0.12), M['acero_poste'], seg=20, r_sup=0.055)
    # brazo inclinado hacia la calle con cabeza LED plana
    brazo = geo.cilindro(f'{nombre} Brazo', 0.03, 1.6, (x, y, z + alto - 0.6), M['acero_poste'], seg=12,
                         rot=(0, math.radians(75), rot_z))
    del brazo
    hx, hy = x + 1.55 * c, y + 1.55 * s
    cabeza = geo.caja(f'{nombre} Cabeza LED', (0.62, 0.26, 0.07), (hx, hy, z + alto - 0.22), M['gris_claro'], rot_z=rot_z, bisel=0.015)
    cabeza.rotation_euler[1] = math.radians(-8)
    geo.caja(f'{nombre} Optica LED', (0.5, 0.2, 0.01), (hx, hy, z + alto - 0.23), M['led'], rot_z=rot_z)
    # panel solar sobre el poste, inclinado ~25° hacia el sur, con caja de batería
    geo.cilindro(f'{nombre} Soporte Panel', 0.04, 0.5, (x, y, z + alto + 0.12), M['acero_poste'], seg=12)
    panel = geo.caja(f'{nombre} Panel Solar', (1.65, 1.0, 0.04), (x, y, z + alto + 0.55), M['panel_solar'], rot_z=rot_z + math.pi / 2, bisel=0.008)
    panel.rotation_euler[0] = math.radians(25)
    geo.caja(f'{nombre} Marco Panel', (1.68, 1.03, 0.025), (x, y, z + alto + 0.53), M['aluminio'], rot_z=rot_z + math.pi / 2).rotation_euler[0] = math.radians(25)
    geo.caja(f'{nombre} Bateria', (0.32, 0.16, 0.4), (x - 0.12 * c, y - 0.12 * s, z + alto - 0.1), M['gris_claro'], rot_z=rot_z, bisel=0.01)


# ---------------------------------------------------------------- bolardo trapezoidal

def bolardo_trapezoidal(nombre, pos, M, rot_z=0.0):
    """Bolardo divisor 1.20 x 0.15 x 0.095 m: sección trapezoidal y extremos en rampa."""
    L, B, b, H, R = 1.20, 0.15, 0.07, 0.095, 0.16  # largo, base, corona, alto, largo de rampa
    xl = L / 2
    verts = [
        (-xl, -B / 2, 0), (xl, -B / 2, 0), (xl, B / 2, 0), (-xl, B / 2, 0),
        (-xl + R, -b / 2, H), (xl - R, -b / 2, H), (xl - R, b / 2, H), (-xl + R, b / 2, H),
    ]
    caras = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = _malla(nombre, verts, caras, M['amarillo_plastico'], pos, rot_z)
    _suavizar_bordes(obj, 0.006)
    # cintas reflejantes en las rampas
    for lado in (-1, 1):
        cinta = geo.caja(f'{nombre} Reflejante', (0.05, 0.075, 0.002), (pos[0] + lado * (xl - R * 0.55) * math.cos(rot_z),
                                                                          pos[1] + lado * (xl - R * 0.55) * math.sin(rot_z), pos[2] + H * 0.5), M['reflejante'], rot_z=rot_z)
        cinta.rotation_euler[1] = lado * math.atan(H / R)
    return obj


# ---------------------------------------------------------------- brocal con tapa

def brocal_con_tapa(nombre, pos, M, diametro=0.92):
    """Brocal de concreto con tapa ligera de patrón radial y barrenos (pozo de visita)."""
    x, y, z = pos
    r = diametro / 2
    geo.cilindro(f'{nombre} Brocal', r + 0.08, 0.14, (x, y, z - 0.12), M['concreto_oscuro'], seg=48)
    tapa = geo.cilindro(f'{nombre} Tapa', r - 0.02, 0.045, (x, y, z - 0.02), M['tapa_concreto'], seg=64)
    del tapa
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        geo.cilindro(f'{nombre} Barreno {i}', 0.035, 0.05, (x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62, z - 0.02), M['negro'], seg=16)
    geo.cilindro(f'{nombre} Barreno Centro', 0.035, 0.05, (x, y, z - 0.02), M['negro'], seg=16)


# ---------------------------------------------------------------- coladera pluvial

def coladera(nombre, pos, M, rot_z=0.0, largo=0.9, ancho=0.45):
    """Coladera de banqueta: marco de hierro y rejilla de soleras sobre un registro oscuro."""
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    geo.caja(f'{nombre} Registro', (largo, ancho, 0.02), (x, y, z - 0.03), M['negro'], rot_z=rot_z)
    marco = 0.04
    for lado in (-1, 1):
        geo.caja(f'{nombre} Marco L', (largo, marco, 0.03), (x - lado * (ancho / 2 - marco / 2) * s, y + lado * (ancho / 2 - marco / 2) * c, z - 0.02), M['hierro'], rot_z=rot_z)
        geo.caja(f'{nombre} Marco C', (marco, ancho, 0.03), (x + lado * (largo / 2 - marco / 2) * c, y + lado * (largo / 2 - marco / 2) * s, z - 0.02), M['hierro'], rot_z=rot_z)
    n = int((largo - 2 * marco) / 0.05)
    for i in range(n):
        u = -largo / 2 + marco + 0.025 + i * 0.05
        geo.caja(f'{nombre} Solera', (0.018, ancho - 2 * marco, 0.028), (x + u * c, y + u * s, z - 0.02), M['hierro'], rot_z=rot_z)


# ---------------------------------------------------------------- parabuses

def _banca_madera(nombre, pos, M, rot_z, largo=1.8):
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    for lado in (-1, 1):
        geo.caja(f'{nombre} Pata', (0.08, 0.42, 0.42), (x + lado * (largo / 2 - 0.15) * c, y + lado * (largo / 2 - 0.15) * s, z), M['acero_negro'], rot_z=rot_z)
    for k in range(4):
        geo.caja(f'{nombre} Tabla {k}', (largo, 0.085, 0.035), (x - (0.15 - k * 0.1) * s, y + (0.15 - k * 0.1) * c, z + 0.42), M['madera_tablas'], rot_z=rot_z, bisel=0.004)
    for k in range(3):
        respaldo = geo.caja(f'{nombre} Respaldo {k}', (largo, 0.03, 0.085), (x - 0.2 * s, y + 0.2 * c, z + 0.55 + k * 0.11), M['madera_tablas'], rot_z=rot_z, bisel=0.004)
        respaldo.rotation_euler[0] = math.radians(-8)


def parabus_elle(nombre, pos, M, rot_z=0.0, logo_mat=None):
    """Parabús ELLE: dos marcos de acero, techo translúcido a un agua, panel publicitario y bancas."""
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    L, F = 5.6, 1.9  # largo y fondo
    def punto(u, v):
        return (x + u * c - v * s, y + u * s + v * c)
    for u in (-L / 2 + 0.3, 0.0, L / 2 - 0.3):
        px, py = punto(u, F / 2 - 0.1)
        geo.caja(f'{nombre} Columna', (0.1, 0.1, 2.75), (px, py, z), M['acero_negro'], rot_z=rot_z)
        px, py = punto(u, 0.0)
        viga = geo.caja(f'{nombre} Viga Techo', (0.08, F + 0.6, 0.1), (px, py, z + 2.7), M['acero_negro'], rot_z=rot_z)
        viga.rotation_euler[0] = math.radians(-9)
    px, py = punto(0, 0.05)
    techo = geo.caja(f'{nombre} Techo', (L, F + 0.7, 0.015), (px, py, z + 2.83), M['policarbonato'], rot_z=rot_z)
    techo.rotation_euler[0] = math.radians(-9)
    # faldón publicitario con el logo y panel trasero
    px, py = punto(0, F / 2 - 0.05)
    geo.caja(f'{nombre} Panel Trasero', (L - 0.6, 0.03, 0.55), (px, py, z + 1.0), M['acero_negro'], rot_z=rot_z)
    geo.caja(f'{nombre} Vidrio Trasero', (L - 0.6, 0.012, 1.0), (px, py, z + 1.6), M['policarbonato'], rot_z=rot_z)
    if logo_mat is not None:
        for u in (-1.3, 1.3):
            lx, ly = punto(u, F / 2 - 0.07)
            placa = geo.plano(f'{nombre} Logo', 1.4, 0.48, (lx, ly, z + 1.27), logo_mat, rot_z=rot_z + math.pi)
            placa.rotation_euler[0] = math.pi / 2
    for u in (-1.2, 1.2):
        bx, by = punto(u, 0.25)
        _banca_madera(f'{nombre} Banca', (bx, by, z), M, rot_z + math.pi, largo=1.9)
    # bote de basura cilíndrico de acero
    tx, ty = punto(L / 2 - 0.2, -0.3)
    geo.cilindro(f'{nombre} Bote', 0.22, 0.85, (tx, ty, z), M['acero_negro'], seg=24)


def parabus_contempo(nombre, pos, M, rot_z=0.0):
    """Parabús CONTEMPO: perfil en L de acero negro con lambrín de madera y banca integrada."""
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    L, F, H = 4.2, 1.6, 2.9
    def punto(u, v):
        return (x + u * c - v * s, y + u * s + v * c)
    px, py = punto(0, F / 2)
    geo.caja(f'{nombre} Muro Acero', (L, 0.18, H), (px, py, z), M['acero_negro'], rot_z=rot_z, bisel=0.01)
    px, py = punto(0, F / 2 - 0.1)
    for k in range(int(L / 0.12)):
        u = -L / 2 + 0.15 + k * 0.12
        lx, ly = punto(u, F / 2 - 0.12)
        geo.caja(f'{nombre} Lambrin {k}', (0.09, 0.04, H - 0.3), (lx, ly, z + 0.15), M['madera_tablas'], rot_z=rot_z)
    px, py = punto(0, 0)
    geo.caja(f'{nombre} Techo Acero', (L, F + 0.18, 0.18), (px, py, z + H), M['acero_negro'], rot_z=rot_z, bisel=0.01)
    for k in range(int((F + 0.1) / 0.12)):
        v = -F / 2 + 0.05 + k * 0.12
        lx, ly = punto(0, v)
        geo.caja(f'{nombre} Plafon {k}', (L - 0.3, 0.09, 0.03), (lx, ly, z + H - 0.03), M['madera_tablas'], rot_z=rot_z)
    bx, by = punto(0, F / 2 - 0.45)
    geo.caja(f'{nombre} Banca Base', (L - 0.6, 0.5, 0.4), (bx, by, z), M['acero_negro'], rot_z=rot_z)
    for k in range(4):
        tx, ty = punto(0, F / 2 - 0.25 - k * 0.12)
        geo.caja(f'{nombre} Asiento {k}', (L - 0.6, 0.1, 0.04), (tx, ty, z + 0.4), M['madera_tablas'], rot_z=rot_z, bisel=0.004)


# ---------------------------------------------------------------- poste de videovigilancia (CCTV)

def poste_videovigilancia(nombre, pos, M, rot_z=0.0, alto=9.0):
    """Poste de videovigilancia urbana: domo PTZ, dos cámaras bala, altavoz, gabinete y botón de pánico."""
    x, y, z = pos
    c, s = math.cos(rot_z), math.sin(rot_z)
    geo.caja(f'{nombre} Base', (0.5, 0.5, 0.15), (x, y, z), M['concreto'], rot_z=rot_z, bisel=0.01)
    geo.cilindro(f'{nombre} Poste', 0.11, alto, (x, y, z + 0.15), M['gris_claro'], seg=20, r_sup=0.08)
    # gabinete de control y botón de pánico a altura de mano
    geo.caja(f'{nombre} Gabinete', (0.45, 0.25, 0.7), (x - 0.2 * s, y + 0.2 * c, z + 1.6), M['gris_claro'], rot_z=rot_z, bisel=0.01)
    geo.caja(f'{nombre} Boton Panico Caja', (0.22, 0.12, 0.3), (x + 0.15 * s, y - 0.15 * c, z + 1.15), M['amarillo_plastico'], rot_z=rot_z, bisel=0.008)
    geo.cilindro(f'{nombre} Boton Panico', 0.045, 0.03, (x + 0.21 * s, y - 0.21 * c, z + 1.3), M['baliza'], seg=16, rot=(math.pi / 2, 0, rot_z))
    # brazo superior con cámaras bala a cada lado y domo PTZ al centro
    zt = z + alto + 0.1
    geo.caja(f'{nombre} Brazo', (1.4, 0.08, 0.08), (x, y, zt - 0.4), M['gris_claro'], rot_z=rot_z)
    for lado in (-1, 1):
        bx, by = x + lado * 0.65 * c, y + lado * 0.65 * s
        geo.caja(f'{nombre} Soporte Camara {lado}', (0.06, 0.06, 0.18), (bx, by, zt - 0.58), M['gris_claro'], rot_z=rot_z)
        bala = geo.caja(f'{nombre} Camara Bala {lado}', (0.12, 0.34, 0.12), (bx, by - 0.08 * c, zt - 0.72), M['blanco'], rot_z=rot_z + lado * 0.5, bisel=0.02)
        bala.rotation_euler[0] = math.radians(-15)
        geo.caja(f'{nombre} Visera {lado}', (0.15, 0.38, 0.02), (bx, by - 0.08 * c, zt - 0.6), M['blanco'], rot_z=rot_z + lado * 0.5)
    geo.cilindro(f'{nombre} Domo Montaje', 0.12, 0.12, (x, y, zt - 0.32), M['blanco'], seg=24)
    geo.esfera(f'{nombre} Domo PTZ', 0.13, (x, y, zt - 0.36), M['vidrio_oscuro'], subdiv=3, escala=(1, 1, 0.9))
    geo.cilindro(f'{nombre} Altavoz', 0.11, 0.3, (x, y, zt - 1.3), M['blanco'], seg=20, r_sup=0.16, rot=(math.radians(100), 0, rot_z))
    geo.cilindro(f'{nombre} Estrobo', 0.06, 0.12, (x, y, zt + 0.05), M['baliza'], seg=16)


# ---------------------------------------------------------------- tinaco (azoteas)

def tinaco(nombre, pos, M, capacidad=1100):
    """Tinaco negro de polietileno con tapa roscada (típico de azoteas en México)."""
    x, y, z = pos
    r, h = (0.55, 1.25) if capacidad <= 1100 else (0.7, 1.55)
    geo.cilindro(f'{nombre} Cuerpo', r, h, (x, y, z), M['tinaco'], seg=28)
    geo.cilindro(f'{nombre} Hombro', r, 0.18, (x, y, z + h), M['tinaco'], seg=28, r_sup=r * 0.45)
    geo.cilindro(f'{nombre} Tapa', r * 0.42, 0.06, (x, y, z + h + 0.18), M['tinaco'], seg=24)
    for k in range(3):
        geo.cilindro(f'{nombre} Costilla {k}', r + 0.012, 0.04, (x, y, z + 0.25 + k * 0.38), M['tinaco'], seg=28)


def materiales_productos(M_base):
    """Materiales adicionales para productos y ciudad (se agregan a la paleta del campus)."""
    from campus import materiales as mt
    M = dict(M_base)
    M.update({
        'concreto': mt.textura('Concreto Liso', 'concrete_pavement_02', 1.5, tinte='#b7b5ae', mezcla=0.4, variacion=0.05),
        'concreto_oscuro': mt.textura('Concreto Oscuro', 'concrete_pavement_02', 1.0, tinte='#77756f', mezcla=0.5, variacion=0.05),
        'tapa_concreto': mt.textura('Tapa Concreto', 'concrete_pavement_02', 0.8, tinte='#a3a39d', mezcla=0.5, variacion=0.0, normal=1.0),
        'acero_poste': mt.pintura('Acero Poste', '#a7adb3', 0.32, 0.85),
        'aluminio': mt.pintura('Aluminio', '#c9cdd1', 0.25, 0.9),
        'gris_claro': mt.pintura('Gris Claro', '#d0d3d6', 0.4, 0.3),
        'acero_negro': mt.pintura('Acero Negro', '#1f2124', 0.45, 0.6),
        'hierro': mt.pintura('Hierro Fundido', '#2a2826', 0.7, 0.75),
        'negro': mt.pintura('Negro Profundo', '#050505', 0.9),
        'amarillo_plastico': mt.pintura('Plastico Amarillo', '#f2c200', 0.38),
        'reflejante': mt.pintura('Reflejante', '#ffffff', 0.15, 0.5, emision='#ffffff', fuerza=0.4),
        'policarbonato': _policarbonato(),
        'madera_tablas': _madera(),
        'tinaco': mt.pintura('Tinaco', '#141516', 0.55),
    })
    return M


def _policarbonato():
    from campus import materiales as mt
    if 'Policarbonato' in mt._cache:
        return mt._cache['Policarbonato']
    mat, nt, bsdf = mt._nuevo('Policarbonato')
    bsdf.inputs['Base Color'].default_value = mt._hex('#e9f1f4')
    bsdf.inputs['Transmission Weight'].default_value = 0.85
    bsdf.inputs['Roughness'].default_value = 0.35
    mt._cache['Policarbonato'] = mat
    return mat


def _madera():
    """Madera de tablas: vetas con ruido estirado y variación por pieza."""
    from campus import materiales as mt
    if 'Madera Tablas' in mt._cache:
        return mt._cache['Madera Tablas']
    mat, nt, bsdf = mt._nuevo('Madera Tablas')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapeo = nt.nodes.new('ShaderNodeMapping')
    mapeo.inputs['Scale'].default_value = (1.0, 18.0, 18.0)
    nt.links.new(coord.outputs['Object'], mapeo.inputs['Vector'])
    vetas = nt.nodes.new('ShaderNodeTexNoise')
    vetas.inputs['Scale'].default_value = 3.0
    vetas.inputs['Detail'].default_value = 10
    nt.links.new(mapeo.outputs['Vector'], vetas.inputs['Vector'])
    rampa = nt.nodes.new('ShaderNodeValToRGB')
    rampa.color_ramp.elements[0].color = mt._hex('#5a3a22')
    rampa.color_ramp.elements[1].color = mt._hex('#9a6a3e')
    nt.links.new(vetas.outputs['Fac'], rampa.inputs['Fac'])
    info = nt.nodes.new('ShaderNodeObjectInfo')
    color = mt._mezcla(nt, 0.2, rampa.outputs['Color'], mt._hex('#7a4f2c'))
    color = mt._mezcla(nt, info.outputs['Random'], color, mt._hex('#6b4426'))
    nt.links.new(color, bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    bsdf.inputs['Coat Weight'].default_value = 0.3
    mt._cache['Madera Tablas'] = mat
    return mat
