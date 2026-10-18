import pytest

from modelo.inventario import ErrorInventario, Inventario
from modelo.inventario_reversible import InventarioReversible


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


# --- Extension reversible: el consumidor externo conserva los registros ---

def objeto_reversible(nombre, pergamino=False):
    from types import SimpleNamespace

    return SimpleNamespace(nombre=nombre, clase="pergamino_retroceso" if pergamino else "objeto")


def verificar_dos_ordenes(inv, esperado):
    assert len(inv.listar()) == len(esperado) == inv.cantidad <= inv.capacidad
    anterior = None
    nodo = inv.frente
    for objeto in esperado:
        assert nodo is not None and nodo.objeto is objeto and nodo.anterior is anterior
        anterior, nodo = nodo, nodo.siguiente
    assert nodo is None and anterior is inv.final
    siguiente = None
    nodo = inv.final
    for objeto in reversed(esperado):
        assert nodo.objeto is objeto and nodo.siguiente is siguiente
        siguiente, nodo = nodo, nodo.anterior
    assert nodo is None and siguiente is inv.frente
    ordinarios = [o for o in esperado if o.clase != "pergamino_retroceso"]
    anterior = None
    nodo = inv.frente_reversible
    for objeto in ordinarios:
        assert nodo is not None and nodo.objeto is objeto
        assert nodo.anterior_reversible is anterior
        anterior, nodo = nodo, nodo.siguiente_reversible
    assert nodo is None and anterior is inv.final_reversible
    siguiente = None
    nodo = inv.final_reversible
    for objeto in reversed(ordinarios):
        assert nodo.objeto is objeto and nodo.siguiente_reversible is siguiente
        siguiente, nodo = nodo, nodo.anterior_reversible
    assert nodo is None and siguiente is inv.frente_reversible
    assert (inv.cursor is None) == (not esperado)
    if esperado:
        assert any(inv.actual() is objeto for objeto in esperado)


@pytest.mark.parametrize("posicion", [0, 1, 2])
def test_reversible_soltar_restaura_mismo_nodo_y_cursor(posicion):
    inv = InventarioReversible(4)
    objetos = [objeto_reversible(nombre) for nombre in ("a", "b", "c")]
    for objeto in objetos:
        inv.recoger(objeto)
    for _ in range(posicion):
        inv.avanzar()
    nodo = inv.cursor
    soltado, cambio = inv.soltar_actual_reversible()
    assert soltado is objetos[posicion]
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, objetos)
    assert inv.cursor is nodo
    with pytest.raises(ErrorInventario, match="ya fue deshecho"):
        inv.deshacer_cambio(cambio)


def test_reversible_equipar_recupera_ranuras_orden_y_objeto_desplazado():
    inv = InventarioReversible(5)
    a, b, c, p = [objeto_reversible(n, n == "p") for n in ("a", "b", "c", "p")]
    for objeto in (a, p, b, c):
        inv.recoger(objeto)
    inv.equipar_actual("arma")
    inv.avanzar()
    inv.avanzar()
    inv.equipar_actual("armadura")
    inv.avanzar()
    inv.avanzar()
    inv.avanzar()
    resultado, cambio = inv.equipar_actual_reversible("arma")
    assert resultado is a and inv.arma_equipada is c
    verificar_dos_ordenes(inv, [c, b, a, p])
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [b, a, p, c])
    assert inv.arma_equipada is a and inv.armadura_equipada is b
    assert inv.actual() is c


def test_reversible_consumir_restaura_primer_objeto_y_equipamiento():
    inv = InventarioReversible(4)
    a, b = objeto_reversible("a"), objeto_reversible("a")
    inv.recoger(a)
    inv.recoger(b)
    inv.equipar_actual("arma")
    resultado, cambio = inv.consumir_primero_reversible(lambda o: o.nombre == "a")
    assert resultado and inv.arma_equipada is None
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [a, b])
    assert inv.arma_equipada is a


def test_reversible_pergaminos_no_generan_cambio_y_no_son_equipables():
    inv = InventarioReversible(3)
    p = objeto_reversible("p", True)
    assert inv.recoger_reversible(p) == (True, None)
    with pytest.raises(ErrorInventario, match="no es equipable"):
        inv.equipar_actual_reversible("arma")
    assert inv.soltar_actual_reversible() == (p, None)
    inv.recoger(p)
    assert inv.consumir_primero_reversible(lambda _: True) == (True, None)
    verificar_dos_ordenes(inv, [])


def test_reversible_pergamino_nuevo_permanece_al_deshacer_recogida():
    inv = InventarioReversible(3)
    a, p = objeto_reversible("a"), objeto_reversible("p", True)
    _, cambio = inv.recoger_reversible(a)
    inv.recoger_reversible(p)
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [p])


def test_reversible_regresion_vecino_consumido_despues_de_mover_su_vecino():
    inv = InventarioReversible(6)
    x, a, p, b, c = [objeto_reversible(n, n == "p") for n in ("x", "a", "p", "b", "c")]
    for objeto in (x, a, p, b, c):
        inv.recoger(objeto)
    for _ in range(3):
        inv.avanzar()
    _, soltar = inv.soltar_actual_reversible()
    inv.cursor = inv.frente.siguiente  # a
    _, equipar = inv.equipar_actual_reversible("arma")
    inv.consumir_primero(lambda o: o is p)
    inv.deshacer_cambio(equipar)
    verificar_dos_ordenes(inv, [x, a, c])
    inv.deshacer_cambio(soltar)
    verificar_dos_ordenes(inv, [x, a, b, c])


def test_reversible_cursor_consumido_no_se_reinserta():
    inv = InventarioReversible(3)
    p, a = objeto_reversible("p", True), objeto_reversible("a")
    inv.recoger(p)
    inv.recoger(a)
    _, cambio = inv.consumir_primero_reversible(lambda o: o is a)
    inv.consumir_primero(lambda o: o is p)
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [a])
    assert inv.actual() is a


def test_reversible_capacidad_y_registro_ajeno_se_rechazan_sin_mutar():
    inv, otro = InventarioReversible(1), InventarioReversible(1)
    a, p = objeto_reversible("a"), objeto_reversible("p", True)
    inv.recoger(a)
    _, cambio = inv.soltar_actual_reversible()
    inv.recoger_reversible(p)
    with pytest.raises(ErrorInventario, match="no pertenece"):
        otro.deshacer_cambio(cambio)
    with pytest.raises(ErrorInventario, match="no hay espacio"):
        inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [p])
    assert not cambio.deshecho
    inv.consumir_primero(lambda _: True)
    inv.deshacer_cambio(cambio)
    verificar_dos_ordenes(inv, [a])


def test_reversible_no_operaciones_no_generan_registro():
    inv = InventarioReversible(1)
    assert inv.soltar_actual_reversible() == (None, None)
    assert inv.equipar_actual_reversible("arma") == (None, None)
    assert inv.consumir_primero_reversible(lambda _: True) == (False, None)
    inv.recoger(objeto_reversible("a"))
    inv.equipar_actual("arma")
    assert inv.equipar_actual_reversible("arma") == (None, None)
    assert inv.recoger_reversible(objeto_reversible("b")) == (False, None)
    with pytest.raises(ErrorInventario, match="tipo de equipo"):
        inv.equipar_actual_reversible("pocion")


def test_reversible_sin_cambios_excluidos_recupera_todo_el_orden_y_cursor():
    from random import Random

    azar = Random(2026)
    inv = InventarioReversible(100)
    for indice in range(8):
        inv.recoger(objeto_reversible(str(indice), indice % 2 == 0))
    registros = []
    for paso in range(50):
        for _ in range(azar.randrange(inv.cantidad + 1)):
            if not inv.avanzar():
                inv.cursor = inv.frente
        antes, cursor = inv.listar(), inv.cursor
        if inv.cursor is not None and inv.cursor.reversible:
            if azar.randrange(2):
                _, cambio = inv.soltar_actual_reversible()
            else:
                _, cambio = inv.equipar_actual_reversible("arma")
        else:
            _, cambio = inv.recoger_reversible(objeto_reversible(f"nuevo{paso}"))
        if cambio is not None:
            registros.append((cambio, antes, cursor))
    while registros:
        cambio, antes, cursor = registros.pop()
        inv.deshacer_cambio(cambio)
        verificar_dos_ordenes(inv, antes)
        assert inv.cursor is cursor


def test_reversible_vecino_pendiente_se_rechaza_antes_de_mutar():
    inv = InventarioReversible(3)
    a, b = objeto_reversible("a"), objeto_reversible("b")
    inv.recoger(a)
    inv.recoger(b)
    _, primero = inv.soltar_actual_reversible()
    _, segundo = inv.soltar_actual_reversible()
    with pytest.raises(ErrorInventario, match="orden inverso"):
        inv.deshacer_cambio(primero)
    verificar_dos_ordenes(inv, [])
    assert not primero.deshecho
    inv.deshacer_cambio(segundo)
    inv.deshacer_cambio(primero)
    verificar_dos_ordenes(inv, [a, b])


def test_reversible_secuencias_con_pergaminos_conservan_orden_y_equipamiento():
    from random import Random

    for semilla in range(20):
        azar = Random(semilla)
        inv = InventarioReversible(100)
        registros = []  # Consumidor simulado solamente en la prueba.
        for paso in range(40):
            if inv.cantidad:
                for _ in range(azar.randrange(inv.cantidad)):
                    if not inv.avanzar():
                        inv.cursor = inv.frente
            antes = [o for o in inv.listar() if o.clase != "pergamino_retroceso"]
            equipo = inv.arma_equipada, inv.armadura_equipada
            operacion = azar.randrange(3)
            if operacion == 0:
                _, cambio = inv.recoger_reversible(objeto_reversible(f"objeto{paso}"))
            elif operacion == 1:
                _, cambio = inv.soltar_actual_reversible()
            elif inv.cursor is not None and inv.actual().clase != "pergamino_retroceso":
                _, cambio = inv.equipar_actual_reversible("arma" if azar.randrange(2) else "armadura")
            else:
                cambio = None
            if cambio is not None:
                registros.append((cambio, antes, equipo))
            if azar.randrange(2):
                inv.recoger_reversible(objeto_reversible(f"p{paso}", True))
            else:
                inv.consumir_primero(lambda o: o.clase == "pergamino_retroceso")
            verificar_dos_ordenes(inv, inv.listar())
        while registros:
            cambio, antes, equipo = registros.pop()
            permanentes = [o for o in inv.listar() if o.clase == "pergamino_retroceso"]
            inv.deshacer_cambio(cambio)
            ordinarios = [o for o in inv.listar() if o.clase != "pergamino_retroceso"]
            assert len(ordinarios) == len(antes)
            assert all(a is b for a, b in zip(ordinarios, antes))
            actuales = [o for o in inv.listar() if o.clase == "pergamino_retroceso"]
            assert len(actuales) == len(permanentes)
            assert all(a is b for a, b in zip(actuales, permanentes))
            assert (inv.arma_equipada, inv.armadura_equipada) == equipo
            verificar_dos_ordenes(inv, inv.listar())
            inv.consumir_primero(lambda o: o.clase == "pergamino_retroceso")
