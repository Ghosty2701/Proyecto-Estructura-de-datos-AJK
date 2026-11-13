"""Piloto de captura con marcas explícitas; NO conectado a la partida.

Hash propio e IDs estables por sesión. Por defecto el oráculo completo detecta
marcas omitidas antes de publicar. El barrido de retiro lee registros, nunca
atributos del modelo. Su costo O(C + E) debe incluirse en toda medición.
"""
import random
import struct
from dataclasses import dataclass

from adaptadores.instantanea_inmutable import (
    InstantaneaInmutable, _TIPOS, _VACIA, capturar_estado,
)
from modelo.indice_versionado import VersionRegistros, ELIMINAR, _localizar, _rehash, _TUMBA
from modelo.tabla_hash import _mezclar


class ErrorCobertura(RuntimeError):
    """El estado incremental no coincide con el estado persistible vivo."""


def _primitivo(valor):
    return valor is None or type(valor) in (bool, int, float, str, bytes)


def _comprobar_tipo(valor):
    tipo = type(valor)
    if tipo not in (tuple, list, dict, random.Random) and _TIPOS.buscar(tipo) is None:
        raise TypeError(f'tipo sin esquema de estado: {tipo.__name__}')


@dataclass(slots=True)
class _Entrada:
    objeto: object
    referencia: tuple
    sucio: bool = True


def _inicio_identidad(numero, mascara):
    plegado = numero >> 4
    return (plegado ^ (plegado >> 16) ^ (plegado >> 32)) & mascara


class _IndicePorId:
    """Hash inverso mutable, privado; entradas vivas, no registros de puntos."""

    def __init__(self):
        self.casillas = [None] * 32
        self.cantidad = self.tumbas = self.recomposiciones = 0

    def copiar(self):
        copia = _IndicePorId()
        copia.casillas = self.casillas.copy()
        copia.cantidad, copia.tumbas = self.cantidad, self.tumbas
        copia.recomposiciones = self.recomposiciones
        return copia

    def _recomponer(self, capacidad):
        self.casillas = _rehash(self.casillas, capacidad)
        self.tumbas = 0
        self.recomposiciones += 1

    def insertar(self, entrada):
        clave = entrada.referencia[0]
        if (self.cantidad + 1) * 10 > len(self.casillas) * 7:
            self._recomponer(len(self.casillas) * 2)
        elif (self.cantidad + self.tumbas + 1) * 10 > len(self.casillas) * 7:
            self._recomponer(len(self.casillas))
        posicion, existe = _localizar(self.casillas, clave)
        if existe:
            raise RuntimeError('ID de sesión duplicado')
        if self.casillas[posicion] is _TUMBA:
            self.tumbas -= 1
        self.casillas[posicion] = (clave, entrada)
        self.cantidad += 1

    def obtener(self, clave):
        posicion, existe = _localizar(self.casillas, clave)
        return self.casillas[posicion][1] if existe else None

    def borrar(self, clave):
        posicion, existe = _localizar(self.casillas, clave)
        if not existe:
            raise RuntimeError('ID retirado sin entrada viva')
        self.casillas[posicion] = _TUMBA
        self.cantidad -= 1
        self.tumbas += 1

    def reducir(self):
        if self.cantidad * 40 < len(self.casillas) * 7 and len(self.casillas) > 8:
            capacidad = 8
            while self.cantidad * 10 > capacidad * 7:
                capacidad *= 2
            self._recomponer(capacidad)


class _Identidades:
    """Índice fuerte por identidad. Copiar el vector permite preparar altas."""

    def __init__(self, capacidad=32):
        tamano = 8
        while tamano < capacidad:
            tamano *= 2
        self.casillas = [None] * tamano
        self.cantidad = 0
        self.siguiente = 0
        self.tumbas = self.recomposiciones = 0
        self.por_id = _IndicePorId()

    def _posicion(self, objeto):
        numero = id(objeto)
        mascara = len(self.casillas) - 1
        posicion = _inicio_identidad(numero, mascara)
        paso = None
        primera_tumba = None
        for _ in range(len(self.casillas)):
            entrada = self.casillas[posicion]
            if entrada is None:
                return posicion if primera_tumba is None else primera_tumba
            if entrada is _TUMBA:
                if primera_tumba is None:
                    primera_tumba = posicion
            elif entrada.objeto is objeto:
                return posicion
            if paso is None:
                paso = (_mezclar(numero ^ 0x9e3779b97f4a7c15) & mascara) | 1
            posicion = (posicion + paso) & mascara
        if primera_tumba is not None:
            return primera_tumba
        raise RuntimeError('índice de identidades lleno')

    def copiar(self):
        copia = _Identidades()
        copia.casillas = self.casillas.copy()
        copia.cantidad, copia.siguiente = self.cantidad, self.siguiente
        copia.tumbas, copia.recomposiciones = self.tumbas, self.recomposiciones
        copia.por_id = self.por_id.copiar()
        return copia

    def entradas(self):
        return (e for e in self.casillas if e is not None and e is not _TUMBA)

    def _recomponer(self, capacidad):
        anteriores = self.casillas
        self.casillas = [None] * capacidad
        for actual in anteriores:
            if actual is not None and actual is not _TUMBA:
                self.casillas[self._posicion(actual.objeto)] = actual
        self.tumbas = 0
        self.recomposiciones += 1

    def insertar(self, entrada):
        if (self.cantidad + 1) * 10 > len(self.casillas) * 7:
            self._recomponer(len(self.casillas) * 2)
        elif (self.cantidad + self.tumbas + 1) * 10 > len(self.casillas) * 7:
            self._recomponer(len(self.casillas))
        posicion = self._posicion(entrada.objeto)
        if self.casillas[posicion] is _TUMBA:
            self.tumbas -= 1
        self.casillas[posicion] = entrada
        self.cantidad += 1
        self.por_id.insertar(entrada)

    def obtener(self, objeto):
        entrada = self.casillas[self._posicion(objeto)]
        return None if entrada is _TUMBA else entrada

    def registrar(self, objeto):
        _comprobar_tipo(objeto)
        entrada = _Entrada(objeto, (self.siguiente,))
        self.siguiente += 1
        self.insertar(entrada)
        return entrada

    def borrar_ids(self, ids):
        for numero in ids:
            entrada = self.por_id.obtener(numero)
            if entrada is None:
                raise RuntimeError('ID retirado sin entrada viva')
            posicion = self._posicion(entrada.objeto)
            self.casillas[posicion] = _TUMBA
            self.cantidad -= 1
            self.tumbas += 1
            self.por_id.borrar(numero)
        if self.cantidad * 40 < len(self.casillas) * 7 and len(self.casillas) > 8:
            capacidad = 8
            while self.cantidad * 10 > capacidad * 7:
                capacidad *= 2
            self._recomponer(capacidad)
        self.por_id.reducir()


def _valores_enlazados(codigo, datos):
    if codigo == 20:  # Random.getstate contiene tuplas de valores, no IDs.
        return ()
    if codigo == 19:
        return (valor for par in datos for valor in par)
    return datos if codigo in (0, 18) else datos[1:]


def _retirar(raiz, version):
    vistos = [False] * len(version.casillas)
    pendientes = [raiz]
    while pendientes:
        valor = pendientes.pop()
        if type(valor) is not tuple:
            continue
        posicion, existe = _localizar(version.casillas, valor[0])
        if not existe:
            raise RuntimeError('referencia sin registro en el punto')
        if vistos[posicion]:
            continue
        vistos[posicion] = True
        codigo, datos = version.casillas[posicion][1]
        pendientes.extend(_valores_enlazados(codigo, datos))
    bajas = [(entrada[0], ELIMINAR)
             for posicion, entrada in enumerate(version.casillas)
             if entrada is not None and entrada != () and not vistos[posicion]]
    return version.con_cambios(bajas) if bajas else version, [numero for numero, _ in bajas]


@dataclass(frozen=True, slots=True)
class PuntoIncremental:
    raiz: object
    version: VersionRegistros

    def a_inmutable(self):
        """IDs dispersos a ordinales locales, sin objetos ni otro índice hash."""
        ordinales = [None] * len(self.version.casillas)
        entradas = []
        for posicion, entrada in enumerate(self.version.casillas):
            if entrada is not None and entrada != ():
                ordinales[posicion] = len(entradas)
                entradas.append(entrada[1])

        def resolver(valor):
            if type(valor) is not tuple:
                return valor
            posicion, existe = _localizar(self.version.casillas, valor[0])
            if not existe:
                raise RuntimeError('referencia sin registro en el punto')
            return (ordinales[posicion],)

        registros = []
        for codigo, datos in entradas:
            if codigo == 20:
                nuevos = datos
            elif codigo == 19:
                nuevos = tuple((resolver(k), resolver(v)) for k, v in datos)
            elif codigo in (0, 18):
                nuevos = tuple(resolver(v) for v in datos)
            else:
                nuevos = (datos[0], *(resolver(v) for v in datos[1:]))
            registros.append((codigo, nuevos))
        return InstantaneaInmutable(resolver(self.raiz), tuple(registros))

    def reconstruir(self, referencias=None, creados=None):
        return self.a_inmutable().reconstruir(referencias, creados)


def _exactamente(a, b):
    pendientes = [(a, b)]
    while pendientes:
        a, b = pendientes.pop()
        if type(a) is not type(b):
            return False
        if type(a) is tuple:
            if len(a) != len(b):
                return False
            pendientes.extend(zip(a, b))
        elif type(a) is float:
            if struct.pack('!d', a) != struct.pack('!d', b):
                return False
        elif a != b:
            return False
    return True


def comprobar_equivalencia(raiz, punto):
    """Normalizar IDs por el mismo recorrido completo, incluido orden y alias."""
    esperado = capturar_estado(raiz)
    obtenido = capturar_estado(punto.reconstruir())
    if not _exactamente((esperado.raiz, esperado.registros),
                       (obtenido.raiz, obtenido.registros)):
        raise ErrorCobertura('mutación sin marcar: estado incremental diferente del completo')


class CapturadorIncremental:
    def __init__(self):
        self._identidades = _Identidades()
        self._pendientes = []
        self.actual = None
        self.estadisticas = {}
        self._cerrado = False

    @property
    def registrados(self):
        return self._identidades.cantidad

    @property
    def pendientes(self):
        return len(self._pendientes)

    @property
    def siguiente_id(self):
        return self._identidades.siguiente

    def _abierto(self):
        if self._cerrado:
            raise RuntimeError('capturador cerrado')

    def marcar(self, objeto):
        self._abierto()
        if _primitivo(objeto):
            return
        entrada = self._identidades.obtener(objeto)
        if entrada is None:
            entrada = self._identidades.registrar(objeto)
            self._pendientes.append(entrada)
        elif not entrada.sucio:
            entrada.sucio = True
            self._pendientes.append(entrada)

    def capturar(self, raiz, *, verificar=True):
        self._abierto()
        identidades = self._identidades.copiar()
        pendientes = self._pendientes.copy()
        cambios = []
        codificados = campos = nuevos = 0

        def referencia(valor):
            nonlocal nuevos
            if _primitivo(valor):
                return valor
            entrada = identidades.obtener(valor)
            if entrada is None:
                entrada = identidades.registrar(valor)
                pendientes.append(entrada)
                nuevos += 1
            return entrada.referencia

        resultado = referencia(raiz)
        # El cursor permite descubrir registros nuevos sin recursión ni duplicados.
        cursor = 0
        while cursor < len(pendientes):
            entrada = pendientes[cursor]
            cursor += 1
            original = entrada.objeto
            tipo = type(original)
            codificados += 1
            if tipo in (tuple, list):
                codigo = 0 if tipo is tuple else 18
                datos = tuple(referencia(v) for v in original)
                campos += len(datos)
            elif tipo is dict:
                codigo = 19
                datos = tuple((referencia(k), referencia(v)) for k, v in original.items())
                campos += 2 * len(datos)
            elif tipo is random.Random:
                codigo, datos = 20, original.getstate()
                campos += 1
            else:
                codigo, _, obligatorios, opcionales, leer = _TIPOS.buscar(tipo)
                valores = ([referencia(getattr(original, n)) for n in obligatorios]
                           if leer is None else [referencia(v) for v in leer(original)])
                campos += len(obligatorios) + len(opcionales)
                mascara = 0
                for bit, nombre in enumerate(opcionales):
                    valor = getattr(original, nombre, _VACIA)
                    if valor is not _VACIA:
                        mascara |= 1 << bit
                        valores.append(referencia(valor))
                datos = (mascara, *valores)
            cambios.append((entrada.referencia[0], (codigo, datos)))
        anterior = self.actual.version if self.actual else VersionRegistros.vacia()
        version, retirados = _retirar(resultado, anterior.con_cambios(cambios))
        identidades.borrar_ids(retirados)
        punto = PuntoIncremental(resultado, version)
        if verificar:
            comprobar_equivalencia(raiz, punto)
        estadisticas = {
            'objetos_codificados': codificados, 'campos_leidos': campos,
            'objetos_nuevos_descubiertos': nuevos,
            'marcas_pendientes': len(self._pendientes),
            'registros_retirados': len(retirados), 'registros_vivos': version.cantidad,
            'capacidad_version': len(version.casillas),
            'capacidad_identidades': len(identidades.casillas),
            'capacidad_inverso': len(identidades.por_id.casillas),
            'tumbas_identidades': identidades.tumbas,
            'tumbas_inverso': identidades.por_id.tumbas,
            'recomposiciones_identidades': identidades.recomposiciones,
            'recomposiciones_inverso': identidades.por_id.recomposiciones,
            'oraculo_completo': verificar,
        }
        # Ninguna escritura del estado de sesión ocurre antes de este punto.
        for entrada in pendientes:
            entrada.sucio = False
        self._identidades, self._pendientes = identidades, []
        self.actual, self.estadisticas = punto, estadisticas
        return punto

    def cerrar(self):
        self._identidades = _Identidades()
        self._pendientes = []
        self.actual = None
        self._cerrado = True

    def __enter__(self):
        self._abierto()
        return self

    def __exit__(self, *error):
        self.cerrar()
