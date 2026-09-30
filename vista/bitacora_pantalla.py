# Bitacora de pantalla: guarda solo los ultimos N mensajes del juego (§4.8).
# Se implementa como un bufer circular sobre un arreglo de tamano fijo, para que:
#   - agregar un mensaje sea O(1) y nunca desplace los mensajes anteriores.
#   - el consumo de memoria se mantenga constante durante toda la partida,
#     sin importar cuantos mensajes se hayan generado en total.

CAPACIDAD_POR_DEFECTO = 20


class BitacoraPantalla:
    def __init__(self, capacidad=CAPACIDAD_POR_DEFECTO):
        if capacidad <= 0:
            raise ValueError("la capacidad de la bitacora debe ser mayor que 0")

        self.capacidad = capacidad
        # Arreglo de tamano fijo; las posiciones se reutilizan en ciclo.
        self._mensajes = [None] * capacidad
        # Indice de la posicion del mensaje mas antiguo aun conservado.
        self._inicio = 0
        # Cuantos mensajes hay guardados ahora mismo (<= capacidad).
        self._cantidad = 0
        # Total historico, solo informativo (no crece la memoria usada).
        self.total_generados = 0

    def agregar(self, mensaje):
        # Escribe en la siguiente posicion libre (o la mas antigua, si ya esta llena).
        posicion = (self._inicio + self._cantidad) % self.capacidad
        self._mensajes[posicion] = mensaje
        self.total_generados += 1

        if self._cantidad < self.capacidad:
            self._cantidad += 1
        else:
            # Bufer lleno: el mensaje mas antiguo se pierde y el inicio avanza uno.
            self._inicio = (self._inicio + 1) % self.capacidad

    def mensajes(self):
        # Devuelve una lista nueva, del mas antiguo al mas reciente.
        # Costo O(capacidad), es decir O(1) real porque la capacidad es fija.
        return [
            self._mensajes[(self._inicio + i) % self.capacidad]
            for i in range(self._cantidad)
        ]

    def mas_reciente(self):
        if self._cantidad == 0:
            return None
        posicion = (self._inicio + self._cantidad - 1) % self.capacidad
        return self._mensajes[posicion]

    def __len__(self):
        return self._cantidad

    def esta_vacia(self):
        return self._cantidad == 0
