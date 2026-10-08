import pytest

from modelo.agenda_eventos import (
    AgendaEventos,
    tiempo_proxima_accion,
    tiempo_por_cambio_velocidad,
)
from modelo.evento import Evento


def test_extrae_por_tiempo_y_luego_por_secuencia():
    agenda = AgendaEventos()
    eventos = [
        Evento(t, "ataque", i)
        for i, t in enumerate([30, 10, 20, 10])
    ]

    for evento in eventos:
        agenda.insertar(evento)

    assert [agenda.extraer_minimo() for _ in eventos] == [
        eventos[1],
        eventos[3],
        eventos[2],
        eventos[0],
    ]
    assert agenda.extraer_minimo() is None


def test_cancelado_no_se_ejecuta():
    agenda = AgendaEventos()
    primero = Evento(10, "ataque", "rata")
    segundo = Evento(20, "ataque", "jugador")

    agenda.insertar(primero)
    agenda.insertar(segundo)
    agenda.cancelar(primero)

    assert agenda.extraer_minimo() is segundo
    assert agenda.extraer_minimo() is None


def test_reprogramacion_recibe_secuencia_nueva():
    agenda = AgendaEventos()
    anterior = Evento(20, "ataque", "rata")
    otro = Evento(10, "ataque", "jugador")
    nuevo = Evento(10, "ataque", "rata")

    agenda.insertar(anterior)
    agenda.insertar(otro)
    agenda.reprogramar(anterior, nuevo)

    assert nuevo.secuencia == 2
    assert agenda.extraer_minimo() is otro
    assert agenda.extraer_minimo() is nuevo
    assert agenda.extraer_minimo() is None


def test_no_permite_reutilizar_evento():
    agenda = AgendaEventos()
    evento = Evento(10, "ataque", "rata")
    agenda.insertar(evento)

    with pytest.raises(ValueError):
        agenda.insertar(evento)

    with pytest.raises(ValueError):
        agenda.reprogramar(evento, evento)

    assert not evento.cancelado
    assert agenda.extraer_minimo() is evento
    assert agenda.extraer_minimo() is None


def test_reprogramacion_invalida_no_cancela_original():
    agenda = AgendaEventos()
    original = Evento(10, "ataque", "rata")
    ocupado = Evento(20, "ataque", "otra")

    agenda.insertar(original)
    agenda.insertar(ocupado)

    with pytest.raises(ValueError):
        agenda.reprogramar(original, ocupado)

    assert not original.cancelado
    assert agenda.extraer_minimo() is original


def test_restauracion_conserva_secuencia():
    agenda = AgendaEventos()
    evento = Evento(10, "ataque", "rata")

    agenda.insertar(evento)
    assert agenda.extraer_minimo() is evento

    agenda.insertar(evento, conservar_secuencia=True)

    assert evento.secuencia == 0
    assert agenda.siguiente_secuencia == 1
    assert agenda.extraer_minimo() is evento


def test_tiempos_del_enunciado():
    assert tiempo_proxima_accion(0, 100, 150) == 66
    assert tiempo_proxima_accion(50, 100, 100) == 150

    # Aceleración.
    assert tiempo_por_cambio_velocidad(100, 40, 100, 200) == 70

    # Ralentización.
    assert tiempo_por_cambio_velocidad(100, 40, 100, 50) == 160

    # El intervalo mínimo es una unidad.
    assert tiempo_por_cambio_velocidad(40, 40, 100, 200) == 41