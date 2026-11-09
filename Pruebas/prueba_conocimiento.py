"""FR-NV-001/002/003/005/006/007/016: conocimiento separado del mundo."""
from types import SimpleNamespace

import pytest

from modelo.conocimiento import ConocimientoMapa, IndiceSalas
from modelo.rastro import Puerta, SalaRastro, SalidaRastro
from modelo.motor_eventos import MotorEventos


def mapa(cantidad=4):
    salas = [SalaRastro(i * 100003 + 1) for i in range(cantidad)]
    for i, sala in enumerate(salas):
        sala.nombre = f"Sala {i}"
        sala.objetos_suelo = []
        sala.contenido_cargado = True
    for a, b in zip(salas, salas[1:]):
        puerta = Puerta()
        ida = SalidaRastro(b, puerta=puerta)
        vuelta = SalidaRastro(a, puerta=puerta)
        ida.direccion, vuelta.direccion = "N", "S"
        a.salidas.append(ida)
        b.salidas.append(vuelta)
    return salas


def test_indice_estatico_colisiones_ausencias_y_capacidad(monkeypatch):
    monkeypatch.setattr(IndiceSalas, '_inicio', lambda self, clave: 0)
    monkeypatch.setattr(IndiceSalas, '_paso', lambda self, clave: 1)
    indice = IndiceSalas([3, 1000000, 2**32 - 1])
    assert indice.capacidad == 8
    assert [indice.obtener(i) for i in (3, 1000000, 2**32 - 1)] == [0, 1, 2]
    assert indice.obtener(99) is None
    with pytest.raises(ValueError, match='duplicado'):
        IndiceSalas([3, 3])


def test_ac001_002_003_inicio_y_precarga_no_revelan():
    salas = mapa()
    motor = MotorEventos()
    conocimiento = ConocimientoMapa(salas)
    conocimiento.entrar(salas[0], False, motor._cambiar)
    assert [s.estado for s in conocimiento.salas] == [2, 1, 0, 0]
    assert conocimiento.salas[1].nombre is None
    assert conocimiento.salas[1].salidas == []
    assert salas[2].salidas[0].puerta.recuerdo.observada is None
    conocimiento.entrar(salas[1], False, motor._cambiar)
    assert [s.estado for s in conocimiento.salas] == [2, 2, 1, 0]


def test_ac004_005_memoria_compartida_y_cierre_remoto():
    salas = mapa()
    k = ConocimientoMapa(salas)
    m = MotorEventos()
    k.entrar(salas[0], False, m._cambiar)
    recuerdo = k.salas[0].salidas[0].puerta
    salas[0].salidas[0].abierta = False
    assert recuerdo.observada is True
    k.entrar(salas[1], False, m._cambiar)
    assert k.salas[1].salidas[0].puerta is recuerdo
    assert recuerdo.observada is False


def test_ac006_007_008_019_antorcha_no_recursiva_y_retroceso():
    salas = mapa(5)
    salas[1].salidas[-1].abierta = False
    enemigo = SimpleNamespace(activo=False)
    salas[2].enemigos.append(enemigo)
    k, m = ConocimientoMapa(salas), MotorEventos()
    k.entrar(salas[0], False, m._cambiar)
    m.iniciar_accion()
    k.entrar(salas[1], True, m._cambiar)
    assert [s.estado for s in k.salas] == [2, 2, 2, 1, 0]
    assert not enemigo.activo
    m.historial.acciones[-1].deshacer()
    assert [s.estado for s in k.salas] == [2, 1, 0, 0, 0]
    assert k.salas[1].nombre is None and not k.salas[1].salidas
    assert salas[1].salidas[-1].puerta.recuerdo.observada is None


def test_ac009_nombre_exacto_duplicados_y_ocultos():
    salas = mapa()
    k, m = ConocimientoMapa(salas), MotorEventos()
    salas[0].nombre = salas[-1].nombre = 'Biblioteca Grande'
    k.entrar(salas[0], False, m._cambiar)
    assert k.resolver('Biblioteca Grande') is k.salas[0]
    with pytest.raises(ValueError):
        k.resolver('biblioteca grande')
    k.entrar(salas[-1], False, m._cambiar)
    with pytest.raises(ValueError, match='ID'):
        k.resolver('Biblioteca Grande')
