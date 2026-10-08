import pytest

from modelo.motor_eventos import ActorTurnos, MotorEventos


def test_jugador_empieza_en_cero_y_enemigo_segun_velocidad():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    rata = ActorTurnos("rata", 20, 150)

    motor.programar_primera_accion_jugador(jugador)
    motor.programar_accion(rata, 100)

    evento = motor.siguiente_evento()
    assert evento.actor is jugador
    assert motor.reloj == 0

    evento = motor.siguiente_evento()
    assert evento.actor is rata
    assert motor.reloj == 66


def test_cambio_velocidad_reajusta_accion_pendiente():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    efecto = ActorTurnos("fuente_efecto", 1, 100)

    anterior = motor.programar_accion(rata, 100)
    motor.programar_evento(efecto, 40, "aceleracion")

    assert motor.siguiente_evento().tipo == "aceleracion"
    assert motor.reloj == 40

    nuevo = motor.cambiar_velocidad(rata, 200)

    assert anterior.cancelado
    assert nuevo.tiempo == 70
    assert nuevo.secuencia > anterior.secuencia

    assert motor.siguiente_evento() is nuevo
    assert motor.reloj == 70
    assert motor.siguiente_evento() is None

    # Descartar el evento viejo no debe avanzar el reloj.
    assert motor.reloj == 70


def test_muerte_cancela_accion_y_efectos_del_actor():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    jugador = ActorTurnos("jugador", 100, 100)

    accion = motor.programar_accion(rata, 100)
    regeneracion = motor.programar_evento(rata, 200, "regeneracion")
    turno_jugador = motor.programar_accion(jugador, 100)

    motor.matar_actor(rata)

    assert accion.cancelado
    assert regeneracion.cancelado
    assert motor.siguiente_evento() is turno_jugador
    assert motor.siguiente_evento() is None
    assert motor.reloj == 100
    assert rata.primer_evento is None


def test_no_permite_dos_acciones_pendientes():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    original = motor.programar_accion(rata, 100)

    with pytest.raises(ValueError):
        motor.programar_accion(rata, 100)

    assert motor.siguiente_evento() is original


def test_velocidad_invalida_no_modifica_actor():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    original = motor.programar_accion(rata, 100)

    with pytest.raises(ValueError):
        motor.cambiar_velocidad(rata, 0)

    assert rata.velocidad == 100
    assert not original.cancelado
    assert rata.proxima_accion is original