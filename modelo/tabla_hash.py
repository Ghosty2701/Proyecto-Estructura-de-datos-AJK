"""Registro disperso propio para las salas alcanzadas por una búsqueda."""


class RegistroBusqueda:
    def __init__(self, sala, distancia, primer_salto=None):
        self.sala = sala
        self.distancia = distancia
        self.primer_salto = primer_salto
        self.posicion_heap = -1
        self.definitivo = False


def _mezclar(entero):
    # Mezcla entera reproducible: no usa hash aleatorio ni el azar de la partida.
    mascara = (1 << 64) - 1
    entero &= mascara
    entero = ((entero ^ (entero >> 30)) * 0xbf58476d1ce4e5b9) & mascara
    entero = ((entero ^ (entero >> 27)) * 0x94d049bb133111eb) & mascara
    return entero ^ (entero >> 31)


class TablaDistancias:
    def __init__(self):
        self.capacidad = 32
        self.cantidad = 0
        self.casillas = [None] * self.capacidad
        self.sondeos = 0
        self.ampliaciones = 0

    def _inicio(self, clave):
        return _mezclar(clave) & (self.capacidad - 1)

    def _paso(self, clave):
        return (_mezclar(clave + 0x9e3779b97f4a7c15) & (self.capacidad - 1)) | 1

    def _localizar(self, clave):
        if type(clave) is not int:
            raise ValueError("El ID de sala debe ser un entero")
        indice = self._inicio(clave)
        paso = self._paso(clave)
        for _ in range(self.capacidad):
            self.sondeos += 1
            actual = self.casillas[indice]
            if actual is None or actual.sala.sala_id == clave:
                return indice, actual
            indice = (indice + paso) & (self.capacidad - 1)
        raise RuntimeError("No hay casilla libre tras recorrer la tabla")

    def obtener(self, clave):
        return self._localizar(clave)[1]

    def insertar(self, registro):
        indice, anterior = self._localizar(registro.sala.sala_id)
        if anterior is not None:
            anterior.distancia = registro.distancia
            anterior.primer_salto = registro.primer_salto
            return anterior
        if (self.cantidad + 1) * 10 > self.capacidad * 7:
            antiguas = self.casillas
            self.capacidad *= 2
            self.casillas = [None] * self.capacidad
            self.ampliaciones += 1
            for actual in antiguas:
                if actual is not None:
                    posicion, _ = self._localizar(actual.sala.sala_id)
                    self.casillas[posicion] = actual
            indice, _ = self._localizar(registro.sala.sala_id)
        self.casillas[indice] = registro
        self.cantidad += 1
        return registro
