import random

from modelo.motor_eventos import MotorEventos


def test_semilla_reproduce_sin_tocar_azar_global():
    estado_global = random.getstate()

    primero = MotorEventos(semilla=2026)
    segundo = MotorEventos(semilla=2026)

    tiradas_primero = [
        primero.azar.randint(0, 4) for _ in range(20)
    ]
    tiradas_segundo = [
        segundo.azar.randint(0, 4) for _ in range(20)
    ]

    assert primero.semilla == 2026
    assert tiradas_primero == tiradas_segundo
    assert random.getstate() == estado_global


def test_deshacer_recupera_estado_previo_no_solo_semilla():
    motor = MotorEventos(semilla=77)

    # Consumimos azar antes del intervalo para comprobar que
    # deshacer restaura ese punto, sin reiniciar el generador.
    motor.azar.randint(0, 4)
    anterior = motor.azar.getstate()

    motor.iniciar_accion()
    tiradas = [motor.azar.randint(0, 4) for _ in range(10)]

    assert motor.deshacer_ultima_accion()
    assert motor.azar.getstate() == anterior

    repetidas = [motor.azar.randint(0, 4) for _ in range(10)]
    assert repetidas == tiradas


def test_dos_intervalos_restauran_dos_estados_del_azar():
    motor = MotorEventos(semilla=7)
    inicial = motor.azar.getstate()

    motor.iniciar_accion()
    for _ in range(4):
        motor.azar.randint(0, 4)

    intermedio = motor.azar.getstate()

    motor.iniciar_accion()
    for _ in range(4):
        motor.azar.randint(0, 4)

    assert motor.deshacer_ultima_accion()
    assert motor.azar.getstate() == intermedio

    assert motor.deshacer_ultima_accion()
    assert motor.azar.getstate() == inicial