"""Piloto aislado del índice: excluye detectar/serializar mutaciones del juego."""
import gc
import json
import platform
import tracemalloc
from pathlib import Path
from time import perf_counter_ns

from modelo.indice_versionado import VersionRegistros, ELIMINAR
from modelo.bench_linea_tiempo import estadisticas


def _lote(paso, registros=6000):
    # 32 actualizaciones + 32 bajas + 32 altas; cardinalidad estable.
    cambios = [(i, (18, (paso,))) for i in range(32)]
    anteriores = range(registros-32, registros) if paso == 0 else range(
        registros+(paso-1)*32, registros+paso*32)
    cambios.extend((i, ELIMINAR) for i in anteriores)
    cambios.extend((i, (18, (paso, i))) for i in range(registros+paso*32, registros+(paso+1)*32))
    return cambios


def medir(versiones=200):
    if not gc.isenabled() or tracemalloc.is_tracing() or versiones < 1:
        raise ValueError('GC habilitado, sin trazado externo y versiones positivas')
    inicial = VersionRegistros.vacia(32)
    inicio = perf_counter_ns()
    inicial = inicial.con_cambios((i, (18, (i,))) for i in range(6000))
    construccion_ms = (perf_counter_ns()-inicio)/1e6
    tiempos, conservadas = [], [inicial]
    for paso in range(versiones):
        lote = _lote(paso)
        inicio = perf_counter_ns()
        nueva = conservadas[-1].con_cambios(lote)
        tiempos.append((perf_counter_ns()-inicio)/1e6)
        conservadas.append(nueva)
        assert nueva.cantidad == 6000
        assert inicial.obtener(0) == (18, (0,))
        assert nueva.obtener(0) == (18, (paso,))
    # Caso de limpieza garantizada al superar ocupación activa + tumbas.
    llena = VersionRegistros.vacia(16384).con_cambios((i, (18, (i,))) for i in range(11468))
    bajas = llena.con_cambios((i, ELIMINAR) for i in range(9000))
    inicio = perf_counter_ns()
    limpia = bajas.con_cambios([(10**12, (18, (99,)))])
    limpieza_ms = (perf_counter_ns()-inicio)/1e6
    assert limpia.tumbas == 0 and len(limpia.casillas) == len(bajas.casillas)
    assert bajas.tumbas == 9000 and limpia.cantidad == 2469
    gc.collect()
    tracemalloc.start()
    try:
        # Incluye índice inicial y todas las versiones del caso de memoria.
        v = VersionRegistros.vacia().con_cambios((i, (18, (i,))) for i in range(6000))
        memoria = [v]
        for paso in range(versiones):
            v = v.con_cambios(_lote(paso))
            memoria.append(v)
        gc.collect()
        actual, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    stats = estadisticas(tiempos)
    stats['excedidos_20ms'] = sum(t >= 20 for t in tiempos)
    return {'python': platform.python_version(), 'versiones': versiones,
            'registros_activos': 6000, 'cambios_por_lote': 96,
            'capacidad_inicial': len(inicial.casillas),
            'capacidad_final': len(conservadas[-1].casillas),
            'construccion_inicial_con_crecimiento_ms': construccion_ms,
            'limpieza_tumbas_9000_a_0_ms': limpieza_ms,
            'publicacion': stats, 'retenida_bytes': actual, 'pico_bytes': pico,
            'gc_habilitado': True, 'tracemalloc_en_tiempos': False,
            'alcance': 'Indice aislado, lotes preparados fuera '
                       'del tiempo. Incluye validacion de registros, copia, tumbas y rehash; '
                       'excluye seguimiento, IDs de modelos, serializacion del juego, replay '
                       'y reconstruccion. Memoria Python de versiones mas inicial en otra '
                       'ejecucion, excluye caso separado de limpieza, no RSS. '
                       'No certifica ciclos ni consultas ni elige K.'}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salida-json', required=True)
    args = p.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir(), ensure_ascii=False, indent=2),
                                     encoding='utf-8')
