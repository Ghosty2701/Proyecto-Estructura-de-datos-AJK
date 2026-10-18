from adaptadores.prefetch import seleccionar_lote, vecinas
from adaptadores.cache_catalogo import ArbolAVL


def test_vecinas_sale_en_orden_n_s_e_o():
    sala = {
        "id": 2,
        "nombre": "Pasillo de las urnas",
        "salidas": {
            "S": {"sala": 1},
            "N": {"sala": 3},
            "E": {"sala": 7, "cerrada": True, "llave": "itm_llave_bronce"},
        },
    }
    assert vecinas(sala) == [3, 1, 7]


def test_vecinas_sin_salidas():
    sala = {"id": 5, "nombre": "Celda", "salidas": {}}
    assert vecinas(sala) == []


def test_vecinas_una_salida_al_oeste():
    sala = {"id": 6, "nombre": "Rincon", "salidas": {"O": {"sala": 4}}}
    assert vecinas(sala) == [4]


def test_lote_solo_contiene_actual_y_vecinas_abiertas():
    esqueleto, contenido = ArbolAVL(), ArbolAVL()
    for i in range(1, 31):
        esqueleto.insertar(i, {"id": i, "salidas": {}})
    esqueleto.buscar(10)["salidas"] = {"N": {"sala": 20, "cerrada": True}, "S": {"sala": 30}}
    assert seleccionar_lote(esqueleto, contenido, 10) == [10, 30]
    assert seleccionar_lote(esqueleto, contenido, 10, solo_vecindad=False) == [10, 30, 20, 1, 2, 3, 4, 5, 6, 7]
    for i in (10, 30, 20):
        contenido.insertar(i, {"sala": i})
    assert seleccionar_lote(esqueleto, contenido, 10) == []
