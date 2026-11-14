"""Recuerdos por sala: solo el trabajador observa la sala presencial actual."""
from modelo.conocimiento import IndiceSalas
from controlador.proyeccion_grafica import ObservacionEnemigos
from dataclasses import dataclass


@dataclass(frozen=True)
class DeltaVisual:
    posicion: int
    acciones_antes: int
    acciones_despues: int
    reloj_antes: int
    reloj_despues: int
    anteriores: tuple


def marca_previa(partida):
    acciones = partida.linea_tiempo.acciones if partida.linea_tiempo else ()
    return (acciones[-1].posicion if acciones else None,
            partida.acciones_ejecutadas, partida.motor.reloj)


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

    def reiniciar(self, partida):
        self.observaciones[:] = [None] * len(self.ids)
        self.deltas.clear()
        self.origen = (len(partida.linea_tiempo.ordenes), partida.acciones_ejecutadas)
        self.observar(partida)

    def actualizar(self, partida, resultado, antes):
        if not resultado.aceptada:
            return
        posicion, contador, reloj = antes
        if resultado.clase == 'accion':
            sala_id = partida.jugador.sala_actual.sala_id
            previo = self.obtener(sala_id)
            self.observar(partida)
            self.deltas.append(DeltaVisual(partida.linea_tiempo.acciones[-1].posicion,
                                           contador, partida.acciones_ejecutadas,
                                           reloj, partida.motor.reloj, ((sala_id, previo),)))
            del self.deltas[:-5]
        elif resultado.clase == 'retroceso':
            delta = self.deltas[-1] if self.deltas else None
            if (delta is None or delta.posicion != posicion or delta.acciones_despues != contador or
                    delta.reloj_despues != reloj or delta.acciones_antes != partida.acciones_ejecutadas or
                    delta.reloj_antes != partida.motor.reloj):
                self.reiniciar(partida)
                return
            for sala_id, observacion in delta.anteriores:
                self.observaciones[self.indice.obtener(sala_id)] = observacion
            self.deltas.pop()
            self.observar(partida)

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
