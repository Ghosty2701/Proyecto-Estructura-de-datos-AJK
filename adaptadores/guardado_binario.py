# Guardado binario de la partida en un formato propio (struct).
# El contenido de cada bloque llega como bytes ya codificados: este modulo solo se ocupa
# del contenedor (cabecera, bloques, indice) y no conoce las clases del modelo.

import struct

MAGIC = b"CRPT"
VERSION_FORMATO = 1

FORMATO_CABECERA = "<4sHII"
FORMATO_PREFIJO = "<I"
FORMATO_ENTRADA = "<III"
TAM_CABECERA = struct.calcsize(FORMATO_CABECERA)
TAM_PREFIJO = struct.calcsize(FORMATO_PREFIJO)
TAM_ENTRADA = struct.calcsize(FORMATO_ENTRADA)

class ErrorGuardado(Exception):
    # Archivo ajeno, de otra version del formato o danado.
    pass


def escribir_guardado(ruta, globales, salas):
    # salas: lista de (id_sala, bytes) ya ordenada por id_sala y sin repetir.
    anterior = None
    for id_sala, _ in salas:
        if anterior is not None and id_sala <= anterior:
            raise ValueError("las salas deben venir ordenadas por id y sin repetir")
        anterior = id_sala

    with open(ruta, "wb") as archivo:
        # Cabecera provisoria: el offset del indice se conoce hasta terminar los bloques.
        archivo.write(struct.pack(FORMATO_CABECERA, MAGIC, VERSION_FORMATO, len(salas), 0))
        _escribir_bloque(archivo, globales)

        entradas = []
        for id_sala, datos in salas:
            offset = archivo.tell()
            _escribir_bloque(archivo, datos)
            entradas.append((id_sala, offset, len(datos)))

        offset_indice = archivo.tell()
        for entrada in entradas:
            archivo.write(struct.pack(FORMATO_ENTRADA, *entrada))

        archivo.seek(0)
        archivo.write(struct.pack(FORMATO_CABECERA, MAGIC, VERSION_FORMATO, len(salas), offset_indice))


def leer_globales(ruta):
    with open(ruta, "rb") as archivo:
        _leer_cabecera(archivo)
        return _leer_bloque(archivo, TAM_CABECERA)


def leer_sala(ruta, id_sala):
    with open(ruta, "rb") as archivo:
        cantidad, offset_indice = _leer_cabecera(archivo)
        entrada = _buscar_en_indice(archivo, offset_indice, cantidad, id_sala)
        if entrada is None:
            return None
        offset, longitud = entrada
        return _leer_bloque(archivo, offset, longitud)


def leer_guardado(ruta):
    """Lee todos los bloques con una sola apertura, conservando el indice propio."""
    with open(ruta, "rb") as archivo:
        cantidad, offset_indice = _leer_cabecera(archivo)
        globales = _leer_bloque(archivo, TAM_CABECERA)
        archivo.seek(offset_indice)
        entradas = []
        anterior = None
        for _ in range(cantidad):
            datos = archivo.read(TAM_ENTRADA)
            if len(datos) != TAM_ENTRADA:
                raise ErrorGuardado("archivo truncado: indice incompleto")
            id_sala, offset, longitud = struct.unpack(FORMATO_ENTRADA, datos)
            if anterior is not None and id_sala <= anterior:
                raise ErrorGuardado("indice de salas fuera de orden o con duplicados")
            anterior = id_sala
            entradas.append((id_sala, offset, longitud))
        salas = [(id_sala, _leer_bloque(archivo, offset, longitud))
                 for id_sala, offset, longitud in entradas]
        return globales, salas


def _escribir_bloque(archivo, datos):
    archivo.write(struct.pack(FORMATO_PREFIJO, len(datos)))
    archivo.write(datos)


def _leer_bloque(archivo, offset, longitud_esperada=None):
    archivo.seek(offset)
    encabezado = archivo.read(TAM_PREFIJO)
    if len(encabezado) < TAM_PREFIJO:
        raise ErrorGuardado("archivo truncado: falta el tamano de un bloque")
    (longitud,) = struct.unpack(FORMATO_PREFIJO, encabezado)
    if longitud_esperada is not None and longitud != longitud_esperada:
        raise ErrorGuardado("bloque inconsistente con el indice")
    datos = archivo.read(longitud)
    if len(datos) < longitud:
        raise ErrorGuardado("archivo truncado: bloque incompleto")
    return datos


def _leer_cabecera(archivo):
    datos = archivo.read(TAM_CABECERA)
    if len(datos) < TAM_CABECERA:
        raise ErrorGuardado("no es un archivo de guardado de Cripta (muy corto)")
    magic, version, cantidad, offset_indice = struct.unpack(FORMATO_CABECERA, datos)
    if magic != MAGIC:
        raise ErrorGuardado("no es un archivo de guardado de Cripta")
    if version != VERSION_FORMATO:
        raise ErrorGuardado(f"version de formato incompatible: el archivo es {version} "
                            f"y este programa usa {VERSION_FORMATO}")
    return cantidad, offset_indice


def _buscar_en_indice(archivo, offset_indice, cantidad, id_sala):
    bajo = 0
    alto = cantidad - 1
    while bajo <= alto:
        medio = (bajo + alto) // 2
        archivo.seek(offset_indice + medio * TAM_ENTRADA)
        datos = archivo.read(TAM_ENTRADA)
        if len(datos) < TAM_ENTRADA:
            raise ErrorGuardado("archivo truncado: indice incompleto")
        id_medio, offset, longitud = struct.unpack(FORMATO_ENTRADA, datos)
        if id_medio == id_sala:
            return offset, longitud
        if id_medio < id_sala:
            bajo = medio + 1
        else:
            alto = medio - 1
    return None
