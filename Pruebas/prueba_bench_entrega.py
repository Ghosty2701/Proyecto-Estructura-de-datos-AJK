"""P2 §6.3; PR-LT-005/008: el comando de entrega incluye todos sus bloques."""
import json

import pytest


@pytest.mark.parametrize('alias', [[], ['--bench-linea-tiempo']])
def test_bench_estandar_incluye_historia_una_vez_sin_red_ni_vista(tmp_path, monkeypatch, alias):
    import main
    from modelo import bench_modelo, bench_cierre
    decisiones = {'equivalentes': True}
    llamadas = []
    monkeypatch.setattr(bench_modelo, 'ejecutar_bench_completo', lambda *a:
                        {'decisiones_linea_tiempo': decisiones})
    monkeypatch.setattr(bench_cierre, 'ejecutar_cierre', lambda *a, **k: llamadas.append((a, k)))
    def prohibido(*a, **k):
        pytest.fail('bench sintético no debe crear HTTP ni vista')
    monkeypatch.setattr(main, 'ClienteHTTP', prohibido)
    monkeypatch.setattr(main, 'VistaConsola', prohibido)
    carpeta = tmp_path / 'salida'
    assert main.main(['--bench', '--repeticiones', '1', '--salida-bench', str(carpeta), *alias]) == 0
    assert len(llamadas) == 1
    assert llamadas[0][0] == (1, 2026)
    assert llamadas[0][1]['carpeta'] == str(carpeta)
    assert llamadas[0][1]['decisiones'] is decisiones


def test_bench_predeterminado_no_escribe_en_evidencia_versionada(monkeypatch):
    import main
    from modelo import bench_modelo, bench_cierre
    llamadas = []
    monkeypatch.setattr(bench_modelo, 'ejecutar_bench_completo', lambda *a: {})
    monkeypatch.setattr(bench_cierre, 'ejecutar_cierre', lambda *a, **k: llamadas.append(k))
    assert main.main(['--bench', '--repeticiones', '1']) == 0
    assert llamadas[0]['carpeta'] == 'resultados/bench'


@pytest.mark.parametrize('fase', ['subsistemas', 'historia'])
def test_bench_fallido_devuelve_error_sin_traceback(monkeypatch, capsys, fase):
    import main
    from modelo import bench_modelo, bench_cierre
    monkeypatch.setattr(bench_modelo, 'ejecutar_bench_completo', lambda *a: {})
    def fallar(*a, **k):
        raise OSError('no se puede escribir')
    monkeypatch.setattr(bench_modelo if fase == 'subsistemas' else bench_cierre,
                        'ejecutar_bench_completo' if fase == 'subsistemas' else 'ejecutar_cierre', fallar)
    assert main.main(['--bench', '--repeticiones', '1']) == 1
    error = capsys.readouterr().err
    assert 'no se puede escribir' in error and 'Traceback' not in error


def test_salida_bench_requiere_bench():
    import main
    with pytest.raises(SystemExit) as e:
        main.main(['--listar', '--salida-bench', 'salida'])
    assert e.value.code == 2


def test_comando_estandar_ejecuta_bloques_reales_y_exporta_k_y_sin_puntos(tmp_path, monkeypatch):
    # Mismas implementaciones del comando completo, escala pequeña para la suite.
    import main
    from modelo import bench_cierre, bench_modelo
    originales = (bench_cierre.medir_consultas, bench_cierre.medir_memoria,
                  bench_cierre.medir_persistencia)
    comunes = {'acciones': 30, 'cantidad_salas': 6, 'valores_k': (3, 5, 10)}
    monkeypatch.setattr(bench_cierre, 'medir_consultas', lambda **k:
                        originales[0](**comunes, **k, cazadores=(0,), muestras=6, informar=False))
    monkeypatch.setattr(bench_cierre, 'medir_memoria', lambda **k:
                        originales[1](**comunes, **k, cazadores=(0,), informar=False))
    monkeypatch.setattr(bench_cierre, 'medir_persistencia', lambda **k:
                        originales[2](**comunes, **k, informar=False))
    from modelo.bench_decisiones import medir_decisiones
    decisiones = medir_decisiones(salas=(6,), cazadores=(0,), acciones=12, rondas=1)
    monkeypatch.setattr(bench_modelo, 'ejecutar_bench_completo', lambda *a:
                        {'decisiones_linea_tiempo': decisiones})
    carpeta = tmp_path / 'real'
    assert main.main(['--bench', '--repeticiones', '1', '--salida-bench', str(carpeta)]) == 0
    datos = json.loads((carpeta / 'mediciones_linea_tiempo.json').read_text(encoding='utf-8'))
    for bloque in ('consultas', 'memoria'):
        assert {e['k'] for e in datos[bloque]['escenarios']} == {3, 5, 10, None}
    assert datos['entorno']['python']
    assert datos['entorno']['k_por_defecto'] == 10
    assert datos['decisiones']
    assert datos['persistencia']
