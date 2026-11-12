"""ABBA de consultas completas: caché individual frente a compartida acotada."""
import json
from pathlib import Path

from adaptadores.bench_adaptadores import ejecutar_bench
from modelo import bench_linea_tiempo as consultas
from modelo import motor_eventos as motor
from modelo.cache_rutas import CacheRutas


def _individual(self, cazador, jugador):
    previa = cazador.ultima_ruta
    if (previa is not None and previa.origen is cazador.sala_actual
            and previa.objetivo is jugador.sala_actual and previa.rango == cazador.rango
            and previa.revision_conexiones == self.revision_conexiones):
        return previa
    nueva = motor.buscar_ruta(cazador.sala_actual, jugador.sala_actual, cazador.rango)
    nueva.revision_conexiones = self.revision_conexiones
    cazador.ultima_ruta = nueva
    return nueva


def medir(capacidades=None):
    if capacidades is not None:
        if len(capacidades) != 2:
            raise ValueError('comparar exactamente dos capacidades')
        for capacidad in capacidades:
            CacheRutas(capacidad)
    original = consultas._medir
    compartida = motor.MotorEventos.ruta_cazador
    buscar = motor.buscar_ruta
    obtener = CacheRutas.obtener
    inicializar = CacheRutas.__init__
    filas = []

    def comparar(partida, destinos, rondas, k, referencias):
        referencia = referencias
        try:
            variantes = [('individual', _individual, 256), ('compartida', compartida, 256),
                         ('compartida', compartida, 256), ('individual', _individual, 256)]
            if capacidades is not None:
                a, b = capacidades
                variantes = [('compartida', compartida, c) for c in (a, b, b, a)]
            for nombre, metodo, capacidad in variantes:
                contadores = [0, 0, 0]

                def configurar(self, _capacidad=256):
                    inicializar(self, capacidad)

                def contar_busqueda(*args):
                    contadores[0] += 1
                    return buscar(*args)

                def contar_cache(self, *args):
                    resultado = obtener(self, *args)
                    contadores[1 if resultado is not None else 2] += 1
                    return resultado

                motor.MotorEventos.ruta_cazador = metodo
                motor.buscar_ruta = contar_busqueda
                CacheRutas.obtener = contar_cache
                CacheRutas.__init__ = configurar
                muestras, obtenidos = original(partida, destinos, rondas, k, referencia)
                if referencia is None:
                    referencia = obtenidos
                fila = {'variante': nombre, 'capacidad': capacidad,
                        'estadisticas': consultas.estadisticas([m['tiempo_ms'] for m in muestras]),
                        'busquedas_dijkstra': contadores[0], 'aciertos_compartidos': contadores[1],
                        'fallos_compartidos': contadores[2]}
                filas.append(fila)
                print(fila, flush=True)
            return muestras, obtenidos
        finally:
            motor.MotorEventos.ruta_cazador = compartida
            motor.buscar_ruta = buscar
            CacheRutas.obtener = obtener
            CacheRutas.__init__ = inicializar

    try:
        consultas._medir = comparar
        resultado = ejecutar_bench(solo='consultas', cripta='cripta-06', acciones=5000,
                                  rondas=3, muestras=12)
    finally:
        consultas._medir = original
    resultado.pop('muestras')
    resultado.pop('estadisticas')
    resultado['comparacion_cache'] = filas
    resultado['capacidades_comparadas'] = list(capacidades) if capacidades is not None else [256]
    resultado['alcance'] += (' ABBA sobre los mismos puntos compactos y consultas. '
                            'Incluye contadores de Dijkstra y de cache; resúmenes equivalentes.')
    return resultado


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salida-json', required=True)
    p.add_argument('--capacidades', type=int, nargs=2)
    args = p.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir(args.capacidades), ensure_ascii=False, indent=2),
                                     encoding='utf-8')
