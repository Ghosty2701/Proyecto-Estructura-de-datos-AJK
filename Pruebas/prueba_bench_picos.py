"""El diagnóstico conserva el recolector y acota su evidencia detallada."""
import gc
import pytest
from modelo import bench_picos


def test_diagnostico_cuenta_acciones_y_restaura_observadores():
    callbacks = gc.callbacks[:]
    umbrales = gc.get_threshold()
    d = bench_picos.diagnosticar(acciones=12, valores_k=(2,), salas=4, cazadores=3)
    f = d['escenarios'][0]
    assert f['ciclos'] == 13 and f['con_punto'] == 6 and f['sin_punto'] == 7
    assert len(f['peores_diez']) <= 10
    assert gc.callbacks == callbacks and gc.get_threshold() == umbrales and gc.isenabled()


def test_diagnostico_restaura_callback_si_falla_preparacion(monkeypatch):
    callbacks = gc.callbacks[:]

    def fallar(*args, **kwargs):
        raise RuntimeError('fallo controlado')

    monkeypatch.setattr(bench_picos, '_preparar', fallar)
    with pytest.raises(RuntimeError, match='fallo controlado'):
        bench_picos.diagnosticar(acciones=12, valores_k=(2,), salas=4, cazadores=3)
    assert gc.callbacks == callbacks and gc.isenabled()
