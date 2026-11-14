"""Recuerdos por sala: solo el trabajador observa la sala presencial actual."""
from modelo.conocimiento import IndiceSalas
from controlador.proyeccion_grafica import ObservacionEnemigos


class MemoriaVisual:
    def __init__(self, partida):
        self.ids = tuple(s.sala_id for s in partida.motor.conocimiento.salas)
        self.indice = IndiceSalas(self.ids)
        self.observaciones = [None] * len(self.ids)
        self.deltas = []
        self.origen = (len(partida.linea_tiempo.ordenes), partida.acciones_ejecutadas)
        self.observar(partida)

    def obtener(self, sala_id):
        posicion = self.indice.obtener(sala_id)
        return self.observaciones[posicion] if posicion is not None else None

    def observar(self, partida):
        sala_id = partida.jugador.sala_actual.sala_id
        grupos = []
        # No se recorre ni se consulta el contenido de otras salas.
        for enemigo in partida._enemigos_presentes():
            clave = (str(enemigo.comportamiento), str(enemigo.nombre))
            posicion = next((i for i, g in enumerate(grupos) if g[:2] == clave), None)
            if posicion is None:
                grupos.append((*clave, 1))
            else:
                grupos[posicion] = (*clave, grupos[posicion][2] + 1)
        observacion = ObservacionEnemigos(sala_id, partida.motor.reloj, tuple(grupos))
        self.observaciones[self.indice.obtener(sala_id)] = observacion
        return observacion
