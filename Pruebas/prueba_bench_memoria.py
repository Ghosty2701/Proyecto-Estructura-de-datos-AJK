"""T029, PR-LT-003/005/007: memoria y puntos sin umbrales dependientes del equipo."""
import tracemalloc
from modelo.bench_memoria import medir_memoria


def test_memoria_y_tiempos_se_miden_separados_y_conservan_la_partida():
    datos = medir_memoria(acciones=12, cantidad_salas=4, valores_k=(2, 4, 8),
                         cazadores=(0, 2), rondas=1, informar=False)
    assert not tracemalloc.is_tracing()
    assert len(datos['escenarios']) == 8
    for f in datos['escenarios']:
        assert f['equivalentes'] and f['http'] == 0
        assert f['memoria_final_bytes'] > 0
        assert f['pico_bytes'] >= f['memoria_final_bytes']
        assert f['memoria_mitad_bytes'] > 0
        assert f['tracemalloc_en_tiempos'] is False
        assert f['ciclos']['cantidad'] == 13  # Solo acciones, incluida la revertida.
        assert f['creacion_puntos']['cantidad'] == (0 if f['k'] is None else 13 // f['k'])
        assert f['puntos'] == 1 + f['creacion_puntos']['cantidad']
