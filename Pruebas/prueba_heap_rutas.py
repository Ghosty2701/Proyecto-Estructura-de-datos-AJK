"""FR-TC-006/009, PR-TC-002: prioridades e índices de rutas."""
from types import SimpleNamespace

import pytest

from modelo.tabla_hash import RegistroBusqueda, TablaDistancias
from modelo.heap_rutas import HeapRutas


def registro(clave, distancia, primer_id):
    return RegistroBusqueda(SimpleNamespace(sala_id=clave), distancia,
                            SimpleNamespace(sala_id=primer_id))


def comprobar_indices(heap):
    for posicion, actual in enumerate(heap.datos):
        assert actual.posicion_heap == posicion


def test_minimos_lexicograficos_mejoras_e_indices():
    heap = HeapRutas()
    registros = [registro(10, 200, 8), registro(20, 100, 8),
                 registro(30, 100, 3), registro(40, 100, 3)]
    for actual in registros:
        heap.insertar(actual)
        comprobar_indices(heap)
    heap.mejorar(registros[0], 100, SimpleNamespace(sala_id=2))
    comprobar_indices(heap)
    for esperado in (registros[0], registros[2], registros[3], registros[1]):
        assert heap.extraer_minimo() is esperado
        assert esperado.posicion_heap == -1 and esperado.definitivo
        comprobar_indices(heap)
    assert heap.extraer_minimo() is None


def test_no_duplicar_entradas_ni_empeorar_prioridades():
    heap = HeapRutas()
    actual = registro(7, 250, 8)
    heap.insertar(actual)
    with pytest.raises(ValueError):
        heap.insertar(actual)
    with pytest.raises(ValueError):
        heap.mejorar(actual, 300, actual.primer_salto)
    heap.mejorar(actual, 250, SimpleNamespace(sala_id=3))
    assert len(heap.datos) == 1
    assert heap.extraer_minimo().primer_salto.sala_id == 3


def test_crecer_hash_no_rompe_indices_del_heap():
    tabla, heap = TablaDistancias(), HeapRutas()
    for clave in range(100):
        actual = registro(clave, 200 - clave, clave)
        tabla.insertar(actual)
        heap.insertar(actual)
    objetivo = tabla.obtener(3)
    heap.mejorar(objetivo, 1, objetivo.primer_salto)
    assert heap.extraer_minimo() is objetivo
    comprobar_indices(heap)
    anterior = -1
    while heap.datos:
        actual = heap.extraer_minimo()
        assert tabla.obtener(actual.sala.sala_id) is actual
        assert actual.distancia >= anterior
        anterior = actual.distancia
        comprobar_indices(heap)
