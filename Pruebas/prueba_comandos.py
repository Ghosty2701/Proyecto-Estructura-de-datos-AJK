from controlador.comandos import parsear


def _t(texto):
    c = parsear(texto)
    return None if c is None else (c.nombre, c.argumento)


def test_direcciones_directas_y_con_ir():
    assert _t("n") == ("mover", "N")
    assert _t("O") == ("mover", "O")
    assert _t("ir e") == ("mover", "E")


def test_abrir_requiere_direccion_valida():
    assert _t("abrir s") == ("abrir", "S")
    assert _t("abrir") is None
    assert _t("abrir x") is None


def test_atacar_y_recoger_con_indice_por_defecto_1():
    assert _t("atacar") == ("atacar", 1)
    assert _t("atacar 3") == ("atacar", 3)
    assert _t("recoger 2") == ("recoger", 2)


def test_indices_invalidos_se_rechazan():
    assert _t("atacar 0") is None
    assert _t("atacar -1") is None
    assert _t("recoger abc") is None


def test_orden_solo_acepta_los_tres_criterios():
    assert _t("orden peso") == ("orden", "peso")
    assert _t("orden color") is None
    assert _t("orden") is None


def test_comandos_simples_y_alias():
    assert _t("esp") == ("esperar", None)
    assert _t("inv") == ("inventario", None)
    assert _t("sig") == ("siguiente", None)
    assert _t("?") == ("ayuda", None)
    assert _t("  SALIR  ") == ("salir", None)


def test_texto_vacio_o_desconocido():
    assert _t("") is None
    assert _t("   ") is None
    assert _t("bailar") is None
    assert _t("esperar ya") is None
