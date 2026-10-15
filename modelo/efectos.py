"""Efectos del modelo. Todos los cambios alcanzables usan deltas del motor.

Convenciones para casos no detallados por el enunciado:
* Veneno renovado: reemplaza dosis y duración; último pulso en aplicación + 400.
* Velocidad renovada: reemplaza velocidad y duración, preservando la base original.
* Antorcha renovada: reemplaza su duración.
Las acciones de consumir objetos pertenecen a la integración con inventario.
"""


def _positivo(valor, nombre):
    if type(valor) is not int or valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo")


class EstadoEfecto:
    def __init__(self, tipo, cantidad=0, fin=None, anterior=None):
        self.tipo = tipo
        self.cantidad = cantidad
        self.fin = fin
        self.anterior = anterior
        self.evento = None


class Trampa:
    """Instancia resuelta. cantidad es daño, dosis o velocidad final absoluta.

    No interpreta JSON ni el significado aritmético de modificador_velocidad.
    """

    def __init__(
        self, instancia_id, tipo, cantidad, *, duracion=None,
        rearme=300, armada=True,
    ):
        if tipo not in ("dano", "veneno", "velocidad"):
            raise ValueError("Tipo de efecto de trampa desconocido")
        _positivo(cantidad, "cantidad")
        _positivo(rearme, "rearme")
        if tipo == "velocidad":
            _positivo(duracion, "duracion")
        self.instancia_id = instancia_id
        self.tipo = tipo
        self.cantidad = cantidad
        self.duracion = duracion
        self.rearme = rearme
        self.armada = armada
        self.evento_rearme = None


class MotorEfectos:
    """Parte de MotorEventos; usa su agenda, enlaces y registro reversible."""

    def _validar_vivo(self, actor):
        if actor.vida <= 0:
            raise ValueError("El actor debe estar vivo")

    def _programar_efecto(self, actor, estado, tiempo, tipo):
        evento = self.programar_evento(actor, tiempo, tipo)
        self._cambiar(evento, "efecto", estado)
        self._cambiar(estado, "evento", evento)
        return evento

    def _cancelar_efecto(self, actor, atributo):
        estado = getattr(actor, atributo)
        if estado is None:
            return False
        if estado.evento is not None:
            self.cancelar_evento(estado.evento)
            self._cambiar(estado, "evento", None)
        self._cambiar(actor, atributo, None)
        return True

    def aplicar_dano(self, actor, cantidad):
        _positivo(cantidad, "cantidad")
        self._validar_vivo(actor)
        restante = max(0, actor.vida - cantidad)
        aplicado = actor.vida - restante
        if restante == 0:
            self.matar_actor(actor)
        else:
            self._cambiar(actor, "vida", restante)
        return aplicado

    def curar(self, actor, cantidad):
        _positivo(cantidad, "cantidad")
        self._validar_vivo(actor)
        nueva = min(actor.vida_max, actor.vida + cantidad)
        recuperado = nueva - actor.vida
        if recuperado:
            self._cambiar(actor, "vida", nueva)
        return recuperado

    def aplicar_veneno(self, actor, dano):
        _positivo(dano, "dano")
        self._validar_vivo(actor)
        self._cancelar_efecto(actor, "veneno")
        estado = EstadoEfecto("veneno", dano, self.reloj + 400)
        self._cambiar(actor, "veneno", estado)
        self._programar_efecto(actor, estado, self.reloj + 80, "pulso_veneno")
        return estado

    def aplicar_antidoto(self, actor):
        self._validar_vivo(actor)
        return self._cancelar_efecto(actor, "veneno")

    def aplicar_velocidad(self, actor, velocidad_nueva, duracion):
        _positivo(velocidad_nueva, "velocidad_nueva")
        _positivo(duracion, "duracion")
        self._validar_vivo(actor)
        previo = actor.efecto_velocidad
        base = actor.velocidad if previo is None else previo.anterior
        self._cancelar_efecto(actor, "efecto_velocidad")
        estado = EstadoEfecto(
            "velocidad", velocidad_nueva, self.reloj + duracion, base
        )
        self._cambiar(actor, "efecto_velocidad", estado)
        self.cambiar_velocidad(actor, velocidad_nueva)
        self._programar_efecto(actor, estado, estado.fin, "fin_velocidad")
        return estado

    def encender_antorcha(self, actor, duracion):
        _positivo(duracion, "duracion")
        self._validar_vivo(actor)
        self._cancelar_efecto(actor, "antorcha")
        estado = EstadoEfecto("antorcha", fin=self.reloj + duracion)
        self._cambiar(actor, "antorcha", estado)
        self._programar_efecto(actor, estado, estado.fin, "fin_antorcha")
        return estado

    def iniciar_regeneracion(self, actor, cantidad=None):
        if cantidad is None:
            cantidad = actor.regeneracion_cantidad
        _positivo(cantidad, "cantidad")
        self._validar_vivo(actor)
        if actor.regeneracion is not None:
            return actor.regeneracion
        estado = EstadoEfecto("regeneracion", cantidad)
        self._cambiar(actor, "regeneracion", estado)
        self._programar_efecto(
            actor, estado, self.reloj + 200, "pulso_regeneracion"
        )
        return estado

    def detener_regeneracion(self, actor):
        return self._cancelar_efecto(actor, "regeneracion")

    def ejecutar_efecto_actor(self, evento):
        tipos = (
            "pulso_veneno", "fin_velocidad", "fin_antorcha",
            "pulso_regeneracion",
        )
        if evento.tipo not in tipos:
            return False
        actor = evento.actor
        if evento.cancelado or actor.vida <= 0:
            return True
        estado = evento.efecto
        if estado is None:
            raise ValueError("El evento de efecto no tiene estado asociado")
        if evento.tipo == "pulso_veneno":
            atributo = "veneno"
        elif evento.tipo == "fin_velocidad":
            atributo = "efecto_velocidad"
        elif evento.tipo == "fin_antorcha":
            atributo = "antorcha"
        else:
            atributo = "regeneracion"
        if getattr(actor, atributo) is not estado or estado.evento is not evento:
            return True
        self._cambiar(estado, "evento", None)

        if evento.tipo == "pulso_veneno":
            self.aplicar_dano(actor, estado.cantidad)
            siguiente = self.reloj + 80
            if actor.vida > 0 and siguiente <= estado.fin:
                self._programar_efecto(actor, estado, siguiente, "pulso_veneno")
            else:
                self._cambiar(actor, "veneno", None)
        elif evento.tipo == "fin_velocidad":
            self._cambiar(actor, "efecto_velocidad", None)
            self.cambiar_velocidad(actor, estado.anterior)
        elif evento.tipo == "fin_antorcha":
            self._cambiar(actor, "antorcha", None)
        else:
            self.curar(actor, estado.cantidad)
            self._programar_efecto(
                actor, estado, self.reloj + 200, "pulso_regeneracion"
            )
        return True

    def activar_trampas(self, jugador):
        from comun.ordenamiento import vista_ordenada

        self._validar_vivo(jugador)
        if jugador.sala_actual is None:
            raise ValueError("El jugador no tiene sala actual")
        trampas = vista_ordenada(
            jugador.sala_actual.trampas, clave=lambda trampa: trampa.instancia_id
        )
        cantidad = 0
        for trampa in trampas:
            if jugador.vida <= 0:
                break
            if not trampa.armada:
                continue
            self._cambiar(trampa, "armada", False)
            evento = self.programar_evento_entorno(
                trampa, self.reloj + trampa.rearme, "rearme_trampa"
            )
            self._cambiar(trampa, "evento_rearme", evento)
            if trampa.tipo == "dano":
                self.aplicar_dano(jugador, trampa.cantidad)
            elif trampa.tipo == "veneno":
                self.aplicar_veneno(jugador, trampa.cantidad)
            else:
                self.aplicar_velocidad(jugador, trampa.cantidad, trampa.duracion)
            cantidad += 1
        return cantidad

    def ejecutar_efecto_entorno(self, evento):
        if evento.tipo != "rearme_trampa":
            return False
        trampa = evento.objetivo
        if not evento.cancelado and trampa.evento_rearme is evento:
            self._cambiar(trampa, "armada", True)
            self._cambiar(trampa, "evento_rearme", None)
        return True
