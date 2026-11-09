"""Heap binario propio; una entrada por sala y prioridad modificable."""


def _clave(registro):
    primero = registro.primer_salto
    return (registro.distancia,
            registro.sala.sala_id if primero is None else primero.sala_id,
            registro.sala.sala_id)


class HeapRutas:
    def __init__(self):
        self.datos = []

    def _poner(self, indice, registro):
        self.datos[indice] = registro
        registro.posicion_heap = indice

    def _subir(self, indice):
        actual = self.datos[indice]
        while indice > 0:
            padre = (indice - 1) // 2
            if _clave(self.datos[padre]) <= _clave(actual):
                break
            self._poner(indice, self.datos[padre])
            indice = padre
        self._poner(indice, actual)

    def insertar(self, registro):
        if registro.posicion_heap != -1 or registro.definitivo:
            raise ValueError("La sala ya tiene entrada o es definitiva")
        self.datos.append(registro)
        self._subir(len(self.datos) - 1)

    def mejorar(self, registro, distancia, primer_salto):
        indice = registro.posicion_heap
        if not 0 <= indice < len(self.datos) or self.datos[indice] is not registro:
            raise ValueError("El registro no pertenece al heap")
        primer_id = registro.sala.sala_id if primer_salto is None else primer_salto.sala_id
        if (distancia, primer_id, registro.sala.sala_id) > _clave(registro):
            raise ValueError("La nueva etiqueta no mejora la prioridad")
        registro.distancia = distancia
        registro.primer_salto = primer_salto
        self._subir(indice)

    def extraer_minimo(self):
        if not self.datos:
            return None
        minimo = self.datos[0]
        ultimo = self.datos.pop()
        if self.datos:
            indice = 0
            hijo = 1
            while hijo < len(self.datos):
                derecho = hijo + 1
                if derecho < len(self.datos) and _clave(self.datos[derecho]) < _clave(self.datos[hijo]):
                    hijo = derecho
                if _clave(ultimo) <= _clave(self.datos[hijo]):
                    break
                self._poner(indice, self.datos[hijo])
                indice = hijo
                hijo = 2 * indice + 1
            self._poner(indice, ultimo)
        minimo.posicion_heap = -1
        minimo.definitivo = True
        return minimo
