import pytest

from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import (
    SalaRastro,
    SalidaRastro,
    rastro_fresco,
    elegir_destino_rastreador,
)


@pytest.mark.parametrize(
    "marca,reloj,esperado",
    [
        (None, 0, False),
        (0, 399, True),
        (0, 400, False),
        (0, 401, False),
        (100, 50, False),
    ],
)
def test_caducidad_del_rastro(marca, reloj, esperado):
    assert rastro_fresco(marca, reloj) is esperado


def test_sala_inicial_recibe_rastro_en_cero():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    sala = SalaRastro(1)

    motor.ubicar_jugador_inicial(jugador, sala)

    assert jugador.sala_actual is sala
    assert sala.ultimo_rastro == 0
    assert motor.historial.acciones == []


def test_retroceso_restaurar_posicion_y_rastros():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    origen = SalaRastro(1)
    destino = SalaRastro(2)

    motor.ubicar_jugador_inicial(jugador, origen)

    # Avanzamos el reloj mediante un evento.
    motor.programar_evento(jugador, 50, "preparacion")
    motor.siguiente_evento()

    motor.iniciar_accion()
    motor.refrescar_rastro_jugador(jugador)
    motor.completar_movimiento_jugador(jugador, destino)

    assert origen.ultimo_rastro == 50
    assert destino.ultimo_rastro == 50
    assert jugador.sala_actual is destino

    # Representa un evento posterior dentro del mismo intervalo.
    motor.programar_evento(jugador, 80, "efecto")
    motor.siguiente_evento()
    assert motor.reloj == 80

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 50
    assert jugador.sala_actual is origen
    assert origen.ultimo_rastro == 0
    assert destino.ultimo_rastro is None


def test_rastreador_elige_rastro_reciente_y_ignora_puerta_cerrada():
    actual = SalaRastro(1)
    antigua = SalaRastro(2)
    reciente = SalaRastro(3)
    cerrada = SalaRastro(4)

    antigua.ultimo_rastro = 50
    reciente.ultimo_rastro = 90
    cerrada.ultimo_rastro = 100

    actual.salidas = [
        SalidaRastro(antigua),
        SalidaRastro(reciente),
        SalidaRastro(cerrada, abierta=False),
    ]

    assert elegir_destino_rastreador(actual, 100) == 3


def test_rastreador_desempata_por_menor_id():
    actual = SalaRastro(1)
    primera = SalaRastro(8)
    segunda = SalaRastro(3)

    primera.ultimo_rastro = 90
    segunda.ultimo_rastro = 90

    actual.salidas = [
        SalidaRastro(primera),
        SalidaRastro(segunda),
    ]

    assert elegir_destino_rastreador(actual, 100) == 3


def test_rastreador_sin_rastro_fresco_no_elige_destino():
    actual = SalaRastro(1)
    vecina = SalaRastro(2)
    vecina.ultimo_rastro = 0
    actual.salidas = [SalidaRastro(vecina)]

    assert elegir_destino_rastreador(actual, 400) is None