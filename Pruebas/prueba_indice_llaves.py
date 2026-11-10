"""FR-RS-005/009/015, PR-RS-002: índices propios con colisiones."""
import pytest
from modelo.indice_llaves import IndiceLlaves
from modelo.conocimiento import IndiceSalas


def test_texto_reserva_colisiones_y_unicode(monkeypatch):
    monkeypatch.setattr(IndiceLlaves, '_hash', staticmethod(lambda clave: 5))
    indice = IndiceLlaves(80)
    for i in range(80):
        assert indice.insertar('llave_ñ_' + str(i), i) == i
    assert indice.capacidad & (indice.capacidad - 1) == 0
    assert 800 <= indice.capacidad * 7
    for i in range(80):
        assert indice.obtener('llave_ñ_' + str(i)) == i
    assert indice.obtener('ausente') is None
    assert indice.insertar('llave_ñ_3', 999) == 3
    with pytest.raises(ValueError):
        indice.obtener(3)


def test_enteros_dispersos_y_duplicados():
    indice = IndiceSalas([10, 10**15, -9])
    assert indice.obtener(10**15) == 1
    assert indice.obtener(8) is None
    with pytest.raises(ValueError):
        IndiceSalas([2, 2])
