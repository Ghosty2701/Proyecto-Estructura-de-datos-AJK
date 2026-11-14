"""Una sola animación de una operación confirmada; nunca ejecuta juego."""
from dataclasses import dataclass, replace
from time import monotonic


@dataclass(frozen=True)
class AnimacionActiva:
    generacion: int
    revision: int
    inicio: float
    duracion: float
    efectos: tuple
    anterior: object


class Animaciones:
    def __init__(self, reloj=monotonic):
        self.reloj = reloj
        self.modo = 'normal'
        self.actual = None

    @property
    def activa(self):
        if self.actual and self.reloj()-self.actual.inicio >= self.actual.duracion:
            self.actual = None
        return self.actual is not None

    @property
    def progreso(self):
        return min(1.0, max(0.0, (self.reloj()-self.actual.inicio)/self.actual.duracion)) if self.actual else 1.0

    def saltar(self):
        self.actual = None

    def incorporar(self, respuesta, anterior):
        foto = respuesta.presentacion
        if foto is None or anterior is None or foto.generacion != anterior.generacion:
            self.saltar()
            return
        if respuesta.resultado.clase != 'accion' or not respuesta.resultado.aceptada:
            self.saltar()
            return
        duracion = 0.5 if self.modo == 'normal' else 0.18 if self.modo == 'reducida' else 0
        if any(e.tipo == 'movimiento' for e in respuesta.efectos):
            duracion = min(duracion, 0.16 if self.modo == 'normal' else 0.08)
        self.actual = (AnimacionActiva(foto.generacion, foto.revision, self.reloj(), duracion,
                                      respuesta.efectos, anterior) if duracion and respuesta.efectos else None)

    def foto_para_dibujo(self, foto):
        if not self.activa or self.actual.anterior.sala_id != foto.sala_id:
            return foto
        anteriores = self.actual.anterior.enemigos
        fantasmas = tuple(replace(e, vida=0) if any(f.actor_id == e.identificador and f.tipo == 'derrota'
                          for f in self.actual.efectos) else e for e in anteriores if any(f.actor_id == e.identificador and
                          f.tipo in ('derrota', 'salida') for f in self.actual.efectos)
                          and not any(n.identificador == e.identificador for n in foto.enemigos))
        return replace(foto, enemigos=foto.enemigos+fantasmas) if fantasmas else foto

    def alfa(self, actor_id):
        if self.activa and any(e.actor_id == actor_id and e.tipo in ('derrota', 'salida') for e in self.actual.efectos):
            return max(0, int(255*(1-self.progreso)))
        return 255

    def dibujar(self, lienzo, escena, ui):
        if not self.activa:
            return
        import math
        import pygame
        progreso = self.progreso
        for i, efecto in enumerate(self.actual.efectos):
            if efecto.sala_id != escena.sala_id:
                continue
            r = escena.region_actor(efecto.actor_id)
            if r is None:
                continue
            if efecto.tipo == 'movimiento':
                velo = pygame.Surface(escena.rect.size, pygame.SRCALPHA)
                velo.fill((8, 7, 5, int(85*(1-progreso))))
                lienzo.blit(velo, escena.rect)
            elif efecto.tipo == 'ataque':
                radio = max(26, r.h//2)
                cuadro = pygame.Rect(0, 0, radio*2, radio*2)
                cuadro.center = r.center
                pygame.draw.arc(lienzo, (251, 213, 130), cuadro,
                                -1.8+progreso*2.0, -0.5+progreso*2.0, 4)
                if escena.jugador_rect:
                    inicio, fin = escena.jugador_rect.center, r.center
                    largo = math.hypot(fin[0]-inicio[0], fin[1]-inicio[1])
                    if largo:
                        punta = (int(inicio[0]+(fin[0]-inicio[0])*min(0.7, progreso)),
                                 int(inicio[1]+(fin[1]-inicio[1])*min(0.7, progreso)))
                        pygame.draw.line(lienzo, (228, 192, 127), inicio, punta, 2)
            elif efecto.tipo in ('dano', 'curacion'):
                color = (255, 136, 112) if efecto.tipo == 'dano' else (127, 231, 177)
                signo = '−' if efecto.tipo == 'dano' else '+'
                y = r.y-20-int(progreso*24)-(i%3)*15
                ui.texto(lienzo, f'{signo}{efecto.cantidad}', (r.centerx-12, y), color)
                if progreso < 0.45:
                    velo = pygame.Surface(r.size, pygame.SRCALPHA)
                    velo.fill((*color, int(65*(1-progreso/0.45))))
                    lienzo.blit(velo, r)
            elif efecto.tipo == 'derrota':
                ui.texto(lienzo, 'Derrotado', (r.centerx-32, r.y-24), (223, 183, 112), ui.pequena)
