from modelo.efectos import MotorEfectos
from modelo.agenda_eventos import (
    AgendaEventos,
    tiempo_proxima_accion,
    tiempo_por_cambio_velocidad,
)
from modelo.evento import Evento
from modelo.retroceso import HistorialRetroceso
from modelo.rastro import elegir_destino_rastreador
from comun.ordenamiento import vista_ordenada
import random

class ActorTurnos:
    def __init__(
        self, actor_id, vida, velocidad, *, ataque=0, defensa=0,
        comportamiento=None, vida_max=None, regeneracion=0,
    ):
        if vida <= 0 or velocidad <= 0:
            raise ValueError("Vida y velocidad deben ser positivas")
        if ataque < 0 or defensa < 0:
            raise ValueError("Ataque y defensa deben ser no negativos")
        if comportamiento not in (None, "guardian", "rastreador", "errante"):
            raise ValueError("Comportamiento desconocido")
        if vida_max is None:
            vida_max = vida
        if type(vida_max) is not int or vida_max < vida:
            raise ValueError("vida_max debe ser un entero no menor que vida")
        if type(regeneracion) is not int or regeneracion < 0:
            raise ValueError("regeneracion debe ser un entero no negativo")
        self.actor_id = actor_id
        self.vida = vida
        self.vida_max = vida_max
        self.velocidad = velocidad
        self.ataque = ataque
        self.defensa = defensa
        self.comportamiento = comportamiento
        self.activo = False
        self.proxima_accion = None
        self.primer_evento = None
        self.sala_actual = None
        self.inventario = None
        self.veneno = None
        self.efecto_velocidad = None
        self.antorcha = None
        self.regeneracion = None
        self.regeneracion_cantidad = regeneracion

class EventoActor(Evento):
    def __init__(self, tiempo, tipo, actor):
        super().__init__(tiempo, tipo, actor.actor_id)
        self.actor = actor
        self.anterior = None
        self.siguiente = None
        self.enlazado = False
        self.efecto = None
        self.sala_actual = None
        
class EventoEntorno(Evento):
    def __init__(self, tiempo, tipo, objetivo):
        super().__init__(tiempo, tipo, None)
        self.actor = None
        self.objetivo = objetivo


class MotorEventos(MotorEfectos):
    def __init__(self, semilla=0):
        self.reloj = 0
        self.agenda = AgendaEventos()
        self.historial = HistorialRetroceso()
        self.semilla = semilla
        self.azar = random.Random(semilla)

    def iniciar_accion(self):
        self.historial.iniciar_accion(self.reloj)
        self.historial.registrar_azar(self.azar)

    def _cambiar(self, objeto, nombre, valor):
        if getattr(objeto, nombre) is valor:
            return

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
        if self.consultar_siguiente_evento() is None:
            return None

        if self.historial.acciones:
            evento = self.historial.extraer_evento_bruto(self.agenda)
        else:
            evento = self.agenda._extraer_raiz()

        if evento.actor is not None:
            self._desenlazar(evento)

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
    
    def consultar_siguiente_evento(self):
        while self.agenda.heap:
            evento = self.agenda.heap[0]

            if not evento.cancelado and (
                evento.actor is None or evento.actor.vida > 0
            ):
                return evento

            if self.historial.acciones:
                descartado = self.historial.extraer_evento_bruto(
                    self.agenda
                )
            else:
                descartado = self.agenda._extraer_raiz()

            if descartado.actor is not None:
                self._desenlazar(descartado)

        return None

    
    def avanzar_hasta_jugador(self, jugador, ejecutar_evento):
        while jugador.vida > 0:
            evento = self.consultar_siguiente_evento()

            if evento is None:
                return None

            if evento.actor is jugador and evento.tipo == "accion":
                self._cambiar(self, "reloj", evento.tiempo)
                return evento

            evento = self.siguiente_evento()
            ejecutar_evento(evento)

        return None   
    
    def usar_objeto_jugador(self, jugador, ejecutar_evento, *, cantidad=None, duracion=None, velocidad=None):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError("El jugador debe estar vivo y tener una sala actual")
        inventario = jugador.inventario
        objeto = inventario.actual() if inventario is not None else None
        if objeto is None:
            raise ValueError("No hay un objeto seleccionado en el inventario")
        tipo = getattr(objeto, "clase", None)
        if tipo not in ("pocion", "antidoto", "antorcha"):
            raise ValueError("Este objeto no es un consumible disponible")
        if tipo == "pocion":
            if velocidad is not None:
                if type(velocidad) is not int or velocidad <= 0:
                    raise ValueError("La velocidad debe ser un entero positivo")
            elif type(cantidad) is not int or cantidad <= 0:
                raise ValueError("La cantidad de curacion debe ser un entero positivo")
        if (tipo == "antorcha" or velocidad is not None) and (type(duracion) is not int or duracion <= 0):
            raise ValueError("La duracion debe ser un entero positivo")
        turno = self.consultar_siguiente_evento()
        if (
            turno is None or turno is not jugador.proxima_accion
            or turno.actor is not jugador or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError("Primero debes llegar a la decision del jugador")

        self.iniciar_accion()
        self.siguiente_evento()
        _, cambio = inventario.soltar_actual_reversible()
        self.historial.registrar_inventario(inventario, cambio)
        self.refrescar_rastro_jugador(jugador)
        if tipo == "pocion":
            if velocidad is not None:
                self.aplicar_velocidad(jugador, velocidad, duracion)
            else:
                self.curar(jugador, cantidad)
        elif tipo == "antidoto":
            self.aplicar_antidoto(jugador)
        else:
            self.encender_antorcha(jugador, duracion)
        self.programar_accion(jugador, 50)
        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)

    def equipar_jugador(self, jugador, ejecutar_evento):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError("El jugador debe estar vivo y tener una sala actual")
        inventario = jugador.inventario
        objeto = inventario.actual() if inventario is not None else None
        if objeto is None:
            raise ValueError("No hay un objeto seleccionado en el inventario")
        tipo = getattr(objeto, "clase", None)
        if tipo not in ("arma", "armadura"):
            raise ValueError("Solo puedes equipar armas y armaduras")
        anterior = inventario.arma_equipada if tipo == "arma" else inventario.armadura_equipada
        if anterior is objeto:
            raise ValueError("Ese objeto ya esta equipado")
        turno = self.consultar_siguiente_evento()
        if (
            turno is None or turno is not jugador.proxima_accion
            or turno.actor is not jugador or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError("Primero debes llegar a la decision del jugador")

        self.iniciar_accion()
        self.siguiente_evento()
        _, cambio = inventario.equipar_actual_reversible(tipo)
        self.historial.registrar_inventario(inventario, cambio)
        self._cambiar(jugador, "ataque", jugador.ataque
                      - getattr(anterior, "ataque_bonus", 0)
                      + getattr(objeto, "ataque_bonus", 0))
        self._cambiar(jugador, "defensa", jugador.defensa
                      - getattr(anterior, "defensa_bonus", 0)
                      + getattr(objeto, "defensa_bonus", 0))
        self.refrescar_rastro_jugador(jugador)
        self.programar_accion(jugador, 50)
        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)

    def recoger_jugador(self, jugador, indice, ejecutar_evento):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError("El jugador debe estar vivo y tener una sala actual")
        suelo = jugador.sala_actual.objetos_suelo
        if type(indice) is not int or not 1 <= indice <= len(suelo):
            raise ValueError("No hay un objeto con ese numero en el suelo")
        inventario = jugador.inventario
        if inventario is None or inventario.esta_lleno():
            raise ValueError("No hay espacio en el inventario")
        turno = self.consultar_siguiente_evento()
        if (
            turno is None or turno is not jugador.proxima_accion
            or turno.actor is not jugador or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError("Primero debes llegar a la decision del jugador")

        objeto = suelo[indice - 1]
        siguiente = None
        for posicion in range(indice, len(suelo)):
            elemento = suelo[posicion]
            if getattr(elemento, "clase", None) != "pergamino_retroceso":
                siguiente = elemento
                break
        self.iniciar_accion()
        self.siguiente_evento()
        _, cambio = inventario.recoger_reversible(objeto)
        suelo.pop(indice - 1)
        self.historial.registrar_recogida(
            inventario, cambio, suelo, siguiente,
        )
        self.refrescar_rastro_jugador(jugador)
        self.programar_accion(jugador, 25)
        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)

    def esperar_jugador(self, jugador, ejecutar_evento):
        if jugador.vida <= 0:
            raise ValueError("El jugador está muerto")

        if jugador.sala_actual is None:
            raise ValueError("El jugador no tiene sala actual")

        turno = self.consultar_siguiente_evento()

        if (
            turno is None
            or turno is not jugador.proxima_accion
            or turno.actor is not jugador
            or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError(
                "Primero debes llegar a la decisión del jugador"
            )

        self.iniciar_accion()
        self.siguiente_evento()
        self.refrescar_rastro_jugador(jugador)
        self.programar_accion(jugador, 100)

        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)
    
    
    def resolver_ataque(self, atacante, defensor):
        if atacante is defensor:
            raise ValueError("Un actor no puede atacarse a sí mismo")

        if atacante.vida <= 0 or defensor.vida <= 0:
            raise ValueError("Ambos actores deben estar vivos")

        if (
            atacante.sala_actual is None
            or atacante.sala_actual is not defensor.sala_actual
        ):
            raise ValueError("Los actores deben estar en la misma sala")

        dano = max(
            1,
            atacante.ataque + self.azar.randint(0, 4) - defensor.defensa,
        )

        vida_nueva = max(0, defensor.vida - dano)

        if vida_nueva == 0:
            self.matar_actor(defensor)
        else:
            self._cambiar(defensor, "vida", vida_nueva)

        return dano
    
    def atacar_jugador(self, jugador, objetivo, ejecutar_evento):
        if jugador.vida <= 0:
            raise ValueError("El jugador está muerto")

        if jugador.sala_actual is None:
            raise ValueError("El jugador no tiene sala actual")

        turno = self.consultar_siguiente_evento()

        if (
            turno is None
            or turno is not jugador.proxima_accion
            or turno.actor is not jugador
            or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError(
                "Primero debes llegar a la decisión del jugador"
            )

        if objetivo is jugador:
            raise ValueError("El jugador no puede atacarse a sí mismo")

        if objetivo.vida <= 0:
            raise ValueError("El objetivo ya está muerto")

        if objetivo.sala_actual is not jugador.sala_actual:
            raise ValueError("El objetivo debe estar en la misma sala")

        self.iniciar_accion()
        self.siguiente_evento()
        self.refrescar_rastro_jugador(jugador)
        self.resolver_ataque(jugador, objetivo)
        self.programar_accion(jugador, 100)

        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)
    
    
    def ejecutar_guardian(self, evento, jugador):
        if evento.tipo != "accion" or evento.actor is jugador:
            raise ValueError(
                "Se esperaba una acción de un enemigo guardián"
            )

        enemigo = evento.actor

        if enemigo.vida <= 0 or jugador.vida <= 0:
            return

        if (
            enemigo.sala_actual is None
            or jugador.sala_actual is None
        ):
            raise ValueError(
                "Ambos actores deben tener una sala asignada"
            )

        if enemigo.sala_actual is jugador.sala_actual:
            self.resolver_ataque(enemigo, jugador)

        self.programar_accion(enemigo, 100)

    def ejecutar_rastreador(self, evento, jugador):
        if evento.tipo != "accion" or evento.actor is jugador:
            raise ValueError(
                "Se esperaba una acción de un enemigo rastreador"
            )

        enemigo = evento.actor

        if enemigo.vida <= 0 or jugador.vida <= 0:
            return

        if (
            enemigo.sala_actual is None
            or jugador.sala_actual is None
        ):
            raise ValueError(
                "Ambos actores deben tener una sala asignada"
            )

        if enemigo.sala_actual is jugador.sala_actual:
            self.resolver_ataque(enemigo, jugador)
        else:
            destino_id = elegir_destino_rastreador(
                enemigo.sala_actual, self.reloj
            )

            if destino_id is not None:
                for salida in enemigo.sala_actual.salidas:
                    if (
                        salida.abierta
                        and salida.destino.sala_id == destino_id
                    ):
                        self._cambiar(
                            enemigo, "sala_actual", salida.destino
                        )
                        break

        self.programar_accion(enemigo, 100)
        
    def ejecutar_errante(self, evento, jugador):
        if evento.tipo != "accion" or evento.actor is jugador:
            raise ValueError(
                "Se esperaba una acción de un enemigo errante"
            )

        enemigo = evento.actor

        if enemigo.vida <= 0 or jugador.vida <= 0:
            return

        if (
            enemigo.sala_actual is None
            or jugador.sala_actual is None
        ):
            raise ValueError(
                "Ambos actores deben tener una sala asignada"
            )

        if enemigo.sala_actual is jugador.sala_actual:
            self.resolver_ataque(enemigo, jugador)
        else:
            salidas = [
                salida
                for salida in enemigo.sala_actual.salidas
                if salida.abierta
            ]

            if salidas:
                indice = self.azar.randrange(len(salidas))
                self._cambiar(
                    enemigo,
                    "sala_actual",
                    salidas[indice].destino,
                )

        self.programar_accion(enemigo, 100)
        
    def ejecutar_enemigo(self, evento, jugador):
        if evento.tipo != "accion" or evento.actor is jugador:
            raise ValueError(
                "Se esperaba una acción de un enemigo"
            )

        comportamiento = evento.actor.comportamiento

        if comportamiento == "guardian":
            self.ejecutar_guardian(evento, jugador)
        elif comportamiento == "rastreador":
            self.ejecutar_rastreador(evento, jugador)
        elif comportamiento == "errante":
            self.ejecutar_errante(evento, jugador)
        else:
            raise ValueError(
                "El enemigo no tiene un comportamiento válido"
            )

    def activar_enemigos(self, jugador, enemigos):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError(
                "El jugador debe estar vivo y ubicado en una sala"
            )

        pendientes = [
            enemigo
            for enemigo in enemigos
            if enemigo is not jugador
            and enemigo.vida > 0
            and not enemigo.activo
            and enemigo.sala_actual is jugador.sala_actual
        ]

        ordenados = vista_ordenada(
            pendientes, clave=lambda enemigo: enemigo.actor_id
        )

        # Validamos el lote antes de programar sus acciones.
        for enemigo in ordenados:
            if enemigo.comportamiento not in (
                "guardian", "rastreador", "errante"
            ):
                raise ValueError(
                    "El enemigo debe tener un comportamiento válido"
                )

            pendiente = enemigo.proxima_accion
            if pendiente is not None and not pendiente.cancelado:
                raise ValueError(
                    "Un enemigo inactivo ya tiene una acción pendiente"
                )

        cantidad = 0

        for enemigo in ordenados:
            # Evita duplicar la activación si una referencia se repite.
            if enemigo.activo:
                continue

            self.programar_accion(enemigo, 100)
            self._cambiar(enemigo, "activo", True)
            if enemigo.regeneracion_cantidad > 0:
                self.iniciar_regeneracion(enemigo)
            cantidad += 1

        return cantidad
    
    def iniciar_partida(self, jugador, sala):
        if (
            self.reloj != 0
            or self.historial.acciones
            or self.agenda.heap
            or self.agenda.siguiente_secuencia != 0
            or jugador.sala_actual is not None
        ):
            raise ValueError(
                "El inicio requiere un motor y un jugador nuevos"
            )

        if jugador.vida <= 0:
            raise ValueError("El jugador debe estar vivo")

        if not sala.contenido_cargado:
            return False

        # Validamos los enemigos antes de modificar la partida.
        for enemigo in sala.enemigos:
            if enemigo.sala_actual is not sala:
                raise ValueError(
                    "Un enemigo no pertenece a la sala inicial"
                )

            if enemigo.vida <= 0:
                continue

            if enemigo.comportamiento not in (
                "guardian", "rastreador", "errante"
            ):
                raise ValueError(
                    "El enemigo debe tener un comportamiento válido"
                )

            if (
                enemigo.activo
                or enemigo.proxima_accion is not None
                or enemigo.primer_evento is not None
            ):
                raise ValueError(
                    "La sala inicial contiene un enemigo ya programado"
                )

        self.ubicar_jugador_inicial(jugador, sala)
        self.programar_primera_accion_jugador(jugador)
        self.activar_enemigos(jugador, sala.enemigos)

        return True
    
    def mover_jugador(self, jugador, salida, ejecutar_evento):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError(
                "El jugador debe estar vivo y ubicado en una sala"
            )

        turno = self.consultar_siguiente_evento()

        if (
            turno is None
            or turno is not jugador.proxima_accion
            or turno.actor is not jugador
            or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError(
                "Primero debes llegar a la decisión del jugador"
            )

        if not any(
            actual is salida
            for actual in jugador.sala_actual.salidas
        ):
            raise ValueError(
                "La salida no pertenece a la sala actual"
            )

        if not salida.abierta:
            raise ValueError("La salida está cerrada")

        destino = salida.destino

        if not destino.contenido_cargado:
            return False

        # Validamos los enemigos por activar antes de mover.
        for enemigo in destino.enemigos:
            if (
                enemigo.sala_actual is not destino
                or enemigo.vida <= 0
                or enemigo.activo
            ):
                continue

            if enemigo.comportamiento not in (
                "guardian", "rastreador", "errante"
            ):
                raise ValueError(
                    "El enemigo debe tener un comportamiento válido"
                )

            pendiente = enemigo.proxima_accion
            if pendiente is not None and not pendiente.cancelado:
                raise ValueError(
                    "Un enemigo inactivo ya tiene una acción pendiente"
                )

        self.iniciar_accion()
        self.siguiente_evento()
        self.refrescar_rastro_jugador(jugador)
        self.completar_movimiento_jugador(jugador, destino)
        self.programar_accion(jugador, 100)
        self.activar_enemigos(jugador, destino.enemigos)
        self.activar_trampas(jugador)

        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)
    
    def abrir_puerta_jugador(self, jugador, salida, ejecutar_evento):
        if jugador.vida <= 0 or jugador.sala_actual is None:
            raise ValueError(
                "El jugador debe estar vivo y ubicado en una sala"
            )

        turno = self.consultar_siguiente_evento()

        if (
            turno is None
            or turno is not jugador.proxima_accion
            or turno.actor is not jugador
            or turno.tipo != "accion"
            or turno.tiempo != self.reloj
        ):
            raise ValueError(
                "Primero debes llegar a la decisión del jugador"
            )

        if not any(
            actual is salida
            for actual in jugador.sala_actual.salidas
        ):
            raise ValueError(
                "La salida no pertenece a la sala actual"
            )

        if salida.abierta:
            raise ValueError("La puerta ya está abierta")

        requerida = salida.puerta.llave

        if requerida is None:
            raise ValueError("La puerta no declara una llave")

        if jugador.inventario is None or not any(
            getattr(objeto, "clase", None) == "llave"
            and getattr(objeto, "id", None) == requerida
            for objeto in jugador.inventario.listar()
        ):
            raise ValueError("No tienes la llave correcta")

        intervalo = salida.puerta.cierre_automatico

        if intervalo is not None and (
            not isinstance(intervalo, int) or intervalo <= 0
        ):
            raise ValueError(
                "El cierre automático debe ser un entero positivo"
            )

        self.iniciar_accion()
        self.siguiente_evento()
        self.refrescar_rastro_jugador(jugador)
        self._cambiar(salida.puerta, "abierta", True)

        if intervalo is not None:
            self.programar_evento_entorno(
                salida.puerta,
                self.reloj + intervalo,
                "cierre_puerta",
            )

        self.programar_accion(jugador, 50)

        return self.avanzar_hasta_jugador(jugador, ejecutar_evento)
    
    def programar_evento_entorno(self, objetivo, tiempo, tipo):
        if tiempo < self.reloj:
            raise ValueError(
                "No se puede programar un evento en el pasado"
            )

        evento = EventoEntorno(tiempo, tipo, objetivo)

        if self.historial.acciones:
            self.historial.programar_evento(self.agenda, evento)
        else:
            self.agenda.insertar(evento)

        return evento

    def ejecutar_evento(self, evento, jugador):
        if evento.cancelado:
            return
        if isinstance(evento, EventoEntorno):
            if self.ejecutar_efecto_entorno(evento):
                return
            if evento.tipo == "cierre_puerta":
                self._cambiar(evento.objetivo, "abierta", False)
            else:
                raise ValueError("Tipo de evento de entorno desconocido")
        elif not self.ejecutar_efecto_actor(evento):
            self.ejecutar_enemigo(evento, jugador)
