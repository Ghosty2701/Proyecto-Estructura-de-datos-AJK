"""FR-RS-009; PR-RS-001/002/003; SC-RS-005, sin aserciones de tiempo frágiles."""
from modelo.bench_resolubilidad import generar_cadena, generar_grupos, medir_entrada, referencia
from modelo.verificacion import normalizar, verificar


def test_cadena_semilla_y_trabajo_incremental():
    entrada = generar_cadena(20, 2026)
    assert entrada == generar_cadena(20, 2026)
    mapa = normalizar(*entrada)
    real = verificar(mapa)
    esperado, visitas = referencia(mapa)
    assert real.resoluble == esperado and real.resoluble
    assert visitas > real.cierre.operaciones * 3
    medicion = medir_entrada(*entrada, repeticiones=2)
    assert medicion['maximo_ms'] >= medicion['minimo_ms'] >= 0
    assert len(medicion['muestras']) == 2 and medicion['coinciden']


def test_muchas_componentes_y_ubicaciones():
    entrada = generar_grupos(12, 2026)
    mapa = normalizar(*entrada)
    resultado = verificar(mapa)
    assert not resultado.resoluble and len(resultado.certificados) == 12
    assert referencia(mapa)[0] is False
    assert medir_entrada(*entrada, repeticiones=1)['coinciden']
