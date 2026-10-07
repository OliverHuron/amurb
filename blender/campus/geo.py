"""Primitivas de geometría en metros (1 unidad = 1 m), sin bpy.ops para que sea rápido."""
import math

import bmesh
import bpy

_coleccion_actual = None


def coleccion(nombre, padre=None):
    col = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    destino = padre or bpy.context.scene.collection
    if col.name not in destino.children:
        destino.children.link(col)
    return col


def usar_coleccion(col):
    global _coleccion_actual
    _coleccion_actual = col


def _vincular(obj, col=None):
    (col or _coleccion_actual or bpy.context.scene.collection).objects.link(obj)
    return obj


def _objeto(nombre, malla, mat, pos, rot, col):
    obj = bpy.data.objects.new(nombre, malla)
    obj.location = pos
    obj.rotation_euler = rot
    if mat is not None:
        malla.materials.append(mat)
    return _vincular(obj, col)


def caja(nombre, dims, pos, mat, rot_z=0.0, bisel=0.0, col=None):
    """Caja con la base en pos[2] y centrada en x/y. dims = (ancho x, fondo y, alto z)."""
    w, d, h = dims
    x, y = w / 2, d / 2
    verts = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0), (-x, -y, h), (x, -y, h), (x, y, h), (-x, y, h)]
    caras = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(verts, [], caras)
    malla.update()
    obj = _objeto(nombre, malla, mat, pos, (0, 0, rot_z), col)
    if bisel > 0:
        mod = obj.modifiers.new('Bisel', 'BEVEL')
        mod.width = bisel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
    return obj


def cilindro(nombre, r, h, pos, mat, seg=24, rot=(0, 0, 0), r_sup=None, col=None, suave=True):
    """Cilindro (o cono si r_sup) con la base en el origen local, eje Z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r_sup is None else r_sup, depth=h)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, h / 2))
    if suave:
        for cara in bm.faces:
            cara.smooth = len(cara.verts) == 4
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    return _objeto(nombre, malla, mat, pos, rot, col)


def esfera(nombre, r, pos, mat, subdiv=3, escala=(1, 1, 1), col=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    for cara in bm.faces:
        cara.smooth = True
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    obj = _objeto(nombre, malla, mat, pos, (0, 0, 0), col)
    obj.scale = escala
    return obj


def plano(nombre, w, d, pos, mat, rot_z=0.0, col=None):
    x, y = w / 2, d / 2
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata([(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0)], [], [(0, 1, 2, 3)])
    malla.update()
    return _objeto(nombre, malla, mat, pos, (0, 0, rot_z), col)


def prisma_triangular(nombre, largo, base, alto, pos, mat, rot_z=0.0, col=None):
    """Prisma a lo largo de X con sección triangular rectángulo (diente de sierra)."""
    l, b = largo / 2, base / 2
    verts = [(-l, -b, 0), (l, -b, 0), (l, b, 0), (-l, b, 0), (-l, b, alto), (l, b, alto)]
    caras = [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(verts, [], caras)
    malla.update()
    return _objeto(nombre, malla, mat, pos, (0, 0, rot_z), col)


def instancia(nombre, coleccion_fuente, pos, rot_z=0.0, escala=1.0, col=None):
    obj = bpy.data.objects.new(nombre, None)
    obj.instance_type = 'COLLECTION'
    obj.instance_collection = coleccion_fuente
    obj.location = pos
    obj.rotation_euler = (0, 0, rot_z)
    obj.scale = (escala, escala, escala)
    return _vincular(obj, col)


def unir(nombre, objetos):
    """Fusiona objetos estáticos en uno solo (menos objetos = escena más ligera)."""
    if len(objetos) < 2:
        return objetos[0] if objetos else None
    ctx = {'active_object': objetos[0], 'selected_editable_objects': objetos, 'object': objetos[0]}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    objetos[0].name = nombre
    return objetos[0]


def rad(grados):
    return math.radians(grados)
