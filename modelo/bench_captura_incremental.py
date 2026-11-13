"""ABBA del capturador piloto: marcas conocidas; no son ciclos del juego."""
import gc
import json
import platform
import tracemalloc
from pathlib import Path
from time import perf_counter_ns

from adaptadores.captura_incremental import CapturadorIncremental, comprobar_equivalencia
from adaptadores.instantanea_inmutable import capturar_estado
from modelo.bench_linea_tiempo import estadisticas
from modelo.rastro import SalaRastro


def _raiz(salas):
    return [[SalaRastro(i) for i in range(salas)], [SalaRastro(-1)]]


def _mutar(raiz, paso, captura=None):
    # 16 escrituras; se sustituye un objeto con sus contenedores para incluir
    # altas/retirada. Mutación y marcado ocurren DENTRO del cronómetro.
    for i in range(16):
        sala = raiz[0][(paso * 17 + i) % len(raiz[0])]
        sala.ultimo_rastro = paso
        if captura is not None:
            captura.marcar(sala)
    raiz[1][0] = SalaRastro(-paso-2)
    if captura is not None:
        captura.marcar(raiz[1])


def _resumen(tiempos):
    return {**estadisticas(tiempos), 'excedidos_20ms': sum(t >= 20 for t in tiempos)}


def _bloque(tipo, salas, versiones):
    raiz = _raiz(salas)
    captura = CapturadorIncremental() if tipo == 'incremental' else None
    inicio = perf_counter_ns()
    inicial = (captura.capturar(raiz, verificar=False) if captura
               else capturar_estado(raiz))
    inicial_ms = (perf_counter_ns() - inicio) / 1e6
    conservados, tiempos = [inicial], []
    codificados, campos, retirados = [], [], 0
    try:
        for paso in range(versiones):
            inicio = perf_counter_ns()
            _mutar(raiz, paso, captura)
            punto = (captura.capturar(raiz, verificar=False) if captura
                     else capturar_estado(raiz, anterior=conservados[-1]))
            tiempos.append((perf_counter_ns() - inicio) / 1e6)
            conservados.append(punto)
            if captura:
                codificados.append(captura.estadisticas['objetos_codificados'])
                campos.append(captura.estadisticas['campos_leidos'])
                retirados += captura.estadisticas['registros_retirados']
        if captura:
            comprobar_equivalencia(raiz, conservados[-1])
            assert captura.registrados == conservados[-1].version.cantidad
        else:
            assert capturar_estado(conservados[-1].reconstruir()).registros == capturar_estado(raiz).registros
        assert conservados[0].reconstruir()[0][0].ultimo_rastro is None
        inicio = perf_counter_ns()
        copia = conservados[-1].reconstruir()
        reconstruccion_ms = (perf_counter_ns() - inicio) / 1e6
        assert copia[1][0].sala_id == -versiones-1
        return {'tipo': tipo, 'inicio_ms': inicial_ms,
                'mutacion_marcado_captura': _resumen(tiempos),
                'reconstruccion_final_ms': reconstruccion_ms,
                'objetos_codificados_por_punto': (
                    {'min': min(codificados), 'max': max(codificados)} if captura else
                    {'min': len(inicial.registros), 'max': len(inicial.registros)}),
                'campos_leidos_por_punto': (
                    {'min': min(campos), 'max': max(campos)} if captura else None),
                'registros_retirados_total': retirados if captura else None,
                'registros_iniciales': (inicial.version.cantidad if captura
                                       else len(inicial.registros)),
                'equivalencia_final_y_punto_inicial': True}
    finally:
        if captura:
            captura.cerrar()


def _memoria(salas, versiones):
    gc.collect()
    tracemalloc.start()
    try:
        raiz = _raiz(salas)
        captura = CapturadorIncremental()
        puntos = [captura.capturar(raiz, verificar=False)]
        for paso in range(versiones):
            _mutar(raiz, paso, captura)
            puntos.append(captura.capturar(raiz, verificar=False))
        gc.collect()
        con_sesion, pico = tracemalloc.get_traced_memory()
        captura.cerrar()
        del raiz
        gc.collect()
        solo_puntos = tracemalloc.get_traced_memory()[0]
        assert puntos[-1].reconstruir()[1][0].sala_id == -versiones-1
        return {'con_sesion_y_modelo_bytes': con_sesion, 'solo_puntos_bytes': solo_puntos,
                'pico_bytes': pico, 'versiones_retenidas': len(puntos), 'es_rss': False}
    finally:
        tracemalloc.stop()


def medir(salas=1500, versiones=200):
    if (type(salas) is not int or salas < 16 or type(versiones) is not int or versiones < 1
            or not gc.isenabled() or tracemalloc.is_tracing()):
        raise ValueError('salas>=16, versiones>=1, enteros, GC habilitado y sin trazado externo')
    bloques = []
    for tipo in ('completo', 'incremental', 'incremental', 'completo'):
        gc.collect()
        bloques.append(_bloque(tipo, salas, versiones))
    return {'python': platform.python_version(), 'salas': salas, 'versiones': versiones,
            'gc_habilitado': True, 'tracemalloc_en_tiempos': False,
            'bloques_abba': bloques, 'memoria_incremental': _memoria(salas, versiones),
            'alcance': 'Carga controlada; no partida ni consultas ni K. '
            'Incluye mutacion, marcas, IDs, codificacion, copia de indices, altas, '
            'alcanzabilidad, retirada y GC; inicio separado. Oraculo fuera del tiempo '
            'solo al final y punto inicial intacto. No prueba cobertura de escrituras '
            'del juego ni certifica 20/50 ms. Memoria en ejecucion aparte; sin RSS. '
            'Reconstruccion final es una muestra, no distribucion de consultas.'}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salas', type=int, default=1500)
    p.add_argument('--versiones', type=int, default=200)
    p.add_argument('--salida-json', required=True)
    args = p.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir(args.salas, args.versiones),
                                                ensure_ascii=False, indent=2), encoding='utf-8')
