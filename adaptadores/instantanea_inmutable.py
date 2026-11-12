"""Puntos en registros inmutables: los enlaces del modelo son IDs locales.

El esquema es el del guardado; esta representación solo existe en memoria.
Las tuplas originales también tienen registro, por lo que una referencia (ID,)
no se confunde con los valores del modelo. No retiene objetos del grafo vivo.
"""
import random
from dataclasses import dataclass

from adaptadores.estado_binario import _ESQUEMAS
from adaptadores.copia_estado import (
    TablaIdentidades, _VACIA, _INMUTABLES, _completar_no_persistentes,
)
from adaptadores.cache_catalogo import ReferenciaFicha
from modelo.conocimiento import ConocimientoMapa
from modelo.rastro import SalaRastro


_TIPOS = TablaIdentidades(64)
_POR_ID = [None] * (max(e[0] for e in _ESQUEMAS) + 1)
for _esquema in _ESQUEMAS:
    _TIPOS.insertar(_esquema[1], _esquema)
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
                    requeridos, mascara, adicionales = datos
                    for nombre, valor in zip(obligatorios, requeridos):
                        setattr(nuevo, nombre, resolver(valor))
                    posicion = 0
                    for bit, nombre in enumerate(opcionales):
                        if mascara & (1 << bit):
                            setattr(nuevo, nombre, resolver(adicionales[posicion]))
                            posicion += 1
                    _completar_no_persistentes(nuevo, nuevo)
            for conocimiento in conocimientos:
                conocimiento.reconstruir()
            return resolver(self.raiz)
        finally:
            # La función recursiva no debe mantener el grafo hasta el próximo GC.
            resolver = None


def capturar_estado(raiz):
    capacidad = 1024
    if (type(raiz) is tuple and raiz and type(raiz[-1]) is list
            and raiz[-1] and type(raiz[-1][0]) is SalaRastro):
        capacidad = max(capacidad, 32 * len(raiz[-1]))
    identidades = TablaIdentidades(capacidad)
    registros, pendientes = [], []

    def referencia(valor):
        tipo = type(valor)
        if tipo in _INMUTABLES:
            return valor
        indice = identidades._localizar(valor)
        if identidades.claves[indice] is not _VACIA:
            return identidades.valores[indice]
        esquema = None if tipo is tuple else _TIPOS.buscar(tipo)
        if tipo is not tuple and esquema is None:
            raise TypeError(f'tipo sin esquema de estado: {tipo.__name__}')
        numero = len(registros)
        ref = (numero,)
        identidades.insertar(valor, ref, indice=indice)
        registros.append(None)
        pendientes.append((numero, valor, esquema))
        return ref

    resultado = referencia(raiz)
    while pendientes:
        numero, original, esquema = pendientes.pop()
        tipo = type(original)
        if tipo in (tuple, list):
            codigo = 0 if tipo is tuple else 18
            datos = tuple(referencia(v) for v in original)
        elif tipo is dict:
            codigo = 19
            datos = tuple((referencia(k), referencia(v)) for k, v in original.items())
        elif tipo is random.Random:
            codigo, datos = 20, original.getstate()
        else:
            codigo, _, obligatorios, opcionales = esquema
            requeridos = tuple(referencia(getattr(original, n)) for n in obligatorios)
            mascara, adicionales = 0, []
            for bit, nombre in enumerate(opcionales):
                valor = getattr(original, nombre, _VACIA)
                if valor is not _VACIA:
                    mascara |= 1 << bit
                    adicionales.append(referencia(valor))
            datos = (requeridos, mascara, tuple(adicionales))
        registros[numero] = (codigo, datos)
    return InstantaneaInmutable(resultado, tuple(registros))
