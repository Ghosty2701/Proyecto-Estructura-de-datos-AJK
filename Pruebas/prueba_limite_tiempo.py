"""T006 — FR-LT-003, AC-LT-004/005: límite de tiempo del motor, solo para copias."""
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro


def preparar():
    sala = SalaRastro(1)
    sala.nombre = 'Sala'
    sala.objetos_suelo = []
    sala.contenido_cargado = True
    motor = MotorEventos(2026)
    jugador = ActorTurnos('j', 500, 100)
    enemigos = []
    for numero, velocidad in enumerate((400, 400, 250)):
        enemigo = ActorTurnos(f'g-{numero}', 50, velocidad, ataque=1, comportamiento='guardian')
        enemigo.sala_actual = sala
        sala.enemigos.append(enemigo)
        enemigos.append(enemigo)
    # Iniciar activa a los enemigos de la sala: eventos en t=25, 25 y 40.
    motor.iniciar_partida(jugador, sala)
    return motor, jugador


def ejecutar(motor, jugador):
    return lambda evento: motor.ejecutar_evento(evento, jugador)


def vida_en(t):
    """Referencia sin límite: vida tras el último evento con tiempo <= t."""
    motor, jugador = preparar()
    registro = []

    def con_registro(evento):
        motor.ejecutar_evento(evento, jugador)
        registro.append((evento.tiempo, jugador.vida))

    motor.esperar_jugador(jugador, con_registro)
    tiempos = [tiempo for tiempo, _ in registro]
    assert tiempos.count(25) == 2 and 40 in tiempos   # dos eventos simultáneos
    return [vida for tiempo, vida in registro if tiempo <= t][-1]


def test_sin_limite_el_comportamiento_no_cambia():
    motor_a, jugador_a = preparar()
    motor_b, jugador_b = preparar()
    motor_b.tiempo_limite = None
    for motor, jugador in ((motor_a, jugador_a), (motor_b, jugador_b)):
        motor.esperar_jugador(jugador, ejecutar(motor, jugador))
    assert (motor_a.reloj, jugador_a.vida) == (motor_b.reloj, jugador_b.vida) == (100, jugador_b.vida)
    assert not motor_b.limite_alcanzado


def test_limite_ejecuta_eventos_hasta_t_y_se_detiene_antes_de_la_decision():
    # AC-LT-004: los dos eventos con el mismo t=25 se ejecutan; ninguno posterior.
    motor, jugador = preparar()
    motor.tiempo_limite = 30
    resultado = motor.esperar_jugador(jugador, ejecutar(motor, jugador))
    assert resultado is None and motor.limite_alcanzado
    assert motor.reloj == 30
    assert jugador.vida == vida_en(30) < 500   # ambos de t=25, ninguno de t=40
    pendiente = motor.consultar_siguiente_evento()
    assert pendiente.tiempo == 40           # el de t=40 sigue en la agenda


def test_limite_igual_a_un_evento_lo_incluye():
    # AC-LT-005: un evento con tiempo == t forma parte del estado en t.
    motor, jugador = preparar()
    motor.tiempo_limite = 40
    motor.esperar_jugador(jugador, ejecutar(motor, jugador))
    assert motor.reloj == 40 and jugador.vida == vida_en(40) < vida_en(30)
    assert motor.limite_alcanzado
