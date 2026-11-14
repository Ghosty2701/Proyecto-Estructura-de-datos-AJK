"""Hechos observables transitorios; no forman parte del esquema de guardado."""
from dataclasses import dataclass


@dataclass(frozen=True)
class EfectoVisual:
    tipo: str
    actor_id: str
    sala_id: int
    reloj: int
    cantidad: int = 0
    nombre: str = ''
    comportamiento: str = ''


def emitir(observar, tipo, actor, sala_id, reloj, cantidad=0):
    if observar is not None:
        observar(EfectoVisual(tipo, str(actor.actor_id), sala_id, reloj, max(0, cantidad),
                              str(getattr(actor, 'nombre', '')), str(getattr(actor, 'comportamiento', ''))))
