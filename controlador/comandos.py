# Traduce texto escrito por el jugador a un Comando. No conoce el modelo ni la vista.

DIRECCIONES = ("N", "S", "E", "O")
ORDENES_VALIDOS = ("peso", "valor", "nombre")


class Comando:
    def __init__(self, nombre, argumento=None):
        self.nombre = nombre
        self.argumento = argumento

    def __repr__(self):
        return f"Comando({self.nombre!r}, {self.argumento!r})"


def _entero_o_defecto(texto, defecto):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None if texto is not None else defecto


def parsear(texto):
    # Devuelve un Comando, o None si el texto no se reconoce o su argumento es invalido.
    partes = texto.strip().lower().split()
    if not partes:
        return None

    palabra, argumentos = partes[0], partes[1:]
    arg = argumentos[0] if argumentos else None

    if palabra.upper() in DIRECCIONES and not argumentos:
        return Comando("mover", palabra.upper())
    if palabra == "ir" and arg is not None and arg.upper() in DIRECCIONES:
        return Comando("mover", arg.upper())
    if palabra == "abrir" and arg is not None and arg.upper() in DIRECCIONES:
        return Comando("abrir", arg.upper())

    if palabra in ("atacar", "recoger"):
        numero = _entero_o_defecto(arg, 1)
        if numero is None or numero < 1:
            return None
        return Comando(palabra, numero)

    if palabra == "orden":
        if arg in ORDENES_VALIDOS:
            return Comando("orden", arg)
        return None

    simples = {
        "esperar": "esperar", "esp": "esperar",
        "usar": "usar", "equipar": "equipar", "soltar": "soltar",
        "inv": "inventario", "inventario": "inventario",
        "sig": "siguiente", "ant": "anterior",
        "retroceder": "retroceder",
        "guardar": "guardar", "cargar": "cargar",
        "ayuda": "ayuda", "?": "ayuda",
        "salir": "salir",
    }
    if palabra in simples and not argumentos:
        return Comando(simples[palabra])
    return None
