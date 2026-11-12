"""FR-TC-011/014: reutilización entre actores sin modificar decisiones."""
import random
import weakref

import pytest

from modelo.cache_rutas import CacheRutas
from modelo.rutas import ResultadoRuta, buscar_ruta
from modelo.motor_eventos import ActorTurnos
from modelo.rastro import SalaRastro
from prueba_rutas import preparar_cazador, conectar
from datos_linea_tiempo import escribir_paquete, crear_partida
from adaptadores.copia_estado import copiar_estado


def registro(origen, objetivo, rango=300, revision=0):
    resultado = ResultadoRuta(origen, objetivo, rango)
    resultado.revision_conexiones = revision
    return resultado


def test_colisiones_limite_y_liberacion(monkeypatch):
    monkeypatch.setattr('modelo.cache_rutas._mezclar', lambda n: 0)
    cache = CacheRutas(8)
    salas = [SalaRastro(i) for i in range(7)]
    for sala in salas[1:6]:
        cache.insertar(registro(salas[0], sala))
    primero = cache.obtener(salas[0], salas[1], 300, 0)
    ref = weakref.ref(primero)
    del primero
    assert cache.cantidad == 5
    assert cache.obtener(salas[0], salas[5], 300, 0) is not None
    cache.insertar(registro(salas[0], salas[6]))
    assert cache.cantidad == 1 and cache.capacidad == 8 and cache.reinicios == 1
    assert cache.obtener(salas[0], salas[1], 300, 0) is None
    assert ref() is None


def test_identidad_rango_revision_y_actualizacion():
    a, b = SalaRastro(1), SalaRastro(2)
    cache = CacheRutas()
    primero = registro(a, b)
    cache.insertar(primero)
    assert cache.obtener(a, b, 300, 0) is primero  # también resultado negativo
    assert cache.obtener(SalaRastro(1), b, 300, 0) is None
    assert cache.obtener(a, b, 299, 0) is None
    assert cache.obtener(a, b, 300, 1) is None
    nuevo = registro(a, b)
    cache.insertar(nuevo)
    assert cache.cantidad == 1 and cache.obtener(a, b, 300, 0) is nuevo


@pytest.mark.parametrize('capacidad', [0, 7, 9, True, 8.0])
def test_rechaza_capacidad_invalida(capacidad):
    with pytest.raises(ValueError):
        CacheRutas(capacidad)


def test_cazadores_comparten_resultados_y_cambios_invalidan(monkeypatch):
    motor, primero, jugador, (a, b, c) = preparar_cazador()
    segundo = ActorTurnos('otro', 100, 100, comportamiento='cazador', rango=300)
    segundo.sala_actual = a
    llamadas = []

    def buscar(*args):
        llamadas.append(1)
        return buscar_ruta(*args)

    monkeypatch.setattr('modelo.motor_eventos.buscar_ruta', buscar)
    original = motor.ruta_cazador(primero, jugador)
    assert motor.ruta_cazador(segundo, jugador) is original
    assert len(llamadas) == 1 and motor.cache_rutas.aciertos == 1
    motor.iniciar_accion()
    motor._cambiar(a.salidas[0], 'costo', 151)
    assert motor.cache_rutas.cantidad == 0
    assert not motor.ruta_cazador(segundo, jugador).encontrada
    assert motor.deshacer_ultima_accion()
    assert motor.cache_rutas.cantidad == 0
    assert motor.ruta_cazador(primero, jugador).costo_total == 300
    assert len(llamadas) == 3


def test_cache_equivale_a_calcular_desde_cero_en_mapa_con_empates():
    motor, actor, jugador, _ = preparar_cazador()
    salas = [SalaRastro(i) for i in range(15)]
    azar = random.Random(2026)
    for i in range(14):
        conectar(salas[i], salas[i + 1], azar.choice((50, 100, 150)))
    for _ in range(30):
        a, b = azar.sample(salas, 2)
        conectar(a, b, azar.choice((50, 100, 150)), abierta=azar.choice((True, False)))
    estado_azar = motor.azar.getstate()
    for _ in range(250):
        actor.sala_actual, jugador.sala_actual = azar.sample(salas, 2)
        actor.rango = azar.choice((0, 100, 300, 1000))
        esperado = buscar_ruta(actor.sala_actual, jugador.sala_actual, actor.rango)
        real = motor.ruta_cazador(actor, jugador)
        assert (real.encontrada, real.costo_total, real.primer_paso) == (
            esperado.encontrada, esperado.costo_total, esperado.primer_paso)
    assert motor.reloj == 0 and motor.azar.getstate() == estado_azar


def test_copia_y_guardado_cargan_cache_vacia(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    for sala in c.salas_ordenadas():
        c.preparar_sala(sala)
    cazador = next(e for e in p.enemigos if e.comportamiento == 'cazador')
    p.motor.ruta_cazador(cazador, p.jugador)
    assert p.motor.cache_rutas.cantidad == 1
    copia, _ = copiar_estado((p, c.salas_ordenadas()))
    assert copia.motor.cache_rutas.cantidad == 0
    punto = p.linea_tiempo.copiar((p, c.salas_ordenadas()))
    copia, _ = punto.reconstruir()
    assert copia.motor.cache_rutas.cantidad == 0
    from adaptadores.estado_binario import codificar_punto, decodificar_punto
    bloque = codificar_punto(p.motor, p.jugador, c.salas_ordenadas(), c._identidad(p), {'partida': p})
    cargado = decodificar_punto(bloque, c._identidad(p))
    assert cargado.motor.cache_rutas.cantidad == 0
