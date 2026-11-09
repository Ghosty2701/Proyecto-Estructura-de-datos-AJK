"""AC-TC-006 a 015: FR-TC-005 a 011 y PR-TC-002."""
import pytest

from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import SalaRastro, SalidaRastro, Puerta
from modelo.rutas import buscar_ruta


def conectar(a, b, costo=100, abierta=True):
    puerta = Puerta(abierta)
    salida = SalidaRastro(b, puerta=puerta, costo=costo)
    a.salidas.append(salida)
    b.salidas.append(SalidaRastro(a, puerta=puerta, costo=costo))
    return salida


def test_ac009_ruta_mas_barata_no_es_la_de_menos_salas():
    a, b, c, d, objetivo = [SalaRastro(i) for i in range(5)]
    conectar(a, b, 200)
    conectar(b, objetivo, 200)
    conectar(a, c)
    conectar(c, d)
    conectar(d, objetivo)
    resultado = buscar_ruta(a, objetivo, 300)
    assert resultado.encontrada
    assert (resultado.primer_paso.destino, resultado.costo_total) == (c, 300)
    assert not a.contenido_cargado  # AC-TC-011: solo esqueleto.


@pytest.mark.parametrize('rango,encontrada', [(599, False), (600, True)])
def test_ac007_008_rango_y_sin_ruta(rango, encontrada):
    a, b = SalaRastro(1), SalaRastro(2)
    salida = conectar(a, b, 600)
    assert buscar_ruta(a, b, rango).encontrada is encontrada
    salida.abierta = False
    assert not buscar_ruta(a, b, 1000).encontrada


def test_ac010_mejorar_primer_salto_con_igual_costo():
    a, menor, mayor, puente, destino = [SalaRastro(i) for i in (1, 3, 8, 10, 20)]
    conectar(a, mayor, 1)
    conectar(mayor, puente, 9)
    conectar(a, menor, 5)
    conectar(menor, puente, 5)
    conectar(puente, destino, 1)
    resultado = buscar_ruta(a, destino, 11)
    assert (resultado.primer_paso.destino.sala_id, resultado.costo_total) == (3, 11)
    a.salidas.reverse()
    assert buscar_ruta(a, destino, 11).primer_paso.destino is menor


def preparar_cazador(rango=300):
    a, b, c = [SalaRastro(i) for i in (1, 2, 3)]
    conectar(a, b, 150)
    conectar(b, c, 150)
    cazador = ActorTurnos('c', 100, 100, ataque=5, comportamiento='cazador', rango=rango)
    jugador = ActorTurnos('j', 100, 100)
    cazador.sala_actual, jugador.sala_actual = a, c
    return MotorEventos(2026), cazador, jugador, (a, b, c)


def turno(motor, actor, jugador):
    motor.programar_accion(actor, 0)
    evento = motor.siguiente_evento()
    inicio = motor.reloj
    motor.ejecutar_enemigo(evento, jugador)
    return actor.proxima_accion.tiempo - inicio


def test_ac006_008_turno_cazador_mueve_espera_ataca():
    motor, actor, jugador, salas = preparar_cazador()
    azar = motor.azar.getstate()
    assert turno(motor, actor, jugador) == 150
    assert actor.sala_actual is salas[1]
    assert motor.azar.getstate() == azar
    motor, actor, jugador, salas = preparar_cazador(299)
    assert turno(motor, actor, jugador) == 100
    assert actor.sala_actual is salas[0]
    jugador.sala_actual = actor.sala_actual
    # Atacar tiene prioridad incluso si el rango no permite ninguna salida.
    actor.rango = -1
    evento = motor.siguiente_evento()
    motor.ejecutar_enemigo(evento, jugador)
    assert jugador.vida < 100


def test_no_se_recibe_un_rango_inventado():
    with pytest.raises(ValueError):
        ActorTurnos('c', 20, 100, comportamiento='cazador')


def test_ac011_buscar_no_altera_estado_azar_ni_reloj():
    motor, actor, jugador, salas = preparar_cazador()
    azar = motor.azar.getstate()
    for _ in range(2):
        assert buscar_ruta(actor.sala_actual, jugador.sala_actual, actor.rango).encontrada
    assert motor.reloj == 0 and motor.azar.getstate() == azar
    assert actor.sala_actual is salas[0]


def test_ac012_013_puertas_reutilizacion_y_cierre_automatico(monkeypatch):
    motor, actor, jugador, (a, b, c) = preparar_cazador(1000)
    d = SalaRastro(4)
    atajo = conectar(a, d, 10, abierta=False)
    conectar(d, c, 10)
    llamadas = []
    def contar(*argumentos):
        llamadas.append(1)
        return buscar_ruta(*argumentos)
    monkeypatch.setattr('modelo.motor_eventos.buscar_ruta', contar)
    original = motor.ruta_cazador(actor, jugador)
    assert original.costo_total == 300
    assert motor.ruta_cazador(actor, jugador) is original
    assert len(llamadas) == 1
    # Abrir una puerta fuera de la ruta anterior crea otra mejor.
    motor._cambiar(atajo.puerta, 'abierta', True)
    nueva = motor.ruta_cazador(actor, jugador)
    assert (nueva.primer_paso.destino, nueva.costo_total) == (d, 20)
    evento = motor.programar_evento_entorno(atajo.puerta, 0, 'cierre_puerta')
    motor.ejecutar_evento(evento, jugador)
    assert motor.ruta_cazador(actor, jugador).costo_total == 300
    assert len(llamadas) == 3


def test_ac014_015_cambios_de_actores_y_objetivo():
    motor, actor, jugador, (a, b, c) = preparar_cazador()
    original = motor.ruta_cazador(actor, jugador)
    motor.cambiar_velocidad(actor, 200)
    motor._cambiar(jugador, 'vida', 99)
    assert motor.ruta_cazador(actor, jugador) is original
    jugador.sala_actual = b
    assert motor.ruta_cazador(actor, jugador).costo_total == 150
    actor.sala_actual = b
    assert motor.ruta_cazador(actor, jugador).costo_total == 0
    actor.rango = 0
    jugador.sala_actual = c
    assert not motor.ruta_cazador(actor, jugador).encontrada


def test_ac019_retroceso_no_revalida_un_resultado_de_otra_historia():
    motor, actor, jugador, (a, b, c) = preparar_cazador()
    puerta = b.salidas[-1].puerta
    original = motor.ruta_cazador(actor, jugador)
    motor.iniciar_accion()
    motor._cambiar(puerta, 'abierta', False)
    assert not motor.ruta_cazador(actor, jugador).encontrada
    revision = motor.revision_conexiones
    assert motor.deshacer_ultima_accion()
    restaurada = motor.ruta_cazador(actor, jugador)
    assert motor.revision_conexiones > revision
    assert restaurada is not original
    assert restaurada.costo_total == original.costo_total
    assert restaurada.primer_paso is original.primer_paso


def test_pr002_mapa_no_visitado_no_incrementa_la_busqueda():
    origen, destino = SalaRastro(1), SalaRastro(2)
    conectar(origen, destino)
    corta = buscar_ruta(origen, destino, 100)
    lejanas = [SalaRastro(i) for i in range(3, 1003)]
    conectar(origen, lejanas[0], 10000)
    for a, b in zip(lejanas, lejanas[1:]):
        conectar(a, b)
    grande = buscar_ruta(origen, destino, 100)
    assert corta.salas_examinadas == grande.salas_examinadas == 2
    assert grande.salidas_examinadas == corta.salidas_examinadas + 1
