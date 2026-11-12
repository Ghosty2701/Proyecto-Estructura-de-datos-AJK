"""Resultados derivados compartidos por motor, con espacio fijo y doble hash."""
from modelo.tabla_hash import _mezclar


class CacheRutas:
    def __init__(self, capacidad=256):
        if type(capacidad) is not int or capacidad < 8 or capacidad & (capacidad - 1):
            raise ValueError('capacidad potencia de dos, al menos 8')
        self.capacidad = capacidad
        self.casillas = [None] * capacidad
        self.cantidad = 0
        self.aciertos = self.fallos = self.reinicios = 0

    def vaciar(self):
        self.casillas = [None] * self.capacidad
        self.cantidad = 0
        self.reinicios += 1

    def _localizar(self, origen, objetivo, rango, revision):
        mascara = self.capacidad - 1
        clave = _mezclar(origen.sala_id) ^ (_mezclar(objetivo.sala_id) << 1)
        clave ^= _mezclar(rango) ^ _mezclar(revision)
        indice = clave & mascara
        paso = None
        for _ in range(self.capacidad):
            actual = self.casillas[indice]
            if actual is None or (actual.origen is origen and actual.objetivo is objetivo
                                  and actual.rango == rango
                                  and actual.revision_conexiones == revision):
                return indice, actual
            if paso is None:
                paso = (_mezclar(clave ^ 0x9e3779b97f4a7c15) & mascara) | 1
            indice = (indice + paso) & mascara
        raise RuntimeError('cache de rutas sin casilla libre')

    def obtener(self, origen, objetivo, rango, revision):
        _, resultado = self._localizar(origen, objetivo, rango, revision)
        if resultado is None:
            self.fallos += 1
        else:
            self.aciertos += 1
        return resultado

    def insertar(self, resultado):
        indice, anterior = self._localizar(resultado.origen, resultado.objetivo,
                                           resultado.rango, resultado.revision_conexiones)
        if anterior is None:
            if (self.cantidad + 1) * 10 > self.capacidad * 7:
                self.vaciar()
                indice, _ = self._localizar(resultado.origen, resultado.objetivo,
                                            resultado.rango, resultado.revision_conexiones)
            self.cantidad += 1
        self.casillas[indice] = resultado
