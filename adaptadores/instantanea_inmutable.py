"""Puntos en registros inmutables: los enlaces del modelo son IDs locales.

El esquema es el del guardado; esta representación solo existe en memoria.
Las tuplas originales también tienen registro, por lo que una referencia (ID,)
no se confunde con los valores del modelo. No retiene objetos del grafo vivo.
"""
import random
import struct
from dataclasses import dataclass
from operator import attrgetter

from adaptadores.estado_binario import _ESQUEMAS
from adaptadores.copia_estado import (
    TablaIdentidades, _VACIA, _completar_no_persistentes,
)
from adaptadores.cache_catalogo import ReferenciaFicha
from modelo.conocimiento import ConocimientoMapa
from modelo.rastro import SalaRastro


# Tipos exactos: None se resuelve antes, sin calcular su tipo. Los valores más
# frecuentes de los campos van primero; no se aceptan subclases sin esquema.
_VALORES_INMUTABLES = (int, str, bool, float, bytes)

# Solo números ordinales: el significado de cada ID pertenece a su punto.
# Catálogo fijo e inmutable, sin modelos ni crecimiento durante las capturas.
_LIMITE_REFERENCIAS_ID = 16384
_REFERENCIAS_ID = tuple((numero,) for numero in range(_LIMITE_REFERENCIAS_ID))

_TIPOS = TablaIdentidades(64)
_POR_ID = [None] * (max(e[0] for e in _ESQUEMAS) + 1)
for _esquema in _ESQUEMAS:
    _nombres = _esquema[2]
    _lector = attrgetter(*_nombres) if len(_nombres) > 1 else None
    _TIPOS.insertar(_esquema[1], (*_esquema, _lector))
    _POR_ID[_esquema[0]] = _esquema


@dataclass(frozen=True)
class InstantaneaInmutable:
    raiz: object
    registros: tuple

    def reconstruir(self, referencias=None, creados=None):
        objetos = [None] * len(self.registros)
        conocimientos = []
        for i, (codigo, datos) in enumerate(self.registros):
            if codigo == 0:
                continue
            clase = _POR_ID[codigo][1]
            if clase is list:
                nuevo = []
            elif clase is dict:
                nuevo = {}
            elif clase is random.Random:
                nuevo = random.Random(0)
                nuevo.setstate(datos)
            else:
                nuevo = clase.__new__(clase)
                if clase is ConocimientoMapa:
                    conocimientos.append(nuevo)
                elif clase is ReferenciaFicha and referencias is not None:
                    referencias.append(nuevo)
            objetos[i] = nuevo
            if creados is not None and clase is not random.Random:
                creados.append(nuevo)

        def resolver(valor):
            if type(valor) is not tuple:
                return valor
            indice = valor[0]
            if objetos[indice] is None:
                objetos[indice] = tuple(resolver(v) for v in self.registros[indice][1])
            return objetos[indice]

        try:
            for i, (codigo, datos) in enumerate(self.registros):
                nuevo = objetos[i]
                if codigo == 0:
                    resolver((i,))
                elif codigo == 18:
                    nuevo.extend(resolver(v) for v in datos)
                elif codigo == 19:
                    for clave, valor in datos:
                        nuevo[resolver(clave)] = resolver(valor)
                elif codigo != 20:
                    _, _, obligatorios, opcionales = _POR_ID[codigo]
                    mascara = datos[0]
                    for posicion, nombre in enumerate(obligatorios, 1):
                        setattr(nuevo, nombre, resolver(datos[posicion]))
                    posicion = len(obligatorios) + 1
                    for bit, nombre in enumerate(opcionales):
                        if mascara & (1 << bit):
                            setattr(nuevo, nombre, resolver(datos[posicion]))
                            posicion += 1
                    _completar_no_persistentes(nuevo, nuevo)
            for conocimiento in conocimientos:
                conocimiento.reconstruir()
            return resolver(self.raiz)
        finally:
            # La función recursiva no debe mantener el grafo hasta el próximo GC.
            resolver = None


def _mismos_tipos_y_bits(a, b):
    """Tras igualdad de tuplas: distinguir tipos numéricos y signo de cero."""
    for i in range(len(a)):
        x, y = a[i], b[i]
        if x is y:
            continue
        tipo = type(x)
        if tipo is not type(y):
            return False
        if tipo is tuple:
            if not _mismos_tipos_y_bits(x, y):
                return False
        elif tipo is float and struct.pack('!d', x) != struct.pack('!d', y):
            return False
    return True


def capturar_estado(raiz, anterior=None):
    previos = anterior.registros if anterior is not None else ()
    capacidad = 1024
    if (type(raiz) is tuple and raiz and type(raiz[-1]) is list
            and raiz[-1] and type(raiz[-1][0]) is SalaRastro):
        # Reserva temporal medida: menor carga y menos colisiones. La tabla
        # se libera al devolver el punto y conserva su crecimiento si hace falta.
        capacidad = max(capacidad, 64 * len(raiz[-1]))
    identidades = TablaIdentidades(capacidad)
    registros, pendientes = [], []

    def referencia(valor):
        if valor is None:
            return None
        tipo = type(valor)
        if tipo in _VALORES_INMUTABLES:
            return valor
        indice = identidades._localizar(valor)
        if identidades.claves[indice] is not _VACIA:
            return identidades.valores[indice]
        # Los contenedores tienen una rama explícita al procesar pendientes;
        # no utilizan campos del esquema ni necesitan buscarlo en la tabla.
        if tipo is tuple or tipo is list or tipo is dict or tipo is random.Random:
            esquema = None
        else:
            esquema = _TIPOS.buscar(tipo)
            if esquema is None:
                raise TypeError(f'tipo sin esquema de estado: {tipo.__name__}')
        numero = len(registros)
        if numero < _LIMITE_REFERENCIAS_ID:
            ref = _REFERENCIAS_ID[numero]
            numero = ref[0]  # reutilizar también el entero en la pila temporal
        else:
            ref = (numero,)
        identidades.insertar(valor, ref, indice=indice)
        registros.append(None)
        pendientes.append((numero, valor, esquema))
        return ref

    resultado = referencia(raiz)
    while pendientes:
        numero, original, esquema = pendientes.pop()
        tipo = type(original)
        if tipo is tuple or tipo is list:
            codigo = 0 if tipo is tuple else 18
            # La comprensión evita suspender/reanudar un generador por campo.
            # La lista temporal solo vive hasta construir esta tupla.
            datos = tuple([referencia(v) for v in original])
        elif tipo is dict:
            codigo = 19
            datos = tuple([(referencia(k), referencia(v)) for k, v in original.items()])
        elif tipo is random.Random:
            codigo, datos = 20, original.getstate()
        else:
            codigo, _, obligatorios, opcionales, leer = esquema
            # Una sola tupla de campos evita retener contenedores separados
            # para requeridos/opcionales en cada objeto de cada punto.
            if leer is None:
                valores = [referencia(getattr(original, n)) for n in obligatorios]
            else:
                valores = [referencia(v) for v in leer(original)]
            mascara = 0
            for bit, nombre in enumerate(opcionales):
                valor = getattr(original, nombre, _VACIA)
                if valor is not _VACIA:
                    mascara |= 1 << bit
                    valores.append(referencia(valor))
            valores.insert(0, mascara)
            datos = tuple(valores)
        if numero < len(previos):
            previo = previos[numero]
            if (previo[0] == codigo and previo[1] == datos
                    and _mismos_tipos_y_bits(previo[1], datos)):
                registros[numero] = previo
                continue
        registros[numero] = (codigo, datos)
    return InstantaneaInmutable(resultado, tuple(registros))
