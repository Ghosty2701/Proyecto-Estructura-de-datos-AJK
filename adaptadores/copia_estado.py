"""Copia completa del estado en memoria para puntos de control (D-LT-04; FR-LT-013/014).

El copiador recorre el grafo con una pila propia (sin recursión) y conserva
referencias compartidas y ciclos mediante una tabla de identidades propia de
direccionamiento abierto. Los campos copiados por tipo son los del esquema
explícito del guardado binario: «estado completo» significa lo mismo al guardar
y al crear un punto. Los auxiliares derivados se reconstruyen como al cargar.
No usa dict/set como índice ni copy.deepcopy (constitución, principio I).
"""
import random

from adaptadores import estado_binario
from adaptadores.cache_catalogo import ReferenciaFicha
from controlador.partida import Partida
from modelo.conocimiento import ConocimientoMapa
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.tabla_hash import _mezclar
from modelo.rastro import SalaRastro

_INMUTABLES = (type(None), bool, int, float, str, bytes)
_VACIA = object()


class TablaIdentidades:
    """Clave: identidad del objeto original; valor: su copia (o datos por tipo).

    Direccionamiento abierto con doble hashing; capacidad potencia de dos y
    crecimiento al superar el 70 % de carga. Guarda la clave para mantenerla
    viva y comparar por identidad.
    """

    def __init__(self, capacidad=64):
        tamano = 8
        while tamano < capacidad:
            tamano *= 2
        self.capacidad = tamano
        self.cantidad = 0
        self.claves = [_VACIA] * tamano
        self.valores = [None] * tamano

    def _localizar(self, clave):
        numero = id(clave)
        mascara = self.capacidad - 1
        # Los bits bajos de las direcciones suelen representar alineación.
        # Plegar bits altos da un índice barato; identidad y doble hashing
        # siguen resolviendo cualquier colisión, sin suponer IDs únicos aquí.
        plegado = numero >> 4
        indice = (plegado ^ (plegado >> 16) ^ (plegado >> 32)) & mascara
        claves = self.claves
        actual = claves[indice]
        if actual is _VACIA or actual is clave:
            return indice
        # El segundo hash solo hace falta si la primera casilla colisionó.
        # Se conserva exactamente la misma secuencia de doble hashing.
        paso = (_mezclar(numero ^ 0x5bd1e995) & mascara) | 1
        while True:
            indice = (indice + paso) & mascara
            actual = claves[indice]
            if actual is _VACIA or actual is clave:
                return indice

    def buscar(self, clave, defecto=None):
        indice = self._localizar(clave)
        return defecto if self.claves[indice] is _VACIA else self.valores[indice]

    def insertar(self, clave, valor, *, indice=None):
        # El copiador puede reutilizar una casilla recién localizada si no
        # insertó otros objetos entre ambas operaciones.
        if indice is None:
            indice = self._localizar(clave)
        if self.claves[indice] is _VACIA:
            if (self.cantidad + 1) * 10 > self.capacidad * 7:
                self._crecer()
                indice = self._localizar(clave)
            self.cantidad += 1
        self.claves[indice] = clave
        self.valores[indice] = valor

    def _crecer(self):
        claves, valores = self.claves, self.valores
        self.capacidad *= 2
        self.claves = [_VACIA] * self.capacidad
        self.valores = [None] * self.capacidad
        for clave, valor in zip(claves, valores):
            if clave is not _VACIA:
                indice = self._localizar(clave)
                self.claves[indice] = clave
                self.valores[indice] = valor


def _campos_por_tipo():
    tabla = TablaIdentidades(len(estado_binario._ESQUEMAS) * 2)
    for _, clase, obligatorios, opcionales in estado_binario._ESQUEMAS:
        if clase not in (list, dict, random.Random):
            tabla.insertar(clase, (obligatorios, opcionales))
    return tabla


_CAMPOS = _campos_por_tipo()


def _completar_no_persistentes(original, copia):
    """Campos que el esquema no guarda: se fijan como al cargar una partida."""
    tipo = type(copia)
    if tipo is ActorTurnos:
        copia.ultima_ruta = None
    elif tipo is MotorEventos:
        copia.revision_conexiones = 0
        copia.hubo_dano = False
        copia.enemigos_entrada = False
        copia.tiempo_limite = None
        copia.limite_alcanzado = False
    elif tipo is Partida:
        copia.preparar_sala = None
        copia.fuente = None
        copia.gestor_guardado = None
        copia._mensajes = []
        copia._inicio_pendiente = False
        copia._ataque_pendiente = None
        copia.ruta_guardado = getattr(original, "ruta_guardado", "partida.bin")
        copia.bitacora_activa = False
        copia.linea_tiempo = None
        copia.gestor_linea = None
        copia._reloj_linea = 0
        copia._acciones_linea = 0


def copiar_estado(raiz, referencias=None, *, sustituciones=(), reconstruir=True, capacidad=None, creados=None):
    """Devuelve una copia independiente del grafo alcanzable desde raiz.

    Si se pasa la lista referencias, recibe las ReferenciaFicha copiadas para que
    el llamador complete sus datos sin red antes de re-simular.
    """
    if capacidad is None:
        capacidad = 1024
        # Las raíces de una partida incluyen la lista de salas. Reservar una
        # estimación evita ampliar y reinsertar varias veces en cada punto.
        # Es solo una reserva: la misma tabla crece si el grafo resulta mayor.
        if (type(raiz) is tuple and raiz and type(raiz[-1]) is list
                and raiz[-1] and type(raiz[-1][0]) is SalaRastro):
            capacidad = max(capacidad, 32 * len(raiz[-1]))
    copias = TablaIdentidades(capacidad)
    # Uso experimental: sustituir enlaces por tokens o resolverlos al restaurar.
    for original, sustituto in sustituciones:
        copias.insertar(original, sustituto)
    pendientes = []
    conocimientos = []
    campos = _CAMPOS

    def copia_de(valor):
        tipo = type(valor)
        if tipo in _INMUTABLES:
            return valor
        indice = copias._localizar(valor)
        if copias.claves[indice] is not _VACIA:
            return copias.valores[indice]
        if tipo is tuple:
            elementos = [copia_de(elemento) for elemento in valor]
            # Una tupla de inmutables se comparte: su contenido no puede cambiar.
            for elemento, nuevo in zip(valor, elementos):
                if elemento is not nuevo:
                    nueva = tuple(elementos)
                    break
            else:
                # Una tupla que no cambió conserva su identidad sin registrarla:
                # volver a encontrarla devolverá el mismo objeto inmutable.
                return valor
            # La recursión de tuplas sí pudo insertar otros objetos o ampliar
            # la tabla: en ese caso se vuelve a localizar la casilla.
            copias.insertar(valor, nueva)
            return nueva
        if tipo is list:
            nueva = []
        elif tipo is dict:
            nueva = {}
        elif tipo is random.Random:
            nueva = random.Random(0)
            nueva.setstate(valor.getstate())
            copias.insertar(valor, nueva, indice=indice)
            return nueva
        else:
            if campos.buscar(tipo) is None:
                raise TypeError(f"tipo sin esquema de estado: {tipo.__name__}")
            nueva = tipo.__new__(tipo)
            if tipo is ConocimientoMapa:
                conocimientos.append(nueva)
            elif tipo is ReferenciaFicha and referencias is not None:
                referencias.append(nueva)
        copias.insertar(valor, nueva, indice=indice)
        if creados is not None:
            creados.append(nueva)
        pendientes.append((valor, nueva))
        return nueva

    try:
        resultado = copia_de(raiz)
        while pendientes:
            original, copia = pendientes.pop()
            tipo = type(copia)
            if tipo is list:
                copia.extend([copia_de(elemento) for elemento in original])
            elif tipo is dict:
                for clave, elemento in original.items():
                    copia[clave] = copia_de(elemento)
            else:
                obligatorios, opcionales = campos.buscar(tipo)
                for nombre in obligatorios:
                    setattr(copia, nombre, copia_de(getattr(original, nombre)))
                for nombre in opcionales:
                    valor = getattr(original, nombre, _VACIA)
                    if valor is not _VACIA:
                        setattr(copia, nombre, copia_de(valor))
                _completar_no_persistentes(original, copia)
        if reconstruir:
            for conocimiento in conocimientos:
                conocimiento.reconstruir()
        return resultado
    finally:
        # Romper la autorreferencia de la funcion recursiva libera su tabla
        # auxiliar al regresar, sin esperar a una recoleccion de ciclos.
        copia_de = None
