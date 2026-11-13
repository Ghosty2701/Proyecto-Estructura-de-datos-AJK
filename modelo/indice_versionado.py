"""Índice experimental de registros inmutables; no conectado al motor.

Un lote trabaja sobre un vector propio; publicar congela el vector. Entradas
no modificadas se comparten. Borrado y rehash nunca escriben en otra versión.
"""
from dataclasses import dataclass
from modelo.tabla_hash import _mezclar

ELIMINAR = object()  # orden de actualización; nunca se almacena en una versión
_TUMBA = ()


def _id_valido(clave):
    if type(clave) is not int or clave < 0:
        raise ValueError('el ID debe ser un entero no negativo')


def _validar_registro(registro):
    if (type(registro) is not tuple or len(registro) != 2
            or type(registro[0]) is not int or registro[0] < 0
            or type(registro[1]) is not tuple):
        raise TypeError('registro esperado: (codigo entero, tupla de datos)')
    pendientes = [registro[1]]
    while pendientes:
        valor = pendientes.pop()
        tipo = type(valor)
        if tipo is tuple:
            pendientes.extend(valor)
        elif tipo not in (type(None), bool, int, float, str, bytes):
            raise TypeError('el registro contiene un valor mutable o sin esquema')


def _inicio(clave, mascara):
    # Los IDs de sesión son ordinales: conservar sus bits bajos evita mezclar
    # dos veces en cada acceso. Plegar altos admite también claves dispersas.
    # Las colisiones conservan el segundo hash impar y la búsqueda acotada.
    return (clave ^ (clave >> 32)) & mascara


def _localizar(casillas, clave):
    mascara = len(casillas) - 1
    indice = _inicio(clave, mascara)
    primera_tumba = None
    paso = None
    for _ in range(len(casillas)):
        entrada = casillas[indice]
        if entrada is None:
            return (indice if primera_tumba is None else primera_tumba), False
        if entrada is _TUMBA:
            if primera_tumba is None:
                primera_tumba = indice
        elif entrada[0] == clave:
            return indice, True
        if paso is None:
            paso = (_mezclar(clave ^ 0x9e3779b97f4a7c15) & mascara) | 1
        indice = (indice + paso) & mascara
    if primera_tumba is not None:
        return primera_tumba, False
    raise RuntimeError('indice sin casilla disponible')


def _rehash(casillas, capacidad):
    nuevas = [None] * capacidad
    for entrada in casillas:
        if entrada is not None and entrada is not _TUMBA:
            indice, _ = _localizar(nuevas, entrada[0])
            nuevas[indice] = entrada
    return nuevas


@dataclass(frozen=True, slots=True)
class VersionRegistros:
    casillas: tuple
    cantidad: int = 0
    tumbas: int = 0

    @classmethod
    def vacia(cls, capacidad=32):
        if type(capacidad) is not int or capacidad < 1:
            raise ValueError('capacidad entera positiva')
        tamano = 8
        while tamano < capacidad:
            tamano *= 2
        return cls((None,) * tamano)

    def obtener(self, clave, defecto=None):
        _id_valido(clave)
        indice, existe = _localizar(self.casillas, clave)
        return self.casillas[indice][1] if existe else defecto

    def registros(self):
        for entrada in self.casillas:
            if entrada is not None and entrada is not _TUMBA:
                yield entrada

    def con_cambios(self, cambios):
        casillas = list(self.casillas)
        cantidad, tumbas = self.cantidad, self.tumbas
        modificado = False
        for clave, registro in cambios:
            _id_valido(clave)
            if registro is not ELIMINAR:
                _validar_registro(registro)
            indice, existe = _localizar(casillas, clave)
            if registro is ELIMINAR:
                if existe:
                    casillas[indice] = _TUMBA
                    cantidad -= 1
                    tumbas += 1
                    modificado = True
                continue
            if existe and casillas[indice][1] is registro:
                continue
            if not existe:
                if (cantidad + 1) * 10 > len(casillas) * 7:
                    casillas = _rehash(casillas, len(casillas) * 2)
                    tumbas = 0
                    indice, _ = _localizar(casillas, clave)
                elif (cantidad + tumbas + 1) * 10 > len(casillas) * 7:
                    casillas = _rehash(casillas, len(casillas))
                    tumbas = 0
                    indice, _ = _localizar(casillas, clave)
                if casillas[indice] is _TUMBA:
                    tumbas -= 1
                cantidad += 1
            casillas[indice] = (clave, registro)
            modificado = True
        return VersionRegistros(tuple(casillas), cantidad, tumbas) if modificado else self
