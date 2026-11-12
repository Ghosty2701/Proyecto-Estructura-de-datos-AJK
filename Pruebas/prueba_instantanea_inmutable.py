"""D-LT-08: FR-LT-013/014, independencia, identidad y ciclos sin grafo retenido."""
import gc
import weakref
import random

import pytest

from adaptadores.instantanea_inmutable import capturar_estado, InstantaneaInmutable
from modelo.rastro import SalaRastro
from datos_linea_tiempo import escribir_paquete, crear_partida, jugar, instantanea


def test_registros_no_retienen_modelos_y_preservan_ciclos():
    habilitado = gc.isenabled()
    gc.disable()
    try:
        sala = SalaRastro(1)
        ref = weakref.ref(sala)
        lista = [sala]
        lista.append(lista)
        punto = capturar_estado(lista)
        del sala
        lista.clear()
        del lista
        assert ref() is None
        copia = punto.reconstruir()
        assert copia[1] is copia and copia[0].sala_id == 1
    finally:
        if habilitado:
            gc.enable()
        gc.collect()


def test_tuplas_diccionarios_y_alias():
    lista = []
    tupla = (lista,)
    lista.append(tupla)
    p = capturar_estado([lista, lista, {'dato': tupla}])
    copia = p.reconstruir()
    assert copia[0] is copia[1]
    assert copia[0][0][0] is copia[0]
    assert copia[2]['dato'] is copia[0][0]


def test_partida_reconstruida_igual_e_independiente(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    jugar(p)
    punto = capturar_estado((p, c.salas_ordenadas()))
    copia, salas = punto.reconstruir()
    assert instantanea(copia) == instantanea(p)
    assert copia.motor.azar.getstate() == p.motor.azar.getstate()
    copia.jugador.vida = 0
    salas[0].salidas.clear()
    otra, _ = punto.reconstruir()
    assert instantanea(otra) == instantanea(p)


def test_registros_solo_contienen_valores_inmutables_y_azar_independiente():
    azar = random.Random(2026)
    punto = capturar_estado([azar, azar, (1, True, b'dato', None)])
    pendientes = [punto.raiz, punto.registros]
    while pendientes:
        valor = pendientes.pop()
        assert type(valor) in (tuple, type(None), bool, int, float, str, bytes)
        if type(valor) is tuple:
            pendientes.extend(valor)
    copia = punto.reconstruir()
    assert copia[0] is copia[1]
    assert copia[0].random() == azar.random()
    copia[0].random()
    assert punto.reconstruir()[0].getstate() == random.Random(2026).getstate()


def test_rechaza_tipos_fuera_del_esquema():
    with pytest.raises(TypeError, match='tipo sin esquema'):
        capturar_estado([object()])


def test_guardado_v6_identico_al_de_puntos_con_grafo_y_recarga_por_id(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache', checkpoint_cada=3)
    jugar(p)
    datos = c._linea_a_datos(p)
    assert len(p.linea_tiempo.puntos) > 1
    for punto in p.linea_tiempo.puntos:
        assert isinstance(punto.estado, InstantaneaInmutable)
        punto.estado = punto.estado.reconstruir()
    # Mismos bytes por punto que el formato anterior: no solo misma salida visible.
    assert c._linea_a_datos(p) == datos
    linea, _, _ = c._datos_a_linea(datos, c._identidad(p))
    for original, recargado in zip(p.linea_tiempo.puntos, linea.puntos):
        assert isinstance(recargado.estado, InstantaneaInmutable)
        restaurado, _ = recargado.estado.reconstruir()
        assert instantanea(restaurado) == instantanea(original.estado[0])
