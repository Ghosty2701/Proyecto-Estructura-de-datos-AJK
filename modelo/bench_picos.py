"""Diagnóstico acotado de ciclos lentos: punto, GC y tiempo de CPU del hilo.

No deshabilita GC ni cambia umbrales. El observador añade sobrecarga: sirve
para localizar picos, no para certificar los presupuestos de producción.
"""
import gc
import json
import platform
import tempfile
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar
from modelo.bench_linea_tiempo import _preparar


def comparar_plantilla():
    """Ensayo exploratorio del prototipo heredado, sin activarlo en el juego."""
    from adaptadores.estado_compartido import ContextoCompartido
    from adaptadores.instantanea_inmutable import capturar_estado
    from adaptadores.bench_persistencia import _cronometrar
    from modelo.bench_linea_tiempo import estadisticas
    with tempfile.TemporaryDirectory(prefix='cripta-explorar-plantilla-') as temporal:
        raiz = Path(temporal)
        _paquete(raiz/'datos', 300, 2026, cazadores=32)
        c = _cargador(raiz/'datos', raiz/'cache')
        p, _ = _preparar(c, 5000, 10000, 32, 2026, [1])
        salas = c.salas_ordenadas()
        estado = (p, salas)
        previo = p.linea_tiempo.puntos[-1].estado
        contexto = ContextoCompartido(p, salas)
        muestras = [[], []]
        for _ in range(10):
            for i in (0, 1, 1, 0):
                gc.collect()
                q, ms = _cronometrar(lambda: capturar_estado(estado, previo) if i == 0
                                     else contexto.capturar(p))
                muestras[i].append(ms)
                if i == 1:
                    copia, _ = q.reconstruir()
                    assert copia.resumen_historico('') == p.resumen_historico('')
                    assert copia.motor.azar.getstate() == p.motor.azar.getstate()
                    del copia
                del q
        return {'acciones': 5000, 'salas': 300, 'cazadores': 32, 'semilla': 2026,
                'captura_actual': estadisticas(muestras[0]),
                'plantilla_heredada': estadisticas(muestras[1]),
                'alcance': 'Exploratorio ABBA de captura aislada, 20 por variante. '
                           'Solo punto inicial en preparacion (K=10000). Plantilla heredada '
                           'conserva grafo mutable; no integrada ni prueba de ciclos, memoria '
                           'o consultas. GC habilitado, recoleccion entre muestras fuera del '
                           'tiempo. Resumen y azar reconstruidos comprobados.'}


def diagnosticar(acciones=5000, valores_k=(10, 25), salas=300, cazadores=32):
    if not gc.isenabled():
        raise ValueError('el diagnostico requiere GC habilitado')
    filas = []
    with tempfile.TemporaryDirectory(prefix='cripta-picos-') as temporal:
        raiz = Path(temporal)
        _paquete(raiz/'datos', salas, 2026, cazadores=cazadores)
        for k in valores_k:
            print(f'DIAGNOSTICO: K={k}, {acciones} acciones', flush=True)
            inicios, duraciones, cantidades = [0]*3, [0]*3, [0]*3
            lentos, peores = [], []
            todos = [0, 0, 0]  # total, con punto, sin punto
            copia_ms = 0

            def observar(fase, info):
                generacion = info['generation']
                if fase == 'start':
                    inicios[generacion] = perf_counter_ns()
                else:
                    duraciones[generacion] += perf_counter_ns() - inicios[generacion]
                    cantidades[generacion] += 1

            def conectar(p):
                original = p.linea_tiempo.copiar

                def copiar(r):
                    nonlocal copia_ms
                    inicio = perf_counter_ns()
                    resultado = original(r)
                    copia_ms += (perf_counter_ns() - inicio)/1e6
                    return resultado

                p.linea_tiempo.copiar = copiar

            def ejecutar(p, texto):
                nonlocal copia_ms
                copia_ms = 0
                numero, puntos = p.acciones_ejecutadas, len(p.linea_tiempo.puntos)
                gc_antes, n_antes = duraciones[:], cantidades[:]
                cpu = thread_time_ns()
                inicio = perf_counter_ns()
                _ejecutar(p, texto)
                ms = (perf_counter_ns() - inicio)/1e6
                cpu_ms = (thread_time_ns() - cpu)/1e6
                if p.acciones_ejecutadas <= numero:
                    return
                con_punto = len(p.linea_tiempo.puntos) > puntos
                todos[0] += 1
                todos[1 if con_punto else 2] += 1
                if ms >= 20:
                    pausas = [(v-a)/1e6 for v, a in zip(duraciones, gc_antes)]
                    ciclos_gc = [v-a for v, a in zip(cantidades, n_antes)]
                    fila = {'accion_ejecutada': todos[0], 'orden': texto, 'con_punto': con_punto,
                            'ciclo_ms': ms, 'captura_ms': copia_ms,
                            'resto_ms': max(0, ms-copia_ms), 'cpu_hilo_ms': cpu_ms,
                            'gc_ms_por_generacion': pausas, 'gc_cantidades': ciclos_gc}
                    lentos.append(fila)
                    peores.append(fila)
                    peores.sort(key=lambda f: f['ciclo_ms'], reverse=True)
                    del peores[10:]

            gc.callbacks.append(observar)
            try:
                c = _cargador(raiz/'datos', raiz/f'cache-{k}')
                p, _ = _preparar(c, acciones, k, cazadores, 2026, [1],
                                 instrumentar=conectar, ejecutar=ejecutar)
                assert p.fuente.solicitudes_realizadas == 0
                filas.append({'k': k, 'ciclos': todos[0], 'con_punto': todos[1],
                    'sin_punto': todos[2], 'lentos': len(lentos),
                    'lentos_con_punto': sum(f['con_punto'] for f in lentos),
                    'lentos_con_gc': sum(any(f['gc_cantidades']) for f in lentos),
                    'lentos_con_gen2': sum(f['gc_cantidades'][2] > 0 for f in lentos),
                    'suma_lentos_ms': sum(f['ciclo_ms'] for f in lentos),
                    'suma_captura_lentos_ms': sum(f['captura_ms'] for f in lentos),
                    'suma_gc_lentos_ms': sum(sum(f['gc_ms_por_generacion']) for f in lentos),
                    'peores_diez': peores})
                print(filas[-1], flush=True)
            finally:
                gc.callbacks.remove(observar)
            del p, c
            gc.collect()
    return {'acciones': acciones, 'salas': salas, 'cazadores': cazadores,
            'semilla': 2026, 'python': platform.python_version(),
            'umbral_gc': gc.get_threshold(), 'gc_habilitado': gc.isenabled(),
            'escenarios': filas,
            'alcance': 'Diagnostico sintetico instrumentado; maximo diez ciclos detallados por K. '
                       'GC incluido en captura y ciclo, no sumar las fases entre si. CPU del '
                       'hilo puede tener resolucion limitada; diferencia con pared no prueba '
                       'por si sola espera del SO. No certifica 20/50 ms ni elige K.'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida-json', required=True)
    parser.add_argument('--comparar-plantilla', action='store_true')
    args = parser.parse_args()
    resultado = comparar_plantilla() if args.comparar_plantilla else diagnosticar()
    Path(args.salida_json).write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                                     encoding='utf-8')
