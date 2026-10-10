from types import SimpleNamespace

from modelo.inventario import Inventario
from modelo.motor_eventos import ActorTurnos, MotorEventos


def es_pergamino(objeto):
    return objeto.clase == "pergamino_retroceso"


def preparar(cantidad_pergaminos):
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    jugador.inventario = Inventario(capacidad=10)
    for _ in range(cantidad_pergaminos):
        jugador.inventario.recoger(SimpleNamespace(clase="pergamino_retroceso"))
    return motor, jugador


def test_usar_pergamino_real_revierte_y_consume_una_unidad():
    motor, jugador = preparar(2)
    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    assert motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.vida == 100
    assert jugador.inventario.cantidad == 1  # el consumo NO se revierte


def test_sin_pergamino_en_inventario_no_deshace():
    motor, jugador = preparar(0)
    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    assert not motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.vida == 80
