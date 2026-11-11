"""Prototipo aprobado: FR-LT-013/014, aislamiento y metadatos inmutables."""
import pytest
from adaptadores.estado_compartido import ContextoCompartido
from datos_linea_tiempo import escribir_paquete, crear_partida, jugar, instantanea


def test_prototipo_conserva_estado_y_no_comparte_mutables(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    jugar(p)
    contexto = ContextoCompartido(p, c.salas_ordenadas())
    uno = contexto.capturar(p)
    dos = contexto.capturar(p)
    assert uno.plantilla is dos.plantilla
    copia, salas = uno.reconstruir()
    assert instantanea(copia) == instantanea(p)
    assert copia.motor.azar.getstate() == p.motor.azar.getstate()
    assert copia.jugador.sala_actual is next(s for s in salas if s.sala_id == p.jugador.sala_actual.sala_id)
    salas[0].salidas[0].puerta.abierta = not salas[0].salidas[0].puerta.abierta
    copia.jugador.vida = 1
    otra, otras = uno.reconstruir()
    assert instantanea(otra) == instantanea(p)
    assert otras[0].salidas[0].puerta is not salas[0].salidas[0].puerta
    assert otras[0].salidas[0].destino is otras[1]


def test_prototipo_detecta_cambio_de_metadatos(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    contexto = ContextoCompartido(p, c.salas_ordenadas())
    c.salas_ordenadas()[0].nombre = 'Cambio'
    with pytest.raises(ValueError, match='plantilla'):
        contexto.capturar(p)


def test_plantilla_solo_contiene_tuplas_y_escalares_y_capturas_independientes(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    ctx = ContextoCompartido(p, c.salas_ordenadas())
    punto = ctx.capturar(p)
    antes = instantanea(p)
    pendientes = [punto.plantilla]
    while pendientes:
        valor = pendientes.pop()
        if type(valor) is tuple:
            pendientes.extend(valor)
        else:
            assert type(valor) in (type(None), bool, int, float, str)
    from adaptadores.bench_persistencia import _ejecutar
    _ejecutar(p, 'esperar')
    nuevo = ctx.capturar(p)
    copia_anterior, _ = punto.reconstruir()
    copia_nueva, _ = nuevo.reconstruir()
    assert instantanea(copia_anterior) == antes
    assert instantanea(copia_nueva) == instantanea(p)
    assert punto.plantilla is nuevo.plantilla


def test_historia_experimental_equivalente_y_sin_efectos():
    from adaptadores.estado_compartido import medir_historia_compartida
    datos = medir_historia_compartida(acciones=12)
    assert [f['modo'] for f in datos['escenarios']] == ['normal', 'compartido']
    assert all(f['equivalentes'] and f['partida_intacta'] for f in datos['escenarios'])


def test_validacion_detecta_enlaces_pero_copia_costos_mutables(tmp_path):
    carpeta = escribir_paquete(tmp_path / 'datos')
    p, c = crear_partida(carpeta, tmp_path / 'cache')
    salas = c.salas_ordenadas()
    ctx = ContextoCompartido(p, salas)
    viejo = ctx.capturar(p)
    costo = salas[0].salidas[0].costo
    salas[0].salidas[0].costo = costo + 7
    nuevo = ctx.capturar(p)
    assert viejo.reconstruir()[1][0].salidas[0].costo == costo
    assert nuevo.reconstruir()[1][0].salidas[0].costo == costo + 7
    salas[0].salidas[0].destino = salas[0]
    with pytest.raises(ValueError, match='plantilla'):
        ctx.capturar(p)
