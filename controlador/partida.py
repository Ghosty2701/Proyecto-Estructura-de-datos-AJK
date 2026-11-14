"""Conexion minima entre los comandos de consola y el motor existente."""

from dataclasses import dataclass, field

from controlador.controlador import AccionInvalida, ejecutar_accion_replay
from modelo.linea_tiempo import ACCION, NAVEGACION, PERGAMINO, ErrorHistoria, ErrorReconstruccion
from adaptadores.cache_catalogo import ErrorCatalogo
from adaptadores.guardado_binario import ErrorGuardado


@dataclass
class RutaSalida:
    direccion: str
    sala_id: int
    nombre: str
    cerrada: bool
    llave: str | None
    costo: int = 100


@dataclass(frozen=True)
class PasoViaje:
    mensajes: tuple
    continuar: bool
    movio: bool


@dataclass
class EstadoPartida:
    sala_id: int
    sala_nombre: str
    reloj: int
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    efectos: list
    salidas: list
    enemigos: list
    objetos_suelo: list
    terminada: bool
    resultado: str | None
    rutas: list = field(default_factory=list)
    solicitudes_usadas: int | None = None
    presupuesto: int | None = None
    solicitudes_normales: int | None = None
    limite_normal: int | None = None
    reserva: int = 0
    reintentos: int = 0
    resumen: dict | None = None


@dataclass
class ResumenHistorico:
    """Contenido mínimo de historia (FR-LT-002); sin referencias al modelo."""
    reloj: int
    titulo: str
    sala_id: int
    sala_nombre: str
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    efectos: list
    inventario: list      # (nombre, equipado, seleccionado) en orden real
    capacidad: int
    enemigos: list        # (nombre con marca de cazador, vida, vida_max, dormido)
    mapa: list            # misma proyección que «ver mapa»


USO_HISTORIA = "Uso: historia <t> (instante entero >= 0) o historia #k (número de acción >= 1)."


class Partida:
    def __init__(self, motor, jugador, enemigos, preparar_sala, fuente=None, *,
                 sala_salida=None, llave_salida=None, id_cripta=None, version_cripta=None):
        self.motor = motor
        self.jugador = jugador
        # Referencias a las instancias cargadas, incluso si cambian de sala.
        self.enemigos = enemigos
        self.preparar_sala = preparar_sala
        self.fuente = fuente
        self._mensajes = []
        self._inicio_pendiente = False
        self._ataque_pendiente = None
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.nombre_jugador = "Jugador"
        self.acciones_ejecutadas = 0
        self.victoria = False
        self.gestor_guardado = None
        self.ruta_guardado = "partida.bin"
        self.bitacora_activa = False
        # Línea de tiempo (FR-LT-001/013): la conecta el cargador; None en dobles de prueba.
        self.linea_tiempo = None
        self.gestor_linea = None
        self._reloj_linea = 0
        self._acciones_linea = 0

    def resultado_final(self):
        if not self.victoria and self.jugador.vida > 0:
            return None
        return {
            "nombre_jugador": self.nombre_jugador,
            "id_cripta": self.id_cripta,
            "version_cripta": self.version_cripta,
            "resultado": "victoria" if self.victoria else "derrota",
            "acciones_jugador": self.acciones_ejecutadas,
            "enemigos_derrotados": sum(1 for enemigo in self.enemigos if enemigo.vida == 0),
            "tiempo_final": self.motor.reloj,
        }

    # --- Línea de tiempo (T009) ---

    def registrar_orden(self, texto):
        """Registra una orden aceptada y reproducible (la misma que va al log).

        El tipo se deduce del contador de acciones: +1 acción, -1 pergamino y 0
        navegación del inventario. Las consultas y comentarios no llegan aquí.
        """
        # Una partida restaurada se crea sin __init__; la línea llega con US6.
        linea = getattr(self, "linea_tiempo", None)
        if linea is None:
            return
        diferencia = self.acciones_ejecutadas - self._acciones_linea
        tipo = {1: ACCION, -1: PERGAMINO, 0: NAVEGACION}.get(diferencia)
        if tipo is None:
            raise RuntimeError("La orden registrada cambió el contador de acciones en más de una unidad.")
        linea.registrar(texto, tipo, self._reloj_linea, self.motor.reloj, self.acciones_ejecutadas)
        self._reloj_linea = self.motor.reloj
        self._acciones_linea = self.acciones_ejecutadas

    def resumen_historico(self, titulo):
        """Resumen del estado de esta partida (viva o copia de la línea)."""
        jugador = self.jugador
        sala = jugador.sala_actual
        inventario = self.inventario
        equipados = (inventario.arma_equipada, inventario.armadura_equipada)
        seleccionado = inventario.actual()
        return ResumenHistorico(
            reloj=self.motor.reloj, titulo=titulo, sala_id=sala.sala_id, sala_nombre=sala.nombre,
            vida=jugador.vida, vida_max=jugador.vida_max, ataque=jugador.ataque,
            defensa=jugador.defensa, efectos=self.estado().efectos,
            inventario=[(o.nombre, any(o is e for e in equipados if e is not None), o is seleccionado)
                        for o in inventario.listar()],
            capacidad=inventario.capacidad,
            enemigos=[(self._nombre_enemigo(e), e.vida, e.vida_max, not e.activo)
                      for e in self._enemigos_presentes()],
            mapa=self.mapa(),
        )

    def historia(self, argumento):
        """Consulta historia <t> o historia #k sin alterar la partida (FR-LT-001/006/007).

        argumento: ("t", instante), ("k", número) o None si la orden está mal formada.
        """
        linea = getattr(self, "linea_tiempo", None)
        if linea is None:
            raise AccionInvalida("La línea de tiempo no está disponible en esta partida.")
        if argumento is None:
            raise AccionInvalida(USO_HISTORIA)
        clase, valor = argumento
        actual = linea.cantidad_acciones + 1
        try:
            if clase == "k":
                objetivo = linea.objetivo_por_k(valor)
                titulo = f"antes de la acción #{valor}"
            else:
                objetivo = linea.objetivo_por_t(valor, self.motor.reloj)
                numero = linea.accion_en(valor)
                if objetivo is None:
                    titulo = f"antes de la acción #{actual}"
                elif objetivo[1] is None:
                    titulo = f"antes de la acción #{numero}"
                else:
                    titulo = f"durante la acción #{numero}"
        except ErrorHistoria as error:
            raise AccionInvalida(f"Historia rechazada: {error}.") from error
        if objetivo is None:
            return self.resumen_historico(f"estado actual, {titulo}")
        try:
            copia = self.reconstruir(objetivo)
        except (ErrorReconstruccion, AccionInvalida, ErrorCatalogo, ValueError) as error:
            raise AccionInvalida(f"No se pudo reconstruir la historia: {error}") from error
        try:
            return copia.resumen_historico(titulo)
        finally:
            liberar = getattr(copia.gestor_guardado, 'liberar_copia', None)
            if liberar is not None:
                liberar()

    def reconstruir(self, objetivo):
        """Copia de trabajo en el objetivo de consulta, sin alterar esta partida.

        objetivo: (posición final exclusiva, límite de tiempo o None) de la línea.
        Copia el último punto anterior y re-ejecuta ≤ K acciones con el mismo
        ejecutor que el replay; la última acción respeta el límite de tiempo.
        """
        posicion, limite = objetivo
        linea = self.linea_tiempo
        punto = linea.punto_para(posicion if limite is None else posicion - 1)
        copia = self.gestor_linea.copia_de_trabajo(punto)
        ordenes = linea.ordenes_entre(punto.posicion, posicion)
        try:
            for numero, orden in enumerate(ordenes, 1):
                if limite is not None and numero == len(ordenes):
                    copia.motor.tiempo_limite = limite
                ejecutar_accion_replay(copia, orden.texto)
        except Exception:
            liberar = getattr(copia.gestor_guardado, 'liberar_copia', None)
            if liberar is not None:
                liberar()
            raise
        return copia

    def _contar_accion(self):
        self.motor._cambiar(self, "acciones_ejecutadas", self.acciones_ejecutadas + 1)

    @property
    def inventario(self):
        return self.jugador.inventario

    def _enemigos_presentes(self):
        return [
            enemigo for enemigo in self.enemigos
            if enemigo.vida > 0 and enemigo.sala_actual is self.jugador.sala_actual
        ]

    @staticmethod
    def _nombre_enemigo(enemigo):
        tipo = " [cazador]" if enemigo.comportamiento == "cazador" else ""
        return f"{enemigo.nombre}{tipo} #{enemigo.actor_id}"

    def estado(self):
        jugador = self.jugador
        sala = jugador.sala_actual
        derrota = jugador.vida <= 0
        efectos = []
        for atributo, nombre in (
            ("veneno", "Veneno"), ("efecto_velocidad", "Velocidad temporal"),
            ("antorcha", "Antorcha encendida"),
        ):
            if getattr(jugador, atributo) is not None:
                efectos.append(nombre)
        return EstadoPartida(
            sala_id=sala.sala_id,
            sala_nombre=sala.nombre,
            reloj=self.motor.reloj,
            vida=jugador.vida,
            vida_max=jugador.vida_max,
            ataque=jugador.ataque,
            defensa=jugador.defensa,
            efectos=efectos,
            salidas=[(s.direccion, s.sala_id, s.cerrada) for s in self._rutas_conocidas(sala)],
            enemigos=[(self._nombre_enemigo(e), e.vida, e.vida_max) for e in self._enemigos_presentes()],
            objetos_suelo=[o.nombre for o in sala.objetos_suelo],
            terminada=derrota or self.victoria,
            resultado="victoria" if self.victoria else ("derrota" if derrota else None),
            resumen=self.resultado_final(),
            rutas=self._rutas_conocidas(sala),
            solicitudes_usadas=getattr(self.fuente, "solicitudes_realizadas", None),
            presupuesto=getattr(self.fuente, "presupuesto_solicitudes", None),
            solicitudes_normales=getattr(self.fuente, "solicitudes_normales", None),
            limite_normal=getattr(self.fuente, "limite_normal", None),
            reserva=getattr(self.fuente, "reserva_solicitudes", 0),
            reintentos=getattr(self.fuente, "solicitudes_reintentos", 0),
        )

    def _comprobar_activa(self):
        if self.victoria:
            raise AccionInvalida("La partida termino: escapaste de la cripta.")
        if self.jugador.vida <= 0:
            raise AccionInvalida("La partida termino: tu vida llego a cero.")

    def _buscar_salida(self, direccion):
        for salida in self.jugador.sala_actual.salidas:
            if salida.direccion == direccion.upper():
                return salida
        raise AccionInvalida(f"No hay una salida hacia {direccion.upper()}.")

    def mapa(self):
        return self.motor.conocimiento.proyeccion() if self.motor.conocimiento is not None else []

    def resolver_viaje(self, texto):
        self._comprobar_activa()
        if self.motor.conocimiento is None:
            raise AccionInvalida('El conocimiento del mapa no esta disponible.')
        try:
            return self.motor.conocimiento.resolver(texto)
        except ValueError as error:
            raise AccionInvalida(str(error)) from error

    def viajar(self, texto, *, registrar=None, comentar=None, interrumpir=None,
               mostrar_paso=None):
        destino = self.resolver_viaje(texto)
        if destino.sala is self.jugador.sala_actual:
            return ['Ya estás en esa sala.']
        if comentar is not None:
            comentar(f'# ir a {texto}')
        mensajes = []
        while True:
            if interrumpir is not None and interrumpir():
                mensajes.append('Viaje interrumpido por el jugador.')
                break
            paso = self.paso_viaje(destino, registrar=registrar, mostrar_paso=mostrar_paso)
            mensajes.extend(paso.mensajes)
            if not paso.continuar:
                break
        return mensajes

    def paso_viaje(self, destino, *, registrar=None, mostrar_paso=None):
        """Un movimiento ordinario y sus paradas; compartido por consola y GUI."""
        self._comprobar_activa()
        if destino.sala is self.jugador.sala_actual:
            return PasoViaje(('Ya estás en esa sala.',), False, False)
        ruta = self.motor.conocimiento.ruta(self.jugador.sala_actual, destino)
        if not ruta.encontrada:
            return PasoViaje(('Viaje detenido: no hay ruta conocida abierta.',), False, False)
        direccion = ruta.primer_paso.direccion
        mensajes = list(self.mover(direccion))
        if registrar is not None:
            registrar(f'ir {direccion}')
        if mostrar_paso is not None:
            mostrar_paso()
        if self.motor.enemigos_entrada:
            mensajes.append('Viaje detenido: enemigos en la sala de entrada.')
        elif self.motor.hubo_dano:
            mensajes.append('Viaje detenido: recibiste daño.')
        elif self.jugador.sala_actual is destino.sala:
            mensajes.append('Viaje completado: llegaste al destino.')
        else:
            return PasoViaje(tuple(mensajes), not (self.victoria or self.jugador.vida <= 0), True)
        return PasoViaje(tuple(mensajes), False, True)

    def _nombre_sala(self, sala):
        if self.motor.conocimiento is None:
            return sala.nombre
        conocida = self.motor.conocimiento.de_sala(sala)
        return conocida.nombre if conocida.estado == 2 else 'Sala avistada'

    def _rutas_conocidas(self, sala):
        if self.motor.conocimiento is None:
            return [RutaSalida(s.direccion, s.destino.sala_id, s.destino.nombre,
                               not s.abierta, s.puerta.llave, s.costo) for s in sala.salidas]
        conocida = self.motor.conocimiento.de_sala(sala)
        return [RutaSalida(s.direccion, s.destino.sala_id,
                           s.destino.nombre if s.destino.estado == 2 else 'Sala avistada',
                           not s.puerta.abierta, None, s.costo) for s in conocida.salidas]

    def _mensaje(self, texto, tiempo=None):
        if tiempo is None:
            tiempo = self.motor.reloj
        self._mensajes.append(f"[t={tiempo}] {texto}")

    def _iniciar_mensajes(self, texto):
        self._mensajes = []
        self._tiempo_accion = self.motor.reloj
        self._vida_inicial = self.jugador.vida
        self._inicio_pendiente = True
        self._ataque_pendiente = None
        self._mensaje(texto)

    def _informar_inicio(self):
        # El motor ejecuta ataque y trampas antes de llamar al primer evento.
        # Observar aqui evita confundir ese daño con ataques o regeneracion posteriores.
        if not self._inicio_pendiente:
            return
        self._inicio_pendiente = False
        perdida = self._vida_inicial - self.jugador.vida
        if perdida > 0:
            self._mensaje(f"Trampas de entrada: pierdes {perdida} de vida.", self._tiempo_accion)
        if self._ataque_pendiente is not None:
            objetivo, vida_anterior = self._ataque_pendiente
            nombre = self._nombre_enemigo(objetivo)
            self._mensaje(
                f"{nombre} pierde {vida_anterior - objetivo.vida} de vida "
                f"y queda en {objetivo.vida}/{objetivo.vida_max}.", self._tiempo_accion,
            )
            if objetivo.vida == 0:
                self._mensaje(f"Derrotaste a {nombre}.", self._tiempo_accion)
                for objeto in getattr(objetivo, "suelta", []):
                    if (
                        getattr(objeto, "clase", None) == "pergamino_retroceso"
                        and getattr(objeto, "recogido_fuera_historial", False)
                    ):
                        continue
                    objetivo.sala_actual.objetos_suelo.append(objeto)
                    self.motor.historial.registrar_botin(objetivo.sala_actual.objetos_suelo, objeto)
                    self._mensaje(f"{nombre} deja {objeto.nombre} en el suelo.", self._tiempo_accion)

    def _ejecutar_evento(self, evento):
        self._informar_inicio()
        vida_anterior = self.jugador.vida
        actor = evento.actor
        sala_anterior = actor.sala_actual if actor is not None else None
        vida_actor = actor.vida if actor is not None else None
        self.motor.ejecutar_evento(evento, self.jugador)
        perdida = vida_anterior - self.jugador.vida
        if perdida > 0:
            if evento.tipo == "accion" and evento.actor is not None:
                origen = self._nombre_enemigo(evento.actor)
            else:
                origen = "Veneno" if evento.tipo == "pulso_veneno" else evento.tipo.replace("_", " ")
            self._mensaje(f"{origen}: pierdes {perdida} de vida.")
        if actor is not None and actor is not self.jugador:
            if actor.sala_actual is not sala_anterior:
                if sala_anterior is self.jugador.sala_actual or actor.sala_actual is self.jugador.sala_actual:
                    self._mensaje(
                        f"{self._nombre_enemigo(actor)} se mueve de {self._nombre_sala(sala_anterior)} "
                        f"a {self._nombre_sala(actor.sala_actual)}."
                    )
            if actor.vida > vida_actor and actor.sala_actual is self.jugador.sala_actual:
                self._mensaje(f"{self._nombre_enemigo(actor)} recupera {actor.vida - vida_actor} de vida.")
        if evento.tipo == "fin_antorcha":
            self._mensaje("Se apaga tu antorcha.")
        if evento.tipo == "fin_velocidad" and actor is self.jugador:
            self._mensaje(f"Termina el cambio de velocidad; vuelves a {self.jugador.velocidad}.")
        if evento.tipo == "rearme_trampa" and any(
            trampa is evento.objetivo for trampa in self.jugador.sala_actual.trampas
        ):
            self._mensaje(f"La trampa {evento.objetivo.instancia_id} vuelve a estar armada.")
        if evento.tipo == "cierre_puerta":
            for salida in self.jugador.sala_actual.salidas:
                if salida.puerta is evento.objetivo:
                    self._mensaje(f"Se cierra la puerta hacia {self._nombre_sala(salida.destino)} ({salida.direccion}).")

    def mover(self, direccion):
        self._comprobar_activa()
        salida = self._buscar_salida(direccion)
        if not salida.abierta:
            raise AccionInvalida("La puerta esta cerrada; primero debes abrirla.")
        self.preparar_sala(salida.destino)
        self.motor.hubo_dano = self.motor.enemigos_entrada = False
        self._iniciar_mensajes(f"Entras en {salida.destino.nombre}.")
        es_salida = (
            self.sala_salida is not None
            and salida.destino.sala_id == self.sala_salida
            and self.llave_salida is not None
            and salida.puerta.llave == self.llave_salida
            and getattr(salida.puerta, "abierta_con_llave", False)
        )
        self.motor.mover_jugador(
            self.jugador, salida, self._ejecutar_evento, finalizar_al_entrar=es_salida,
        )
        self._contar_accion()
        if es_salida:
            self.motor._cambiar(self, "victoria", True)
        self._informar_inicio()
        return self._mensajes

    def esperar(self):
        self._comprobar_activa()
        self._iniciar_mensajes("Esperas.")
        self.motor.esperar_jugador(self.jugador, self._ejecutar_evento)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def atacar(self, indice):
        self._comprobar_activa()
        presentes = self._enemigos_presentes()
        if type(indice) is not int or not 1 <= indice <= len(presentes):
            raise AccionInvalida("No hay un enemigo con ese numero en esta sala.")
        objetivo = presentes[indice - 1]
        if self.gestor_guardado is not None:
            self.gestor_guardado.preparar_botin(objetivo)
        nombre = self._nombre_enemigo(objetivo)
        self._iniciar_mensajes(f"Atacas a {nombre}.")
        self._ataque_pendiente = objetivo, objetivo.vida
        self.motor.atacar_jugador(self.jugador, objetivo, self._ejecutar_evento)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    @staticmethod
    def _pendiente():
        raise AccionInvalida("Este comando todavia no esta integrado en la partida de prueba.")

    def abrir(self, direccion):
        self._comprobar_activa()
        salida = self._buscar_salida(direccion)
        if salida.abierta:
            raise AccionInvalida("La puerta ya esta abierta.")
        requerida = salida.puerta.llave
        if requerida is None:
            raise AccionInvalida("La puerta no declara una llave.")
        if not any(
            getattr(objeto, "clase", None) == "llave"
            and getattr(objeto, "id", None) == requerida
            for objeto in self.inventario.listar()
        ):
            raise AccionInvalida(f"No tienes la llave correcta: {requerida}.")
        self._iniciar_mensajes(
            f"Abres la puerta hacia {self._nombre_sala(salida.destino)} ({salida.direccion})."
        )
        self.motor.abrir_puerta_jugador(self.jugador, salida, self._ejecutar_evento)
        if not hasattr(salida.puerta, "abierta_con_llave"):
            salida.puerta.abierta_con_llave = False
        self.motor._cambiar(salida.puerta, "abierta_con_llave", True)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def recoger(self, indice):
        self._comprobar_activa()
        suelo = self.jugador.sala_actual.objetos_suelo
        if type(indice) is not int or not 1 <= indice <= len(suelo):
            raise AccionInvalida("No hay un objeto con ese numero en el suelo.")
        if self.inventario.esta_lleno():
            raise AccionInvalida("El inventario esta lleno.")
        objeto = suelo[indice - 1]
        self._iniciar_mensajes(f"Recoges {objeto.nombre}.")
        self.motor.recoger_jugador(self.jugador, indice, self._ejecutar_evento)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def usar(self):
        self._comprobar_activa()
        objeto = self.inventario.actual()
        if objeto is None:
            raise AccionInvalida("El inventario esta vacio.")
        tipo = getattr(objeto, "clase", None)
        ficha = getattr(objeto, "ficha", None) or {}
        cantidad = None
        duracion = None
        velocidad = None
        if tipo == "pocion":
            if "modificador_velocidad" in ficha:
                porcentaje = ficha["modificador_velocidad"]
                duracion = ficha.get("duracion")
                if type(porcentaje) is not int or type(duracion) is not int or duracion <= 0:
                    raise AccionInvalida("La pocion requiere porcentaje entero y duracion positiva.")
                efecto = self.jugador.efecto_velocidad
                base = self.jugador.velocidad if efecto is None else efecto.anterior
                velocidad = base * (100 + porcentaje) // 100
                if velocidad < 1:
                    raise AccionInvalida("La pocion produciria una velocidad menor que 1.")
                mensaje = f"Usas {objeto.nombre}: velocidad {velocidad} durante {duracion} unidades virtuales."
            else:
                cantidad = ficha.get("cura")
                if type(cantidad) is not int or cantidad <= 0:
                    raise AccionInvalida("La pocion no declara una cantidad de curacion valida.")
                recuperada = min(cantidad, self.jugador.vida_max - self.jugador.vida)
                mensaje = f"Usas {objeto.nombre}: recuperas {recuperada} de vida."
        elif tipo == "antidoto":
            mensaje = f"Usas {objeto.nombre}: " + (
                "cancelas el veneno." if self.jugador.veneno is not None else "no tenias veneno."
            )
        elif tipo == "antorcha":
            duracion = ficha.get("duracion")
            if type(duracion) is not int or duracion <= 0:
                raise AccionInvalida("La antorcha no declara una duracion valida.")
            mensaje = f"Enciendes {objeto.nombre} durante {duracion} unidades virtuales."
        elif tipo == "pergamino_retroceso":
            return self._retroceder_con_pergamino(objeto)
        else:
            raise AccionInvalida("Ese objeto no se puede consumir; usa equipar para armas y armaduras.")
        self._iniciar_mensajes(mensaje)
        self.motor.usar_objeto_jugador(
            self.jugador, self._ejecutar_evento, cantidad=cantidad,
            duracion=duracion, velocidad=velocidad,
        )
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def equipar(self):
        self._comprobar_activa()
        objeto = self.inventario.actual()
        if objeto is None:
            raise AccionInvalida("El inventario esta vacio.")
        tipo = getattr(objeto, "clase", None)
        if tipo not in ("arma", "armadura"):
            raise AccionInvalida("Solo puedes equipar armas y armaduras.")
        anterior = self.inventario.arma_equipada if tipo == "arma" else self.inventario.armadura_equipada
        if anterior is objeto:
            raise AccionInvalida("Ese objeto ya esta equipado.")
        self._iniciar_mensajes(f"Equipas {objeto.nombre}.")
        self.motor.equipar_jugador(self.jugador, self._ejecutar_evento)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def soltar(self):
        self._comprobar_activa()
        objeto = self.inventario.actual()
        if objeto is None:
            raise AccionInvalida("El inventario esta vacio.")
        self._iniciar_mensajes(f"Sueltas {objeto.nombre} en el suelo.")
        self.motor.soltar_jugador(self.jugador, self._ejecutar_evento)
        self._contar_accion()
        self._informar_inicio()
        return self._mensajes

    def retroceder(self):
        return self._retroceder_con_pergamino()

    def _retroceder_con_pergamino(self, elegido=None):
        self._comprobar_activa()
        if not self.motor.historial.acciones:
            raise AccionInvalida("No hay acciones disponibles para retroceder.")

        def coincide(objeto):
            return (
                getattr(objeto, "clase", None) == "pergamino_retroceso"
                and (elegido is None or objeto is elegido)
            )

        if not any(coincide(objeto) for objeto in self.inventario.listar()):
            raise AccionInvalida("No tienes un pergamino de retroceso.")
        if not self.motor.historial.cabe_inventario_al_deshacer(self.inventario, espacios_liberados=1):
            raise AccionInvalida("No hay espacio para restaurar el inventario; conservas el pergamino.")
        tiempo_anterior = self.motor.reloj
        if self.gestor_guardado is not None:
            self.gestor_guardado.preparar_retroceso(self)
        self.motor.usar_pergamino(self.jugador, coincide)
        self._mensajes = []
        self._inicio_pendiente = False
        self._ataque_pendiente = None
        self._mensaje(f"Consumes un pergamino y retrocedes de t={tiempo_anterior} a t={self.motor.reloj}.")
        return self._mensajes

    def guardar(self):
        self._comprobar_activa()
        if self.gestor_guardado is None:
            raise AccionInvalida("No hay un gestor de guardado conectado a esta partida.")
        try:
            self.gestor_guardado.guardar_sesion(self, self.ruta_guardado)
        except (ErrorGuardado, OSError) as error:
            raise AccionInvalida(f"No se pudo guardar: {error}") from error
        self._mensajes = []
        self._mensaje(f"Partida guardada en {self.ruta_guardado}.")
        return self._mensajes

    def cargar(self):
        self._comprobar_activa()
        if self.bitacora_activa:
            raise AccionInvalida(
                "No puedes cargar mientras registras una bitacora. "
                "Reanuda el archivo en otra ejecucion con --cargar."
            )
        if self.gestor_guardado is None:
            raise AccionInvalida("No hay un gestor de guardado conectado a esta partida.")
        try:
            cargada = self.gestor_guardado.leer_sesion(self.ruta_guardado, self.id_cripta, self.version_cripta)
            self.gestor_guardado.aplicar_sesion(self, cargada)
        except (ErrorGuardado, OSError) as error:
            raise AccionInvalida(f"No se pudo cargar: {error}") from error
        self._mensaje(f"Partida cargada desde {self.ruta_guardado}.")
        return self._mensajes
