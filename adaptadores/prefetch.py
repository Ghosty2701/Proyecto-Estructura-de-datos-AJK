def vecinas(sala):
    ids = []
    for direccion in ("N", "S", "E", "O"):
        salida = sala["salidas"].get(direccion)
        if salida is not None:
            ids.append(salida["sala"])
    return ids


def _salas_por_id(nodo):
    if nodo is not None:
        yield from _salas_por_id(nodo.izquierdo)
        yield nodo.valor
        yield from _salas_por_id(nodo.derecho)


def seleccionar_lote(esqueleto, contenido, sala_id, *, solo_vecindad=True):
    """Actual y vecinas abiertas; no rellena con salas lejanas por defecto.

    El modo anterior de lotes completos queda disponible solo para comparar
    politicas en la auditoria. El limite HTTP continua siendo diez salas.
    """
    sala = esqueleto.buscar(sala_id)
    candidatos = [sala_id]
    for cerrada in (False, True):
        if solo_vecindad and cerrada:
            break
        for direccion in ("N", "S", "E", "O"):
            salida = sala.get("salidas", {}).get(direccion)
            if salida is not None and bool(salida.get("cerrada")) == cerrada:
                candidatos.append(salida["sala"])
    lote = []
    for identificador in candidatos:
        if contenido.buscar(identificador) is None and identificador not in lote:
            lote.append(identificador)
    if solo_vecindad or not lote:
        return lote
    for otra in _salas_por_id(esqueleto.raiz):
        identificador = otra["id"]
        if contenido.buscar(identificador) is None and identificador not in lote:
            lote.append(identificador)
        if len(lote) == 10:
            break
    return lote
