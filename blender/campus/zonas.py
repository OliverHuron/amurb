"""Las 10 zonas del campus AmUrb a escala real (metros). Centro del campus en el origen; +Y = norte.

Fila norte (y≈+80): Construcción, Acero, Hidráulicos y sanitarios, Eléctrico.
Fila media (y≈0): CCTV y tecnología, Sede AmUrb, Textiles y equipo técnico.
Fila sur (y≈-72): Logística y suministro, Ingeniería y proyectos, Calidad y soporte.
"""
import math
import os
import random

from . import geo
from . import piezas as P

Z0 = 0.15  # nivel de patios (banqueta sobre el asfalto)

ZONAS = {
    'construccion': {'titulo': 'Construcción', 'centro': (-120, 80), 'tam': (66, 50)},
    'acero': {'titulo': 'Acero', 'centro': (-40, 80), 'tam': (66, 50)},
    'hidraulicos': {'titulo': 'Hidráulicos y sanitarios', 'centro': (40, 80), 'tam': (66, 50)},
    'electrico': {'titulo': 'Eléctrico', 'centro': (120, 80), 'tam': (66, 50)},
    'cctv': {'titulo': 'CCTV y tecnología', 'centro': (-110, 0), 'tam': (90, 56)},
    'sede': {'titulo': 'Sede AmUrb', 'centro': (0, 0), 'tam': (90, 56)},
    'textiles': {'titulo': 'Textiles y equipo técnico', 'centro': (110, 0), 'tam': (90, 56)},
    'logistica': {'titulo': 'Logística y suministro', 'centro': (-110, -72), 'tam': (90, 52)},
    'ingenieria': {'titulo': 'Ingeniería y proyectos estratégicos', 'centro': (0, -72), 'tam': (90, 52)},
    'calidad': {'titulo': 'Calidad y soporte', 'centro': (110, -72), 'tam': (90, 52)},
}


def base(clave, M, piso=None):
    """Patio de la zona: franja de césped perimetral + pavimento elevado (banqueta)."""
    z = ZONAS[clave]
    (cx, cy), (w, d) = z['centro'], z['tam']
    geo.caja(f'{clave} Franja Cesped', (w, d, Z0 - 0.02), (cx, cy, 0.0), M['cesped'])
    geo.caja(f'{clave} Patio', (w - 5, d - 5, 0.02), (cx, cy, Z0 - 0.02), piso or M['banqueta'])
    return cx, cy, w, d


def _arboles_borde(clave, cx, cy, w, d, arboles, semilla, densidad=0.7):
    rnd = random.Random(semilla)
    for lado in range(4):
        largo = w if lado < 2 else d
        for t in range(int(largo // 9)):
            if rnd.random() > densidad:
                continue
            u = -largo / 2 + 4.5 + t * 9 + rnd.uniform(-1, 1)
            if lado == 0:
                x, y = cx + u, cy + d / 2 - 1.3
            elif lado == 1:
                x, y = cx + u, cy - d / 2 + 1.3
            elif lado == 2:
                x, y = cx + w / 2 - 1.3, cy + u
            else:
                x, y = cx - w / 2 + 1.3, cy + u
            geo.instancia(f'{clave} Arbol', rnd.choice(arboles), (x, y, 0.1), rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.15))


def sede(M, F, raiz):
    cx, cy, w, d = base('sede', M, M['plaza'])
    # ala oeste de concreto, atrio de vidrio y ala este con logotipo
    P.oficina('Sede Ala Oeste', 26, 24, 5, (cx - 25, cy + 9, Z0), M, semilla=11)
    P.muro_cortina('Sede Atrio', 22, 26, 22, (cx, cy + 10, Z0), M)
    P.oficina('Sede Ala Este', 26, 24, 6, (cx + 25, cy + 9, Z0), M, semilla=12, vidrio=M['vidrio'])
    for i in range(8):
        geo.caja(f'Sede Panel Solar {i}', (4.2, 1.8, 0.1), (cx - 8 + (i % 4) * 5.2, cy + 4 + (i // 4) * 8, Z0 + 22.7), M['panel_solar'])
    # marquesina de acceso, escalinata y fuente
    geo.caja('Sede Marquesina', (16, 7, 0.5), (cx, cy - 6, Z0 + 5.0), M['blanco'], bisel=0.05)
    for i in range(4):
        geo.cilindro(f'Sede Columna {i}', 0.3, 5.0, (cx - 6 + i * 4, cy - 8.8, Z0), M['blanco'], seg=16)
    geo.caja('Sede Fuente Borde', (14, 6, 0.5), (cx, cy - 17, Z0), M['fachada'])
    geo.caja('Sede Fuente Agua', (13, 5, 0.42), (cx, cy - 17, Z0 + 0.1), M['agua'])
    # logotipo AmUrb en la fachada sur del ala este
    logo = os.path.join(raiz, 'public', 'brand', 'logo.webp')
    if os.path.exists(logo):
        from . import materiales
        placa = geo.plano('Sede Logo AmUrb', 14, 5, (cx + 25, cy + 9 - 12.08, Z0 + 15.5), materiales.imagen_alfa('Logo AmUrb', logo))
        placa.rotation_euler = (math.pi / 2, 0, 0)
    P.estacionamiento('Sede Estacionamiento Oeste', cx - 30, cy - 18, 1, 9, M, F['auto'], semilla=5)
    P.estacionamiento('Sede Estacionamiento Este', cx + 30, cy - 18, 1, 9, M, F['auto'], semilla=6)
    _arboles_borde('sede', cx, cy, w, d, F['arboles'], 21, 0.6)


def cctv(M, F):
    cx, cy, w, d = base('cctv', M)
    P.oficina('CCTV Centro Monitoreo', 38, 20, 3, (cx - 6, cy + 10, Z0), M, semilla=31, vidrio=M['vidrio'])
    # torre de telecomunicaciones de celosía (40 m)
    tx, ty = cx + 30, cy + 14
    for i in range(4):
        geo.cilindro(f'CCTV Torre Pata {i}', 0.18, 40, (tx + (1.2 if i % 2 else -1.2), ty + (1.2 if i < 2 else -1.2), Z0), M['acero'], seg=8)
    for k in range(1, 14):
        z = Z0 + k * 3
        for lado in range(4):
            dx, dy = ((2.4, 0.1), (2.4, 0.1), (0.1, 2.4), (0.1, 2.4))[lado]
            ox, oy = ((0, 1.2), (0, -1.2), (1.2, 0), (-1.2, 0))[lado]
            geo.caja(f'CCTV Torre Travesano {k}{lado}', (dx, dy, 0.1), (tx + ox, ty + oy, z), M['acero'])
    for i, ang in enumerate((0, 2.1, 4.2)):
        geo.cilindro(f'CCTV Antena {i}', 0.35, 2.4, (tx + math.cos(ang) * 1.4, ty + math.sin(ang) * 1.4, Z0 + 35), M['blanco'], seg=12)
    geo.cilindro('CCTV Baliza', 0.25, 0.4, (tx, ty, Z0 + 40), M['baliza'])
    P.estacionamiento('CCTV Estacionamiento', cx - 6, cy - 16, 2, 11, M, F['auto'], semilla=7)
    _arboles_borde('cctv', cx, cy, w, d, F['arboles'], 22, 0.55)


def textiles(M, F):
    cx, cy, w, d = base('textiles', M)
    P.diente_sierra('Textiles Planta', 44, 26, 7, 5, (cx - 8, cy + 8, Z0), M)
    P.oficina('Textiles Oficinas', 14, 10, 2, (cx + 28, cy + 14, Z0), M, semilla=41)
    rnd = random.Random(4)
    for i in range(10):
        geo.caja(f'Textiles Tarima {i}', (1.2, 1.0, 0.15), (cx + 20 + (i % 5) * 2.0, cy - 10 - (i // 5) * 2.4, Z0), M['madera'])
        geo.caja(f'Textiles Rollos {i}', (1.1, 0.9, rnd.uniform(0.6, 1.3)), (cx + 20 + (i % 5) * 2.0, cy - 10 - (i // 5) * 2.4, Z0 + 0.15), M['carton'])
    P.estacionamiento('Textiles Estacionamiento', cx - 10, cy - 18, 1, 13, M, F['auto'], semilla=8)
    _arboles_borde('textiles', cx, cy, w, d, F['arboles'], 23, 0.6)


def logistica(M, F):
    cx, cy, w, d = base('logistica', M)
    P.nave('Logistica Centro Distribucion', 62, 24, 11, (cx - 6, cy + 11, Z0), M, andenes=8, lado_andenes=-1)
    rnd = random.Random(5)
    paso = 62 / 9
    for i in range(8):
        if rnd.random() < 0.75:
            geo.instancia(f'Logistica Trailer {i}', F['camion'], (cx - 6 - 31 + paso * (i + 1), cy - 9.5, Z0), -math.pi / 2)
    for i in range(14):
        geo.caja(f'Logistica Tarima {i}', (1.2, 1.0, 0.15), (cx + 30 + (i % 7) * 1.6, cy - 18 + (i // 7) * 2.0, Z0), M['madera'])
        geo.caja(f'Logistica Carga {i}', (1.1, 0.9, rnd.uniform(0.7, 1.4)), (cx + 30 + (i % 7) * 1.6, cy - 18 + (i // 7) * 2.0, Z0 + 0.15), M['carton'])
    for i in range(3):
        geo.caja(f'Logistica Contenedor {i}', (12.2, 2.45, 2.6), (cx - 38, cy - 14 + i * 2.6, Z0 + (2.6 if i == 2 else 0)), [M['lamina_azul'], M['oxido'], M['lamina']][i], bisel=0.03)
    _arboles_borde('logistica', cx, cy, w, d, F['arboles'], 24, 0.5)


def ingenieria(M, F):
    cx, cy, w, d = base('ingenieria', M, M['cesped'])
    geo.caja('Ingenieria Paseo', (6, d - 6, 0.04), (cx, cy, Z0), M['plaza'])
    geo.caja('Ingenieria Paseo Transversal', (w - 6, 4, 0.04), (cx, cy, Z0), M['plaza'])
    geo.caja('Ingenieria Estanque Borde', (8, 20, 0.5), (cx + 14, cy + 8, Z0), M['fachada'])
    geo.caja('Ingenieria Estanque Agua', (7.2, 19.2, 0.42), (cx + 14, cy + 8, Z0 + 0.1), M['agua'])
    # pérgola con paneles solares
    for i in range(6):
        geo.cilindro(f'Ingenieria Pergola Columna {i}', 0.15, 3.2, (cx - 22 + (i % 3) * 6, cy + 4 + (i // 3) * 6, Z0), M['acero'], seg=10)
    for i in range(3):
        geo.caja(f'Ingenieria Pergola Panel {i}', (5.6, 7.4, 0.12), (cx - 22 + i * 6, cy + 7, Z0 + 3.2), M['panel_solar'])
    # monolito con el lema
    geo.caja('Ingenieria Monolito', (6, 0.8, 5), (cx + 14, cy - 12, Z0), M['gris_oscuro'], bisel=0.05)
    rnd = random.Random(6)
    for i in range(46):
        x = cx + rnd.uniform(-w / 2 + 3, w / 2 - 3)
        y = cy + rnd.uniform(-d / 2 + 3, d / 2 - 3)
        if abs(x - cx) < 5 or abs(y - cy) < 4 or (abs(x - cx - 14) < 6 and abs(y - cy - 8) < 12):
            continue
        geo.instancia('Ingenieria Arbol', rnd.choice(F['arboles']), (x, y, Z0), rnd.uniform(0, 6.28), rnd.uniform(0.8, 1.25))


def calidad(M, F):
    cx, cy, w, d = base('calidad', M)
    P.oficina('Calidad Laboratorio', 34, 18, 2, (cx - 16, cy + 11, Z0), M, semilla=51, vidrio=M['vidrio'])
    geo.cilindro('Calidad Tanque', 7, 7, (cx + 22, cy + 12, Z0), M['fachada'], seg=40)
    geo.cilindro('Calidad Tanque Agua', 6.6, 0.2, (cx + 22, cy + 12, Z0 + 7.0), M['agua'], seg=40)
    P.oficina('Calidad Anexo', 14, 12, 2, (cx + 26, cy - 6, Z0), M, semilla=52, azotea=False)
    geo.caja('Calidad Anexo Techo Verde', (13, 11, 0.3), (cx + 26, cy - 6, Z0 + 7.8), M['verde_techo'])
    # cochera solar
    for i in range(4):
        geo.cilindro(f'Calidad Cochera Columna {i}', 0.15, 3.0, (cx - 30 + i * 10, cy - 14, Z0), M['acero'], seg=10)
    for i in range(6):
        p = geo.caja(f'Calidad Cochera Panel {i}', (5.2, 6.5, 0.12), (cx - 32 + i * 5.4, cy - 14, Z0 + 3.0), M['panel_solar'])
        p.rotation_euler[0] = math.radians(-6)
    P.estacionamiento('Calidad Estacionamiento', cx - 18, cy - 14, 1, 11, M, F['auto'], semilla=9, ocupacion=0.85)
    _arboles_borde('calidad', cx, cy, w, d, F['arboles'], 25, 0.6)


def construccion(M, F):
    cx, cy, w, d = base('construccion', M, M['grava'])
    for i in range(2):
        sx = cx - 22 + i * 8
        geo.cilindro(f'Construccion Silo {i}', 3.2, 14, (sx, cy + 14, Z0 + 4), M['acero'], seg=32)
        geo.cilindro(f'Construccion Silo Tolva {i}', 0.6, 4, (sx, cy + 14, Z0), M['acero'], seg=24, r_sup=3.2)
        geo.cilindro(f'Construccion Silo Techo {i}', 3.2, 1.6, (sx, cy + 14, Z0 + 18), M['acero'], seg=32, r_sup=0.4)
    for i, (px, py, r) in enumerate(((cx - 4, cy + 12, 7), (cx + 9, cy + 15, 6), (cx + 2, cy + 3, 5))):
        geo.cilindro(f'Construccion Monton {i}', r, r * 0.55, (px, py, Z0), M['tierra'], seg=40, r_sup=0.4)
    banda = geo.caja('Construccion Banda', (16, 1.2, 0.5), (cx - 11, cy + 13, Z0 + 6), M['gris_oscuro'])
    banda.rotation_euler[1] = math.radians(-20)
    rnd = random.Random(7)
    for i in range(24):
        geo.caja(f'Construccion Block {i}', (1.8, 1.2, rnd.uniform(0.8, 1.6)), (cx + 6 + (i % 6) * 2.6, cy - 8 - (i // 6) * 2.2, Z0), M['fachada'])
    P.oficina('Construccion Oficina', 12, 8, 1, (cx - 22, cy - 12, Z0), M, semilla=61, azotea=False)
    _arboles_borde('construccion', cx, cy, w, d, F['arboles'], 26, 0.5)


def acero(M, F):
    cx, cy, w, d = base('acero', M)
    P.nave('Acero Nave', 44, 22, 12, (cx - 6, cy + 12, Z0), M, techo=M['lamina_azul'])
    # grúa pórtico amarilla sobre el patio de almacenamiento
    for lado in (-1, 1):
        for k in (-1, 1):
            geo.caja(f'Acero Grua Pata {lado}{k}', (0.6, 0.6, 9), (cx + k * 14, cy - 8 + lado * 6, Z0), M['amarillo'])
        geo.caja(f'Acero Grua Viga {lado}', (30, 0.8, 0.9), (cx, cy - 8 + lado * 6, Z0 + 9), M['amarillo'])
    geo.caja('Acero Grua Puente', (1.0, 13, 0.8), (cx - 3, cy - 8, Z0 + 9.9), M['amarillo'])
    for f in range(3):
        for c in range(6):
            geo.caja(f'Acero Viga {f}{c}', (12, 0.3, 0.4), (cx - 6, cy - 12 + f * 2.2 + c * 0.32, Z0 + (c % 2) * 0.4), M['oxido'])
    for i in range(12):
        geo.cilindro(f'Acero Tubo {i}', 0.25, 11, (cx + 8, cy - 14 + (i % 6) * 0.52, Z0 + 0.25 + (i // 6) * 0.48), M['acero'], seg=12, rot=(0, math.pi / 2, 0))
    for i in range(6):
        geo.cilindro(f'Acero Bobina {i}', 0.9, 1.2, (cx + 22 + (i % 3) * 2.2, cy - 6 - (i // 3) * 2.4, Z0 + 0.9), M['acero'], seg=24, rot=(math.pi / 2, 0, 0))
    _arboles_borde('acero', cx, cy, w, d, F['arboles'], 27, 0.45)


def hidraulicos(M, F):
    cx, cy, w, d = base('hidraulicos', M)
    for i in range(2):
        geo.cilindro(f'Hidraulicos Tanque Blanco {i}', 6, 9, (cx - 20 + i * 13, cy + 13, Z0), M['blanco'], seg=40)
    for i in range(5):
        geo.cilindro(f'Hidraulicos Tanque Azul {i}', 2.2, 8, (cx + 6 + i * 5, cy + 15, Z0), M['azul_tanque'], seg=28)
        geo.esfera(f'Hidraulicos Domo {i}', 2.2, (cx + 6 + i * 5, cy + 15, Z0 + 8), M['azul_tanque'], escala=(1, 1, 0.35))
    for i in range(2):
        bx = cx - 14 + i * 16
        geo.caja(f'Hidraulicos Pileta {i}', (14, 10, 1.2), (bx, cy - 8, Z0), M['fachada'])
        geo.caja(f'Hidraulicos Pileta Agua {i}', (13.2, 9.2, 1.12), (bx, cy - 8, Z0 + 0.05), M['agua'])
        for lado in (-1, 1):
            geo.caja(f'Hidraulicos Baranda {i}{lado}', (14, 0.06, 0.06), (bx, cy - 8 + lado * 5, Z0 + 2.2), M['amarillo'])
    for k in range(2):
        geo.cilindro(f'Hidraulicos Tuberia {k}', 0.35 - k * 0.1, 52, (cx - 26, cy + 4 + k * 1.2, Z0 + 3.5 + k * 0.6), M['azul_tanque'] if k else M['acero'], seg=14, rot=(0, math.pi / 2, 0))
    for i in range(6):
        geo.caja(f'Hidraulicos Soporte {i}', (0.3, 2.6, 0.3), (cx - 22 + i * 9, cy + 4.6, Z0 + 3.2), M['acero'])
        geo.caja(f'Hidraulicos Soporte Pata {i}', (0.3, 0.3, 3.2), (cx - 22 + i * 9, cy + 4.6, Z0), M['acero'])
    P.oficina('Hidraulicos Casa Bombas', 12, 9, 1, (cx + 20, cy - 10, Z0), M, semilla=71, azotea=False)
    _arboles_borde('hidraulicos', cx, cy, w, d, F['arboles'], 28, 0.45)


def electrico(M, F):
    cx, cy, w, d = base('electrico', M, M['grava'])
    # granja solar: hileras de paneles inclinados 20° hacia el sur
    for f in range(4):
        for c in range(3):
            p = geo.caja(f'Electrico Panel {f}{c}', (9, 2.2, 0.08), (cx - 18 + c * 10, cy + 6 + f * 4.6, Z0 + 1.2), M['panel_solar'])
            p.rotation_euler[0] = math.radians(20)
            geo.caja(f'Electrico Panel Soporte {f}{c}', (8, 0.1, 1.2), (cx - 18 + c * 10, cy + 6 + f * 4.6, Z0), M['acero'])
    P.oficina('Electrico Cuarto Control', 10, 8, 1, (cx + 22, cy + 14, Z0), M, semilla=81, azotea=False)
    for i in range(4):
        cable_x = cx - 22 + i * 3.4
        geo.cilindro(f'Electrico Carrete {i}', 1.2, 0.9, (cable_x, cy - 18, Z0 + 1.2), M['madera'], seg=24, rot=(math.pi / 2, 0, 0))
    _arboles_borde('electrico', cx, cy, w, d, F['arboles'], 29, 0.45)


def subestacion(nombre, x, y, M, n_trafos=2):
    """Subestación cercada: transformadores con aletas, aisladores y pórtico."""
    geo.caja(f'{nombre} Plataforma', (8 + n_trafos * 5, 12, 0.2), (x, y, Z0), M['grava'])
    for i in range(n_trafos):
        tx = x - (n_trafos - 1) * 2.6 + i * 5.2
        geo.caja(f'{nombre} Trafo {i}', (3.2, 2.4, 2.8), (tx, y + 1, Z0 + 0.2), M['gris'], bisel=0.04)
        for k in range(6):
            geo.caja(f'{nombre} Aleta {i}{k}', (0.06, 3.0, 2.2), (tx - 1.5 + k * 0.6, y + 1, Z0 + 0.5), M['gris_oscuro'])
        for k in range(3):
            geo.cilindro(f'{nombre} Aislador {i}{k}', 0.12, 1.0, (tx - 0.9 + k * 0.9, y + 1, Z0 + 3.0), M['oxido'], seg=10)
    for k in (-1, 1):
        geo.caja(f'{nombre} Portico Poste {k}', (0.35, 0.35, 8), (x + k * (n_trafos * 2.6 + 1.5), y - 3.5, Z0), M['acero'])
    geo.caja(f'{nombre} Portico Viga', (n_trafos * 5.2 + 3.4, 0.3, 0.4), (x, y - 3.5, Z0 + 7.6), M['acero'])
    # cerca perimetral: postes cada 2.5 m y tres hilos
    w, d = 8 + n_trafos * 5, 12
    for lado in (-1, 1):
        for altura in (0.3, 1.3, 2.3):
            geo.caja(f'{nombre} Cerca Hilo {lado}', (w, 0.04, 0.04), (x, y + lado * d / 2, Z0 + altura), M['acero'])
            geo.caja(f'{nombre} Cerca Hilo L {lado}', (0.04, d, 0.04), (x + lado * w / 2, y, Z0 + altura), M['acero'])
        for t in range(int(w // 2.5) + 1):
            geo.caja(f'{nombre} Cerca Poste', (0.08, 0.08, 2.4), (x - w / 2 + t * w / int(w // 2.5), y + lado * d / 2, Z0), M['acero'])
        for t in range(int(d // 2.5) + 1):
            geo.caja(f'{nombre} Cerca Poste L', (0.08, 0.08, 2.4), (x + lado * w / 2, y - d / 2 + t * d / int(d // 2.5), Z0), M['acero'])
