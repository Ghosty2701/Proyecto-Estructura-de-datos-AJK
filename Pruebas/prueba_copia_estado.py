"""T002 — FR-LT-013/014, AC-LT-019/021: tabla de identidades y copia completa del estado."""
import random

import pytest

from adaptadores.copia_estado import TablaIdentidades, copiar_estado
from datos_linea_tiempo import crear_partida, escribir_paquete, instantanea, jugar
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro, SalidaRastro


class Clave:
    pass


def test_tabla_identidades_crece_y_resuelve_colisiones():
    # FR-LT-013: tabla propia, capacidad potencia de dos y carga máxima 70 %.
    tabla = TablaIdentidades()
    claves = [Clave() for _ in range(500)]
    for numero, clave in enumerate(claves):
        assert tabla.buscar(clave) is None
        tabla.insertar(clave, numero)
    assert tabla.cantidad == 500
    assert tabla.capacidad & (tabla.capacidad - 1) == 0
    assert tabla.cantidad * 10 <= tabla.capacidad * 7
    assert all(tabla.buscar(clave) == numero for numero, clave in enumerate(claves))
    assert tabla.buscar(Clave()) is None


def _anillo(cantidad):
    salas = [SalaRastro(numero) for numero in range(cantidad)]
    for numero, sala in enumerate(salas):
        sala.nombre = f"S{numero}"
        sala.objetos_suelo = []
        sala.contenido_cargado = True
        for direccion, salto in (("N", 1), ("S", -1)):
            salida = SalidaRastro(salas[(numero + salto) % cantidad])
            salida.direccion = direccion
            sala.salidas.append(salida)
    return salas


def test_copia_anillo_grande_sin_recursion_y_sin_compartir_mutables():
    # FR-LT-013: grafo con ciclos (anillo de 1 000 salas) sin RecursionError.
    salas = _anillo(1000)
    motor = MotorEventos(7)
    jugador = ActorTurnos("j", 50, 100)
    motor.iniciar_partida(jugador, salas[0])
    motor.azar.random()
    copia_motor, copia_jugador, copia_salas = copiar_estado((motor, jugador, salas))
    assert copia_salas is not salas and len(copia_salas) == 1000
    assert copia_jugador is not jugador and copia_jugador.sala_actual is copia_salas[0]
    assert copia_salas[0].salidas[0].destino is copia_salas[1]
    assert copia_salas[999].salidas[0].destino is copia_salas[0]
    assert copia_motor.azar is not motor.azar
    assert copia_motor.azar.getstate() == motor.azar.getstate()
    assert copia_motor.agenda is not motor.agenda
    assert copia_motor.agenda.heap[0] is not motor.agenda.heap[0]
    # Mutar la copia no altera el original.
    copia_jugador.vida = 1
    copia_salas[0].salidas.clear()
    copia_motor.azar.random()
    assert jugador.vida == 50 and len(salas[0].salidas) == 2
    assert copia_motor.azar.getstate() != motor.azar.getstate()


def test_copia_comparte_referencias_e_inmutables():
    # FR-LT-013: una puerta compartida sigue siendo un solo objeto en la copia.
    salas = _anillo(3)
    puerta = salas[0].salidas[0].puerta
    salas[1].salidas[1].puerta = puerta
    copia = copiar_estado(salas)
    assert copia[0].salidas[0].puerta is copia[1].salidas[1].puerta
    assert copia[0].salidas[0].puerta is not puerta
    assert copia[0].nombre is salas[0].nombre  # texto inmutable compartido


def test_copia_rechaza_tipos_sin_esquema():
    with pytest.raises(TypeError, match="esquema"):
        copiar_estado([object()])


@pytest.fixture
def partida_jugada(tmp_path):
    carpeta = escribir_paquete(tmp_path / "datos")
    partida, cargador = crear_partida(carpeta, tmp_path / "cache")
    jugar(partida)
    return partida, cargador


def test_copia_de_partida_real_es_equivalente_e_independiente(partida_jugada):
    # FR-LT-013/014, AC-LT-021: misma observación; enlaces excluidos; azar por estado.
    partida, cargador = partida_jugada
    salas = cargador.salas_ordenadas()
    copia, copia_salas = copiar_estado((partida, salas))
    assert copia is not partida and copia.motor is not partida.motor
    assert instantanea(copia) == instantanea(partida)
    assert copia.motor.azar.getstate() == partida.motor.azar.getstate()
    assert copia.preparar_sala is None and copia.gestor_guardado is None and copia.fuente is None
    assert getattr(copia, "linea_tiempo", None) is None
    assert all(e.ultima_ruta is None for e in copia.enemigos)
    assert {s.sala_id for s in copia_salas} == {s.sala_id for s in salas}
    # El historial de retroceso también se copia y apunta a objetos de la copia.
    assert len(copia.motor.historial.acciones) == len(partida.motor.historial.acciones)
    # Continuar la copia no altera la partida original.
    antes = instantanea(partida)
    copia.preparar_sala = lambda sala: None
    copia.esperar()
    assert instantanea(partida) == antes
    assert copia.motor.reloj > partida.motor.reloj


def test_copia_avanza_igual_que_el_original(partida_jugada):
    # FR-LT-014: copiar y seguir jugando produce el mismo resultado que el original.
    partida, cargador = partida_jugada
    copia, _ = copiar_estado((partida, cargador.salas_ordenadas()))
    copia.preparar_sala = lambda sala: None
    for juego in (partida, copia):
        juego.esperar()
        juego.esperar()
    assert instantanea(copia) == instantanea(partida)
    assert copia.motor.azar.getstate() == partida.motor.azar.getstate()


def test_copia_de_random_conserva_secuencia():
    azar = random.Random(11)
    azar.random()
    copia = copiar_estado([azar])[0]
    assert copia is not azar and [copia.random() for _ in range(3)] == [azar.random() for _ in range(3)]
