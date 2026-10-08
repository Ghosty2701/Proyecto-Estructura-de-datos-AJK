from modelo.agenda_eventos import (
    AgendaEventos,
    tiempo_proxima_accion,
    tiempo_por_cambio_velocidad,
)
from modelo.evento import Evento
from modelo.retroceso import HistorialRetroceso

class ActorTurnos:
    def __init__(self, actor_id, vida, velocidad):
        if vida <= 0 or velocidad <= 0:
            raise ValueError("Vida y velocidad deben ser positivas")

        self.actor_id = actor_id
        self.vida = vida
        self.velocidad = velocidad

        self.proxima_accion = None
        self.primer_evento = None
        self.sala_actual = None
        self.inventario = None

class EventoActor(Evento):
    def __init__(self, tiempo, tipo, actor):
        super().__init__(tiempo, tipo, actor.actor_id)
        self.actor = actor
        self.anterior = None
        self.siguiente = None
        self.enlazado = False
        self.sala_actual = None


class MotorEventos:
    def __init__(self):
        self.reloj = 0
        self.agenda = AgendaEventos()
        self.historial = HistorialRetroceso()

    def iniciar_accion(self):
        self.historial.iniciar_accion(self.reloj)

    def _cambiar(self, objeto, nombre, valor):
        if self.historial.acciones:
            self.historial.registrar_atributo(objeto, nombre)

        setattr(objeto, nombre, valor)

    def _enlazar(self, evento):
        actor = evento.actor
        primero = actor.primer_evento

        self._cambiar(evento, "siguiente", primero)

        if primero is not None:
            self._cambiar(primero, "anterior", evento)

        self._cambiar(actor, "primer_evento", evento)
        self._cambiar(evento, "enlazado", True)

    def _desenlazar(self, evento):
        if not evento.enlazado:
            return

        actor = evento.actor
        anterior = evento.anterior
        siguiente = evento.siguiente

        if anterior is None:
            self._cambiar(actor, "primer_evento", siguiente)
        else:
            self._cambiar(anterior, "siguiente", siguiente)

        if siguiente is not None:
            self._cambiar(siguiente, "anterior", anterior)

        self._cambiar(evento, "anterior", None)
        self._cambiar(evento, "siguiente", None)
        self._cambiar(evento, "enlazado", False)

        if actor.proxima_accion is evento:
            self._cambiar(actor, "proxima_accion", None)

    def programar_evento(self, actor, tiempo, tipo):
        if actor.vida <= 0:
            raise ValueError("Un actor muerto no puede programar eventos")

        if tiempo < self.reloj:
            raise ValueError("No se puede programar un evento en el pasado")

        evento = EventoActor(tiempo, tipo, actor)

        if self.historial.acciones:
            self.historial.programar_evento(self.agenda, evento)
        else:
            self.agenda.insertar(evento)

        self._enlazar(evento)
        return evento

    def cancelar_evento(self, evento):
        if self.historial.acciones:
            self.historial.cancelar_evento(self.agenda, evento)
        else:
            self.agenda.cancelar(evento)

    def programar_accion(self, actor, costo):
        pendiente = actor.proxima_accion

        if pendiente is not None and not pendiente.cancelado:
            raise ValueError("El actor ya tiene una acción pendiente")

        tiempo = tiempo_proxima_accion(
            self.reloj,
            costo,
            actor.velocidad,
        )

        evento = self.programar_evento(actor, tiempo, "accion")
        self._cambiar(actor, "proxima_accion", evento)
        return evento
    
    def ubicar_jugador_inicial(self, jugador, sala):
        if self.reloj != 0 or self.historial.acciones:
            raise ValueError("La ubicación inicial se establece al comenzar")

        if jugador.sala_actual is not None:
            raise ValueError("El jugador ya tiene una ubicación inicial")

        jugador.sala_actual = sala
        sala.ultimo_rastro = 0

    def refrescar_rastro_jugador(self, jugador):
        if not self.historial.acciones:
            raise RuntimeError("Primero debes iniciar la acción del jugador")

        if jugador.sala_actual is None:
            raise ValueError("El jugador no tiene sala actual")

        self._cambiar(
            jugador.sala_actual,
            "ultimo_rastro",
            self.reloj,
        )

    def completar_movimiento_jugador(self, jugador, destino):
        if not self.historial.acciones:
            raise RuntimeError("Primero debes iniciar la acción del jugador")

        if jugador.sala_actual is None:
            raise ValueError("El jugador no tiene sala actual")

        self._cambiar(jugador, "sala_actual", destino)
        self.refrescar_rastro_jugador(jugador)
        
    def programar_primera_accion_jugador(self, actor):
        if self.reloj != 0:
            raise ValueError("La primera acción se programa al iniciar")

        pendiente = actor.proxima_accion

        if pendiente is not None and not pendiente.cancelado:
            raise ValueError("El jugador ya tiene una acción pendiente")

        evento = self.programar_evento(actor, 0, "accion")
        self._cambiar(actor, "proxima_accion", evento)
        return evento

    def cambiar_velocidad(self, actor, velocidad_nueva):
        if velocidad_nueva <= 0:
            raise ValueError("La velocidad debe ser positiva")

        if actor.vida <= 0:
            raise ValueError("No se puede reajustar un actor muerto")

        anterior = actor.proxima_accion

        if anterior is not None and not anterior.cancelado:
            tiempo = tiempo_por_cambio_velocidad(
                anterior.tiempo,
                self.reloj,
                actor.velocidad,
                velocidad_nueva,
            )

            nuevo = self.programar_evento(actor, tiempo, anterior.tipo)
            self.cancelar_evento(anterior)
            self._cambiar(actor, "proxima_accion", nuevo)

        self._cambiar(actor, "velocidad", velocidad_nueva)
        return actor.proxima_accion

    def matar_actor(self, actor):
        self._cambiar(actor, "vida", 0)

        evento = actor.primer_evento

        while evento is not None:
            self.cancelar_evento(evento)
            evento = evento.siguiente

        self._cambiar(actor, "proxima_accion", None)

    def siguiente_evento(self):
        while True:
            if self.historial.acciones:
                evento = self.historial.extraer_evento_bruto(self.agenda)
            else:
                evento = self.agenda._extraer_raiz()

            if evento is None:
                return None

            self._desenlazar(evento)

            if evento.cancelado or evento.actor.vida <= 0:
                continue

            self._cambiar(self, "reloj", evento.tiempo)
            return evento

    def deshacer_ultima_accion(self):
        reloj_anterior = self.historial.deshacer_ultima()

        if reloj_anterior is None:
            return False

        self.reloj = reloj_anterior
        return True
    
    def usar_pergamino(self, jugador, es_pergamino):
        if not self.historial.acciones:
            return False

        if jugador.inventario is None:
            raise ValueError("El jugador no tiene inventario asignado")

        if not jugador.inventario.consumir_primero(es_pergamino):
            return False

        return self.deshacer_ultima_accion()