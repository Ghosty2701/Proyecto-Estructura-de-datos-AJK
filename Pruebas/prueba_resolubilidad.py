"""FR-RS-001 a 006/009/013; AC-RS-001..007/016."""
from copy import deepcopy
from Pruebas.datos_resolubilidad import datos, conectar, ubicaciones
from modelo.verificacion import normalizar, verificar


def test_ac001_002_005_cadena_y_llaves_no_consumidas():
    general, salas = datos(4)
    conectar(salas, 1, 2, 'A')
    conectar(salas, 2, 3, 'A')
    conectar(salas, 3, 4, 'K')
    for sala in salas:
        for salida in sala['salidas'].values():
            salida['cierre_automatico'] = 1
    respuesta = ubicaciones(('A', 1), ('K', 3))
    respuesta['llaves'][0]['enemigo'] = 'guardian-inicial'
    respuesta['llaves'][1]['enemigo'] = 'errante-inicial'
    # AC-RS-005: ni combate ni cierres/trampas se simulan; bastan estas ubicaciones.
    mapa = normalizar(general, salas, respuesta)
    resultado = verificar(mapa)
    assert resultado.resoluble
    assert [mapa.llaves[k].id for k in resultado.cierre.orden] == ['A', 'K']
    assert resultado.cierre.operaciones <= 4 + 6 + 3


def test_ac003_004_sala_salida_sola_no_basta():
    general, salas = datos(3, salida=2)
    conectar(salas, 1, 2)
    assert not verificar(normalizar(general, salas, ubicaciones(('K', 3)))).resoluble
    assert not verificar(normalizar(general, salas, ubicaciones(('K', 1)))).resoluble


def test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial():
    general, salas = datos(2)
    conectar(salas, 1, 2, 'K')
    respuesta = {'llaves': [{'id': 'K', 'sala': 1, 'enemigo': 'errante'}]}
    original = deepcopy((general, salas, respuesta))
    mapa = normalizar(general, salas, respuesta)
    primero, segundo = verificar(mapa), verificar(mapa)
    assert primero == segundo
    assert primero.resoluble
    assert (general, salas, respuesta) == original


def test_varias_ubicaciones_basta_una_y_puerta_abierta_no_exige_llave():
    general, salas = datos(3, salida=2)
    conectar(salas, 1, 2, 'K', cerrada=False)
    mapa = normalizar(general, salas, ubicaciones(('K', 3), ('K', 2)))
    assert verificar(mapa).resoluble
