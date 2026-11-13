"""FR-CI-002/003/006: versiones independientes, bajas y publicación atómica."""
import struct
import random
import pytest
from dataclasses import FrozenInstanceError
from modelo.indice_versionado import VersionRegistros, ELIMINAR


def r(valor):
    return (18, (valor,))


def test_versiones_comparten_registros_sin_mutar_antecesor():
    a = VersionRegistros.vacia().con_cambios([(1, r(10)), (2, r(20))])
    b = a.con_cambios([(1, r(11)), (3, r(30))])
    assert a.obtener(1) == r(10) and a.obtener(3) is None
    assert b.obtener(1) == r(11) and b.obtener(3) == r(30)
    assert a.obtener(2) is b.obtener(2)
    assert a.casillas is not b.casillas
    with pytest.raises(FrozenInstanceError):
        b.cantidad = 0


def test_colisiones_borrado_y_actualizacion_no_duplican(monkeypatch):
    monkeypatch.setattr('modelo.indice_versionado._mezclar', lambda n: 0)
    a = VersionRegistros.vacia(8).con_cambios((i, r(i)) for i in range(5))
    b = a.con_cambios([(1, ELIMINAR), (4, r(40)), (8, r(8))])
    assert b.cantidad == 5 and len(b.casillas) == 8
    assert b.obtener(1) is None and b.obtener(4) == r(40)
    assert all(b.obtener(i) == r(i) for i in (0, 2, 3, 8))
    assert a.obtener(1) == r(1) and a.obtener(4) == r(4)


def test_limpia_tumbas_sin_crecer_y_admite_id_grande():
    a = VersionRegistros.vacia(8).con_cambios((i, r(i)) for i in range(5))
    b = a.con_cambios((i, ELIMINAR) for i in range(4))
    c = b.con_cambios([(2**80, r(99))])
    assert len(c.casillas) == 8 and c.tumbas == 0 and c.cantidad == 2
    assert c.obtener(2**80) == r(99) and a.obtener(2**80) is None


def test_fallo_de_lote_no_publica_cambios_parciales():
    a = VersionRegistros.vacia().con_cambios([(1, r(1))])
    with pytest.raises(TypeError):
        a.con_cambios([(1, r(2)), (2, (18, ([3],)))])
    assert a.obtener(1) == r(1) and a.cantidad == 1
    def fallar():
        yield 1, r(9)
        raise RuntimeError('fallo')
    with pytest.raises(RuntimeError):
        a.con_cambios(fallar())
    assert a.obtener(1) == r(1)


@pytest.mark.parametrize('clave', [-1, True, 1.0, '1'])
def test_ids_invalidos(clave):
    a = VersionRegistros.vacia()
    with pytest.raises(ValueError):
        a.con_cambios([(clave, r(0))])
    with pytest.raises(ValueError):
        a.obtener(clave)


def test_actualizaciones_preservan_tipos_y_bits():
    a = VersionRegistros.vacia().con_cambios([(1, r(True)), (2, r(0.0))])
    b = a.con_cambios([(1, r(1)), (2, r(-0.0))])
    assert type(a.obtener(1)[1][0]) is bool and type(b.obtener(1)[1][0]) is int
    assert struct.pack('!d', b.obtener(2)[1][0]) == struct.pack('!d', -0.0)
    assert struct.pack('!d', a.obtener(2)[1][0]) == struct.pack('!d', 0.0)


def test_secuencia_aleatoria_conserva_todas_las_versiones():
    azar = random.Random(2026)
    version = VersionRegistros.vacia(8)
    esperado = [None] * 80
    anteriores = []
    for paso in range(300):
        clave = azar.randrange(80)
        valor = None if azar.randrange(4) == 0 else r(paso)
        anteriores.append((version, esperado[:]))
        version = version.con_cambios([(clave, ELIMINAR if valor is None else valor)])
        esperado[clave] = valor
        assert version.cantidad == sum(v is not None for v in esperado)
        assert version.cantidad * 10 <= len(version.casillas) * 7
    for previa, referencia in anteriores + [(version, esperado)]:
        assert [previa.obtener(i) for i in range(80)] == referencia
        assert len(list(previa.registros())) == previa.cantidad
