"""PR-LT-001/007: medir sin convertir los límites en pruebas dependientes del equipo."""
from modelo.bench_presupuestos import medir_presupuestos


def test_presupuestos_incluyen_registro_copia_y_estado_intacto():
    d = medir_presupuestos(acciones=12, salas=4, valores_k=(2, 5), cazadores=3,
                           rondas=1, muestras=6, informar=False)
    for f in d['escenarios']:
        assert f['ciclos']['cantidad'] == 13
        assert f['consultas']['cantidad'] == 6
        assert f['copias']['cantidad'] == 13 // f['k']
        assert f['ciclos_con_punto']['cantidad'] == 13 // f['k']
        assert f['partida_intacta'] and f['http'] == 0
        assert f['maximo_acciones_reaplicadas'] <= f['k']
