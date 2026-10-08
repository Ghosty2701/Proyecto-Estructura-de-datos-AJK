from modelo.motor_eventos import ActorTurnos, MotorEventos


def test_retroceso_restaurar_velocidad_y_evento():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    original = motor.programar_accion(rata, 100)

    motor.iniciar_accion()
    nuevo = motor.cambiar_velocidad(rata, 200)

    assert nuevo.tiempo == 50
    assert motor.siguiente_evento() is nuevo
    assert motor.reloj == 50

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 0
    assert rata.velocidad == 100
    assert rata.proxima_accion is original
    assert not original.cancelado
    assert motor.agenda.siguiente_secuencia == 1

    assert motor.siguiente_evento() is original
    assert motor.reloj == 100
    assert motor.siguiente_evento() is None


def test_retroceso_restaurar_actor_muerto_y_sus_eventos():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)

    accion = motor.programar_accion(rata, 100)
    regeneracion = motor.programar_evento(
        rata, 200, "regeneracion"
    )

    motor.iniciar_accion()
    motor.matar_actor(rata)

    # También debemos restaurar los cancelados que ya salieron del heap.
    assert motor.siguiente_evento() is None

    assert motor.deshacer_ultima_accion()

    assert rata.vida == 20
    assert rata.proxima_accion is accion
    assert not accion.cancelado
    assert not regeneracion.cancelado

    assert motor.siguiente_evento() is accion
    assert motor.siguiente_evento() is regeneracion
    assert motor.siguiente_evento() is None


def test_evento_deshhecho_no_rompe_lista_del_actor():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    original = motor.programar_accion(rata, 100)

    motor.iniciar_accion()
    descartado = motor.cambiar_velocidad(rata, 50)

    assert descartado.tiempo == 200
    assert motor.deshacer_ultima_accion()

    # La cancelación del evento nuevo no debe afectar al original.
    motor.matar_actor(rata)

    assert original.cancelado
    assert motor.siguiente_evento() is None
    assert rata.primer_evento is None


def test_dos_retrocesos_recuperan_dos_acciones():
    motor = MotorEventos()
    rata = ActorTurnos("rata", 20, 100)
    original = motor.programar_accion(rata, 100)

    motor.iniciar_accion()
    intermedio = motor.cambiar_velocidad(rata, 200)

    motor.iniciar_accion()
    motor.matar_actor(rata)

    assert motor.deshacer_ultima_accion()
    assert rata.vida == 20
    assert rata.velocidad == 200
    assert rata.proxima_accion is intermedio
    assert not intermedio.cancelado

    assert motor.deshacer_ultima_accion()
    assert rata.velocidad == 100
    assert rata.proxima_accion is original
    assert not original.cancelado

    assert not motor.deshacer_ultima_accion()