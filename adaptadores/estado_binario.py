"""Esquema explicito del modelo, IDs mediante AVL y campos binarios propios.

El guardado captura el estado actual y los deltas ya existentes. Nunca crea
snapshots por accion ni cambia la implementacion del retroceso o del heap.
"""

import math
import os
import random
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from adaptadores.cache_catalogo import ArbolAVL
from adaptadores.guardado_binario import (
    ErrorGuardado, escribir_guardado, leer_globales, leer_guardado, leer_sala,
)
from comun.ordenamiento import vista_ordenada
from modelo.agenda_eventos import AgendaEventos
from modelo.efectos import EstadoEfecto, Trampa
from modelo.evento import Evento
from modelo.inventario import Inventario, NodoInventario
from modelo.inventario_reversible import InventarioReversible, NodoReversible, CambioInventario
from controlador.partida import Partida
from modelo.motor_eventos import ActorTurnos, EventoActor, EventoEntorno, MotorEventos
from modelo.rastro import Puerta, SalaRastro, SalidaRastro
from modelo.retroceso import CambiosAccion, HistorialRetroceso

VERSION_MODELO = 2
MAGIC_MODELO = b"MDLO"
MAGIC_SALA = b"SALA"


@dataclass
class ObjetoPartida:
    """Registro de objeto para la frontera con el inventario, sin reglas de uso."""
    id: str
    clase: str
    nombre: str
    peso: int = 0
    valor: int = 0
    ataque_bonus: int = 0
    defensa_bonus: int = 0
    ficha: object = None


@dataclass
class IdentidadGuardado:
    id_cripta: str
    version_cripta: str
    version_catalogo: str


@dataclass
class PartidaCargada:
    motor: MotorEventos
    jugador: ActorTurnos
    salas: list
    identidad: IdentidadGuardado
    datos_extra: object = None


@dataclass
class SalaGuardada:
    """Vista de disco autocontenida, no una sala del motor con enlaces incompletos.

    salidas: (direccion, destino_id, abierta, llave, cierre_automatico).
    actores: (actor_id, es_jugador, vida, vida_max, ataque, defensa, velocidad).
    objetos: (id, clase, nombre). trampas: (id, tipo, cantidad, duracion,
    rearme, armada, tiempo_rearme). Los registros completos estan en el bloque.
    """
    sala_id: int
    nombre: str
    ultimo_rastro: object
    contenido_cargado: bool
    salidas: tuple
    actores: tuple
    objetos: tuple
    trampas: tuple


# IDs de tipo y orden de campos son parte del formato VERSION_MODELO.
# Cada campo requerido y opcional se enumera: no se serializa __dict__.
_ITEM_OPCIONALES = (
    "id", "clase", "nombre", "peso", "valor", "ataque_bonus", "defensa_bonus",
    "ficha", "cantidad", "curacion", "duracion", "modificador_velocidad", "recogido_fuera_historial",
)
_ESQUEMAS = (
    (1, MotorEventos, ("reloj", "agenda", "historial", "semilla", "azar"), ()),
    (2, AgendaEventos, ("heap", "siguiente_secuencia"), ()),
    (3, HistorialRetroceso, ("acciones",), ()),
    (4, CambiosAccion, ("reloj_anterior", "cambios"), ()),
    (5, ActorTurnos, (
        "actor_id", "vida", "vida_max", "velocidad", "ataque", "defensa",
        "comportamiento", "activo", "proxima_accion", "primer_evento", "sala_actual",
        "inventario", "veneno", "efecto_velocidad", "antorcha", "regeneracion",
        "regeneracion_cantidad",
    ), ("tipo", "nombre", "ficha", "suelta")),
    (6, SalaRastro, (
        "sala_id", "ultimo_rastro", "salidas", "enemigos", "trampas", "contenido_cargado",
    ), ("nombre", "objetos_suelo")),
    (7, Puerta, ("abierta", "llave", "cierre_automatico"), ("abierta_con_llave",)),
    (8, SalidaRastro, ("destino", "puerta"), ("direccion",)),
    (9, Evento, ("tiempo", "tipo", "actor_id", "secuencia", "cancelado"), ()),
    (10, EventoActor, (
        "tiempo", "tipo", "actor_id", "secuencia", "cancelado", "actor", "anterior",
        "siguiente", "enlazado", "efecto", "sala_actual",
    ), ()),
    (11, EventoEntorno, (
        "tiempo", "tipo", "actor_id", "secuencia", "cancelado", "actor", "objetivo",
    ), ()),
    (12, EstadoEfecto, ("tipo", "cantidad", "fin", "anterior", "evento"), ()),
    (13, Trampa, (
        "instancia_id", "tipo", "cantidad", "duracion", "rearme", "armada", "evento_rearme",
    ), ("ficha",)),
    (14, Inventario, (
        "capacidad", "frente", "final", "cantidad", "cursor", "_arma_equipada", "_armadura_equipada",
    ), ()),
    (15, NodoInventario, ("objeto", "anterior", "siguiente"), ()),
    (16, ObjetoPartida, (
        "id", "clase", "nombre", "peso", "valor", "ataque_bonus", "defensa_bonus", "ficha",
    ), ("recogido_fuera_historial",)),
    # Compatibilidad con registros de objeto usados por las pruebas actuales.
    (17, SimpleNamespace, (), _ITEM_OPCIONALES),
    (18, list, (), ()),
    # Solo registros de datos (p. ej. fichas JSON); los indices usan ArbolAVL.
    (19, dict, (), ()),
    (20, random.Random, (), ()),
    (21, InventarioReversible, (
        "capacidad", "frente", "final", "cantidad", "cursor", "_arma_equipada", "_armadura_equipada",
        "frente_reversible", "final_reversible",
    ), ()),
    (22, NodoReversible, (
        "objeto", "anterior", "siguiente", "reversible", "anterior_reversible", "siguiente_reversible",
    ), ()),
    (23, CambioInventario, (
        "inventario", "tipo", "nodo", "anterior", "siguiente", "anterior_reversible",
        "siguiente_reversible", "cursor", "arma", "armadura", "deshecho",
    ), ()),
    (24, Partida, (
        "motor", "jugador", "enemigos", "sala_salida", "llave_salida", "id_cripta",
        "version_cripta", "nombre_jugador", "acciones_ejecutadas", "victoria",
    ), ()),
)

_PARTIDA_NO_PERSISTENTES = (
    "preparar_sala", "fuente", "_mensajes", "_inicio_pendiente", "_ataque_pendiente",
    "_tiempo_accion", "_vida_inicial", "gestor_guardado", "ruta_guardado", "bitacora_activa",
)


def _esquema(clase_o_numero):
    for esquema in _ESQUEMAS:
        if esquema[0] == clase_o_numero or esquema[1] is clase_o_numero:
            return esquema
    raise ErrorGuardado(f"tipo sin esquema binario: {clase_o_numero!r}")


class _Referencia:
    def __init__(self, numero):
        self.numero = numero


class _Escritor:
    def __init__(self):
        self.datos = bytearray()

    def numero(self, formato, valor):
        try:
            self.datos.extend(struct.pack(formato, valor))
        except (struct.error, OverflowError) as error:
            raise ErrorGuardado(f"numero fuera del formato {formato}: {valor!r}") from error

    def bloque(self, datos):
        self.numero("<I", len(datos))
        self.datos.extend(datos)


class _Lector:
    def __init__(self, datos):
        self.datos = memoryview(datos)
        self.posicion = 0

    def tomar(self, cantidad):
        if cantidad < 0 or cantidad > len(self.datos) - self.posicion:
            raise ErrorGuardado("estado binario truncado")
        inicio = self.posicion
        self.posicion += cantidad
        return self.datos[inicio:self.posicion].tobytes()

    def numero(self, formato):
        return struct.unpack(formato, self.tomar(struct.calcsize(formato)))[0]

    def bloque(self):
        return self.tomar(self.numero("<I"))

    def cantidad(self):
        cantidad = self.numero("<I")
        if cantidad > len(self.datos) - self.posicion:
            raise ErrorGuardado("cantidad inconsistente con el bloque")
        return cantidad

    def terminar(self):
        if self.posicion != len(self.datos):
            raise ErrorGuardado("datos sobrantes en el bloque del modelo")


def _escribir_valor(salida, valor, registrar=None, propietario=None):
    if valor is None:
        salida.numero("<B", 0)
    elif type(valor) is bool:
        salida.numero("<B", 2 if valor else 1)
    elif type(valor) is int:
        salida.numero("<B", 3)
        cantidad = max(1, (valor.bit_length() + 8) // 8)
        salida.bloque(valor.to_bytes(cantidad, "little", signed=True))
    elif type(valor) is float:
        if not math.isfinite(valor):
            raise ErrorGuardado("el estado contiene un numero no finito")
        salida.numero("<B", 4)
        salida.numero("<d", valor)
    elif type(valor) is str:
        salida.numero("<B", 5)
        salida.bloque(valor.encode("utf-8"))
    elif type(valor) is bytes:
        salida.numero("<B", 6)
        salida.bloque(valor)
    elif type(valor) is tuple:
        salida.numero("<B", 8)
        salida.numero("<I", len(valor))
        for elemento in valor:
            _escribir_valor(salida, elemento, registrar, propietario)
    elif registrar is not None:
        salida.numero("<B", 7)
        salida.numero("<I", registrar(valor, propietario))
    else:
        raise ErrorGuardado("un resumen de sala contiene una referencia no resuelta")


def _leer_valor(entrada):
    tipo = entrada.numero("<B")
    if tipo == 0:
        return None
    if tipo in (1, 2):
        return tipo == 2
    if tipo == 3:
        datos = entrada.bloque()
        if not datos:
            raise ErrorGuardado("entero binario vacio")
        return int.from_bytes(datos, "little", signed=True)
    if tipo == 4:
        valor = entrada.numero("<d")
        if not math.isfinite(valor):
            raise ErrorGuardado("numero no finito en el archivo")
        return valor
    if tipo == 5:
        try:
            return entrada.bloque().decode("utf-8")
        except UnicodeError as error:
            raise ErrorGuardado("texto UTF-8 invalido en el estado") from error
    if tipo == 6:
        return entrada.bloque()
    if tipo == 7:
        return _Referencia(entrada.numero("<I"))
    if tipo == 8:
        return tuple(_leer_valor(entrada) for _ in range(entrada.cantidad()))
    raise ErrorGuardado(f"etiqueta de valor desconocida: {tipo}")


def _cabecera(entrada, magic):
    if entrada.tomar(4) != magic:
        raise ErrorGuardado("el bloque no contiene el esquema binario del modelo")
    version = entrada.numero("<H")
    if version != VERSION_MODELO:
        raise ErrorGuardado(f"version de modelo incompatible: {version}")


def _iniciar(salida, magic):
    salida.datos.extend(magic)
    salida.numero("<H", VERSION_MODELO)


def _campo(objeto, nombre, defecto=None):
    # Una ficha JSON es un registro de datos, no un indice de entidades.
    return objeto.get(nombre, defecto) if type(objeto) is dict else getattr(objeto, nombre, defecto)


def _resumen_sala(sala, actores, jugador):
    salidas = tuple((getattr(salida, "direccion", None), salida.destino.sala_id,
                     salida.abierta, salida.puerta.llave, salida.puerta.cierre_automatico)
                    for salida in sala.salidas)
    ocupantes = tuple((actor.actor_id, actor is jugador, actor.vida, actor.vida_max,
                       actor.ataque, actor.defensa, actor.velocidad)
                      for actor in actores if actor.sala_actual is sala)
    objetos = tuple((_campo(objeto, "id"), _campo(objeto, "clase"), _campo(objeto, "nombre"))
                    for objeto in getattr(sala, "objetos_suelo", ()))
    trampas = tuple((trampa.instancia_id, trampa.tipo, trampa.cantidad, trampa.duracion,
                     trampa.rearme, trampa.armada,
                     trampa.evento_rearme.tiempo if trampa.evento_rearme is not None else None)
                    for trampa in sala.trampas)
    return (sala.sala_id, getattr(sala, "nombre", ""), sala.ultimo_rastro,
            sala.contenido_cargado, salidas, ocupantes, objetos, trampas)


class _Registro:
    def __init__(self, salas):
        self.por_identidad = ArbolAVL()
        self.por_sala = ArbolAVL()
        self.objetos = []
        self.globales = []
        for sala in salas:
            if type(sala) is not SalaRastro or type(sala.sala_id) is not int or not 0 <= sala.sala_id < 2**32:
                raise ErrorGuardado("cada sala necesita un ID entero sin signo de 32 bits")
            if self.por_sala.buscar(sala.sala_id) is not None:
                raise ErrorGuardado(f"sala duplicada: {sala.sala_id}")
            self.por_sala.insertar(sala.sala_id, [])

    def registrar(self, objeto, propietario=None):
        encontrado = self.por_identidad.buscar(id(objeto))
        if encontrado is not None:
            return encontrado
        esquema = _esquema(type(objeto))
        if type(objeto) is SalaRastro:
            propietario = objeto.sala_id
        elif type(objeto) is ActorTurnos and objeto.sala_actual is not None:
            propietario = objeto.sala_actual.sala_id
        elif type(objeto) is EventoActor and objeto.actor.sala_actual is not None:
            propietario = objeto.actor.sala_actual.sala_id
        if propietario is not None and self.por_sala.buscar(propietario) is None:
            raise ErrorGuardado(f"la sala referenciada {propietario} no fue incluida")
        if esquema[1] not in (list, dict, random.Random):
            for nombre in vars(objeto):
                if type(objeto) is Partida and nombre in _PARTIDA_NO_PERSISTENTES:
                    continue
                if nombre not in esquema[2] and nombre not in esquema[3]:
                    raise ErrorGuardado(f"campo sin esquema: {type(objeto).__name__}.{nombre}")
        numero = len(self.objetos) + 1
        self.por_identidad.insertar(id(objeto), numero)
        self.objetos.append((objeto, propietario, esquema))
        return numero

    def codificar_registros(self):
        # Lista de pendientes por posicion: no desplaza elementos ni usa deque.
        posicion = 0
        while posicion < len(self.objetos):
            objeto, propietario, esquema = self.objetos[posicion]
            salida = _Escritor()
            salida.numero("<I", posicion + 1)
            salida.numero("<B", esquema[0])
            clase = esquema[1]
            if clase is list:
                salida.numero("<I", len(objeto))
                for valor in objeto:
                    _escribir_valor(salida, valor, self.registrar, propietario)
            elif clase is dict:
                salida.numero("<I", len(objeto))
                for clave, valor in objeto.items():
                    if type(clave) is not str:
                        raise ErrorGuardado("las fichas/los datos extra necesitan claves de texto")
                    _escribir_valor(salida, clave)
                    _escribir_valor(salida, valor, self.registrar, propietario)
            elif clase is random.Random:
                _escribir_valor(salida, objeto.getstate(), self.registrar, propietario)
            else:
                for nombre in esquema[2]:
                    if not hasattr(objeto, nombre):
                        raise ErrorGuardado(f"falta el campo requerido {clase.__name__}.{nombre}")
                    _escribir_valor(salida, getattr(objeto, nombre), self.registrar, propietario)
                for nombre in esquema[3]:
                    presente = hasattr(objeto, nombre)
                    salida.numero("<B", presente)
                    if presente:
                        _escribir_valor(salida, getattr(objeto, nombre), self.registrar, propietario)
            registros = self.globales if propietario is None else self.por_sala.buscar(propietario)
            registros.append(bytes(salida.datos))
            posicion += 1


def _escribir_registros(salida, registros):
    salida.numero("<I", len(registros))
    for registro in registros:
        salida.bloque(registro)


def guardar_partida(ruta, motor, jugador, salas, *, id_cripta, version_cripta,
                    version_catalogo, datos_extra=None):
    """Guarda sin alterar el modelo. Publica el archivo completo con os.replace."""
    if type(motor) is not MotorEventos or type(jugador) is not ActorTurnos:
        raise ErrorGuardado("se requieren MotorEventos y ActorTurnos reales")
    if not salas:
        raise ErrorGuardado("la partida no contiene salas")
    identidad = IdentidadGuardado(id_cripta, version_cripta, version_catalogo)
    _validar_identidad(identidad)
    ordenadas = vista_ordenada(salas, clave=lambda sala: sala.sala_id)
    registro = _Registro(ordenadas)
    raices_salas = [(sala.sala_id, registro.registrar(sala, sala.sala_id)) for sala in ordenadas]
    raiz_motor = registro.registrar(motor)
    raiz_jugador = registro.registrar(jugador)
    raiz_extra = 0 if datos_extra is None else registro.registrar(datos_extra)
    registro.codificar_registros()
    objetos = [objeto for objeto, _, _ in registro.objetos]
    _validar_modelo(motor, jugador, ordenadas, objetos)

    globales = _Escritor()
    _iniciar(globales, MAGIC_MODELO)
    for valor in (id_cripta, version_cripta, version_catalogo):
        _escribir_valor(globales, valor)
    for numero in (raiz_motor, raiz_jugador, raiz_extra):
        globales.numero("<I", numero)
    globales.numero("<I", len(raices_salas))
    for id_sala, raiz_sala in raices_salas:
        globales.numero("<I", id_sala)
        globales.numero("<I", raiz_sala)
    _escribir_registros(globales, registro.globales)
    actores_por_sala = ArbolAVL()
    for sala in ordenadas:
        actores_por_sala.insertar(sala.sala_id, [])
    for objeto in objetos:
        if type(objeto) is ActorTurnos and objeto.sala_actual is not None:
            actores_por_sala.buscar(objeto.sala_actual.sala_id).append(objeto)
    bloques = []
    for sala, (_, raiz_sala) in zip(ordenadas, raices_salas):
        salida = _Escritor()
        _iniciar(salida, MAGIC_SALA)
        salida.numero("<I", raiz_sala)
        _escribir_valor(salida, _resumen_sala(sala, actores_por_sala.buscar(sala.sala_id), jugador))
        _escribir_registros(salida, registro.por_sala.buscar(sala.sala_id))
        bloques.append((sala.sala_id, bytes(salida.datos)))

    destino = Path(ruta)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(prefix=destino.name + ".", suffix=".tmp",
                                         dir=destino.parent, delete=False) as archivo:
            temporal = Path(archivo.name)
        escribir_guardado(temporal, bytes(globales.datos), bloques)
        os.replace(temporal, destino)
    except OSError as error:
        raise ErrorGuardado(f"no se pudo guardar {ruta}: {error}") from error
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def _validar_identidad(identidad):
    for valor in (identidad.id_cripta, identidad.version_cripta, identidad.version_catalogo):
        if type(valor) is not str or not valor:
            raise ErrorGuardado("id y versiones de la partida deben ser textos no vacios")


def _leer_globales_modelo(datos):
    entrada = _Lector(datos)
    _cabecera(entrada, MAGIC_MODELO)
    identidad = IdentidadGuardado(*(_leer_valor(entrada) for _ in range(3)))
    _validar_identidad(identidad)
    raices = tuple(entrada.numero("<I") for _ in range(3))
    salas = [(entrada.numero("<I"), entrada.numero("<I")) for _ in range(entrada.cantidad())]
    registros = [entrada.bloque() for _ in range(entrada.cantidad())]
    entrada.terminar()
    return identidad, raices, salas, registros


def _leer_bloque_sala(datos):
    entrada = _Lector(datos)
    _cabecera(entrada, MAGIC_SALA)
    raiz = entrada.numero("<I")
    resumen = _leer_valor(entrada)
    if type(resumen) is not tuple or len(resumen) != 8:
        raise ErrorGuardado("resumen de sala invalido")
    registros = [entrada.bloque() for _ in range(entrada.cantidad())]
    entrada.terminar()
    return raiz, SalaGuardada(*resumen), registros


def leer_identidad_guardada(ruta):
    try:
        return _leer_globales_modelo(leer_globales(ruta))[0]
    except OSError as error:
        raise ErrorGuardado(f"no se pudo leer {ruta}: {error}") from error


def leer_sala_guardada(ruta, id_sala):
    """Recupera la vista de una sala con el indice, sin cargar el resto del modelo."""
    try:
        datos = leer_sala(ruta, id_sala)
        if datos is None:
            return None
        _, sala, _ = _leer_bloque_sala(datos)
        if sala.sala_id != id_sala:
            raise ErrorGuardado("la sala no coincide con la entrada de su indice")
        return sala
    except OSError as error:
        raise ErrorGuardado(f"no se pudo leer {ruta}: {error}") from error


def _resolver(valor, objetos):
    if type(valor) is _Referencia:
        objeto = objetos.buscar(valor.numero)
        if objeto is None:
            raise ErrorGuardado(f"referencia a objeto inexistente: {valor.numero}")
        return objeto
    if type(valor) is tuple:
        return tuple(_resolver(elemento, objetos) for elemento in valor)
    return valor


def _leer_registro(datos):
    entrada = _Lector(datos)
    numero = entrada.numero("<I")
    esquema = _esquema(entrada.numero("<B"))
    clase = esquema[1]
    if clase in (list, dict):
        cantidad = entrada.cantidad()
        valores = []
        claves = ArbolAVL()
        for _ in range(cantidad):
            if clase is dict:
                clave = _leer_valor(entrada)
                if type(clave) is not str or claves.buscar(clave) is not None:
                    raise ErrorGuardado("clave de registro de datos invalida o duplicada")
                claves.insertar(clave, True)
                valores.append((clave, _leer_valor(entrada)))
            else:
                valores.append(_leer_valor(entrada))
    elif clase is random.Random:
        valores = _leer_valor(entrada)
    else:
        valores = [(nombre, _leer_valor(entrada)) for nombre in esquema[2]]
        for nombre in esquema[3]:
            presente = entrada.numero("<B")
            if presente not in (0, 1):
                raise ErrorGuardado("marca de campo opcional invalida")
            if presente:
                valores.append((nombre, _leer_valor(entrada)))
    entrada.terminar()
    return numero, esquema, valores


def _crear_registro(datos, objetos):
    numero, esquema, valores = _leer_registro(datos)
    if numero == 0 or objetos.buscar(numero) is not None:
        raise ErrorGuardado("ID de objeto invalido o duplicado")
    clase = esquema[1]
    objeto = random.Random(0) if clase is random.Random else clase.__new__(clase)
    objetos.insertar(numero, objeto)
    return objeto, esquema, valores


def cargar_partida(ruta, *, id_cripta=None, version_cripta=None, version_catalogo=None):
    """Crea todas las entidades antes de resolver IDs. No modifica una partida viva."""
    try:
        globales, bloques = leer_guardado(ruta)
    except OSError as error:
        raise ErrorGuardado(f"no se pudo cargar {ruta}: {error}") from error
    identidad, raices, raices_salas, datos = _leer_globales_modelo(globales)
    for nombre, esperado in (("id_cripta", id_cripta), ("version_cripta", version_cripta),
                             ("version_catalogo", version_catalogo)):
        if esperado is not None and getattr(identidad, nombre) != esperado:
            raise ErrorGuardado(f"{nombre} incompatible con el guardado")
    if len(bloques) != len(raices_salas):
        raise ErrorGuardado("cantidad de salas inconsistente")
    for (id_sala, bloque), (id_esperado, raiz_esperada) in zip(bloques, raices_salas):
        raiz, resumen, registros = _leer_bloque_sala(bloque)
        if id_sala != id_esperado or resumen.sala_id != id_sala or raiz != raiz_esperada:
            raise ErrorGuardado("salas y referencias inconsistentes con el indice")
        datos.extend(registros)
    objetos = ArbolAVL()
    registros = [_crear_registro(dato, objetos) for dato in datos]
    for objeto, esquema, valores in registros:
        clase = esquema[1]
        if clase is list:
            objeto.extend(_resolver(valor, objetos) for valor in valores)
        elif clase is dict:
            for clave, valor in valores:
                objeto[clave] = _resolver(valor, objetos)
        elif clase is random.Random:
            try:
                objeto.setstate(_resolver(valores, objetos))
            except (ValueError, TypeError, OverflowError) as error:
                raise ErrorGuardado("estado de azar invalido") from error
        else:
            for nombre, valor in valores:
                setattr(objeto, nombre, _resolver(valor, objetos))
    motor = _resolver(_Referencia(raices[0]), objetos)
    jugador = _resolver(_Referencia(raices[1]), objetos)
    salas = [_resolver(_Referencia(raiz), objetos) for _, raiz in raices_salas]
    for (id_esperado, _), sala in zip(raices_salas, salas):
        _exigir(type(sala) is SalaRastro and sala.sala_id == id_esperado,
                "ID de sala inconsistente con su entidad")
    extra = None if raices[2] == 0 else _resolver(_Referencia(raices[2]), objetos)
    _validar_modelo(motor, jugador, salas, [objeto for objeto, _, _ in registros])
    return PartidaCargada(motor, jugador, salas, identidad, extra)


def _exigir(condicion, mensaje):
    if not condicion:
        raise ErrorGuardado(mensaje)


def _validar_inventario(inventario):
    _exigir(type(inventario.capacidad) is int and inventario.capacidad > 0,
            "capacidad de inventario invalida")
    _exigir(type(inventario.cantidad) is int and 0 <= inventario.cantidad <= inventario.capacidad,
            "cantidad de inventario invalida")
    vistos = ArbolAVL()
    anterior = None
    actual = inventario.frente
    cantidad = 0
    while actual is not None:
        _exigir(type(actual) in (NodoInventario, NodoReversible) and vistos.buscar(id(actual)) is None,
                "enlaces de inventario invalidos o ciclicos")
        _exigir(actual.anterior is anterior, "enlace anterior del inventario inconsistente")
        vistos.insertar(id(actual), True)
        anterior, actual = actual, actual.siguiente
        cantidad += 1
    _exigir(cantidad == inventario.cantidad and anterior is inventario.final,
            "frente/final/cantidad del inventario inconsistentes")
    for nodo in (inventario.cursor, inventario._arma_equipada, inventario._armadura_equipada):
        _exigir(nodo is None or vistos.buscar(id(nodo)) is not None,
                "cursor o equipo fuera del inventario")
    _exigir((inventario.cursor is None) == (cantidad == 0), "cursor de inventario inconsistente")
    if type(inventario) is InventarioReversible:
        anterior = None
        esperado = inventario.frente_reversible
        actual = inventario.frente
        while actual is not None:
            _exigir(type(actual) is NodoReversible and type(actual.reversible) is bool,
                    "nodo reversible invalido")
            _exigir(actual.reversible == (getattr(actual.objeto, "clase", None) != "pergamino_retroceso"),
                    "marca reversible incompatible con el objeto")
            if actual.reversible:
                _exigir(actual is esperado and actual.anterior_reversible is anterior,
                        "orden auxiliar del inventario inconsistente")
                anterior, esperado = actual, actual.siguiente_reversible
            else:
                _exigir(actual.anterior_reversible is None and actual.siguiente_reversible is None,
                        "pergamino enlazado al orden reversible")
            actual = actual.siguiente
        _exigir(esperado is None and anterior is inventario.final_reversible,
                "final del orden reversible inconsistente")


def _validar_enlaces_actor(actor):
    vistos = ArbolAVL()
    anterior = None
    evento = actor.primer_evento
    while evento is not None:
        _exigir(type(evento) is EventoActor and vistos.buscar(id(evento)) is None,
                "cadena de eventos invalida o ciclica")
        _exigir(evento.actor is actor and evento.enlazado is True and evento.anterior is anterior,
                "enlaces de eventos inconsistentes con su actor")
        vistos.insertar(id(evento), True)
        anterior, evento = evento, evento.siguiente
    if actor.proxima_accion is not None:
        _exigir(vistos.buscar(id(actor.proxima_accion)) is not None,
                "proxima accion fuera de la cadena del actor")


def _validar_modelo(motor, jugador, salas, objetos):
    _exigir(type(motor) is MotorEventos and type(jugador) is ActorTurnos, "raices del modelo invalidas")
    _exigir(type(motor.reloj) is int and motor.reloj >= 0, "reloj invalido")
    _exigir(type(motor.agenda) is AgendaEventos and type(motor.historial) is HistorialRetroceso,
            "agenda o historial invalido")
    _exigir(type(motor.azar) is random.Random, "generador de azar invalido")
    _exigir(type(motor.historial.acciones) is list and len(motor.historial.acciones) <= 5,
            "el historial supera los cinco intervalos")
    for accion in motor.historial.acciones:
        _exigir(type(accion) is CambiosAccion and type(accion.cambios) is list,
                "intervalo reversible invalido")
        for cambio in accion.cambios:
            _exigir(type(cambio) is tuple and len(cambio) == 3, "delta reversible invalido")
            tipo, objeto, anterior = cambio
            _exigir(tipo in ("rastro", "vida", "evento_cancelado", "evento_programado",
                            "evento_extraido", "azar", "atributo", "inventario", "recogida",
                            "objeto_soltado", "botin"), "tipo de delta desconocido")
            if tipo == "atributo":
                _exigir(type(anterior) is tuple and len(anterior) == 2, "delta de atributo invalido")
                esquema = _esquema(type(objeto))
                _exigir(anterior[0] in esquema[2] + esquema[3], "atributo del delta fuera del esquema")
            elif tipo == "rastro":
                _exigir(type(objeto) is SalaRastro and (anterior is None or type(anterior) is int),
                        "delta de rastro invalido")
            elif tipo == "vida":
                _exigir(type(objeto) is ActorTurnos and type(anterior) is int and anterior >= 0,
                        "delta de vida invalido")
            elif tipo in ("inventario", "recogida", "objeto_soltado"):
                _exigir(type(objeto) is InventarioReversible, "inventario de delta invalido")
                if tipo == "inventario":
                    cambio_inventario = anterior
                else:
                    _exigir(type(anterior) is tuple and len(anterior) == (3 if tipo == "recogida" else 2),
                            "delta de suelo invalido")
                    cambio_inventario = anterior[0]
                    _exigir(type(anterior[1]) is list, "suelo de delta invalido")
                _exigir(type(cambio_inventario) is CambioInventario and cambio_inventario.inventario is objeto
                        and not cambio_inventario.deshecho, "cambio de inventario inconsistente")
            elif tipo == "botin":
                _exigir(type(objeto) is list, "suelo de botin invalido")
            elif tipo == "evento_cancelado":
                _exigir(type(objeto) in (Evento, EventoActor, EventoEntorno) and type(anterior) is bool,
                        "delta de cancelacion invalido")
            elif tipo == "evento_programado":
                _exigir(type(objeto) is AgendaEventos and type(anterior) is tuple and len(anterior) == 2
                        and type(anterior[0]) in (Evento, EventoActor, EventoEntorno)
                        and type(anterior[1]) is int and anterior[1] >= 0,
                        "delta de programacion invalido")
            elif tipo == "evento_extraido":
                _exigir(type(objeto) is AgendaEventos and type(anterior) in (Evento, EventoActor, EventoEntorno),
                        "delta de extraccion invalido")
            elif tipo == "azar":
                _exigir(type(objeto) is random.Random, "delta de azar con objeto invalido")
                try:
                    random.Random(0).setstate(anterior)
                except (ValueError, TypeError, OverflowError) as error:
                    raise ErrorGuardado("delta de azar invalido") from error
    _exigir(type(motor.agenda.heap) is list, "heap invalido")
    _exigir(type(motor.agenda.siguiente_secuencia) is int and motor.agenda.siguiente_secuencia >= 0,
            "contador de secuencia invalido")
    secuencias = ArbolAVL()
    for posicion, evento in enumerate(motor.agenda.heap):
        _exigir(type(evento) in (Evento, EventoActor, EventoEntorno), "objeto ajeno al heap")
        _exigir(type(evento.tiempo) is int and evento.tiempo >= 0 and
                type(evento.secuencia) is int and evento.secuencia >= 0,
                "prioridad de evento invalida")
        if posicion:
            padre = motor.agenda.heap[(posicion - 1) // 2]
            _exigir((padre.tiempo, padre.secuencia) <= (evento.tiempo, evento.secuencia),
                    "el heap no conserva su orden")
        if not evento.cancelado:
            _exigir(evento.secuencia < motor.agenda.siguiente_secuencia and
                    secuencias.buscar(evento.secuencia) is None, "secuencia activa invalida o duplicada")
            secuencias.insertar(evento.secuencia, True)
    _exigir(bool(salas) and all(type(sala) is SalaRastro for sala in salas), "salas invalidas")
    salas_validas = ArbolAVL()
    for sala in salas:
        salas_validas.insertar(id(sala), True)
    _exigir(salas_validas.buscar(id(jugador.sala_actual)) is not None,
            "jugador fuera de las salas guardadas")
    for objeto in objetos:
        if type(objeto) in (Inventario, InventarioReversible):
            _validar_inventario(objeto)
        elif type(objeto) is ActorTurnos:
            _exigir(type(objeto.vida) is int and type(objeto.vida_max) is int and
                    0 <= objeto.vida <= objeto.vida_max and objeto.vida_max > 0,
                    "vida de actor invalida")
            _exigir(type(objeto.velocidad) is int and objeto.velocidad > 0, "velocidad de actor invalida")
            _exigir(type(objeto.activo) is bool and type(objeto.ataque) is int and objeto.ataque >= 0 and
                    type(objeto.defensa) is int and objeto.defensa >= 0, "atributos de actor invalidos")
            _exigir(objeto.comportamiento in (None, "guardian", "errante", "rastreador"),
                    "comportamiento de actor invalido")
            _exigir(objeto.inventario is None or type(objeto.inventario) in (Inventario, InventarioReversible),
                    "referencia de inventario invalida")
            _exigir(objeto.sala_actual is None or salas_validas.buscar(id(objeto.sala_actual)) is not None,
                    "actor fuera de las salas guardadas")
            for nombre in ("veneno", "antorcha", "regeneracion", "efecto_velocidad"):
                _exigir(getattr(objeto, nombre) is None or type(getattr(objeto, nombre)) is EstadoEfecto,
                        "referencia de efecto invalida")
            _exigir(objeto.proxima_accion is None or
                    (type(objeto.proxima_accion) is EventoActor and objeto.proxima_accion.actor is objeto),
                    "referencia de proxima accion inconsistente")
            _validar_enlaces_actor(objeto)
        elif type(objeto) is SalaRastro:
            _exigir(salas_validas.buscar(id(objeto)) is not None, "sala fuera de las raices guardadas")
            _exigir(type(objeto.contenido_cargado) is bool and
                    (objeto.ultimo_rastro is None or type(objeto.ultimo_rastro) is int),
                    "estado de sala invalido")
            for nombre, clase in (("salidas", SalidaRastro), ("enemigos", ActorTurnos), ("trampas", Trampa)):
                valores = getattr(objeto, nombre)
                _exigir(type(valores) is list and all(type(valor) is clase for valor in valores),
                        f"lista de {nombre} invalida")
            if hasattr(objeto, "objetos_suelo"):
                _exigir(type(objeto.objetos_suelo) is list, "lista de objetos del suelo invalida")
        elif type(objeto) is Puerta:
            _exigir(type(getattr(objeto, "abierta_con_llave", False)) is bool, "marca de apertura invalida")
            _exigir(type(objeto.abierta) is bool and (objeto.cierre_automatico is None or
                    (type(objeto.cierre_automatico) is int and objeto.cierre_automatico > 0)),
                    "estado de puerta invalido")
        elif type(objeto) is SalidaRastro:
            _exigir(type(objeto.destino) is SalaRastro and type(objeto.puerta) is Puerta,
                    "referencias de salida invalidas")
            _exigir(salas_validas.buscar(id(objeto.destino)) is not None,
                    "destino fuera de las salas guardadas")
        elif type(objeto) is EventoActor:
            _exigir(type(objeto.actor) is ActorTurnos and objeto.actor_id == objeto.actor.actor_id,
                    "referencia de actor en evento inconsistente")
            _exigir(objeto.anterior is None or type(objeto.anterior) is EventoActor,
                    "enlace anterior de evento invalido")
            _exigir(objeto.siguiente is None or type(objeto.siguiente) is EventoActor,
                    "enlace siguiente de evento invalido")
            _exigir(type(objeto.enlazado) is bool and type(objeto.cancelado) is bool,
                    "marcas de evento invalidas")
        elif type(objeto) is EventoEntorno:
            _exigir(objeto.actor is None and type(objeto.objetivo) in (Puerta, Trampa),
                    "objetivo de entorno invalido")
        elif type(objeto) is EstadoEfecto:
            _exigir(objeto.tipo in ("veneno", "velocidad", "antorcha", "regeneracion") and
                    type(objeto.cantidad) is int and objeto.cantidad >= 0,
                    "estado de efecto invalido")
            _exigir(objeto.evento is None or
                    (type(objeto.evento) is EventoActor and objeto.evento.efecto is objeto),
                    "referencia del temporizador de efecto invalida")
        elif type(objeto) is Trampa:
            _exigir(objeto.tipo in ("dano", "veneno", "velocidad") and type(objeto.armada) is bool and
                    type(objeto.cantidad) is int and objeto.cantidad > 0 and
                    type(objeto.rearme) is int and objeto.rearme > 0,
                    "estado de trampa invalido")
            _exigir(objeto.evento_rearme is None or
                    (type(objeto.evento_rearme) is EventoEntorno and objeto.evento_rearme.objetivo is objeto),
                    "referencia del rearme de trampa invalida")
        elif type(objeto) is CambioInventario:
            _exigir(type(objeto.inventario) is InventarioReversible and type(objeto.nodo) is NodoReversible,
                    "referencias de cambio de inventario invalidas")
            _exigir(objeto.tipo in ("recoger", "retirar", "equipar") and type(objeto.deshecho) is bool,
                    "estado de cambio de inventario invalido")
        elif type(objeto) is Partida:
            _exigir(objeto.motor is motor and objeto.jugador is jugador,
                    "raices de la sesion inconsistentes")
            _exigir(type(objeto.acciones_ejecutadas) is int and objeto.acciones_ejecutadas >= 0
                    and type(objeto.victoria) is bool and type(objeto.nombre_jugador) is str,
                    "contadores de la sesion invalidos")
            _exigir(type(objeto.enemigos) is list and all(type(e) is ActorTurnos for e in objeto.enemigos),
                    "lista de enemigos de la sesion invalida")
