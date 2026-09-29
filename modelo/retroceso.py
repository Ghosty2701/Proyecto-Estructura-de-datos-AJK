from modelo.rastro import registrar_rastro, restaurar_rastro


class CambiosAccion:
    def __init__(self, reloj_anterior):
        self.reloj_anterior = reloj_anterior
        self.cambios = []

    def cambiar_rastro(self, sala, reloj_actual):
        valor_anterior = registrar_rastro(sala, reloj_actual)
        self.cambios.append(("rastro", sala, valor_anterior))

    def registrar_vida(self, actor):
        self.cambios.append(("vida", actor, actor.vida))
        
    def programar_evento(self, agenda, evento):
        secuencia_anterior = agenda.siguiente_secuencia
        agenda.insertar(evento)
        self.cambios.append(("evento_programado", agenda, (evento, secuencia_anterior)))
        
    def extraer_evento(self, agenda):
        evento = agenda.extraer_minimo()

        if evento is not None:
            self.cambios.append(("evento_extraido", agenda, evento))

        return evento

    def deshacer(self):
        while self.cambios:
            tipo, objeto, valor_anterior = self.cambios.pop()

            if tipo == "rastro":
                restaurar_rastro(objeto, valor_anterior)
            elif tipo == "vida":
                objeto.vida = valor_anterior
            elif tipo == "evento_programado":
                evento, secuencia_anterior = valor_anterior
                objeto.cancelar(evento)
                objeto.siguiente_secuencia = secuencia_anterior
            elif tipo == "evento_extraido":
                objeto.insertar(valor_anterior, conservar_secuencia=True)
    
            
class HistorialRetroceso:
    def __init__(self):
        self.acciones = []

    def iniciar_accion(self, reloj_actual):
        self.acciones.append(CambiosAccion(reloj_actual))

        if len(self.acciones) > 5:
            self.acciones.pop(0)

    def registrar_rastro(self, sala, reloj_actual):
        if not self.acciones:
            raise RuntimeError("No hay una acción activa")

        self.acciones[-1].cambiar_rastro(sala, reloj_actual)

    def deshacer_ultima(self):
        if not self.acciones:
            return None

        cambios = self.acciones.pop()
        cambios.deshacer()
        return cambios.reloj_anterior
    
    def registrar_vida(self, actor):
        if not self.acciones:
            raise RuntimeError("No hay una acción activa")

        self.acciones[-1].registrar_vida(actor)
        
    def programar_evento(self, agenda, evento):
        if not self.acciones:
            raise RuntimeError("No hay una acción activa")

        
        self.acciones[-1].programar_evento(agenda, evento)
        
    def extraer_evento(self, agenda):
        if not self.acciones:
            raise RuntimeError("No hay una acción activa")

        return self.acciones[-1].extraer_evento(agenda)
    
    

