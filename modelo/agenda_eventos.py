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
            
        heap = self.heap
        heap.append(evento)
        i = len(heap) - 1
        # Subir por huecos evita intercambios y tuplas temporales en cada nivel.
        while i > 0:
            padre = (i - 1) // 2
            anterior = heap[padre]
            if (evento.tiempo < anterior.tiempo or
                    (evento.tiempo == anterior.tiempo and evento.secuencia < anterior.secuencia)):
                heap[i] = anterior
                i = padre
            else:
                break
        heap[i] = evento
        
            
    def _extraer_raiz(self):
        # Retira el primer evento, aunque este cancelado.
        heap = self.heap
        if not heap:
            return None

        minimo = heap[0]
        ultimo = heap.pop()

        cantidad = len(heap)
        if not cantidad:
            return minimo

        # Bajar el hueco por el menor hijo y colocar el ultimo una sola vez.
        i = 0
        hijo = 1
        while hijo < cantidad:
            menor = heap[hijo]
            derecho = hijo + 1
            if derecho < cantidad:
                otro = heap[derecho]
                if (otro.tiempo < menor.tiempo or
                        (otro.tiempo == menor.tiempo and otro.secuencia < menor.secuencia)):
                    hijo = derecho
                    menor = otro
            if (ultimo.tiempo < menor.tiempo or
                    (ultimo.tiempo == menor.tiempo and ultimo.secuencia <= menor.secuencia)):
                break
            heap[i] = menor
            i = hijo
            hijo = 2 * i + 1
        heap[i] = ultimo
              
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
