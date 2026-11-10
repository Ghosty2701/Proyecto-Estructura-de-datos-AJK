"""Índice estático propio de texto; D-RS-03A, sin hash aleatorio del proceso."""
from modelo.tabla_hash import _mezclar


class IndiceLlaves:
    def __init__(self, reserva):
        self.capacidad = 2
        while reserva * 10 > self.capacidad * 7:
            self.capacidad *= 2
        self.claves = [None] * self.capacidad
        self.valores = [None] * self.capacidad
        self.sondeos = 0

    @staticmethod
    def _hash(clave):
        acumulador = 0xcbf29ce484222325
        for caracter in clave:
            acumulador = _mezclar(acumulador ^ ord(caracter))
        return acumulador

    def _localizar(self, clave):
        if type(clave) is not str or not clave:
            raise ValueError('El ID de llave debe ser texto no vacío')
        mezcla = self._hash(clave)
        mascara = self.capacidad - 1
        posicion = mezcla & mascara
        paso = (_mezclar(mezcla ^ 0x9e3779b97f4a7c15) & mascara) | 1
        for _ in range(self.capacidad):
            self.sondeos += 1
            if self.claves[posicion] is None or self.claves[posicion] == clave:
                return posicion
            posicion = (posicion + paso) & mascara
        raise ValueError('Índice de llaves sin casilla libre')

    def obtener(self, clave):
        posicion = self._localizar(clave)
        return self.valores[posicion] if self.claves[posicion] is not None else None

    def insertar(self, clave, valor):
        posicion = self._localizar(clave)
        if self.claves[posicion] is None:
            self.claves[posicion], self.valores[posicion] = clave, valor
        return self.valores[posicion]
