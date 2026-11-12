"""Medir ciclos y consultas del mismo juego, con GC habilitado y resumen compacto."""
import gc
import platform
import tempfile
from pathlib import Path

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar, _cronometrar
from modelo.bench_linea_tiempo import _preparar, _indices, _consultas, _medir, _firma, estadisticas


def _tiempos(valores, limite):
    if not valores:
        return {'cantidad': 0}
    d = estadisticas(valores)
    d.pop('excedidos_50ms')
    d['limite_ms'] = limite
    d['excedidos'] = sum(t >= limite for t in valores)
    return d


def medir_presupuestos(acciones=5000, salas=300, valores_k=(5, 10, 25), cazadores=32,
                       rondas=3, muestras=12, semilla=2026, informar=True):
    if acciones < 3 or salas < 3 or muestras < 6 or rondas < 1 or cazadores < 0:
        raise ValueError('carga invalida')
    if not valores_k or any(type(k) is not int or k < 1 for k in valores_k):
        raise ValueError('K invalido')
    if not gc.isenabled():
        raise ValueError('mantener GC habilitado para medir el uso normal')
    filas = []
    referencias = None
    with tempfile.TemporaryDirectory(prefix='cripta-presupuestos-') as temporal:
        p = Path(temporal)
        _paquete(p/'datos', salas, semilla, cazadores=cazadores)
        for k in valores_k:
            if informar:
                print(f'PRESUPUESTOS: K={k}, {acciones} acciones, {salas} salas, {cazadores} cazadores', flush=True)
            c = _cargador(p/'datos', p/f'cache-{k}')
            ciclos, copias, con_punto, sin_punto = [], [], [], []

            def conectar(partida):
                original = partida.linea_tiempo.copiar

                def copiar(raiz):
                    resultado, ms = _cronometrar(lambda: original(raiz))
                    copias.append(ms)
                    return resultado

                partida.linea_tiempo.copiar = copiar

            def ejecutar(partida, texto):
                antes, puntos = partida.acciones_ejecutadas, len(partida.linea_tiempo.puntos)
                _, ms = _cronometrar(lambda: _ejecutar(partida, texto))
                if partida.acciones_ejecutadas > antes:
                    ciclos.append(ms)
                    (con_punto if len(partida.linea_tiempo.puntos) > puntos else sin_punto).append(ms)

            a, capturas = _preparar(c, acciones, k, cazadores, semilla, _indices(acciones, muestras),
                                    instrumentar=conectar, ejecutar=ejecutar)
            consultas = _consultas(_indices(acciones, muestras), capturas, a.motor.reloj)
            firma = _firma(a, c)
            medidas, obtenidos = _medir(a, consultas, rondas, k, referencias)
            assert _firma(a, c) == firma
            if referencias is None:
                referencias = obtenidos
            fila = {'k': k, 'ciclos': _tiempos(ciclos, 20), 'copias': _tiempos(copias, 20),
                    'ciclos_con_punto': _tiempos(con_punto, 20),
                    'ciclos_sin_punto': _tiempos(sin_punto, 20),
                    'consultas': _tiempos([m['tiempo_ms'] for m in medidas], 50),
                    'maximo_acciones_reaplicadas': max(m['acciones_reaplicadas'] for m in medidas),
                    'partida_intacta': True, 'http': 0}
            filas.append(fila)
            if informar:
                print(f"  ciclo max {fila['ciclos']['maximo_ms']:.3f} ms; >=20: {fila['ciclos']['excedidos']}; "
                      f"consulta max {fila['consultas']['maximo_ms']:.3f} ms; >=50: {fila['consultas']['excedidos']}", flush=True)
            del a, c, capturas
            gc.collect()
    return {'semilla': semilla, 'acciones': acciones, 'salas': salas, 'cazadores': cazadores,
            'rondas_consulta': rondas, 'rondas_ciclos': 1, 'gc_habilitado': True,
            'python': platform.python_version(), 'plataforma': platform.platform(), 'escenarios': filas,
            'alcance': 'Sintetico de produccion; ciclos incluyen accion/registro/punto; '
                       'consultas incluyen copia/re-simulacion/resumen. Sin red/renderizado. '
                       'No elige K ni certifica referencia oficial. Se incluyen todos los picos.'}


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--salida-json', required=True)
    args = parser.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir_presupuestos(), ensure_ascii=False, indent=2), encoding='utf-8')
