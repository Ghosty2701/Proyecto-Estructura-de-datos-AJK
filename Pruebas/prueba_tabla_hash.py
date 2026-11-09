"""FR-TC-006/009, PR-TC-002: colisiones y referencias de la búsqueda."""
from types import SimpleNamespace

from modelo.tabla_hash import RegistroBusqueda, TablaDistancias


def registro(clave, distancia=100):
    return RegistroBusqueda(SimpleNamespace(sala_id=clave), distancia)


def test_colisiones_con_doble_hash_recuperan_la_clave_exacta():
    tabla = TablaDistancias()
    tabla._inicio = lambda clave: 0
    tabla._paso = lambda clave: 3
    registros = [registro(i) for i in range(20)]
    for actual in registros:
        tabla.insertar(actual)
    assert tabla.cantidad == 20
    for actual in registros:
        assert tabla.obtener(actual.sala.sala_id) is actual
    assert tabla.obtener(200) is None


def test_actualizar_no_duplica_ni_crece_y_conserva_la_referencia():
    tabla = TablaDistancias()
    for clave in range(22):
        tabla.insertar(registro(clave, 250))
    anterior = tabla.obtener(7)
    anterior.posicion_heap = 4
    assert tabla.insertar(registro(7, 180)) is anterior
    assert (anterior.distancia, anterior.posicion_heap) == (180, 4)
    assert (tabla.cantidad, tabla.capacidad) == (22, 32)
    tabla.insertar(registro(22))
    assert (tabla.cantidad, tabla.capacidad) == (23, 64)
    assert tabla.obtener(7) is anterior


def test_varios_crecimientos_con_ids_ordenados_y_negativos():
    tabla = TablaDistancias()
    registros = [registro(i * 64) for i in range(-100, 100)]
    for actual in registros:
        tabla.insertar(actual)
        assert tabla.cantidad * 10 <= tabla.capacidad * 7
    for actual in registros:
        assert tabla.obtener(actual.sala.sala_id) is actual
    for clave in range(200):
        paso = tabla._paso(clave)
        assert 0 < paso < tabla.capacidad and paso % 2 == 1

