import pytest

from modelo.inventario import ErrorInventario, Inventario


class Objeto:
    # Objeto minimo para las pruebas: solo lo que el inventario podria necesitar
    # a traves de una clave, nunca por su cuenta.
    def __init__(self, nombre, peso=0, valor=0):
        self.nombre = nombre
        self.peso = peso
        self.valor = valor

    def __repr__(self):
        return f"Objeto({self.nombre!r})"


# --- Estado inicial y capacidad ---

def test_inventario_vacio_al_crearse():
    inv = Inventario(capacidad=5)
    assert inv.esta_vacio()
    assert not inv.esta_lleno()
    assert inv.cantidad == 0
    assert inv.actual() is None
    assert inv.listar() == []


def test_capacidad_invalida_lanza_error():
    with pytest.raises(ValueError):
        Inventario(capacidad=0)
    with pytest.raises(ValueError):
        Inventario(capacidad=-3)


def test_recoger_hasta_llenar_y_luego_rechaza():
    inv = Inventario(capacidad=2)
    assert inv.recoger(Objeto("a")) is True
    assert inv.recoger(Objeto("b")) is True
    assert inv.esta_lleno()
    assert inv.recoger(Objeto("c")) is False  # no cabe: no cambia nada
    assert inv.cantidad == 2
    assert [o.nombre for o in inv.listar()] == ["a", "b"]


def test_recoger_no_depende_del_peso():
    # "Cada objeto ocupa una posicion, sin importar su peso" (§2.7).
    inv = Inventario(capacidad=2)
    inv.recoger(Objeto("pluma", peso=0))
    inv.recoger(Objeto("yunque", peso=500))
    assert inv.esta_lleno()


# --- Recorrido bidireccional ---

def test_recorrido_hacia_adelante_y_hacia_atras():
    inv = Inventario(capacidad=5)
    for nombre in ["a", "b", "c"]:
        inv.recoger(Objeto(nombre))

    assert inv.actual().nombre == "a"  # el cursor arranca en el primero recogido
    assert inv.avanzar() is True
    assert inv.actual().nombre == "b"
    assert inv.avanzar() is True
    assert inv.actual().nombre == "c"
    assert inv.avanzar() is False  # ya esta en el ultimo
    assert inv.actual().nombre == "c"

    assert inv.retroceder() is True
    assert inv.actual().nombre == "b"
    assert inv.retroceder() is True
    assert inv.actual().nombre == "a"
    assert inv.retroceder() is False  # ya esta en el primero


def test_avanzar_y_retroceder_en_inventario_vacio():
    inv = Inventario(capacidad=3)
    assert inv.avanzar() is False
    assert inv.retroceder() is False


# --- Soltar el objeto actual, en cualquier posicion ---

def test_soltar_actual_en_medio_no_rompe_el_recorrido():
    inv = Inventario(capacidad=5)
    for nombre in ["a", "b", "c", "d"]:
        inv.recoger(Objeto(nombre))

    inv.avanzar()
    inv.avanzar()
    assert inv.actual().nombre == "c"

    soltado = inv.soltar_actual()
    assert soltado.nombre == "c"
    assert [o.nombre for o in inv.listar()] == ["a", "b", "d"]
    # El cursor pasa al vecino siguiente ("d"); si no hay, iria al anterior.
    assert inv.actual().nombre == "d"
    assert inv.cantidad == 3


def test_soltar_actual_cuando_es_el_ultimo_mueve_cursor_al_anterior():
    inv = Inventario(capacidad=5)
    for nombre in ["a", "b", "c"]:
        inv.recoger(Objeto(nombre))
    inv.avanzar()
    inv.avanzar()
    assert inv.actual().nombre == "c"

    inv.soltar_actual()
    assert inv.actual().nombre == "b"


def test_soltar_el_unico_objeto_deja_el_inventario_vacio():
    inv = Inventario(capacidad=3)
    inv.recoger(Objeto("a"))
    soltado = inv.soltar_actual()
    assert soltado.nombre == "a"
    assert inv.esta_vacio()
    assert inv.actual() is None


def test_soltar_actual_en_inventario_vacio_devuelve_none():
    inv = Inventario(capacidad=3)
    assert inv.soltar_actual() is None


def test_soltar_libera_espacio_para_recoger_de_nuevo():
    inv = Inventario(capacidad=1)
    inv.recoger(Objeto("a"))
    assert inv.recoger(Objeto("b")) is False
    inv.soltar_actual()
    assert inv.recoger(Objeto("b")) is True
    assert inv.actual().nombre == "b"


# --- Equipar ---

def test_equipar_mueve_al_frente_del_orden_real():
    inv = Inventario(capacidad=5)
    for nombre in ["a", "b", "c"]:
        inv.recoger(Objeto(nombre))

    inv.avanzar()
    inv.avanzar()
    assert inv.actual().nombre == "c"

    desplazado = inv.equipar_actual("arma")
    assert desplazado is None  # no habia nada equipado antes
    assert [o.nombre for o in inv.listar()] == ["c", "a", "b"]
    assert inv.arma_equipada.nombre == "c"


def test_equipar_otro_del_mismo_tipo_sustituye_pero_no_suelta_el_anterior():
    inv = Inventario(capacidad=5)
    espada = Objeto("espada")
    daga = Objeto("daga")
    inv.recoger(espada)
    inv.recoger(daga)

    inv.equipar_actual("arma")  # cursor esta en "espada"
    assert inv.arma_equipada is espada

    inv.avanzar()
    assert inv.actual() is daga
    desplazada = inv.equipar_actual("arma")

    assert desplazada is espada
    assert inv.arma_equipada is daga
    # La espada sigue en el inventario, solo que ya no equipada.
    assert espada in inv.listar()


def test_arma_y_armadura_son_ranuras_independientes():
    inv = Inventario(capacidad=5)
    espada = Objeto("espada")
    escudo = Objeto("escudo")
    inv.recoger(espada)
    inv.recoger(escudo)

    inv.equipar_actual("arma")  # cursor en "espada"
    inv.avanzar()
    inv.equipar_actual("armadura")  # cursor en "escudo"

    assert inv.arma_equipada is espada
    assert inv.armadura_equipada is escudo


def test_reequipar_el_mismo_objeto_no_hace_nada():
    inv = Inventario(capacidad=5)
    inv.recoger(Objeto("espada"))
    inv.equipar_actual("arma")
    orden_antes = inv.listar()

    resultado = inv.equipar_actual("arma")
    assert resultado is None
    assert inv.listar() == orden_antes


def test_soltar_el_objeto_equipado_lo_desequipa():
    inv = Inventario(capacidad=5)
    inv.recoger(Objeto("espada"))
    inv.equipar_actual("arma")
    assert inv.arma_equipada is not None

    inv.soltar_actual()
    assert inv.arma_equipada is None


def test_equipar_con_tipo_invalido_lanza_error():
    inv = Inventario(capacidad=3)
    inv.recoger(Objeto("espada"))
    with pytest.raises(ErrorInventario):
        inv.equipar_actual("pocion")


def test_equipar_en_inventario_vacio_no_hace_nada():
    inv = Inventario(capacidad=3)
    assert inv.equipar_actual("arma") is None
    assert inv.arma_equipada is None


# --- Vistas ordenadas, sin alterar el orden real ---

def test_vista_ordenada_por_peso_no_altera_el_orden_real():
    inv = Inventario(capacidad=5)
    inv.recoger(Objeto("escudo", peso=8))
    inv.recoger(Objeto("daga", peso=2))
    inv.recoger(Objeto("pocion", peso=1))

    orden_real_antes = [o.nombre for o in inv.listar()]
    vista = inv.vista_ordenada(clave=lambda o: o.peso)

    assert [o.nombre for o in vista] == ["pocion", "daga", "escudo"]
    assert [o.nombre for o in inv.listar()] == orden_real_antes  # sin cambios


def test_vista_ordenada_por_nombre():
    inv = Inventario(capacidad=5)
    inv.recoger(Objeto("zeta"))
    inv.recoger(Objeto("alfa"))
    inv.recoger(Objeto("beta"))

    vista = inv.vista_ordenada(clave=lambda o: o.nombre)
    assert [o.nombre for o in vista] == ["alfa", "beta", "zeta"]


# --- consumir_primero (contrato que usa MotorEventos.usar_pergamino) ---

def test_consumir_primero_quita_el_primer_objeto_que_cumple():
    inv = Inventario(capacidad=5)
    inv.recoger(Objeto("daga"))
    inv.recoger(Objeto("pergamino"))
    inv.recoger(Objeto("pergamino"))

    assert inv.consumir_primero(lambda o: o.nombre == "pergamino") is True
    assert [o.nombre for o in inv.listar()] == ["daga", "pergamino"]
    assert inv.cantidad == 2


def test_consumir_primero_sin_coincidencias_devuelve_false_y_no_cambia_nada():
    inv = Inventario(capacidad=3)
    inv.recoger(Objeto("daga"))
    assert inv.consumir_primero(lambda o: o.nombre == "pergamino") is False
    assert inv.cantidad == 1


def test_consumir_primero_en_inventario_vacio():
    assert Inventario(capacidad=3).consumir_primero(lambda o: True) is False


def test_consumir_primero_mueve_el_cursor_si_estaba_en_ese_objeto():
    inv = Inventario(capacidad=3)
    inv.recoger(Objeto("pergamino"))
    inv.recoger(Objeto("daga"))
    assert inv.actual().nombre == "pergamino"
    inv.consumir_primero(lambda o: o.nombre == "pergamino")
    assert inv.actual().nombre == "daga"


def test_consumir_primero_desequipa_si_era_el_equipado():
    inv = Inventario(capacidad=3)
    inv.recoger(Objeto("espada"))
    inv.equipar_actual("arma")
    inv.consumir_primero(lambda o: o.nombre == "espada")
    assert inv.arma_equipada is None
