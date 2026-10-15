from types import SimpleNamespace
from modelo.rastro import SalaRastro, SalidaRastro
import pytest

from modelo.inventario import Inventario
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro
from modelo.rastro import Puerta, SalaRastro, SalidaRastro


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
    
def test_consultar_no_extrae_ni_avanza_el_reloj():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    turno = motor.programar_accion(jugador, 100)

    assert motor.consultar_siguiente_evento() is turno
    assert motor.consultar_siguiente_evento() is turno
    assert motor.reloj == 0
    assert jugador.proxima_accion is turno
    assert turno.enlazado

    assert motor.siguiente_evento() is turno
    assert motor.reloj == 100
    assert jugador.proxima_accion is None


def test_consultar_descarta_invalidos_sin_consumir_el_valido():
    motor = MotorEventos()
    enemigo = ActorTurnos("enemigo", 20, 100)
    jugador = ActorTurnos("jugador", 100, 100)

    cancelado = motor.programar_evento(enemigo, 10, "efecto")
    motor.cancelar_evento(cancelado)
    motor.programar_accion(enemigo, 25)
    motor.matar_actor(enemigo)

    turno = motor.programar_accion(jugador, 100)

    assert motor.consultar_siguiente_evento() is turno
    assert motor.reloj == 0
    assert enemigo.primer_evento is None
    assert motor.siguiente_evento() is turno


def test_intervalo_iniciado_antes_de_extraer_recupera_turno():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    original = motor.programar_primera_accion_jugador(jugador)

    assert motor.consultar_siguiente_evento() is original
    assert motor.historial.acciones == []

    # Representa una acción ya validada: abrir el intervalo
    # antes de consumir el turno permite restaurarlo.
    motor.iniciar_accion()
    assert motor.siguiente_evento() is original
    motor._cambiar(jugador, "vida", 80)
    futuro = motor.programar_accion(jugador, 100)

    assert motor.consultar_siguiente_evento() is futuro

    assert motor.deshacer_ultima_accion()
    assert motor.reloj == 0
    assert jugador.vida == 100
    assert jugador.proxima_accion is original
    assert motor.consultar_siguiente_evento() is original
    assert motor.siguiente_evento() is original
    assert motor.siguiente_evento() is None
    
    
def test_procesa_enemigo_conserva_turno_y_permite_retroceder():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 150)

    inicial = motor.programar_primera_accion_jugador(jugador)
    turno_enemigo = motor.programar_accion(enemigo, 100)

    def ejecutar(evento):
        assert evento.actor is enemigo
        motor._cambiar(jugador, "vida", jugador.vida - 10)
        motor.programar_accion(enemigo, 100)

    # Al inicio, todavía no debe actuar ningún enemigo.
    assert motor.avanzar_hasta_jugador(jugador, ejecutar) is inicial
    assert jugador.vida == 100

    # Representamos una acción válida del jugador en tiempo 0.
    motor.iniciar_accion()
    assert motor.siguiente_evento() is inicial
    siguiente = motor.programar_accion(jugador, 100)

    assert motor.avanzar_hasta_jugador(jugador, ejecutar) is siguiente

    # El enemigo actuó en 66 y vuelve a actuar en 132.
    assert jugador.vida == 90
    assert enemigo.proxima_accion.tiempo == 132
    assert motor.reloj == 100

    # El turno del jugador sigue pendiente, sin extraerse.
    assert jugador.proxima_accion is siguiente
    assert motor.consultar_siguiente_evento() is siguiente

    assert motor.deshacer_ultima_accion()
    assert motor.reloj == 0
    assert jugador.vida == 100
    assert jugador.proxima_accion is inicial
    assert enemigo.proxima_accion is turno_enemigo
    assert motor.consultar_siguiente_evento() is inicial


@pytest.mark.parametrize("enemigo_primero", [True, False])
def test_empate_respeta_secuencia(enemigo_primero):
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 100)

    if enemigo_primero:
        motor.programar_accion(enemigo, 100)
        turno = motor.programar_accion(jugador, 100)
    else:
        turno = motor.programar_accion(jugador, 100)
        motor.programar_accion(enemigo, 100)

    ejecutados = []

    resultado = motor.avanzar_hasta_jugador(
        jugador, ejecutados.append
    )

    assert resultado is turno
    assert motor.reloj == 100
    assert motor.consultar_siguiente_evento() is turno

    if enemigo_primero:
        assert len(ejecutados) == 1
        assert ejecutados[0].actor is enemigo
    else:
        assert ejecutados == []


def test_detiene_procesamiento_si_muere_el_jugador():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 100)

    motor.programar_accion(enemigo, 25)
    motor.programar_accion(jugador, 100)

    def ejecutar(evento):
        assert evento.actor is enemigo
        motor.matar_actor(jugador)

    assert motor.avanzar_hasta_jugador(jugador, ejecutar) is None
    assert jugador.vida == 0
    assert motor.reloj == 25


def test_dos_esperas_y_dos_pergaminos_recuperan_las_decisiones():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 150)
    sala = SalaRastro(1)

    motor.ubicar_jugador_inicial(jugador, sala)
    jugador.inventario = Inventario(capacidad=10)

    for _ in range(2):
        jugador.inventario.recoger(
            SimpleNamespace(clase="pergamino_retroceso")
        )

    inicial = motor.programar_primera_accion_jugador(jugador)
    motor.programar_accion(enemigo, 100)

    def ejecutar(evento):
        # Comportamiento simulado únicamente para esta prueba.
        assert evento.actor is enemigo
        motor._cambiar(jugador, "vida", jugador.vida - 10)
        motor.programar_accion(enemigo, 100)

    primera_decision = motor.esperar_jugador(jugador, ejecutar)

    # El enemigo actuó en 66.
    assert motor.reloj == 100
    assert jugador.vida == 90
    assert sala.ultimo_rastro == 0
    assert motor.consultar_siguiente_evento() is primera_decision

    segunda_decision = motor.esperar_jugador(jugador, ejecutar)

    # Ahora el enemigo actuó también en 132 y 198.
    assert motor.reloj == 200
    assert jugador.vida == 70
    assert sala.ultimo_rastro == 100
    assert motor.consultar_siguiente_evento() is segunda_decision
    assert len(motor.historial.acciones) == 2

    def es_pergamino(objeto):
        return objeto.clase == "pergamino_retroceso"

    assert motor.usar_pergamino(jugador, es_pergamino)

    assert motor.reloj == 100
    assert jugador.vida == 90
    assert sala.ultimo_rastro == 0
    assert jugador.inventario.cantidad == 1
    assert motor.consultar_siguiente_evento() is primera_decision

    assert motor.usar_pergamino(jugador, es_pergamino)

    assert motor.reloj == 0
    assert jugador.vida == 100
    assert sala.ultimo_rastro == 0
    assert jugador.inventario.cantidad == 0
    assert motor.consultar_siguiente_evento() is inicial
    assert motor.historial.acciones == []


def test_esperar_fuera_de_turno_no_abre_intervalo():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 100)

    motor.ubicar_jugador_inicial(jugador, SalaRastro(1))
    pendiente = motor.programar_accion(enemigo, 25)
    motor.programar_accion(jugador, 100)

    ejecutados = []

    with pytest.raises(ValueError):
        motor.esperar_jugador(jugador, ejecutados.append)

    assert ejecutados == []
    assert motor.reloj == 0
    assert motor.historial.acciones == []
    assert motor.consultar_siguiente_evento() is pendiente
    
def _preparar_activacion():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    motor.ubicar_jugador_inicial(jugador, SalaRastro(1))
    return motor, jugador


def _crear_enemigo_activacion(actor_id, sala, velocidad=100):
    enemigo = ActorTurnos(
        actor_id, 20, velocidad, comportamiento="guardian"
    )
    enemigo.sala_actual = sala
    return enemigo


def test_activacion_ordena_ids_y_calcula_desde_reloj_actual():
    motor, jugador = _preparar_activacion()

    motor.programar_evento(jugador, 50, "preparacion")
    motor.siguiente_evento()

    segundo = _crear_enemigo_activacion(
        "e-02", jugador.sala_actual, velocidad=150
    )
    primero = _crear_enemigo_activacion(
        "e-01", jugador.sala_actual
    )
    enemigos = [segundo, primero]

    assert motor.activar_enemigos(jugador, enemigos) == 2

    assert primero.activo
    assert segundo.activo
    assert (
        primero.proxima_accion.secuencia
        < segundo.proxima_accion.secuencia
    )
    assert primero.proxima_accion.tiempo == 150
    assert segundo.proxima_accion.tiempo == 116

    # La vista ordenada no modifica la lista recibida.
    assert enemigos == [segundo, primero]


def test_activacion_excluye_otras_salas_muertos_y_ya_activos():
    motor, jugador = _preparar_activacion()

    local = _crear_enemigo_activacion(
        "e-01", jugador.sala_actual
    )
    lejano = _crear_enemigo_activacion("e-02", SalaRastro(2))
    muerto = _crear_enemigo_activacion(
        "e-03", jugador.sala_actual
    )
    motor.matar_actor(muerto)

    enemigos = [lejano, muerto, local]

    assert motor.activar_enemigos(jugador, enemigos) == 1
    pendiente = local.proxima_accion

    assert motor.activar_enemigos(jugador, enemigos) == 0
    assert local.proxima_accion is pendiente
    assert local.activo
    assert not lejano.activo
    assert not muerto.activo
    assert lejano.proxima_accion is None
    assert muerto.proxima_accion is None


def test_retroceso_restaura_enemigo_inactivo():
    motor, jugador = _preparar_activacion()
    enemigo = _crear_enemigo_activacion(
        "e-01", jugador.sala_actual
    )

    motor.iniciar_accion()
    assert motor.activar_enemigos(jugador, [enemigo]) == 1

    assert motor.deshacer_ultima_accion()

    assert not enemigo.activo
    assert enemigo.proxima_accion is None
    assert enemigo.primer_evento is None
    assert motor.consultar_siguiente_evento() is None
    assert motor.agenda.siguiente_secuencia == 0

    # Puede activarse nuevamente después del retroceso.
    assert motor.activar_enemigos(jugador, [enemigo]) == 1


def test_activacion_valida_lote_antes_de_programar():
    motor, jugador = _preparar_activacion()

    valido = _crear_enemigo_activacion(
        "e-01", jugador.sala_actual
    )
    sin_comportamiento = ActorTurnos("e-02", 20, 100)
    sin_comportamiento.sala_actual = jugador.sala_actual

    with pytest.raises(ValueError, match="comportamiento"):
        motor.activar_enemigos(
            jugador, [valido, sin_comportamiento]
        )

    assert not valido.activo
    assert valido.proxima_accion is None
    assert motor.agenda.siguiente_secuencia == 0
    
def test_inicio_programa_jugador_y_activa_enemigos_por_id():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    sala = SalaRastro(1)
    sala.contenido_cargado = True

    segundo = _crear_enemigo_activacion(
        "e-02", sala, velocidad=150
    )
    primero = _crear_enemigo_activacion("e-01", sala)
    sala.enemigos = [segundo, primero]

    assert motor.iniciar_partida(jugador, sala)

    assert jugador.sala_actual is sala
    assert sala.ultimo_rastro == 0
    assert motor.reloj == 0
    assert jugador.proxima_accion.tiempo == 0
    assert jugador.proxima_accion.secuencia == 0

    assert primero.activo
    assert segundo.activo
    assert (
        primero.proxima_accion.secuencia
        < segundo.proxima_accion.secuencia
    )
    assert primero.proxima_accion.tiempo == 100
    assert segundo.proxima_accion.tiempo == 66
    assert motor.historial.acciones == []


def test_inicio_pendiente_no_modifica_estado_y_permite_reintentar():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    sala = SalaRastro(1)

    assert motor.iniciar_partida(jugador, sala) is False

    assert jugador.sala_actual is None
    assert jugador.proxima_accion is None
    assert sala.ultimo_rastro is None
    assert motor.reloj == 0
    assert motor.agenda.heap == []
    assert motor.agenda.siguiente_secuencia == 0
    assert motor.historial.acciones == []

    # Representa contenido ya preparado por la capa de aplicación.
    sala.contenido_cargado = True

    assert motor.iniciar_partida(jugador, sala)
    assert jugador.sala_actual is sala
    assert jugador.proxima_accion.tiempo == 0


def test_inicio_con_enemigo_invalido_no_deja_estado_parcial():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    sala = SalaRastro(1)
    sala.contenido_cargado = True

    valido = _crear_enemigo_activacion("e-01", sala)
    invalido = ActorTurnos("e-02", 20, 100)
    invalido.sala_actual = sala
    sala.enemigos = [valido, invalido]

    with pytest.raises(ValueError, match="comportamiento"):
        motor.iniciar_partida(jugador, sala)

    assert jugador.sala_actual is None
    assert jugador.proxima_accion is None
    assert sala.ultimo_rastro is None
    assert not valido.activo
    assert valido.proxima_accion is None
    assert motor.agenda.heap == []
    assert motor.agenda.siguiente_secuencia == 0


def test_inicio_repetido_no_duplica_turnos():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    sala = SalaRastro(1)
    sala.contenido_cargado = True

    assert motor.iniciar_partida(jugador, sala)
    turno = jugador.proxima_accion

    with pytest.raises(ValueError, match="nuevos"):
        motor.iniciar_partida(jugador, sala)

    assert jugador.proxima_accion is turno
    assert len(motor.agenda.heap) == 1
    
def _preparar_movimiento():
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos(
        "jugador", 100, 100, defensa=2
    )
    origen = SalaRastro(1)
    destino = SalaRastro(2)

    origen.contenido_cargado = True
    destino.contenido_cargado = True

    salida = SalidaRastro(destino)
    origen.salidas = [salida]

    assert motor.iniciar_partida(jugador, origen)

    return motor, jugador, origen, destino, salida


def test_movimiento_activa_enemigo_y_deshace_intervalo_completo():
    motor, jugador, origen, destino, salida = _preparar_movimiento()

    enemigo = ActorTurnos(
        "e-01",
        20,
        150,
        ataque=5,
        comportamiento="guardian",
    )
    enemigo.sala_actual = destino
    destino.enemigos = [enemigo]

    def ejecutar(evento):
        motor.ejecutar_enemigo(evento, jugador)

    motor.esperar_jugador(jugador, ejecutar)

    turno_anterior = jugador.proxima_accion
    estado_azar = motor.azar.getstate()
    assert not enemigo.activo

    turno = motor.mover_jugador(jugador, salida, ejecutar)

    # Se mueve en 100. El enemigo se activa y ataca en 166.
    assert jugador.sala_actual is destino
    assert motor.reloj == 200
    assert jugador.vida == 97
    assert origen.ultimo_rastro == 100
    assert destino.ultimo_rastro == 100
    assert enemigo.activo
    assert enemigo.proxima_accion.tiempo == 232
    assert motor.consultar_siguiente_evento() is turno

    assert motor.deshacer_ultima_accion()

    assert jugador.sala_actual is origen
    assert jugador.proxima_accion is turno_anterior
    assert jugador.vida == 100
    assert motor.reloj == 100
    assert origen.ultimo_rastro == 0
    assert destino.ultimo_rastro is None
    assert not enemigo.activo
    assert enemigo.proxima_accion is None
    assert motor.azar.getstate() == estado_azar
    assert len(motor.historial.acciones) == 1

    # El contenido disponible permanece cargado.
    assert destino.contenido_cargado


def test_movimiento_pendiente_conserva_turno_y_permite_reintentar():
    motor, jugador, origen, destino, salida = _preparar_movimiento()
    destino.contenido_cargado = False

    turno = jugador.proxima_accion
    estado_azar = motor.azar.getstate()
    ejecutados = []

    assert motor.mover_jugador(
        jugador, salida, ejecutados.append
    ) is False

    assert jugador.sala_actual is origen
    assert jugador.proxima_accion is turno
    assert motor.reloj == 0
    assert motor.historial.acciones == []
    assert motor.azar.getstate() == estado_azar
    assert ejecutados == []

    destino.contenido_cargado = True

    resultado = motor.mover_jugador(
        jugador, salida, ejecutados.append
    )

    assert resultado is jugador.proxima_accion
    assert jugador.sala_actual is destino
    assert motor.reloj == 100


@pytest.mark.parametrize("caso", ["cerrada", "ajena"])
def test_movimiento_rechaza_salida_invalida_sin_consumir_turno(caso):
    motor, jugador, origen, destino, salida = _preparar_movimiento()
    turno = jugador.proxima_accion

    if caso == "cerrada":
        salida.abierta = False
    else:
        salida = SalidaRastro(destino)

    with pytest.raises(ValueError):
        motor.mover_jugador(jugador, salida, lambda evento: None)

    assert jugador.sala_actual is origen
    assert jugador.proxima_accion is turno
    assert motor.reloj == 0
    assert motor.historial.acciones == []


def test_movimiento_valida_enemigos_antes_de_cambiar_estado():
    motor, jugador, origen, destino, salida = _preparar_movimiento()
    turno = jugador.proxima_accion

    enemigo = ActorTurnos("e-01", 20, 100)
    enemigo.sala_actual = destino
    destino.enemigos = [enemigo]

    with pytest.raises(ValueError, match="comportamiento"):
        motor.mover_jugador(jugador, salida, lambda evento: None)

    assert jugador.sala_actual is origen
    assert jugador.proxima_accion is turno
    assert motor.reloj == 0
    assert motor.historial.acciones == []
    assert not enemigo.activo


def test_movimiento_desempata_antes_de_enemigo_recien_activado():
    motor, jugador, _, destino, salida = _preparar_movimiento()

    enemigo = ActorTurnos(
        "e-01",
        20,
        100,
        ataque=5,
        comportamiento="guardian",
    )
    enemigo.sala_actual = destino
    destino.enemigos = [enemigo]

    def ejecutar(evento):
        motor.ejecutar_enemigo(evento, jugador)

    turno = motor.mover_jugador(jugador, salida, ejecutar)

    assert motor.reloj == 100
    assert jugador.vida == 100
    assert enemigo.proxima_accion.tiempo == 100
    assert turno.secuencia < enemigo.proxima_accion.secuencia
    
def _preparar_puerta():
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos("jugador", 100, 100)
    jugador.inventario = Inventario(capacidad=10)

    origen = SalaRastro(1)
    destino = SalaRastro(2)
    origen.contenido_cargado = True

    puerta = Puerta(
        abierta=False, llave="itm_llave_bronce"
    )
    salida = SalidaRastro(destino, puerta=puerta)
    regreso = SalidaRastro(origen, puerta=puerta)

    origen.salidas = [salida]
    destino.salidas = [regreso]

    assert motor.iniciar_partida(jugador, origen)

    return motor, jugador, origen, destino, salida, regreso


def test_abrir_puerta_comparte_estado_y_puede_deshacerse():
    motor, jugador, origen, destino, salida, regreso = (
        _preparar_puerta()
    )
    llave = SimpleNamespace(
        clase="llave", id="itm_llave_bronce"
    )
    jugador.inventario.recoger(llave)

    motor.esperar_jugador(jugador, lambda evento: None)
    turno_anterior = jugador.proxima_accion

    resultado = motor.abrir_puerta_jugador(
        jugador, salida, lambda evento: None
    )

    assert resultado is jugador.proxima_accion
    assert motor.reloj == 150
    assert jugador.sala_actual is origen
    assert origen.ultimo_rastro == 100
    assert salida.abierta
    assert regreso.abierta
    assert jugador.inventario.cantidad == 1
    assert jugador.inventario.actual() is llave
    assert not destino.contenido_cargado

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 100
    assert jugador.proxima_accion is turno_anterior
    assert origen.ultimo_rastro == 0
    assert not salida.abierta
    assert not regreso.abierta
    assert jugador.inventario.cantidad == 1
    assert jugador.inventario.actual() is llave


@pytest.mark.parametrize(
    "caso",
    ["sin_inventario", "vacio", "incorrecta", "otro_objeto"],
)
def test_abrir_sin_llave_correcta_no_consume_turno(caso):
    motor, jugador, _, _, salida, regreso = _preparar_puerta()

    if caso == "sin_inventario":
        jugador.inventario = None
    elif caso == "incorrecta":
        jugador.inventario.recoger(
            SimpleNamespace(clase="llave", id="otra_llave")
        )
    elif caso == "otro_objeto":
        jugador.inventario.recoger(
            SimpleNamespace(
                clase="pocion", id="itm_llave_bronce"
            )
        )

    turno = jugador.proxima_accion
    estado_azar = motor.azar.getstate()

    with pytest.raises(ValueError, match="llave correcta"):
        motor.abrir_puerta_jugador(
            jugador, salida, lambda evento: None
        )

    assert not salida.abierta
    assert not regreso.abierta
    assert jugador.proxima_accion is turno
    assert motor.reloj == 0
    assert motor.historial.acciones == []
    assert motor.azar.getstate() == estado_azar


def test_abrir_puerta_ya_abierta_no_crea_otra_accion():
    motor, jugador, _, _, salida, _ = _preparar_puerta()
    jugador.inventario.recoger(
        SimpleNamespace(
            clase="llave", id="itm_llave_bronce"
        )
    )

    motor.abrir_puerta_jugador(
        jugador, salida, lambda evento: None
    )
    turno = jugador.proxima_accion
    cantidad_intervalos = len(motor.historial.acciones)

    with pytest.raises(ValueError, match="ya está abierta"):
        motor.abrir_puerta_jugador(
            jugador, salida, lambda evento: None
        )

    assert motor.reloj == 50
    assert jugador.proxima_accion is turno
    assert len(motor.historial.acciones) == cantidad_intervalos
    
def test_cierre_entorno_se_ejecuta_y_puede_deshacerse():
    motor, jugador, _, _, salida, regreso = _preparar_puerta()
    salida.abierta = True
    inicial = jugador.proxima_accion

    cierre = motor.programar_evento_entorno(
        salida.puerta, 30, "cierre_puerta"
    )
    assert cierre.actor is None

    def ejecutar(evento):
        motor.ejecutar_evento(evento, jugador)

    turno = motor.esperar_jugador(jugador, ejecutar)

    assert not salida.abierta
    assert not regreso.abierta
    assert motor.reloj == 100
    assert motor.consultar_siguiente_evento() is turno

    assert motor.deshacer_ultima_accion()

    assert salida.abierta
    assert regreso.abierta
    assert motor.reloj == 0
    assert jugador.proxima_accion is inicial

    # Se recuperan tanto el turno como el cierre pendiente.
    assert motor.siguiente_evento() is inicial
    assert motor.siguiente_evento() is cierre


def test_muerte_de_actor_no_cancela_cierre_del_entorno():
    motor = MotorEventos()
    jugador = ActorTurnos("jugador", 100, 100)
    enemigo = ActorTurnos("enemigo", 20, 100)
    puerta = Puerta(abierta=True)

    motor.programar_accion(enemigo, 10)
    cierre = motor.programar_evento_entorno(
        puerta, 20, "cierre_puerta"
    )
    motor.matar_actor(enemigo)

    assert motor.siguiente_evento() is cierre

    motor.ejecutar_evento(cierre, jugador)

    assert not puerta.abierta
    assert motor.reloj == 20


def test_cancelacion_de_entorno_puede_deshacerse():
    motor = MotorEventos()
    puerta = Puerta(abierta=True)
    cierre = motor.programar_evento_entorno(
        puerta, 10, "cierre_puerta"
    )

    motor.iniciar_accion()
    motor.cancelar_evento(cierre)

    assert motor.siguiente_evento() is None
    assert motor.reloj == 0
    assert puerta.abierta

    assert motor.deshacer_ultima_accion()

    assert not cierre.cancelado
    assert motor.siguiente_evento() is cierre


@pytest.mark.parametrize("entorno_primero", [True, False])
def test_empate_entre_actor_y_entorno_respeta_secuencia(
    entorno_primero,
):
    motor = MotorEventos()
    enemigo = ActorTurnos("enemigo", 20, 100)
    puerta = Puerta(abierta=True)

    if entorno_primero:
        cierre = motor.programar_evento_entorno(
            puerta, 10, "cierre_puerta"
        )
        accion = motor.programar_accion(enemigo, 10)
    else:
        accion = motor.programar_accion(enemigo, 10)
        cierre = motor.programar_evento_entorno(
            puerta, 10, "cierre_puerta"
        )

    esperado = (
        [cierre, accion]
        if entorno_primero
        else [accion, cierre]
    )

    assert [
        motor.siguiente_evento(),
        motor.siguiente_evento(),
    ] == esperado
    
def _preparar_cierre_automatico(intervalo):
    motor, jugador, origen, destino, salida, regreso = (
        _preparar_puerta()
    )
    salida.puerta.cierre_automatico = intervalo
    jugador.inventario.recoger(
        SimpleNamespace(
            clase="llave", id="itm_llave_bronce"
        )
    )
    return motor, jugador, origen, destino, salida, regreso


def test_cierre_automatico_durante_apertura_y_retroceso():
    motor, jugador, _, _, salida, regreso = (
        _preparar_cierre_automatico(30)
    )
    inicial = jugador.proxima_accion
    ejecutados = []

    def ejecutar(evento):
        ejecutados.append((motor.reloj, evento.tipo))
        motor.ejecutar_evento(evento, jugador)

    motor.abrir_puerta_jugador(jugador, salida, ejecutar)

    assert ejecutados == [(30, "cierre_puerta")]
    assert motor.reloj == 50
    assert not salida.abierta
    assert not regreso.abierta
    assert jugador.inventario.cantidad == 1

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 0
    assert not salida.abierta
    assert jugador.proxima_accion is inicial

    # Deshacer la apertura también elimina su cierre futuro.
    assert motor.siguiente_evento() is inicial
    assert motor.siguiente_evento() is None


def test_deshacer_espera_recupera_puerta_abierta_y_cierre_pendiente():
    motor, jugador, _, _, salida, _ = (
        _preparar_cierre_automatico(120)
    )

    def ejecutar(evento):
        motor.ejecutar_evento(evento, jugador)

    motor.abrir_puerta_jugador(jugador, salida, ejecutar)

    assert motor.reloj == 50
    assert salida.abierta

    cierre = next(
        evento
        for evento in motor.agenda.heap
        if evento.tipo == "cierre_puerta"
        and not evento.cancelado
    )
    assert cierre.tiempo == 120

    motor.esperar_jugador(jugador, ejecutar)

    assert motor.reloj == 150
    assert not salida.abierta

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 50
    assert salida.abierta
    assert not cierre.cancelado

    motor.esperar_jugador(jugador, ejecutar)

    assert motor.reloj == 150
    assert not salida.abierta


def test_cierre_automatico_no_desplaza_al_jugador():
    motor, jugador, origen, destino, salida, regreso = (
        _preparar_cierre_automatico(120)
    )
    destino.contenido_cargado = True

    def ejecutar(evento):
        motor.ejecutar_evento(evento, jugador)

    motor.abrir_puerta_jugador(jugador, salida, ejecutar)
    motor.mover_jugador(jugador, salida, ejecutar)

    assert motor.reloj == 150
    assert jugador.sala_actual is destino
    assert not salida.abierta
    assert not regreso.abierta

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 50
    assert jugador.sala_actual is origen
    assert salida.abierta


def test_reabrir_programa_un_nuevo_cierre_reversible():
    motor, jugador, _, _, salida, _ = (
        _preparar_cierre_automatico(30)
    )
    tiempos = []

    def ejecutar(evento):
        tiempos.append(evento.tiempo)
        motor.ejecutar_evento(evento, jugador)

    motor.abrir_puerta_jugador(jugador, salida, ejecutar)
    motor.abrir_puerta_jugador(jugador, salida, ejecutar)

    assert tiempos == [30, 80]
    assert motor.reloj == 100
    assert jugador.inventario.cantidad == 1

    assert motor.deshacer_ultima_accion()

    assert motor.reloj == 50
    assert not salida.abierta

    motor.abrir_puerta_jugador(jugador, salida, ejecutar)

    assert tiempos == [30, 80, 80]
    assert motor.reloj == 100


@pytest.mark.parametrize("intervalo", [0, -1, 1.5])
def test_puerta_rechaza_intervalo_de_cierre_invalido(intervalo):
    with pytest.raises(ValueError, match="entero positivo"):
        Puerta(cierre_automatico=intervalo)

# Fase de efectos temporales: agregar al archivo de pruebas del motor.
from modelo.efectos import Trampa


def _fx_actor(vida=100, vida_max=100, velocidad=100):
    motor = MotorEventos(semilla=42)
    actor = ActorTurnos("actor", vida, velocidad, vida_max=vida_max)
    return motor, actor


def _fx_hasta(motor, actor, limite):
    # Acciones simuladas solo en estas pruebas unitarias de los temporizadores.
    for _ in range(2000):
        evento = motor.consultar_siguiente_evento()
        if evento is None or evento.tiempo > limite:
            return
        evento = motor.siguiente_evento()
        if evento.tipo == "accion":
            motor.programar_accion(evento.actor, 100)
        else:
            motor.ejecutar_evento(evento, actor)
    raise AssertionError("Demasiados eventos para esta carga de prueba")


def _fx_movimiento(trampas):
    motor = MotorEventos(semilla=42)
    jugador = ActorTurnos("jugador", 100, 100)
    origen = SalaRastro(1)
    destino = SalaRastro(2)
    origen.contenido_cargado = True
    destino.contenido_cargado = True
    destino.trampas = trampas
    salida = SalidaRastro(destino)
    regreso = SalidaRastro(origen)
    origen.salidas = [salida]
    destino.salidas = [regreso]
    assert motor.iniciar_partida(jugador, origen)
    return motor, jugador, origen, destino, salida, regreso


@pytest.mark.parametrize("dano", [1, 3])
def test_fx_veneno_cinco_pulsos_y_caducidad(dano):
    motor, actor = _fx_actor()
    motor.aplicar_veneno(actor, dano)
    _fx_hasta(motor, actor, 400)
    assert actor.vida == 100 - 5 * dano
    assert actor.veneno is None
    assert motor.reloj == 400
    assert motor.siguiente_evento() is None


def test_fx_antidoto_antes_del_pulso_no_produce_dano():
    motor, actor = _fx_actor()
    estado = motor.aplicar_veneno(actor, 2)
    pulso = estado.evento
    motor.programar_evento(actor, 40, "preparacion")
    assert motor.siguiente_evento().tiempo == 40
    assert motor.aplicar_antidoto(actor)
    assert pulso.cancelado
    assert actor.veneno is None
    assert motor.siguiente_evento() is None
    assert actor.vida == 100
    assert motor.reloj == 40
    assert not motor.aplicar_antidoto(actor)


def test_fx_retroceso_del_antidoto_recupera_pulso_descartado():
    motor, actor = _fx_actor()
    estado = motor.aplicar_veneno(actor, 2)
    pulso = estado.evento
    motor.iniciar_accion()
    motor.aplicar_antidoto(actor)
    assert motor.siguiente_evento() is None
    assert motor.deshacer_ultima_accion()
    assert actor.veneno is estado
    assert estado.evento is pulso
    assert not pulso.cancelado
    _fx_hasta(motor, actor, 80)
    assert actor.vida == 98


def test_fx_reaplicar_veneno_reemplaza_dosis_y_duracion():
    motor, actor = _fx_actor()
    viejo = motor.aplicar_veneno(actor, 1).evento
    motor.programar_evento(actor, 40, "preparacion")
    motor.siguiente_evento()
    nuevo = motor.aplicar_veneno(actor, 4)
    assert viejo.cancelado
    assert nuevo.fin == 440
    _fx_hasta(motor, actor, 440)
    assert actor.vida == 80
    assert actor.veneno is None


def test_fx_veneno_mortal_cancela_accion_y_otros_efectos():
    motor, actor = _fx_actor(vida=3)
    accion = motor.programar_accion(actor, 100)
    antorcha = motor.encender_antorcha(actor, 1000).evento
    regeneracion = motor.iniciar_regeneracion(actor, 2).evento
    motor.aplicar_veneno(actor, 3)
    _fx_hasta(motor, actor, 80)
    assert actor.vida == 0
    assert accion.cancelado and antorcha.cancelado and regeneracion.cancelado
    assert motor.siguiente_evento() is None
    assert motor.reloj == 80


def test_fx_deshacer_aplicacion_y_pulso_restauran_estado_anterior():
    motor, actor = _fx_actor()
    original = motor.programar_accion(actor, 100)
    motor.iniciar_accion()
    motor.aplicar_veneno(actor, 7)
    _fx_hasta(motor, actor, 80)
    assert actor.vida == 93
    assert motor.deshacer_ultima_accion()
    assert actor.vida == 100 and actor.veneno is None
    assert motor.reloj == 0 and actor.proxima_accion is original
    assert motor.siguiente_evento() is original
    assert motor.siguiente_evento() is None


def test_fx_velocidad_reajusta_al_aplicarse_y_al_terminar():
    motor, actor = _fx_actor()
    original = motor.programar_accion(actor, 100)
    motor.programar_evento(actor, 40, "preparacion")
    motor.siguiente_evento()
    motor.aplicar_velocidad(actor, 200, 20)
    assert original.cancelado
    assert actor.proxima_accion.tiempo == 70
    _fx_hasta(motor, actor, 60)
    assert actor.velocidad == 100
    assert actor.efecto_velocidad is None
    assert actor.proxima_accion.tiempo == 80


def test_fx_velocidad_sin_accion_pendiente_tambien_caduca():
    motor, actor = _fx_actor()
    motor.aplicar_velocidad(actor, 50, 20)
    _fx_hasta(motor, actor, 20)
    assert actor.velocidad == 100
    assert actor.efecto_velocidad is None
    assert actor.proxima_accion is None


def test_fx_renovar_velocidad_conserva_base_original():
    motor, actor = _fx_actor()
    motor.programar_accion(actor, 100)
    anterior = motor.aplicar_velocidad(actor, 200, 80)
    viejo_fin = anterior.evento
    motor.programar_evento(actor, 20, "preparacion")
    motor.siguiente_evento()
    nuevo = motor.aplicar_velocidad(actor, 50, 40)
    assert viejo_fin.cancelado
    assert nuevo.anterior == 100
    _fx_hasta(motor, actor, 60)
    assert actor.velocidad == 100
    assert actor.proxima_accion.tiempo == 100


def test_fx_retroceso_de_velocidad_recupera_evento_original():
    motor, actor = _fx_actor()
    original = motor.programar_accion(actor, 100)
    motor.iniciar_accion()
    motor.aplicar_velocidad(actor, 200, 20)
    _fx_hasta(motor, actor, 20)
    assert actor.proxima_accion.tiempo == 80
    assert motor.deshacer_ultima_accion()
    assert actor.velocidad == 100
    assert actor.efecto_velocidad is None
    assert actor.proxima_accion is original
    assert not original.cancelado
    assert motor.agenda.siguiente_secuencia == 1


@pytest.mark.parametrize("velocidad,duracion", [(0, 20), (200, 0), (200, -1)])
def test_fx_velocidad_invalida_no_modifica_estado(velocidad, duracion):
    motor, actor = _fx_actor()
    original = motor.programar_accion(actor, 100)
    with pytest.raises(ValueError):
        motor.aplicar_velocidad(actor, velocidad, duracion)
    assert actor.velocidad == 100 and actor.efecto_velocidad is None
    assert actor.proxima_accion is original and not original.cancelado


def test_fx_antorcha_se_apaga_en_su_duracion():
    motor, actor = _fx_actor()
    estado = motor.encender_antorcha(actor, 45)
    assert actor.antorcha is estado and estado.fin == 45
    _fx_hasta(motor, actor, 45)
    assert actor.antorcha is None and actor.vida == 100


def test_fx_renovar_antorcha_cancela_apagado_anterior():
    motor, actor = _fx_actor()
    viejo = motor.encender_antorcha(actor, 40).evento
    motor.programar_evento(actor, 20, "preparacion")
    motor.siguiente_evento()
    nuevo = motor.encender_antorcha(actor, 50)
    assert viejo.cancelado and nuevo.fin == 70
    _fx_hasta(motor, actor, 40)
    assert actor.antorcha is nuevo
    _fx_hasta(motor, actor, 70)
    assert actor.antorcha is None


def test_fx_retroceso_recupera_antorcha_y_apagado_pendiente():
    motor, actor = _fx_actor()
    estado = motor.encender_antorcha(actor, 40)
    apagado = estado.evento
    motor.iniciar_accion()
    _fx_hasta(motor, actor, 40)
    assert actor.antorcha is None
    assert motor.deshacer_ultima_accion()
    assert actor.antorcha is estado and estado.evento is apagado
    assert motor.siguiente_evento() is apagado


def test_fx_regeneracion_empieza_al_activar_y_no_supera_maximo():
    motor, jugador = _preparar_activacion()
    enemigo = ActorTurnos(
        "e-01", 45, 100, vida_max=50, regeneracion=7, comportamiento="guardian"
    )
    enemigo.sala_actual = jugador.sala_actual
    assert enemigo.regeneracion is None
    assert motor.activar_enemigos(jugador, [enemigo]) == 1
    assert enemigo.regeneracion.evento.tiempo == 200
    _fx_hasta(motor, jugador, 400)
    assert enemigo.vida == 50
    assert enemigo.regeneracion.evento.tiempo == 600


def test_fx_regeneracion_dormida_no_se_programa_al_crear_actor():
    enemigo = ActorTurnos("e-01", 40, 100, vida_max=50, regeneracion=5)
    assert not enemigo.activo
    assert enemigo.regeneracion is None
    assert enemigo.primer_evento is None


def test_fx_detener_regeneracion_impide_pulsos_futuros():
    motor, actor = _fx_actor(vida=40, vida_max=50)
    motor.iniciar_regeneracion(actor, 5)
    _fx_hasta(motor, actor, 200)
    assert actor.vida == 45
    assert motor.detener_regeneracion(actor)
    _fx_hasta(motor, actor, 400)
    assert actor.vida == 45 and actor.regeneracion is None


def test_fx_muerte_cancela_regeneracion_y_retroceso_la_recupera():
    motor, actor = _fx_actor(vida=40, vida_max=50)
    estado = motor.iniciar_regeneracion(actor, 5)
    pulso = estado.evento
    motor.iniciar_accion()
    motor.matar_actor(actor)
    assert motor.siguiente_evento() is None
    assert actor.vida == 0 and pulso.cancelado
    assert motor.deshacer_ultima_accion()
    assert actor.vida == 40 and not pulso.cancelado
    _fx_hasta(motor, actor, 200)
    assert actor.vida == 45


@pytest.mark.parametrize("cantidad,esperada", [(1, 49), (20, 50)])
def test_fx_curacion_respeta_vida_max(cantidad, esperada):
    motor, actor = _fx_actor(vida=48, vida_max=50)
    assert motor.curar(actor, cantidad) == esperada - 48
    assert actor.vida == esperada


def test_fx_iniciar_regeneracion_dos_veces_conserva_cadencia():
    motor, actor = _fx_actor(vida=40, vida_max=50)
    estado = motor.iniciar_regeneracion(actor, 5)
    pulso = estado.evento
    assert motor.iniciar_regeneracion(actor, 5) is estado
    assert estado.evento is pulso and motor.agenda.siguiente_secuencia == 1


def test_fx_trampa_dano_se_aplica_durante_movimiento_sin_evento_extra():
    trampa = Trampa("t-01", "dano", 4)
    motor, jugador, _, destino, salida, _ = _fx_movimiento([trampa])
    ejecutados = []
    def ejecutar(evento):
        ejecutados.append(evento.tipo)
        motor.ejecutar_evento(evento, jugador)
    motor.mover_jugador(jugador, salida, ejecutar)
    assert jugador.sala_actual is destino and jugador.vida == 96
    assert ejecutados == []
    assert not trampa.armada and trampa.evento_rearme.tiempo == 300


def test_fx_trampa_desarmada_no_repite_y_rearme_no_ataca_ocupante():
    trampa = Trampa("t-01", "dano", 4)
    motor, jugador, _, _, salida, regreso = _fx_movimiento([trampa])
    def ejecutar(evento):
        motor.ejecutar_evento(evento, jugador)
    motor.mover_jugador(jugador, salida, ejecutar)
    motor.mover_jugador(jugador, regreso, ejecutar)
    motor.mover_jugador(jugador, salida, ejecutar)
    assert motor.reloj == 300 and jugador.vida == 96 and trampa.armada
    motor.mover_jugador(jugador, regreso, ejecutar)
    motor.mover_jugador(jugador, salida, ejecutar)
    assert jugador.vida == 92 and trampa.evento_rearme.tiempo == 700


def test_fx_trampa_respeta_rearme_personalizado():
    trampa = Trampa("t-01", "dano", 4, rearme=50)
    motor, jugador, _, _, salida, _ = _fx_movimiento([trampa])
    motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    )
    assert trampa.armada and trampa.evento_rearme is None
    assert jugador.vida == 96


def test_fx_trampa_veneno_programa_pulsos_sin_dano_inmediato():
    trampa = Trampa("t-01", "veneno", 3)
    motor, jugador, _, _, salida, _ = _fx_movimiento([trampa])
    motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    )
    assert jugador.vida == 97
    assert jugador.veneno.fin == 400
    assert jugador.veneno.evento.tiempo == 160


def test_fx_trampa_velocidad_reajusta_turno_del_movimiento():
    trampa = Trampa("t-01", "velocidad", 200, duracion=30)
    motor, jugador, _, _, salida, _ = _fx_movimiento([trampa])
    motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    )
    assert motor.reloj == 70
    assert jugador.velocidad == 100 and jugador.efecto_velocidad is None
    assert jugador.vida == 100


def test_fx_trampa_mortal_detiene_juego_y_rearme_es_independiente():
    trampa = Trampa("t-01", "dano", 200)
    motor, jugador, _, destino, salida, _ = _fx_movimiento([trampa])
    assert motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    ) is None
    assert jugador.vida == 0 and motor.reloj == 0
    assert jugador.sala_actual is destino
    # Procesamiento directo para verificar el evento de entorno; la partida ya terminó.
    evento = motor.siguiente_evento()
    assert evento.tipo == "rearme_trampa"
    motor.ejecutar_evento(evento, jugador)
    assert trampa.armada and jugador.vida == 0


def test_fx_retroceso_movimiento_restaura_trampa_y_cancela_rearme():
    trampa = Trampa("t-01", "dano", 4)
    motor, jugador, origen, destino, salida, _ = _fx_movimiento([trampa])
    inicial = jugador.proxima_accion
    motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    )
    assert motor.deshacer_ultima_accion()
    assert jugador.sala_actual is origen and jugador.vida == 100
    assert jugador.proxima_accion is inicial and motor.reloj == 0
    assert trampa.armada and trampa.evento_rearme is None
    assert destino.ultimo_rastro is None and destino.contenido_cargado
    assert motor.siguiente_evento() is inicial
    assert motor.siguiente_evento() is None


def test_fx_retroceso_del_rearme_recupera_evento_pendiente():
    trampa = Trampa("t-01", "dano", 4)
    motor, jugador, _, _, salida, _ = _fx_movimiento([trampa])
    def ejecutar(evento):
        motor.ejecutar_evento(evento, jugador)
    motor.mover_jugador(jugador, salida, ejecutar)
    rearme = trampa.evento_rearme
    motor.esperar_jugador(jugador, ejecutar)
    motor.esperar_jugador(jugador, ejecutar)
    assert motor.reloj == 300 and trampa.armada
    assert motor.deshacer_ultima_accion()
    assert motor.reloj == 200 and not trampa.armada
    assert trampa.evento_rearme is rearme
    motor.esperar_jugador(jugador, ejecutar)
    assert trampa.armada


def test_fx_varias_trampas_se_activan_en_orden_de_instancia():
    veneno = Trampa("t-01", "veneno", 1)
    mortal = Trampa("t-02", "dano", 200)
    motor, jugador, _, _, salida, _ = _fx_movimiento([mortal, veneno])
    motor.mover_jugador(
        jugador, salida, lambda evento: motor.ejecutar_evento(evento, jugador)
    )
    assert not veneno.armada and not mortal.armada
    assert jugador.vida == 0
    assert jugador.veneno.evento.cancelado


@pytest.mark.parametrize(
    "tipo,cantidad,duracion,rearme",
    [("otro", 1, None, 300), ("dano", 0, None, 300),
     ("dano", 1, None, 0), ("velocidad", 200, None, 300)],
)
def test_fx_trampa_invalida_se_rechaza(tipo, cantidad, duracion, rearme):
    with pytest.raises(ValueError):
        Trampa("t-01", tipo, cantidad, duracion=duracion, rearme=rearme)


@pytest.mark.parametrize("tipo", ["veneno", "antorcha", "regeneracion"])
def test_fx_parametros_invalidos_no_crean_eventos(tipo):
    motor, actor = _fx_actor()
    with pytest.raises(ValueError):
        if tipo == "veneno":
            motor.aplicar_veneno(actor, 0)
        elif tipo == "antorcha":
            motor.encender_antorcha(actor, 0)
        else:
            motor.iniciar_regeneracion(actor, 0)
    assert motor.agenda.heap == []
    assert actor.veneno is None and actor.antorcha is None
    assert actor.regeneracion is None
