"""FR-CI-006/008/009: arnés integral y control negativo del seguimiento."""
import pytest

from adaptadores.captura_incremental import ErrorCobertura
from adaptadores.frontera_incremental import FronteraIncremental
from modelo.bench_historia_incremental import medir


def test_historias_consultas_y_bytes_de_todos_los_puntos():
    resultado = medir(acciones=30, salas=12, cazadores=2, valores_k=(5, 10, 25),
                      rondas=1, muestras=6, verificar_puntos=True)
    escenarios = resultado['escenarios']
    assert len(escenarios) == 6
    assert len({e['sha256_bytes_v6_puntos'] for e in escenarios if e['k'] == 25}) == 1
    assert all(e['http'] == 0 and e['partida_intacta'] for e in escenarios)
    assert all(e['maximo_acciones_reaplicadas'] <= e['k'] for e in escenarios)
    assert all(e['ordenes_incluido_undo']['cantidad'] > e['ciclos']['cantidad'] for e in escenarios)


def test_medicion_detecta_observador_que_omite_marcas(monkeypatch):
    monkeypatch.setattr(FronteraIncremental, 'ejecutar', lambda self, op: op())
    with pytest.raises((ErrorCobertura, AssertionError)):
        medir(acciones=30, salas=12, cazadores=2, valores_k=(5,),
              rondas=1, muestras=6, comparar=False, verificar_puntos=True)


def test_comparacion_abba_restauracion_y_equivalencia_de_puntos(monkeypatch):
    # PR-CI-001/FR-CI-009: probar arnés sin exigir historial Git al ejecutar tests.
    from modelo import bench_historia_incremental as modulo
    monkeypatch.setattr(modulo.subprocess, 'check_output', lambda *a, **k:
                        'from adaptadores.captura_incremental import CapturadorIncremental')
    original = modulo.CapturadorIncremental
    r = modulo.comparar_indice('5ab4c78', acciones=30, salas=12, cazadores=2, rondas=1, muestras=6)
    assert modulo.CapturadorIncremental is original
    assert [e['variante_indice'] for e in r['escenarios']] == ['anterior', 'inverso', 'inverso', 'anterior']
    assert len({e['sha256_bytes_v6_puntos'] for e in r['escenarios']}) == 1


def test_comparacion_restaurada_si_falla_el_experimento(monkeypatch):
    from modelo import bench_historia_incremental as modulo
    original = modulo.CapturadorIncremental
    monkeypatch.setattr(modulo.subprocess, 'check_output', lambda *a, **k:
                        'from adaptadores.captura_incremental import CapturadorIncremental')
    def fallar(**kwargs):
        raise RuntimeError('ensayo interrumpido')
    monkeypatch.setattr(modulo, 'medir', fallar)
    with pytest.raises(RuntimeError, match='interrumpido'):
        modulo.comparar_indice('referencia')
    assert modulo.CapturadorIncremental is original
    assert '_captura_indice_referencia' not in modulo.sys.modules
