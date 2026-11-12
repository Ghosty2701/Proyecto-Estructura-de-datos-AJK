"""Exportar evidencia suficiente sin almacenar cada muestra del benchmark."""
from comun.ordenamiento import ordenar


def _estadisticas(valores):
    if not valores:
        return {'cantidad': 0}
    ordenados, _ = ordenar(valores)
    n = len(ordenados)
    return {'cantidad': n, 'minimo_ms': ordenados[0],
            'promedio_ms': sum(ordenados) / n,
            'mediana_ms': ordenados[n // 2] if n % 2 else
                          (ordenados[n // 2 - 1] + ordenados[n // 2]) / 2,
            'p95_ms': ordenados[(95 * n + 99) // 100 - 1],
            'maximo_ms': ordenados[-1],
            'muestras_ge20ms': sum(v >= 20 for v in valores),
            'muestras_ge50ms': sum(v >= 50 for v in valores)}


def resumir_mediciones(datos, clave='', padre=''):
    """Copia registros JSON, conservando configuraciones y fallos observados.

    Solo compacta listas de tiempos y muestras identificadas; no modifica los
    resultados en memoria usados por las comprobaciones de los benchmarks.
    """
    if isinstance(datos, dict):
        return {k: resumir_mediciones(v, k, clave) for k, v in datos.items()}
    if isinstance(datos, list):
        if (clave.endswith('_ms') or padre == 'muestras_ms') and all(
                type(v) in (int, float) for v in datos):
            return _estadisticas(datos)
        if clave == 'muestras' and all(isinstance(v, dict) for v in datos):
            resumen = {'cantidad': len(datos)}
            for campo in ('acciones_reaplicadas', 'comparaciones_puntos'):
                valores = [v[campo] for v in datos if campo in v]
                if valores:
                    resumen['maximo_' + campo] = max(valores)
            return resumen
        return [resumir_mediciones(v) for v in datos]
    return datos
