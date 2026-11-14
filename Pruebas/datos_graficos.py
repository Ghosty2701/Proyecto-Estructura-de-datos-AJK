"""Cargas offline de interfaz (PR-IG-001; AC-IG-001/003/004/008/016/020).

Solo datos sintéticos de pruebas; ninguna regla ni cripta de producción.
"""
import json
from pathlib import Path

from Pruebas.datos_linea_tiempo import escribir_paquete, crear_partida


def paquete_grafico(carpeta, *, resoluble=True, cinco=False):
    carpeta = Path(carpeta)
    objetos = ['pergamino'] * 5 if cinco else None
    escribir_paquete(carpeta, objetos_entrada=objetos)
    if resoluble:
        base = carpeta / 'criptas/lt'
        (base / 'llaves.json').write_text(
            json.dumps({'llaves': [{'id': 'llave_salida', 'sala': 1}]}), encoding='utf-8')
        contenido = json.loads((base / 'contenido/1.json').read_text(encoding='utf-8'))
        contenido['objetos'].append('llave_salida')
        (base / 'contenido/1.json').write_text(json.dumps(contenido), encoding='utf-8')
        (carpeta / 'catalogo/llave_salida.json').write_text(json.dumps({
            'id': 'llave_salida', 'clase': 'llave', 'nombre': 'Llave de salida',
        }), encoding='utf-8')
    return carpeta


def partida_grafica(carpeta, *, cinco=False):
    carpeta = Path(carpeta)
    return crear_partida(paquete_grafico(carpeta / 'datos', cinco=cinco), carpeta / 'cache')


def mapa_sintetico(cantidad=300, *, conflicto=False):
    """Proyección de conocimiento: IDs dispersos y sin referencias al motor."""
    salas = []
    for i in range(cantidad):
        identificador = 101 + 17 * i
        salidas = []
        if i + 1 < cantidad:
            salidas.append(('E', identificador + 17, 'Sala', 100, True))
        if i:
            salidas.append(('O', identificador - 17, 'Sala', 100, True))
        if conflicto and i == 0 and cantidad > 2:
            salidas.append(('N', identificador + 34, 'Sala', 100, False))
        salas.append((identificador, 2, f'Sala {i + 1}', salidas))
    return salas
