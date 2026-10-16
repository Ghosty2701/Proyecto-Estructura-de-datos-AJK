from adaptadores.prefetch import vecinas


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