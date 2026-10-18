from modelo.rastro import registrar_rastro, restaurar_rastro



class CambiosAccion:
    def __init__(self, reloj_anterior):
        self.reloj_anterior = reloj_anterior
        self.cambios = []

    def cambiar_rastro(self, sala, reloj_actual):
        anterior = registrar_rastro(sala, reloj_actual)
        self.cambios.append(("rastro", sala, anterior))

    def registrar_vida(self, actor):
        self.cambios.append(("vida", actor, actor.vida))

    def registrar_recogida(self, inventario, cambio, suelo, siguiente):
        if cambio is not None:
            self.cambios.append(("recogida", inventario, (cambio, suelo, siguiente)))

    def registrar_inventario(self, inventario, cambio):
        if cambio is not None:
            self.cambios.append(("inventario", inventario, cambio))

    def programar_evento(self, agenda, evento):
        secuencia_anterior = agenda.siguiente_secuencia
        agenda.insertar(evento)
        self.cambios.append(
            ("evento_programado", agenda, (evento, secuencia_anterior))
        )

    def cancelar_evento(self, agenda, evento):
        # Guardamos la marca anterior, incluso si ya estaba cancelado.
        self.cambios.append(
            ("evento_cancelado", evento, evento.cancelado)
        )
        agenda.cancelar(evento)

    def reprogramar_evento(self, agenda, anterior, nuevo):
        if anterior is nuevo:
            raise ValueError("La reprogramación requiere un evento nuevo")

        self.programar_evento(agenda, nuevo)
        self.cancelar_evento(agenda, anterior)
        return nuevo

    def extraer_evento(self, agenda):
        # Registrar también los cancelados permite recuperarlos al deshacer.
        while True:
            evento = agenda._extraer_raiz()

            if evento is None:
                return None

            self.cambios.append(("evento_extraido", agenda, evento))

            if not evento.cancelado:
                return evento

    def deshacer(self):
        # Los cambios se revierten en orden inverso.
        while self.cambios:
            tipo, objeto, anterior = self.cambios.pop()

            if tipo == "rastro":
                restaurar_rastro(objeto, anterior)

            elif tipo == "vida":
                objeto.vida = anterior

            elif tipo == "inventario":
                objeto.deshacer_cambio(anterior)

            elif tipo == "recogida":
                cambio, suelo, siguiente = anterior
                objeto.deshacer_cambio(cambio)
                # Busca por identidad: dos objetos pueden compartir la misma ficha.
                posicion = len(suelo)
                for indice, elemento in enumerate(suelo):
                    if elemento is siguiente:
                        posicion = indice
                        break
                suelo.insert(posicion, cambio.nodo.objeto)

            elif tipo == "evento_cancelado":
                objeto.cancelado = anterior

            elif tipo == "evento_programado":
                evento, secuencia_anterior = anterior
                objeto.cancelar(evento)
                objeto.siguiente_secuencia = secuencia_anterior

            elif tipo == "evento_extraido":
                objeto.insertar(anterior, conservar_secuencia=True)

            elif tipo == "azar":
                objeto.setstate(anterior)

            elif tipo == "atributo":
                nombre, valor = anterior
                setattr(objeto, nombre, valor)
                
    def registrar_atributo(self, objeto, nombre):
        anterior = getattr(objeto, nombre)
        self.cambios.append(
            ("atributo", objeto, (nombre, anterior))
        )

    def extraer_evento_bruto(self, agenda):
        # Incluye eventos cancelados: también deben poder restaurarse.
        evento = agenda._extraer_raiz()

        if evento is not None:
            self.cambios.append(("evento_extraido", agenda, evento))

        return evento
    
    def registrar_azar(self, azar):
        self.cambios.append(("azar", azar, azar.getstate()))


class HistorialRetroceso:
    def __init__(self):
        self.acciones = []

    def _accion_actual(self):
        if not self.acciones:
            raise RuntimeError("No hay una acción activa")
        return self.acciones[-1]

    def registrar_recogida(self, inventario, cambio, suelo, siguiente):
        self._accion_actual().registrar_recogida(inventario, cambio, suelo, siguiente)

    def registrar_inventario(self, inventario, cambio):
        self._accion_actual().registrar_inventario(inventario, cambio)

    def iniciar_accion(self, reloj_actual):
        self.acciones.append(CambiosAccion(reloj_actual))

        if len(self.acciones) > 5:
            self.acciones.pop(0)

    def registrar_rastro(self, sala, reloj_actual):
        self._accion_actual().cambiar_rastro(sala, reloj_actual)

    def registrar_vida(self, actor):
        self._accion_actual().registrar_vida(actor)

    def programar_evento(self, agenda, evento):
        self._accion_actual().programar_evento(agenda, evento)

    def cancelar_evento(self, agenda, evento):
        self._accion_actual().cancelar_evento(agenda, evento)

    def reprogramar_evento(self, agenda, anterior, nuevo):
        return self._accion_actual().reprogramar_evento(
            agenda, anterior, nuevo
        )

    def extraer_evento(self, agenda):
        return self._accion_actual().extraer_evento(agenda)

    def deshacer_ultima(self):
        if not self.acciones:
            return None

        accion = self.acciones.pop()
        accion.deshacer()
        return accion.reloj_anterior
    
    def registrar_atributo(self, objeto, nombre):
        self._accion_actual().registrar_atributo(objeto, nombre)

    def extraer_evento_bruto(self, agenda):
        return self._accion_actual().extraer_evento_bruto(agenda)
    
    def registrar_azar(self, azar):
        self._accion_actual().registrar_azar(azar)
