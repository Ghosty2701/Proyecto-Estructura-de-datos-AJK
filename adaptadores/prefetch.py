def vecinas(sala):
    ids = []
    for direccion in ("N", "S", "E", "O"):
        salida = sala["salidas"].get(direccion)
        if salida is not None:
            ids.append(salida["sala"])
    return ids