# Agenda que mantiene el evento mas proximo en la raiz del heap.
class AgendaEventos:
    def __init__(self):
        self.heap = []
        self.siguiente_secuencia = 0
        
    def insertar(self, evento, conservar_secuencia=False):
        if conservar_secuencia:
            if evento.secuencia is None:
                raise ValueError("El evento no tiene secuencia que restaurar")
        elif evento.secuencia is not None or evento.cancelado:
            raise ValueError(
                "Para programar una nueva acción, crea un Evento nuevo"
            )
        if not conservar_secuencia:
            evento.secuencia = self.siguiente_secuencia
            self.siguiente_secuencia += 1
            
        self.heap.append(evento)
        i = len(self.heap) - 1
            # Sube el evento hasta que su padre tenga prioridad igual o mayor.
        while i > 0:
            padre = (i - 1) // 2
            if (self.heap[i].tiempo, self.heap[i].secuencia) < \
                (self.heap[padre].tiempo, self.heap[padre].secuencia):
                temporal = self.heap[padre]
                self.heap[padre] = self.heap[i]
                self.heap[i] = temporal
                i = padre
            else:
                break
        
            
    def _extraer_raiz(self):
        # Retira el primer evento, aunque este cancelado.
        if not self.heap:
            return None

        minimo = self.heap[0]
        ultimo = self.heap.pop()

        if not self.heap:
            return minimo

        # Coloca el ultimo evento en la raiz y lo baja hasta ordenar el heap.
        self.heap[0] = ultimo
        i = 0
        
        while True:
            menor = i
            izquierdo = 2 * i + 1
            derecho = 2 * i + 2

            # Elige el evento mas proximo entre el padre y sus hijos.
            if izquierdo < len(self.heap) and (self.heap[izquierdo].tiempo, self.heap[izquierdo].secuencia ) < (self.heap[menor].tiempo, self.heap[menor].secuencia):
                menor = izquierdo

            if derecho < len(self.heap) and (self.heap[derecho].tiempo, self.heap[derecho].secuencia) < (self.heap[menor].tiempo, self.heap[menor].secuencia):
                menor = derecho

            if menor == i:
                break   
            
            temporal = self.heap[i]
            self.heap[i] = self.heap[menor]
            self.heap[menor] = temporal
            i = menor
              
        return minimo
    
    
    def extraer_minimo(self):
        # Devuelve el siguiente evento activo, o None si no queda ninguno.
        evento = self._extraer_raiz()

        while evento is not None and evento.cancelado:
            evento = self._extraer_raiz()

        return evento

    def cancelar(self, evento):
        # Se marca ahora y se descarta cuando llegue a la raiz.
        evento.cancelado = True

    def reprogramar(self, evento_anterior, evento_nuevo):
        if evento_anterior is evento_nuevo:
            raise ValueError("La reprogramación requiere un evento nuevo")

        # Si insertar falla, el original permanece activo.
        self.insertar(evento_nuevo)
        self.cancelar(evento_anterior)
        return evento_nuevo


def tiempo_proxima_accion(reloj_actual, costo, velocidad):
    if costo < 0 or velocidad <= 0:
        raise ValueError(
            "El costo debe ser no negativo y la velocidad positiva"
        )

    intervalo = max(1, costo * 100 // velocidad)
    return reloj_actual + intervalo


def tiempo_por_cambio_velocidad(
    tiempo_siguiente,
    reloj_actual,
    velocidad_anterior,
    velocidad_nueva,
):
    if velocidad_anterior <= 0 or velocidad_nueva <= 0:
        raise ValueError("Las velocidades deben ser positivas")

    if tiempo_siguiente < reloj_actual:
        raise ValueError(
            "No se puede reajustar una acción que quedó en el pasado"
        )

    restante = tiempo_siguiente - reloj_actual
    restante_nuevo = max(
        1,
        restante * velocidad_anterior // velocidad_nueva,
    )
    return reloj_actual + restante_nuevo