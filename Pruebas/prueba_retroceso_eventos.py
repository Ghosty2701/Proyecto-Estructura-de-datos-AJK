from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento
from modelo.retroceso import HistorialRetroceso


def test_deshacer_cancelacion_recupera_evento():
    agenda = AgendaEventos()
    historial = HistorialRetroceso()
    evento = Evento(70, "ataque", "rata")
    agenda.insertar(evento)

    historial.iniciar_accion(50)
    historial.cancelar_evento(agenda, evento)

    assert evento.cancelado is True
    assert historial.deshacer_ultima() == 50
    assert evento.cancelado is False
    assert agenda.extraer_minimo() is evento


def test_deshacer_recupera_cancelado_que_fue_descartado():
    agenda = AgendaEventos()
    historial = HistorialRetroceso()
    evento = Evento(70, "ataque", "rata")
    agenda.insertar(evento)

    historial.iniciar_accion(50)
    historial.cancelar_evento(agenda, evento)

    # La extracción retira el cancelado del heap.
    assert historial.extraer_evento(agenda) is None

    historial.deshacer_ultima()

    assert evento.cancelado is False
    assert agenda.extraer_minimo() is evento


def test_deshacer_reprogramacion_recupera_evento_original():
    agenda = AgendaEventos()
    historial = HistorialRetroceso()
    original = Evento(70, "ataque", "rata")
    agenda.insertar(original)
    secuencia_original = original.secuencia

    historial.iniciar_accion(50)
    nuevo = Evento(90, "ataque", "rata")
    historial.reprogramar_evento(agenda, original, nuevo)

    assert original.cancelado is True
    assert historial.extraer_evento(agenda) is nuevo

    historial.deshacer_ultima()

    assert original.cancelado is False
    assert original.secuencia == secuencia_original
    assert agenda.extraer_minimo() is original
    assert agenda.extraer_minimo() is None
    assert agenda.siguiente_secuencia == 1


def test_deshacer_respeta_cancelacion_preexistente():
    agenda = AgendaEventos()
    historial = HistorialRetroceso()
    evento = Evento(70, "ataque", "rata")
    agenda.insertar(evento)
    agenda.cancelar(evento)

    historial.iniciar_accion(50)
    historial.cancelar_evento(agenda, evento)
    historial.deshacer_ultima()

    assert evento.cancelado is True
    assert agenda.extraer_minimo() is None


def test_historial_conserva_solo_cinco_acciones():
    historial = HistorialRetroceso()

    for reloj in range(6):
        historial.iniciar_accion(reloj)

    assert len(historial.acciones) == 5

    for reloj in range(5, 0, -1):
        assert historial.deshacer_ultima() == reloj

    assert historial.deshacer_ultima() is None  