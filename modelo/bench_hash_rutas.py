"""Comparar el segundo hash anticipado/diferido sobre la misma historia oficial.

Solo el proceso de benchmark sustituye temporalmente el método. La partida,
puntos, consultas y secuencia de sondeos son los mismos. Exporta resúmenes.
"""
import json
from pathlib import Path

from adaptadores.bench_adaptadores import ejecutar_bench
from modelo import bench_linea_tiempo as consultas
from modelo.tabla_hash import TablaDistancias


def _anticipado(self, clave):
    """Referencia anterior al cambio; misma mezcla y doble hashing."""
    if type(clave) is not int:
        raise ValueError('El ID de sala debe ser un entero')
    indice, paso = self._inicio(clave), self._paso(clave)
    for _ in range(self.capacidad):
        self.sondeos += 1
        actual = self.casillas[indice]
        if actual is None or actual.sala.sala_id == clave:
            return indice, actual
        indice = (indice + paso) & (self.capacidad - 1)
    raise RuntimeError('No hay casilla libre tras recorrer la tabla')


def medir(cripta='cripta-06', acciones=5000, rondas=3):
    medir_original = consultas._medir
    localizar = TablaDistancias._localizar
    resultados = []

    def comparar(partida, destinos, _, k, referencias):
        referencia = referencias
        try:
            # ABBA reduce el sesgo por orden; GC permanece habilitado.
            for nombre, metodo in (('anticipado', _anticipado), ('diferido', localizar),
                                   ('diferido', localizar), ('anticipado', _anticipado)):
                TablaDistancias._localizar = metodo
                muestras, obtenidos = medir_original(partida, destinos, rondas, k, referencia)
                if referencia is None:
                    referencia = obtenidos
                resumen = consultas.estadisticas([m['tiempo_ms'] for m in muestras])
                resultados.append({'variante': nombre, 'estadisticas': resumen})
                print(nombre, resumen, flush=True)
            return muestras, obtenidos
        finally:
            TablaDistancias._localizar = localizar

    try:
        consultas._medir = comparar
        resultado = ejecutar_bench(solo='consultas', cripta=cripta, acciones=acciones,
                                  rondas=rondas, muestras=12)
    finally:
        consultas._medir = medir_original
    resultado.pop('muestras')
    resultado.pop('estadisticas')
    resultado['comparacion_hash'] = resultados
    resultado['alcance'] += (' Comparacion ABBA sobre la misma partida; cada variante '
                            'incluye copia/replay/resumen/liberacion, sin trazado de memoria.')
    return resultado


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--salida-json', required=True)
    args = p.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir(), ensure_ascii=False, indent=2),
                                     encoding='utf-8')
