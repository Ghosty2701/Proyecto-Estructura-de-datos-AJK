"""Captura/memoria por punto frente al código local de una revisión Git fija.

La revisión se carga solo para este ensayo, nunca en el juego. Tiempos y
tracemalloc se ejecutan por separado; exportación sin muestras individuales.
"""
import gc
import json
import platform
import subprocess
import sys
import tempfile
import tracemalloc
from pathlib import Path
from types import ModuleType

from adaptadores.bench_persistencia import _paquete, _cargador, _cronometrar
from adaptadores.instantanea_inmutable import capturar_estado
from adaptadores.estado_binario import codificar_punto
from controlador.cargar_partida import _GestorConsulta
from modelo.bench_linea_tiempo import _preparar, estadisticas


def medir_costo_catalogo():
    """Estimar aparte el costo fijo con una réplica de su construcción."""
    from adaptadores.instantanea_inmutable import _REFERENCIAS_ID
    if tracemalloc.is_tracing():
        raise RuntimeError('detener el trazado externo antes de medir el catalogo')
    gc.collect()
    tracemalloc.start()
    try:
        replica = tuple((i,) for i in range(len(_REFERENCIAS_ID)))
        gc.collect()
        actual, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert replica == _REFERENCIAS_ID
    return {'capacidad': len(_REFERENCIAS_ID), 'asignaciones_estimadas_bytes': actual,
            'pico_construccion_bytes': pico,
            'alcance': 'Replica de la construccion fija tras el import, con GC y tracemalloc; '
                       'incluye indice, tokens y enteros nuevos. No RSS. El catalogo real '
                       'ya existia antes de trazar cada punto y se contabiliza aparte.'}


def medir(revision='de2b408', rondas=5, exigir_registros_iguales=False, alternar=False):
    if rondas < 1 or not gc.isenabled() or tracemalloc.is_tracing():
        raise ValueError('rondas positivas, GC habilitado y sin trazado externo')
    ruta = 'adaptadores/instantanea_inmutable.py'
    codigo = subprocess.check_output(['git', 'show', f'{revision}:{ruta}'], encoding='utf-8')
    anterior = ModuleType('_instantanea_referencia_bench')
    sys.modules[anterior.__name__] = anterior
    try:
        exec(compile(codigo, f'{revision}:{ruta}', 'exec'), anterior.__dict__)
        with tempfile.TemporaryDirectory(prefix='cripta-registros-') as temporal:
            carpeta = Path(temporal)
            _paquete(carpeta/'datos', 300, 2026, cazadores=32)
            c = _cargador(carpeta/'datos', carpeta/'cache')
            p, _ = _preparar(c, 5000, 5001, 32, 2026, [1])
            raiz = (p, c.salas_ordenadas())
            identidad = c._identidad(p)
            esperado = codificar_punto(p.motor, p.jugador, raiz[1], identidad, {'partida': p})
            referencia = anterior.capturar_estado(raiz)
            def ensayar(capturar, capturas, restauraciones, cantidad):
                for _ in range(cantidad):
                    gc.collect()
                    punto, ms = _cronometrar(lambda: capturar(raiz))
                    capturas.append(ms)
                    if exigir_registros_iguales:
                        assert punto.raiz == referencia.raiz
                        assert punto.registros == referencia.registros
                    creados = []
                    (copia, salas), ms = _cronometrar(lambda: punto.reconstruir(creados=creados))
                    restauraciones.append(ms)
                    try:
                        assert codificar_punto(copia.motor, copia.jugador, salas, identidad,
                                              {'partida': copia}) == esperado
                    finally:
                        _GestorConsulta(creados).liberar_copia()
                    del punto, copia, salas

            def medir_fila(nombre, capturar, capturas, restauraciones):
                gc.collect()
                tracemalloc.start()
                try:
                    punto = capturar(raiz)
                    gc.collect()
                    retenida, pico = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()
                registros = len(punto.registros)
                del punto
                fila = {'variante': nombre, 'captura': estadisticas(capturas),
                        'restauracion': estadisticas(restauraciones),
                        'retenida_bytes': retenida, 'pico_bytes': pico, 'registros': registros}
                fila['captura']['excedidos_20ms'] = sum(ms >= 20 for ms in capturas)
                print(nombre, fila, flush=True)
                return fila

            variantes = [('anterior', anterior.capturar_estado), ('actual', capturar_estado)]
            filas = []
            if alternar:
                capturas, restauraciones = [[], []], [[], []]
                for _ in range(rondas):
                    for i in (0, 1, 1, 0):
                        ensayar(variantes[i][1], capturas[i], restauraciones[i], 1)
                # Memoria después de todos los tiempos, sin intercalar trazado.
                for i, (nombre, capturar) in enumerate(variantes):
                    filas.append(medir_fila(nombre, capturar, capturas[i], restauraciones[i]))
            else:
                for i in (0, 1, 1, 0):
                    nombre, capturar = variantes[i]
                    capturas, restauraciones = [], []
                    ensayar(capturar, capturas, restauraciones, rondas)
                    filas.append(medir_fila(nombre, capturar, capturas, restauraciones))
            return {'referencia_git': revision, 'acciones': 5000, 'salas': 300,
                    'cazadores': 32, 'semilla': 2026, 'rondas_por_bloque': rondas,
                    'python': platform.python_version(), 'plataforma': platform.platform(),
                    'gc_habilitado': gc.isenabled(), 'resultados': filas,
                    'registros_iguales_exigidos': exigir_registros_iguales,
                    'catalogo_actual': medir_costo_catalogo(),
                    'orden': 'ABBA intercalado por captura' if alternar else 'ABBA por bloques',
                    'alcance': 'ABBA; un punto de la misma partida sintetica, fuente excluida '
                               'del trazado; memoria Python, no RSS ni historia completa. '
                               'Tiempos sin tracemalloc; restauracion sin replay/liberacion. '
                               'Bytes v6 equivalentes en todas las restauraciones.'}
    finally:
        sys.modules.pop(anterior.__name__, None)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida-json', required=True)
    parser.add_argument('--revision', default='de2b408')
    parser.add_argument('--rondas', type=int, default=5)
    parser.add_argument('--exigir-registros-iguales', action='store_true')
    parser.add_argument('--alternar', action='store_true')
    args = parser.parse_args()
    resultado = medir(args.revision, args.rondas, args.exigir_registros_iguales, args.alternar)
    Path(args.salida_json).write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                                     encoding='utf-8')
