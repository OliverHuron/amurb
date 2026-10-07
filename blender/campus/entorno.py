"""Calles, muro perimetral, elementos interactivos (postes, cámaras, subestaciones) y ciudad de contexto."""
import math
import random

from . import geo
from . import piezas as P
from . import zonas as Z

LIMITE_X, LIMITE_Y = 172, 112  # muro perimetral del campus

# Ejes de calle internos: (orientación, coordenada fija, desde, hasta)
CALLES = [
    ('H', 41.5, -170, 170), ('H', -37.0, -170, 170), ('H', -104.0, -170, 170),
    ('V', -55.0, -104, 41.5), ('V', 55.0, -104, 41.5),
    ('V', -80.0, 41.5, 110), ('V', 0.0, 41.5, 110), ('V', 80.0, 41.5, 110),
]

POSTES = [(x, -29.0, -math.pi / 2) for x in (-140, -80, -25, 25, 80, 140)] + \
         [(x, 29.5, math.pi / 2) for x in (-140, -80, -25, 25, 80, 140)]

CAMARAS = [
    (-152, -22, 0.6), (-152, 24, -0.6), (-68, 24, -2.4), (-70, -22, 2.4),
    (-12, -106, 1.57), (40, -24, -1.2), (-62, -50, 2.0), (-12, 58, -2.0),
]


def suelo(M):
    geo.plano('Terreno', 1600, 1300, (0, 0, -0.03), M['terreno'])
    # asfalto del campus y de las calles de la ciudad de contexto (manzanas de ±5 x ±5)
    geo.plano('Asfalto', 78 * 11 - 10, 66 * 11 - 10, (0, 0, 0.0), M['asfalto'])


def senalizacion(M):
    piezas = []
    for orient, fija, a, b in CALLES:
        t = a + 4
        while t < b - 4:
            if orient == 'H':
                piezas.append(geo.caja('Linea', (3.0, 0.15, 0.02), (t, fija, 0.0), M['pintura_vial']))
            else:
                piezas.append(geo.caja('Linea', (0.15, 3.0, 0.02), (fija, t, 0.0), M['pintura_vial']))
            t += 9
    # pasos peatonales frente a la sede y en el acceso
    for cx, cy, orient in ((0, -37, 'H'), (0, -104, 'H'), (-55, -37, 'V'), (55, -37, 'V')):
        for i in range(8):
            off = -5.25 + i * 1.5
            if orient == 'H':
                piezas.append(geo.caja('Cebra', (0.7, 5.5, 0.02), (cx + off, cy, 0.0), M['pintura_vial']))
            else:
                piezas.append(geo.caja('Cebra', (5.5, 0.7, 0.02), (cx, cy + off, 0.0), M['pintura_vial']))
    geo.unir('Senalizacion Vial', piezas)


def muro_y_acceso(M, F):
    piezas = []
    for lado in (-1, 1):
        piezas.append(geo.caja('Muro', (LIMITE_X * 2, 0.4, 2.4), (0, lado * LIMITE_Y, 0), M['fachada']))
        piezas.append(geo.caja('Muro', (0.4, LIMITE_Y * 2, 2.4), (lado * LIMITE_X, 0, 0), M['fachada']))
    geo.unir('Muro Perimetral', piezas)
    # hueco del portón: se tapa con el pórtico y la caseta
    geo.caja('Acceso Hueco', (16, 0.5, 2.5), (0, -LIMITE_Y, -0.1), M['asfalto'])
    for k in (-1, 1):
        geo.caja(f'Acceso Pilar {k}', (1.6, 1.6, 7.5), (k * 9, -LIMITE_Y, 0), M['gris_oscuro'], bisel=0.05)
    geo.caja('Acceso Portico', (20, 2.4, 1.4), (0, -LIMITE_Y, 7.5), M['blanco'], bisel=0.05)
    geo.caja('Acceso Caseta', (5, 4, 3.2), (-14, -LIMITE_Y + 5, 0), M['fachada'], bisel=0.05)
    geo.caja('Acceso Caseta Ventana', (5.1, 4.1, 1.2), (-14, -LIMITE_Y + 5, 1.2), M['vidrio_oscuro'])
    geo.caja('Acceso Pluma', (7, 0.12, 0.12), (-4, -LIMITE_Y + 3, 1.1), M['baliza'])
    geo.instancia('Acceso Trailer', F['camion'], (3.5, -LIMITE_Y - 6, 0.0), math.pi / 2)


def interactivos(M):
    """Postes, cámaras y subestaciones con anclas para los hotspots de la web."""
    for i, (x, y, giro) in enumerate(POSTES, start=1):
        n = f'Poste Inteligente {i:02d}'
        P.poste_inteligente(n, (x, y, Z.Z0), M, giro)
        P.ancla(n, (x, y, Z.Z0 + 9.2), 'poste', n)
    for i, (x, y, giro) in enumerate(CAMARAS, start=1):
        n = f'Camara CCTV {i:02d}'
        z0 = 0.0 if y < -100 else Z.Z0
        P.camara_cctv(n, (x, y, z0), M, giro)
        P.ancla(n, (x, y, z0 + 6.6), 'camara', n)
    Z.subestacion('Subestacion 01', 122, 63, M, n_trafos=3)
    P.ancla('Subestacion 01', (122, 63, Z.Z0 + 8), 'subestacion', 'Subestación 01')
    Z.subestacion('Subestacion 02', 74, -17, M, n_trafos=1)
    P.ancla('Subestacion 02', (74, -17, Z.Z0 + 8), 'subestacion', 'Subestación 02')
    for clave, zona in Z.ZONAS.items():
        cx, cy = zona['centro']
        P.ancla(f'Zona {clave}', (cx, cy, 24), 'zona', zona['titulo'])


def ciudad_contexto(M, F, semilla=3):
    """Manzanas urbanas alrededor del campus para dar escala (como en Apple Maps)."""
    rnd = random.Random(semilla)
    piezas_calle = []
    paso_x, paso_y, calle = 78, 66, 16
    for gx in range(-5, 6):
        for gy in range(-5, 6):
            cx, cy = gx * paso_x, gy * paso_y
            if abs(cx) < LIMITE_X + paso_x / 2 + 6 and abs(cy) < LIMITE_Y + paso_y / 2 + 6:
                continue
            w, d = paso_x - calle, paso_y - calle
            piezas_calle.append(geo.caja('Manzana', (w, d, Z.Z0), (cx, cy, 0), M['banqueta']))
            if rnd.random() < 0.18:
                # parque de manzana
                piezas_calle.append(geo.caja('Parque', (w - 4, d - 4, 0.03), (cx, cy, Z.Z0), M['cesped']))
                for _ in range(10):
                    geo.instancia('Parque Arbol', rnd.choice(F['arboles']), (cx + rnd.uniform(-w / 2 + 4, w / 2 - 4), cy + rnd.uniform(-d / 2 + 4, d / 2 - 4), Z.Z0), rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.3))
                continue
            # 2 a 4 edificios por manzana, alturas variadas
            n = rnd.choice((2, 3, 4))
            for k in range(n):
                bw = (w - 6) / n - 2
                bx = cx - w / 2 + 3 + bw / 2 + k * (bw + 2)
                bd = rnd.uniform(d * 0.45, d - 8)
                pisos = rnd.choice((2, 3, 3, 4, 5, 6, 8, 10))
                if rnd.random() < 0.25:
                    P.nave(f'Contexto Nave {gx}{gy}{k}', bw, bd, rnd.uniform(7, 11), (bx, cy, Z.Z0), M, claraboyas=False)
                else:
                    P.oficina(f'Contexto Edificio {gx}{gy}{k}', bw, bd, pisos, (bx, cy + rnd.uniform(-3, 3), Z.Z0), M, semilla=rnd.randint(0, 999), azotea=pisos > 3)
            for t in range(int(w // 10)):
                geo.instancia('Banqueta Arbol', rnd.choice(F['arboles']), (cx - w / 2 + 5 + t * 10, cy - d / 2 + 1.5, Z.Z0), rnd.uniform(0, 6.28), rnd.uniform(0.75, 1.0))
    geo.unir('Manzanas Contexto', piezas_calle)
