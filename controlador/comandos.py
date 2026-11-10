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


def _entero_sin_signo(texto):
    # Solo digitos ASCII en base 10: sin signo, decimales ni otros sistemas numericos.
    if not texto or any(c not in "0123456789" for c in texto):
        return None
    return int(texto)


def _historia(argumentos):
    # historia <t> -> ("t", t); historia #k -> ("k", k) con k >= 1; mal formada -> None.
    if len(argumentos) != 1:
        return None
    argumento = argumentos[0]
    if argumento.startswith("#"):
        numero = _entero_sin_signo(argumento[1:])
        return None if numero is None or numero < 1 else ("k", numero)
    instante = _entero_sin_signo(argumento)
    return None if instante is None else ("t", instante)


def parsear(texto):
    # Devuelve un Comando, o None si el texto no se reconoce o su argumento es invalido.
    # "historia" con argumento invalido devuelve Comando("historia", None): error de uso.
    palabras = texto.strip().split()
    if palabras and palabras[0].lower() == "historia":
        return Comando("historia", _historia(palabras[1:]))
    original = texto.strip().split(maxsplit=2)
    if len(original) == 2 and [s.lower() for s in original] == ['ver', 'mapa']:
        return Comando('mapa')
    if len(original) == 3 and original[0].lower() == 'ir' and original[1].lower() == 'a':
        return Comando('viajar', original[2])
    partes = texto.strip().lower().split()
    if not partes:
        return None

    palabra, argumentos = partes[0], partes[1:]
    arg = argumentos[0] if argumentos else None

    if not argumentos:
        if palabra == "w":
            return Comando("mover", "N")
        if palabra == "a":
            return Comando("mover", "O")
        if palabra == "d":
            return Comando("mover", "E")
        if palabra == "s":
            return Comando("mover", "S")

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
