"""PR-LT-001/007: medir sin convertir los límites en pruebas dependientes del equipo."""
from modelo.bench_presupuestos import medir_presupuestos


def test_comparador_entrega_el_punto_previo_a_la_referencia(monkeypatch):
    # PR-LT-007: no comparar una versión con reutilización contra otra sin ella.
    from modelo import bench_presupuestos as bench
    from controlador import cargar_partida
    original = cargar_partida.capturar_estado
    monkeypatch.setattr(bench.subprocess, 'check_output', lambda *a, **k:
                        'from adaptadores.instantanea_inmutable import capturar_estado')
    def medir(**opciones):
        capturar = cargar_partida.capturar_estado
        a = capturar([1])
        b = capturar([1], anterior=a)
        assert b.registros[0] is a.registros[0]
        return {'escenarios': [{'sha256_puntos_v6': 'igual'}], 'alcance': ''}
    monkeypatch.setattr(bench, 'medir_presupuestos', medir)
    r = bench.comparar_captura('referencia', k=10)
    assert len(r['escenarios']) == 4
    assert cargar_partida.capturar_estado is original


def test_huellas_de_todos_los_puntos_en_carga_real_pequena():
    # FR-LT-014/015: comparar estado completo, no solamente resúmenes.
    r = medir_presupuestos(acciones=12, salas=4, valores_k=(2, 5), cazadores=3,
                          rondas=1, muestras=6, informar=False, verificar_puntos=True)
    for f in r['escenarios']:
        assert len(f['sha256_puntos_v6']) == 64
        assert f['puntos_verificados'] >= 3


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
