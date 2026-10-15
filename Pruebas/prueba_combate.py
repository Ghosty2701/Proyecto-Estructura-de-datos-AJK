import random

import pytest

from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro
from modelo.rastro import SalaRastro, SalidaRastro

def preparar(ataque=6, defensa=2, vida=20):
    motor = MotorEventos(semilla=42)
    atacante = ActorTurnos(
        "jugador", 100, 100, ataque=ataque
    )
    defensor = ActorTurnos(
        "enemigo", vida, 100, defensa=defensa
    )

    sala = SalaRastro(1)
    atacante.sala_actual = sala
    defensor.sala_actual = sala

    return motor, atacante, defensor


def test_ataque_aplica_formula_y_no_avanza_reloj():
    motor, atacante, defensor = preparar()
    referencia = random.Random(42)
    esperado = max(1, 6 + referencia.randint(0, 4) - 2)

    motor.iniciar_accion()
    dano = motor.resolver_ataque(atacante, defensor)

    assert dano == esperado
    assert defensor.vida == 20 - esperado
    assert motor.reloj == 0


def test_defensa_alta_no_elimina_dano_minimo():
    motor, atacante, defensor = preparar(
        ataque=0, defensa=100
    )

    motor.iniciar_accion()

    assert motor.resolver_ataque(atacante, defensor) == 1
    assert defensor.vida == 19


def test_muerte_y_azar_se_restauran_al_retroceder():
    motor, atacante, defensor = preparar(
        ataque=10, defensa=0, vida=3
    )
    pendiente = motor.programar_accion(defensor, 100)
    estado_azar = motor.azar.getstate()

    motor.iniciar_accion()
    dano = motor.resolver_ataque(atacante, defensor)

    assert defensor.vida == 0
    assert pendiente.cancelado
    assert motor.consultar_siguiente_evento() is None

    assert motor.deshacer_ultima_accion()

    assert defensor.vida == 3
    assert not pendiente.cancelado
    assert defensor.proxima_accion is pendiente
    assert motor.consultar_siguiente_evento() is pendiente
    assert motor.azar.getstate() == estado_azar

    # Repetir el ataque obtiene la misma tirada.
    motor.iniciar_accion()
    assert motor.resolver_ataque(atacante, defensor) == dano


def test_otra_sala_rechaza_ataque_sin_consumir_azar():
    motor, atacante, defensor = preparar()
    defensor.sala_actual = SalaRastro(2)

    motor.iniciar_accion()
    estado_azar = motor.azar.getstate()
    cantidad_cambios = len(motor.historial.acciones[-1].cambios)

    with pytest.raises(ValueError):
        motor.resolver_ataque(atacante, defensor)

    assert defensor.vida == 20
    assert motor.azar.getstate() == estado_azar
    assert (
        len(motor.historial.acciones[-1].cambios)
        == cantidad_cambios
    )
    
def preparar_ataque_jugador(vida_enemigo=30, ataque_jugador=6):
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos(
        "jugador", 100, 100, ataque=ataque_jugador, defensa=2
    )
    enemigo = ActorTurnos(
        "enemigo", vida_enemigo, 150, ataque=5, defensa=1
    )

    sala = SalaRastro(1)
    motor.ubicar_jugador_inicial(jugador, sala)
    enemigo.sala_actual = sala

    inicial = motor.programar_primera_accion_jugador(jugador)
    pendiente = motor.programar_accion(enemigo, 100)

    return motor, jugador, enemigo, inicial, pendiente


def test_ataque_y_respuesta_enemiga_se_deshacen_juntos():
    motor, jugador, enemigo, inicial, pendiente = preparar_ataque_jugador()
    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        # Simulamos únicamente la ejecución del turno enemigo.
        assert evento.actor is enemigo
        motor.resolver_ataque(enemigo, jugador)
        motor.programar_accion(enemigo, 100)

    turno = motor.atacar_jugador(jugador, enemigo, ejecutar)

    referencia = random.Random(42)
    dano_jugador = max(1, 6 + referencia.randint(0, 4) - 1)
    dano_enemigo = max(1, 5 + referencia.randint(0, 4) - 2)

    assert enemigo.vida == 30 - dano_jugador
    assert jugador.vida == 100 - dano_enemigo
    assert motor.reloj == 100
    assert enemigo.proxima_accion.tiempo == 132
    assert motor.consultar_siguiente_evento() is turno
    assert len(motor.historial.acciones) == 1

    assert motor.deshacer_ultima_accion()

    assert enemigo.vida == 30
    assert jugador.vida == 100
    assert motor.reloj == 0
    assert jugador.proxima_accion is inicial
    assert enemigo.proxima_accion is pendiente
    assert motor.azar.getstate() == estado_azar
    assert motor.consultar_siguiente_evento() is inicial


def test_ataque_mortal_impide_respuesta_y_puede_deshacerse():
    motor, jugador, enemigo, inicial, pendiente = preparar_ataque_jugador(
        vida_enemigo=3, ataque_jugador=10
    )
    ejecutados = []

    turno = motor.atacar_jugador(
        jugador, enemigo, ejecutados.append
    )

    assert enemigo.vida == 0
    assert pendiente.cancelado
    assert ejecutados == []
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert motor.consultar_siguiente_evento() is turno

    assert motor.deshacer_ultima_accion()

    assert enemigo.vida == 3
    assert not pendiente.cancelado
    assert enemigo.proxima_accion is pendiente
    assert jugador.proxima_accion is inicial
    assert motor.reloj == 0


@pytest.mark.parametrize(
    "caso", ["otra_sala", "muerto", "uno_mismo"]
)
def test_objetivo_invalido_no_consume_turno_ni_azar(caso):
    motor, jugador, enemigo, inicial, _ = preparar_ataque_jugador()
    objetivo = enemigo

    if caso == "otra_sala":
        enemigo.sala_actual = SalaRastro(2)
    elif caso == "muerto":
        motor.matar_actor(enemigo)
    else:
        objetivo = jugador

    estado_azar = motor.azar.getstate()
    ejecutados = []

    with pytest.raises(ValueError):
        motor.atacar_jugador(
            jugador, objetivo, ejecutados.append
        )

    assert ejecutados == []
    assert motor.historial.acciones == []
    assert motor.reloj == 0
    assert jugador.proxima_accion is inicial
    assert motor.consultar_siguiente_evento() is inicial
    assert motor.azar.getstate() == estado_azar

def preparar_guardian(misma_sala=True, vida_jugador=100, ataque=5):
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos(
        "jugador", vida_jugador, 100, defensa=2
    )
    guardian = ActorTurnos(
        "guardian", 20, 150, ataque=ataque
    )

    sala = SalaRastro(1)
    motor.ubicar_jugador_inicial(jugador, sala)

    guardian.sala_actual = (
        sala if misma_sala else SalaRastro(2)
    )

    inicial = motor.programar_primera_accion_jugador(jugador)
    pendiente = motor.programar_accion(guardian, 100)

    return motor, jugador, guardian, inicial, pendiente


def test_guardian_ataca_y_el_intervalo_puede_deshacerse():
    motor, jugador, guardian, inicial, pendiente = preparar_guardian()
    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_guardian(evento, jugador)

    turno = motor.esperar_jugador(jugador, ejecutar)

    # Con semilla 42, la primera tirada es 0:
    # daño = max(1, 5 + 0 - 2) = 3.
    assert jugador.vida == 97
    assert motor.reloj == 100
    assert guardian.proxima_accion.tiempo == 132
    assert motor.consultar_siguiente_evento() is turno
    assert len(motor.historial.acciones) == 1

    assert motor.deshacer_ultima_accion()

    assert jugador.vida == 100
    assert motor.reloj == 0
    assert motor.azar.getstate() == estado_azar
    assert jugador.proxima_accion is inicial
    assert guardian.proxima_accion is pendiente
    assert motor.consultar_siguiente_evento() is inicial


def test_guardian_en_otra_sala_espera_sin_consumir_azar():
    motor, jugador, guardian, _, _ = preparar_guardian(
        misma_sala=False
    )
    sala_guardian = guardian.sala_actual
    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_guardian(evento, jugador)

    motor.esperar_jugador(jugador, ejecutar)

    assert jugador.vida == 100
    assert guardian.sala_actual is sala_guardian
    assert guardian.proxima_accion.tiempo == 132
    assert motor.reloj == 100
    assert motor.azar.getstate() == estado_azar


def test_guardian_mata_jugador_y_el_retroceso_lo_restaura():
    motor, jugador, guardian, inicial, pendiente = preparar_guardian(
        vida_jugador=2, ataque=10
    )

    def ejecutar(evento):
        motor.ejecutar_guardian(evento, jugador)

    resultado = motor.esperar_jugador(jugador, ejecutar)

    assert resultado is None
    assert jugador.vida == 0
    assert motor.reloj == 66

    # Probamos la reversibilidad interna del motor.
    # Esto no habilita usar pergaminos después de la derrota.
    assert motor.deshacer_ultima_accion()

    assert jugador.vida == 2
    assert motor.reloj == 0
    assert jugador.proxima_accion is inicial
    assert guardian.proxima_accion is pendiente
    assert motor.consultar_siguiente_evento() is inicial
    
def preparar_rastreador():
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos(
        "jugador", 100, 100, defensa=2
    )
    rastreador = ActorTurnos(
        "rastreador", 20, 150, ataque=5
    )

    motor.ubicar_jugador_inicial(jugador, SalaRastro(1))
    rastreador.sala_actual = SalaRastro(2)

    return motor, jugador, rastreador


def test_rastreador_se_mueve_sin_ataque_gratuito_y_puede_volver():
    motor, jugador, rastreador = preparar_rastreador()
    origen = rastreador.sala_actual
    origen.salidas = [SalidaRastro(jugador.sala_actual)]

    inicial = motor.programar_primera_accion_jugador(jugador)
    pendiente = motor.programar_accion(rastreador, 100)
    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_rastreador(evento, jugador)

    turno = motor.esperar_jugador(jugador, ejecutar)

    # Se mueve en 66, pero no ataca al llegar.
    assert rastreador.sala_actual is jugador.sala_actual
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert rastreador.proxima_accion.tiempo == 132
    assert motor.consultar_siguiente_evento() is turno
    assert motor.azar.getstate() == estado_azar
    assert jugador.sala_actual.ultimo_rastro == 0
    assert origen.ultimo_rastro is None

    assert motor.deshacer_ultima_accion()

    assert rastreador.sala_actual is origen
    assert rastreador.proxima_accion is pendiente
    assert jugador.proxima_accion is inicial
    assert motor.reloj == 0


def test_rastreador_prioriza_atacar_si_comparte_sala():
    motor, jugador, rastreador = preparar_rastreador()
    rastreador.sala_actual = jugador.sala_actual

    vecina = SalaRastro(3)
    vecina.ultimo_rastro = 0
    rastreador.sala_actual.salidas = [SalidaRastro(vecina)]

    motor.programar_primera_accion_jugador(jugador)
    motor.programar_accion(rastreador, 100)

    def ejecutar(evento):
        motor.ejecutar_rastreador(evento, jugador)

    motor.esperar_jugador(jugador, ejecutar)

    assert jugador.vida == 97
    assert rastreador.sala_actual is jugador.sala_actual
    assert rastreador.proxima_accion.tiempo == 132


@pytest.mark.parametrize(
    "caso", ["sin_rastro", "caducado", "cerrada"]
)
def test_rastreador_espera_si_no_hay_destino_valido(caso):
    motor, jugador, rastreador = preparar_rastreador()
    origen = rastreador.sala_actual
    vecina = SalaRastro(3)

    if caso == "sin_rastro":
        vecina.ultimo_rastro = None
    elif caso == "caducado":
        vecina.ultimo_rastro = 0
    else:
        vecina.ultimo_rastro = 399

    origen.salidas = [
        SalidaRastro(vecina, abierta=caso != "cerrada")
    ]

    # Probamos este comportamiento directamente en tiempo 400.
    rastreador.velocidad = 25
    motor.programar_accion(rastreador, 100)
    evento = motor.siguiente_evento()

    assert motor.reloj == 400
    estado_azar = motor.azar.getstate()

    motor.ejecutar_rastreador(evento, jugador)

    assert rastreador.sala_actual is origen
    assert rastreador.proxima_accion.tiempo == 800
    assert jugador.vida == 100
    assert motor.azar.getstate() == estado_azar 
    

def preparar_errante():
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos(
        "jugador", 100, 100, defensa=2
    )
    errante = ActorTurnos(
        "errante", 20, 150, ataque=5
    )

    motor.ubicar_jugador_inicial(jugador, SalaRastro(1))
    errante.sala_actual = SalaRastro(2)

    inicial = motor.programar_primera_accion_jugador(jugador)
    pendiente = motor.programar_accion(errante, 100)

    return motor, jugador, errante, inicial, pendiente


def test_errante_elige_salida_abierta_y_repite_tras_retroceder():
    motor, jugador, errante, inicial, pendiente = preparar_errante()
    origen = errante.sala_actual
    otra = SalaRastro(3)

    origen.salidas = [
        SalidaRastro(SalaRastro(4), abierta=False),
        SalidaRastro(jugador.sala_actual),
        SalidaRastro(otra),
    ]

    abiertas = [jugador.sala_actual, otra]
    referencia = random.Random(42)
    esperada = abiertas[referencia.randrange(len(abiertas))]
    estado_inicial = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_errante(evento, jugador)

    turno = motor.esperar_jugador(jugador, ejecutar)

    assert errante.sala_actual is esperada
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert errante.proxima_accion.tiempo == 132
    assert motor.consultar_siguiente_evento() is turno

    estado_posterior = motor.azar.getstate()

    assert motor.deshacer_ultima_accion()

    assert errante.sala_actual is origen
    assert errante.proxima_accion is pendiente
    assert jugador.proxima_accion is inicial
    assert motor.azar.getstate() == estado_inicial

    motor.esperar_jugador(jugador, ejecutar)

    assert errante.sala_actual is esperada
    assert motor.azar.getstate() == estado_posterior


@pytest.mark.parametrize("con_salida_cerrada", [False, True])
def test_errante_sin_salidas_abiertas_espera_sin_azar(
    con_salida_cerrada,
):
    motor, jugador, errante, _, _ = preparar_errante()
    origen = errante.sala_actual

    if con_salida_cerrada:
        origen.salidas = [
            SalidaRastro(jugador.sala_actual, abierta=False)
        ]

    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_errante(evento, jugador)

    motor.esperar_jugador(jugador, ejecutar)

    assert errante.sala_actual is origen
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert errante.proxima_accion.tiempo == 132
    assert motor.azar.getstate() == estado_azar


def test_errante_prioriza_ataque_sobre_movimiento():
    motor, jugador, errante, _, _ = preparar_errante()
    errante.sala_actual = jugador.sala_actual
    errante.sala_actual.salidas = [
        SalidaRastro(SalaRastro(3))
    ]

    referencia = random.Random(42)
    dano = max(1, 5 + referencia.randint(0, 4) - 2)

    def ejecutar(evento):
        motor.ejecutar_errante(evento, jugador)

    motor.esperar_jugador(jugador, ejecutar)

    assert jugador.vida == 100 - dano
    assert errante.sala_actual is jugador.sala_actual
    assert errante.proxima_accion.tiempo == 132

    # Solo se consumió el azar del ataque.
    assert motor.azar.getstate() == referencia.getstate()
    
@pytest.mark.parametrize(
    "comportamiento,destino_id",
    [
        ("guardian", 2),
        ("rastreador", 1),
        ("errante", 3),
    ],
)
def test_seleccion_de_comportamiento_y_retroceso(
    comportamiento, destino_id
):
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos(
        "enemigo",
        20,
        150,
        ataque=5,
        comportamiento=comportamiento,
    )

    motor.ubicar_jugador_inicial(jugador, SalaRastro(1))
    origen = SalaRastro(2)
    enemigo.sala_actual = origen

    # La primera vecina no tiene rastro.
    # La segunda contiene al jugador y tiene rastro en 0.
    origen.salidas = [
        SalidaRastro(SalaRastro(3)),
        SalidaRastro(jugador.sala_actual),
    ]

    inicial = motor.programar_primera_accion_jugador(jugador)
    pendiente = motor.programar_accion(enemigo, 100)
    estado_azar = motor.azar.getstate()

    def ejecutar(evento):
        motor.ejecutar_enemigo(evento, jugador)

    turno = motor.esperar_jugador(jugador, ejecutar)

    # Guardián: permanece en 2.
    # Rastreador: sigue el rastro hacia 1.
    # Errante: con esta semilla elige la primera salida, hacia 3.
    assert enemigo.sala_actual.sala_id == destino_id
    assert enemigo.proxima_accion.tiempo == 132
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert motor.consultar_siguiente_evento() is turno

    assert motor.deshacer_ultima_accion()

    assert enemigo.sala_actual is origen
    assert enemigo.proxima_accion is pendiente
    assert jugador.proxima_accion is inicial
    assert motor.reloj == 0
    assert motor.azar.getstate() == estado_azar


def test_actor_rechaza_comportamiento_desconocido():
    with pytest.raises(ValueError, match="Comportamiento"):
        ActorTurnos(
            "enemigo",
            20,
            100,
            comportamiento="desconocido",
        )