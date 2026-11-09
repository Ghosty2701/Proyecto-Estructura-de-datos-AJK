"""AC-TC-001 a 005: FR-TC-001 a 004, terreno y reloj virtual."""
import pytest

from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro, SalidaRastro


@pytest.mark.parametrize('costo,velocidad,intervalo', [(100, 100, 100), (250, 125, 200), (1, 500, 1)])
def test_ac001_003_movimiento_programa_el_intervalo_de_la_salida(costo, velocidad, intervalo):
    origen, destino = SalaRastro(1), SalaRastro(2)
    origen.contenido_cargado = destino.contenido_cargado = True
    salida = SalidaRastro(destino, costo=costo)
    origen.salidas.append(salida)
    motor, jugador = MotorEventos(2026), ActorTurnos('j', 100, velocidad)
    motor.iniciar_partida(jugador, origen)
    motor.mover_jugador(jugador, salida, lambda e: motor.ejecutar_evento(e, jugador))
    assert motor.reloj == intervalo
    assert jugador.sala_actual is destino


def test_ac004_velocidad_reescala_solo_tiempo_restante():
    motor, actor = MotorEventos(), ActorTurnos('a', 100, 100)
    motor.programar_accion(actor, 300)
    motor.reloj = 100
    motor.cambiar_velocidad(actor, 200)
    assert actor.proxima_accion.tiempo == 200


@pytest.mark.parametrize('comportamiento', ['errante', 'rastreador', 'cazador'])
def test_ac002_005_movimiento_enemigo_y_espera_conservan_sus_costos(comportamiento):
    a, b = SalaRastro(1), SalaRastro(2)
    a.salidas.append(SalidaRastro(b, costo=250))
    b.ultimo_rastro = 0
    enemigo = ActorTurnos('e', 20, 125, comportamiento=comportamiento,
                         rango=250 if comportamiento == 'cazador' else None)
    enemigo.sala_actual = a
    jugador = ActorTurnos('j', 100, 100)
    jugador.sala_actual = b
    motor = MotorEventos(2026)
    motor.programar_accion(enemigo, 0)
    evento = motor.siguiente_evento()
    inicio = motor.reloj
    motor.ejecutar_enemigo(evento, jugador)
    assert enemigo.sala_actual is b
    assert enemigo.proxima_accion.tiempo - inicio == 200


def test_ac001_costo_omitido_y_costos_invalidos():
    destino = SalaRastro(2)
    assert SalidaRastro(destino).costo == 100
    for invalido in (0, -1, True, 1.5, '100'):
        with pytest.raises(ValueError):
            SalidaRastro(destino, costo=invalido)


def test_cargador_conserva_costo_y_comparte_estado_de_puerta():
    # FR-TC-001/010/014: simetria de datos normalizados, sin red.
    from types import SimpleNamespace
    from adaptadores.cache_catalogo import ArbolAVL
    from controlador.cargar_partida import CargadorPartida, ErrorDatosPartida
    arbol = ArbolAVL()
    for clave, direccion, destino in ((1, 'E', 2), (2, 'O', 1)):
        arbol.insertar(clave, {'id': clave, 'nombre': 'Sala', 'salidas': {
            direccion: {'sala': destino, 'costo': 250, 'cerrada': True, 'llave': 'k'}}})
    cargador = CargadorPartida(SimpleNamespace(esqueleto=arbol, cache=SimpleNamespace()))
    cargador._construir_esqueleto()
    ida = cargador.salas.buscar(1).salidas[0]
    vuelta = cargador.salas.buscar(2).salidas[0]
    assert ida.costo == vuelta.costo == 250
    assert ida.puerta is vuelta.puerta
    ida.abierta = True
    assert vuelta.abierta
    arbol.buscar(2)['salidas']['O']['costo'] = 100
    otro = CargadorPartida(SimpleNamespace(esqueleto=arbol, cache=SimpleNamespace()))
    with pytest.raises(ErrorDatosPartida):
        otro._construir_esqueleto()
