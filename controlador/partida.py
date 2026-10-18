"""Conexion minima entre los comandos de consola y el motor existente."""

from dataclasses import dataclass, field

from controlador.controlador import AccionInvalida


@dataclass
class RutaSalida:
    direccion: str
    sala_id: int
    nombre: str
    cerrada: bool
    llave: str | None


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


class Partida:
    def __init__(self, motor, jugador, enemigos, preparar_sala, fuente=None):
        self.motor = motor
        self.jugador = jugador
        # Referencias a las instancias cargadas, incluso si cambian de sala.
        self.enemigos = enemigos
        self.preparar_sala = preparar_sala
        self.fuente = fuente
        self._mensajes = []
        self._inicio_pendiente = False
        self._ataque_pendiente = None

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
        return f"{enemigo.nombre} #{enemigo.actor_id}"

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
            salidas=[(s.direccion, s.destino.sala_id, not s.abierta) for s in sala.salidas],
            enemigos=[(self._nombre_enemigo(e), e.vida, e.vida_max) for e in self._enemigos_presentes()],
            objetos_suelo=[o.nombre for o in sala.objetos_suelo],
            terminada=derrota,
            resultado="derrota" if derrota else None,
            rutas=[RutaSalida(s.direccion, s.destino.sala_id, s.destino.nombre,
                              not s.abierta, s.puerta.llave) for s in sala.salidas],
            solicitudes_usadas=getattr(self.fuente, "solicitudes_realizadas", None),
            presupuesto=getattr(self.fuente, "presupuesto_solicitudes", None),
            solicitudes_normales=getattr(self.fuente, "solicitudes_normales", None),
            limite_normal=getattr(self.fuente, "limite_normal", None),
            reserva=getattr(self.fuente, "reserva_solicitudes", 0),
            reintentos=getattr(self.fuente, "solicitudes_reintentos", 0),
        )

    def _comprobar_activa(self):
        if self.jugador.vida <= 0:
            raise AccionInvalida("La partida termino: tu vida llego a cero.")

    def _buscar_salida(self, direccion):
        for salida in self.jugador.sala_actual.salidas:
            if salida.direccion == direccion.upper():
                return salida
        raise AccionInvalida(f"No hay una salida hacia {direccion.upper()}.")

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
                    objetivo.sala_actual.objetos_suelo.append(objeto)
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
                        f"{self._nombre_enemigo(actor)} se mueve de {sala_anterior.nombre} "
                        f"a {actor.sala_actual.nombre}."
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
                    self._mensaje(f"Se cierra la puerta hacia {salida.destino.nombre} ({salida.direccion}).")

    def mover(self, direccion):
        self._comprobar_activa()
        salida = self._buscar_salida(direccion)
        if not salida.abierta:
            raise AccionInvalida("La puerta esta cerrada; primero debes abrirla.")
        self.preparar_sala(salida.destino)
        self._iniciar_mensajes(f"Entras en {salida.destino.nombre}.")
        self.motor.mover_jugador(self.jugador, salida, self._ejecutar_evento)
        self._informar_inicio()
        return self._mensajes

    def esperar(self):
        self._comprobar_activa()
        self._iniciar_mensajes("Esperas.")
        self.motor.esperar_jugador(self.jugador, self._ejecutar_evento)
        self._informar_inicio()
        return self._mensajes

    def atacar(self, indice):
        self._comprobar_activa()
        presentes = self._enemigos_presentes()
        if type(indice) is not int or not 1 <= indice <= len(presentes):
            raise AccionInvalida("No hay un enemigo con ese numero en esta sala.")
        objetivo = presentes[indice - 1]
        nombre = self._nombre_enemigo(objetivo)
        self._iniciar_mensajes(f"Atacas a {nombre}.")
        self._ataque_pendiente = objetivo, objetivo.vida
        self.motor.atacar_jugador(self.jugador, objetivo, self._ejecutar_evento)
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
            f"Abres la puerta hacia {salida.destino.nombre} ({salida.direccion})."
        )
        self.motor.abrir_puerta_jugador(self.jugador, salida, self._ejecutar_evento)
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
            raise AccionInvalida("Los pergaminos requieren integrar el retroceso completo de la partida.")
        else:
            raise AccionInvalida("Ese objeto no se puede consumir; usa equipar para armas y armaduras.")
        self._iniciar_mensajes(mensaje)
        self.motor.usar_objeto_jugador(
            self.jugador, self._ejecutar_evento, cantidad=cantidad,
            duracion=duracion, velocidad=velocidad,
        )
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
        self._informar_inicio()
        return self._mensajes

    def soltar(self):
        return self._pendiente()

    def retroceder(self):
        return self._pendiente()

    def guardar(self):
        return self._pendiente()

    def cargar(self):
        return self._pendiente()
