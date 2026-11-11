"""T029: asignaciones Python con tracemalloc y tiempos en ejecuciones separadas.

Reutiliza la carga de consultas y las decisiones aprobadas; no cambia K.
"""
import gc
import platform
import tempfile
import tracemalloc
from pathlib import Path
from time import perf_counter_ns

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar
from modelo.bench_linea_tiempo import _preparar, _resumen, estadisticas


def medir_memoria(acciones=5000, cantidad_salas=200, valores_k=(10, 25, 50, 100),
                   cazadores=(0, 32), rondas=1, semilla=2026, informar=True):
    if (acciones < 3 or cantidad_salas < 3 or rondas < 1 or not valores_k or not cazadores
            or any(type(k) is not int or k < 1 for k in valores_k)
            or any(type(c) is not int or c < 0 for c in cazadores)):
        raise ValueError('acciones/salas >= 3, rondas/K positivos y cazadores >= 0')
    if tracemalloc.is_tracing():
        raise RuntimeError('detener el trazado externo antes de medir tiempos')
    filas = []
    with tempfile.TemporaryDirectory(prefix='cripta-bench-memoria-') as temporal:
        raiz = Path(temporal)
        for cantidad in cazadores:
            paquete = raiz / f'datos-{cantidad}'
            _paquete(paquete, cantidad_salas, semilla, cazadores=cantidad)
            for k in (*valores_k, None):
                if informar:
                    print(f'MEMORIA/PUNTOS: {acciones} acciones, {cantidad_salas} salas, '
                          f'{cantidad} cazadores, K={k}', flush=True)
                efectivo = acciones + 2 if k is None else k
                gc.collect()
                mitad = []

                def observar(partida, texto):
                    _ejecutar(partida, texto)
                    if partida.acciones_ejecutadas == acciones // 2 and not mitad:
                        gc.collect()
                        mitad.append(tracemalloc.get_traced_memory()[0])

                tracemalloc.start()
                try:
                    cargador = _cargador(paquete, raiz / f'mem-{cantidad}-{k}')
                    partida, capturas = _preparar(cargador, acciones, efectivo, cantidad,
                                                  semilla, [1], ejecutar=observar)
                    del capturas
                    gc.collect()
                    actual, pico = tracemalloc.get_traced_memory()
                    esperado = _resumen(partida)
                    puntos = len(partida.linea_tiempo.puntos)
                    assert partida.fuente.solicitudes_realizadas == 0
                finally:
                    tracemalloc.stop()
                del partida, cargador
                gc.collect()
                copias, ciclos = [], []

                def instrumentar(partida):
                    original = partida.linea_tiempo.copiar

                    def copiar(estado):
                        inicio = perf_counter_ns()
                        resultado = original(estado)
                        copias.append((perf_counter_ns() - inicio) / 1e6)
                        return resultado

                    partida.linea_tiempo.copiar = copiar

                def cronometrar(partida, texto):
                    assert not tracemalloc.is_tracing()
                    antes = partida.acciones_ejecutadas
                    inicio = perf_counter_ns()
                    _ejecutar(partida, texto)
                    ms = (perf_counter_ns() - inicio) / 1e6
                    if partida.acciones_ejecutadas > antes:
                        ciclos.append(ms)

                for ronda in range(rondas):
                    cargador = _cargador(paquete, raiz / f'tiempo-{cantidad}-{k}-{ronda}')
                    partida, capturas = _preparar(cargador, acciones, efectivo, cantidad,
                        semilla, [1], instrumentar=instrumentar, ejecutar=cronometrar)
                    assert _resumen(partida) == esperado, 'el trazado cambio el resultado'
                    assert len(partida.linea_tiempo.puntos) == puntos
                    assert partida.fuente.solicitudes_realizadas == 0
                    del partida, cargador, capturas
                    gc.collect()
                tiempos_copia = estadisticas(copias) if copias else {'cantidad': 0}
                tiempos_ciclo = estadisticas(ciclos)
                tiempos_ciclo.pop('excedidos_50ms')
                tiempos_ciclo['excedidos_20ms'] = sum(t >= 20 for t in ciclos)
                fila = {'k': k, 'cazadores': cantidad, 'puntos': puntos,
                        'memoria_mitad_bytes': mitad[0], 'memoria_final_bytes': actual,
                        'pico_bytes': pico, 'creacion_puntos': tiempos_copia,
                        'ciclos': tiempos_ciclo, 'tiempos_puntos_ms': copias,
                        'tiempos_ciclos_ms': ciclos, 'tracemalloc_en_tiempos': False,
                        'equivalentes': True, 'http': 0, 'vista': False}
                filas.append(fila)
                if informar:
                    print(f'  retenida {actual / 2**20:.2f} MiB; pico {pico / 2**20:.2f} MiB; '
                          f'punto max {max(copias, default=0):.3f} ms; '
                          f'ciclo max {max(ciclos):.3f} ms; >=20 ms: '
                          f"{tiempos_ciclo['excedidos_20ms']}/{len(ciclos)}", flush=True)
    return {'acciones': acciones, 'salas': cantidad_salas, 'rondas_tiempo': rondas,
            'rondas_memoria': 1, 'semilla': semilla, 'python': platform.python_version(),
            'plataforma': platform.platform(), 'escenarios': filas,
            'alcance': 'Asignaciones Python trazadas desde antes del cargador hasta el final; '
                       'incluye infraestructura y puntos, no RSS ni memoria nativa total. '
                       'Mitad/final tras GC. Tiempo en otra ejecucion sin tracemalloc, GC habilitado. '
                       'Copia periodica medida, punto inicial excluido de tiempos. Ciclo incluye '
                       'accion y registro, incluida copia cuando corresponde. Carga sintetica de '
                       'consultas con movimiento ponderado y pergamino; no certifica referencia oficial.'}
