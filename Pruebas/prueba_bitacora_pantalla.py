import pytest

from vista.bitacora_pantalla import BitacoraPantalla


def test_bitacora_vacia_al_crearse():
    bitacora = BitacoraPantalla(capacidad=3)
    assert bitacora.esta_vacia()
    assert len(bitacora) == 0
    assert bitacora.mensajes() == []
    assert bitacora.mas_reciente() is None


def test_agregar_menos_mensajes_que_la_capacidad():
    bitacora = BitacoraPantalla(capacidad=5)
    bitacora.agregar("a")
    bitacora.agregar("b")
    assert bitacora.mensajes() == ["a", "b"]
    assert bitacora.mas_reciente() == "b"
    assert len(bitacora) == 2


def test_agregar_exactamente_la_capacidad():
    bitacora = BitacoraPantalla(capacidad=3)
    bitacora.agregar("a")
    bitacora.agregar("b")
    bitacora.agregar("c")
    assert bitacora.mensajes() == ["a", "b", "c"]
    assert len(bitacora) == 3


def test_superar_la_capacidad_descarta_el_mas_antiguo():
    bitacora = BitacoraPantalla(capacidad=3)
    for mensaje in ["a", "b", "c", "d"]:
        bitacora.agregar(mensaje)
    # "a" ya no cabe: solo quedan los 3 ultimos, en orden.
    assert bitacora.mensajes() == ["b", "c", "d"]
    assert bitacora.mas_reciente() == "d"
    assert len(bitacora) == 3


def test_varias_vueltas_completas_mantienen_el_orden():
    bitacora = BitacoraPantalla(capacidad=3)
    for i in range(1, 11):  # 10 mensajes sobre una capacidad de 3: varias vueltas
        bitacora.agregar(f"m{i}")
    assert bitacora.mensajes() == ["m8", "m9", "m10"]
    assert bitacora.total_generados == 10


def test_memoria_interna_es_constante_sin_importar_cuantos_mensajes_entraron():
    bitacora = BitacoraPantalla(capacidad=20)
    for i in range(5000):
        bitacora.agregar(f"evento {i}")
    # El arreglo interno nunca crece mas alla de la capacidad declarada.
    assert len(bitacora._mensajes) == 20
    assert len(bitacora) == 20
    assert bitacora.total_generados == 5000
    assert bitacora.mensajes()[0] == "evento 4980"
    assert bitacora.mensajes()[-1] == "evento 4999"


def test_agregar_no_desplaza_los_mensajes_existentes_en_el_arreglo():
    # "Agregar no debe implicar desplazar fisicamente los anteriores" (§4.8):
    # se verifica que las posiciones internas de los mensajes viejos no se muevan,
    # solo se sobrescribe la posicion mas antigua y avanzan los indices.
    bitacora = BitacoraPantalla(capacidad=3)
    bitacora.agregar("a")  # posicion 0
    bitacora.agregar("b")  # posicion 1
    bitacora.agregar("c")  # posicion 2
    assert bitacora._mensajes == ["a", "b", "c"]

    bitacora.agregar("d")  # deberia sobrescribir "a" en la posicion 0, sin mover "b" ni "c"
    assert bitacora._mensajes == ["d", "b", "c"]
    assert bitacora.mensajes() == ["b", "c", "d"]


def test_capacidad_invalida_lanza_error():
    with pytest.raises(ValueError):
        BitacoraPantalla(capacidad=0)
    with pytest.raises(ValueError):
        BitacoraPantalla(capacidad=-1)


def test_capacidad_por_defecto_es_20():
    bitacora = BitacoraPantalla()
    assert bitacora.capacidad == 20
