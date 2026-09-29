# Agenda que mantiene el evento mas proximo en la raiz del heap.
class AgendaEventos:
    def __init__(self):
        self.heap = []
        self.siguiente_secuencia = 0
        
    def insertar(self, evento, conservar_secuencia=False):
        # Solo los eventos nuevos reciben una secuencia nueva.
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
        # Reemplaza el evento anterior por uno con nuevos datos.
        self.cancelar(evento_anterior)
        self.insertar(evento_nuevo)
        return evento_nuevo


