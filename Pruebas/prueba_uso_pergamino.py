from types import SimpleNamespace

from modelo.motor_eventos import ActorTurnos, MotorEventos


class InventarioSimulado:
    def __init__(self, cantidad):
        self.cantidad = cantidad

    def consumir_primero(self, cumple):
        objeto = SimpleNamespace(clase="pergamino_retroceso")

        if self.cantidad == 0 or not cumple(objeto):
            return False

        self.cantidad -= 1
        return True


def es_pergamino(objeto):
    return objeto.clase == "pergamino_retroceso"


def preparar(cantidad):
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    jugador.inventario = InventarioSimulado(cantidad)
    return motor, jugador


def test_consumir_y_restaurar_sin_crear_otra_accion():
    motor, jugador = preparar(1)

    motor.programar_evento(jugador, 50, "preparacion")
    motor.siguiente_evento()

    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    motor.programar_evento(jugador, 80, "efecto")
    motor.siguiente_evento()

    assert motor.usar_pergamino(jugador, es_pergamino)

    assert jugador.vida == 100
    assert jugador.inventario.cantidad == 0
    assert motor.reloj == 50
    assert motor.historial.acciones == []


def test_sin_historial_no_consume():
    motor, jugador = preparar(1)

    assert not motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.inventario.cantidad == 1


def test_sin_pergamino_no_deshace():
    motor, jugador = preparar(0)
    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    assert not motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.vida == 80
    assert len(motor.historial.acciones) == 1


def test_dos_usos_deshacen_dos_acciones():
    motor, jugador = preparar(2)

    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 90)

    motor.iniciar_accion()
    motor._cambiar(jugador, "vida", 80)

    assert motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.vida == 90
    assert jugador.inventario.cantidad == 1

    assert motor.usar_pergamino(jugador, es_pergamino)
    assert jugador.vida == 100
    assert jugador.inventario.cantidad == 0
    assert motor.historial.acciones == []