from types import SimpleNamespace

from modelo.inventario import Inventario
from modelo.motor_eventos import ActorTurnos, MotorEventos


def es_pergamino(objeto):
    return objeto.clase == "pergamino_retroceso"


def preparar(cantidad):
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    jugador.inventario = Inventario(capacidad=10)

    for _ in range(cantidad):
        jugador.inventario.recoger(
            SimpleNamespace(clase="pergamino_retroceso")
        )

    return motor, jugador


def test_recoger_pergamino_no_se_deshace_al_retroceder():
    motor, jugador = preparar(1)
    pergamino = SimpleNamespace(clase="pergamino_retroceso")
    suelo = [pergamino]

    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    # La transferencia del pergamino queda fuera del historial.
    assert jugador.inventario.recoger(suelo[0])
    suelo.pop(0)

    assert jugador.inventario.cantidad == 2
    assert motor.usar_pergamino(jugador, es_pergamino)

    assert jugador.vida == 100
    assert jugador.inventario.cantidad == 1
    assert jugador.inventario.actual() is pergamino
    assert suelo == []
    assert motor.historial.acciones == []


def test_soltar_pergamino_no_se_deshace_al_retroceder():
    motor, jugador = preparar(2)
    suelo = []
    pergamino = jugador.inventario.actual()

    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    # Soltar tampoco registra una operación inversa del pergamino.
    suelo.append(jugador.inventario.soltar_actual())

    assert jugador.inventario.cantidad == 1
    assert motor.usar_pergamino(jugador, es_pergamino)

    assert jugador.vida == 100
    assert jugador.inventario.cantidad == 0
    assert suelo == [pergamino]
    assert motor.historial.acciones == []