from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento
from modelo.retroceso import HistorialRetroceso

agenda = AgendaEventos()
historial = HistorialRetroceso()

historial.iniciar_accion(50)
historial.programar_evento(agenda, Evento(70, "ataque", "rata"))

print(agenda.siguiente_secuencia)  # 1
historial.deshacer_ultima()
print(agenda.siguiente_secuencia)  # 0
print(agenda.extraer_minimo())     # None

agenda = AgendaEventos()
agenda.insertar(Evento(70, "ataque", "rata"))

historial = HistorialRetroceso()
historial.iniciar_accion(50)

evento = historial.extraer_evento(agenda)
print(evento.tiempo, evento.secuencia)  # 70 0

historial.deshacer_ultima()
evento_restaurado = agenda.extraer_minimo()
print(evento_restaurado.tiempo, evento_restaurado.secuencia)  # 70 