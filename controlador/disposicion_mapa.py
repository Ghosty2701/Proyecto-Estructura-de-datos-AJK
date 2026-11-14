"""Croquis determinista a partir exclusivamente de salas conocidas."""
from dataclasses import dataclass
from modelo.conocimiento import IndiceSalas
from comun.ordenamiento import vista_ordenada


@dataclass(frozen=True)
class CasillaMapa:
    sala_id: int
    posicion: tuple


@dataclass(frozen=True)
class EnlaceCroquis:
    origen: int
    destino: int
    desde: tuple
    hasta: tuple
    conexion: object
    esquematico: bool


@dataclass(frozen=True)
class Croquis:
    casillas: tuple
    enlaces: tuple
    limites: tuple

    def casilla(self, sala_id):
        return next((c for c in self.casillas if c.sala_id == sala_id), None)


def construir_croquis(salas, actual, ancla=None):
    salas = vista_ordenada([s for s in salas if s.estado in (1, 2)], lambda s: s.sala_id)
    if not salas:
        return Croquis((), (), (0, 0, 0, 0))
    indice = IndiceSalas([s.sala_id for s in salas])
    posiciones = [None] * len(salas)
    ancla = ancla if ancla is not None and indice.obtener(ancla) is not None else actual
    inicio = indice.obtener(ancla)
    if inicio is None:
        inicio = 0
    cola, enlaces = [], []
    maximo = 0
    # Cada componente usa un vector y un cursor, sin cola de biblioteca.
    while True:
        posiciones[inicio] = (0, 0) if not cola else (maximo + 2, 0)
        maximo = max(maximo, posiciones[inicio][0])
        cursor = len(cola)
        cola.append(inicio)
        while cursor < len(cola):
            u = cola[cursor]
            cursor += 1
            sala = salas[u]
            x, y = posiciones[u]
            for direccion, dx, dy in (('N', 0, -1), ('S', 0, 1), ('E', 1, 0), ('O', -1, 0)):
                salidas = vista_ordenada([e for e in sala.salidas if e.direccion == direccion], lambda e: e.destino)
                for conexion in salidas:
                    v = indice.obtener(conexion.destino)
                    if v is None:
                        continue
                    deseada = (x + dx, y + dy)
                    if posiciones[v] is None:
                        posiciones[v] = (maximo + 2, 0) if deseada in posiciones else deseada
                        maximo = max(maximo, posiciones[v][0])
                        cola.append(v)
                    enlaces.append(EnlaceCroquis(sala.sala_id, conexion.destino,
                                                posiciones[u], posiciones[v], conexion,
                                                posiciones[v] != deseada))
        inicio = next((i for i, p in enumerate(posiciones) if p is None), None)
        if inicio is None:
            break
    casillas = tuple(CasillaMapa(s.sala_id, posiciones[i]) for i, s in enumerate(salas))
    return Croquis(casillas, tuple(enlaces),
                   (min(p[0] for p in posiciones), min(p[1] for p in posiciones),
                    max(p[0] for p in posiciones), max(p[1] for p in posiciones)))
