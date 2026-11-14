"""Habitación ilustrada. Posiciones escénicas sin reglas de movimiento interiores."""
from dataclasses import dataclass
import pygame
from vista.pygame_ui.recursos import Recursos
from vista.pygame_ui.componentes import ACENTO, TEXTO, TENUE


@dataclass(frozen=True)
class RegionEscena:
    clase: str
    objetivo: object
    rect: object


class EscenaSala:
    def __init__(self):
        self.recursos = Recursos()
        self.regiones = []
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.direcciones = ()
        self.pagina_enemigos = 0
        self.pagina_objetos = 0
        self.jugador_rect = None
        self.clave = None
        self.sala_id = None

    def seleccionar(self, posicion):
        for region in reversed(self.regiones):
            if region.rect.collidepoint(posicion):
                return (('puerta', region.objetivo) if region.clase == 'puerta'
                        else ('objetivo', region.objetivo))
        return None

    def region_actor(self, actor_id):
        if actor_id == 'jugador':
            return self.jugador_rect
        return next((r.rect for r in self.regiones if r.clase == 'enemigo' and
                     r.objetivo.identificador == actor_id), None)

    def dibujar(self, lienzo, rect, foto, ui, seleccionado=None, puerta=None, animacion=None):
        self.rect = pygame.Rect(rect)
        self.sala_id = foto.sala_id
        clave = (foto.generacion, foto.sala_id)
        if clave != self.clave:
            self.clave = clave
            self.pagina_enemigos = self.pagina_objetos = 0
        self.pagina_enemigos = min(self.pagina_enemigos, max(0, (len(foto.enemigos)-1)//12))
        self.pagina_objetos = min(self.pagina_objetos, max(0, (len(foto.objetos)-1)//8))
        enemigos = foto.enemigos[self.pagina_enemigos*12:(self.pagina_enemigos+1)*12]
        objetos = foto.objetos[self.pagina_objetos*8:(self.pagina_objetos+1)*8]
        alto = max(42, int(self.rect.h*(0.32 if len(enemigos) <= 3 else 0.13)))
        self.recursos.preparar(self.rect.size, alto)
        lienzo.blit(self.recursos.fondo, self.rect)
        self.regiones.clear()
        actual = next(s for s in foto.salas if s.actual)
        self.direcciones = tuple(s.direccion for s in actual.salidas)
        for salida in actual.salidas:
            x, y = next((x, y) for d, x, y in (('N', 0.5, 0.10), ('S', 0.5, 0.91),
                        ('E', 0.94, 0.5), ('O', 0.06, 0.5)) if d == salida.direccion)
            imagen = self.recursos.puerta(salida.observada is True, salida.direccion)
            r = imagen.get_rect(center=(self.rect.x+int(self.rect.w*x), self.rect.y+int(self.rect.h*y)))
            r.clamp_ip(self.rect)
            lienzo.blit(imagen, r)
            if salida.direccion == puerta:
                pygame.draw.rect(lienzo, ACENTO, r.inflate(4, 4), 2, border_radius=5)
            ui.texto(lienzo, salida.direccion, (r.centerx-6, r.bottom-15), ACENTO, ui.pequena)
            self.regiones.append(RegionEscena('puerta', salida.direccion, r))
        jugador = self.recursos.actor('jugador')
        self.jugador_rect = jugador.get_rect(midbottom=(self.rect.x+int(self.rect.w*0.26),
                                                       self.rect.y+int(self.rect.h*0.71)))
        self._sombra(lienzo, self.jugador_rect)
        lienzo.blit(jugador, self.jugador_rect)
        for i, objetivo in enumerate(enemigos):
            imagen = self.recursos.actor(objetivo.comportamiento)
            if animacion is not None and animacion.alfa(objetivo.identificador) < 255:
                imagen = imagen.copy()
                imagen.set_alpha(animacion.alfa(objetivo.identificador))
            columnas = min(3, len(enemigos))
            filas = (len(enemigos)+2)//3
            x = 0.53 + (i % columnas)*0.15
            y = (0.52 if filas == 1 else 0.34+(i//3)*0.135)
            r = imagen.get_rect(midbottom=(self.rect.x+int(self.rect.w*x), self.rect.y+int(self.rect.h*y)))
            self._sombra(lienzo, r, objetivo == seleccionado)
            lienzo.blit(imagen, r)
            barra = pygame.Rect(r.centerx-24, r.y-9, 48, 4)
            pygame.draw.rect(lienzo, (43, 21, 22), barra)
            proporcion = max(0, min(1, (objetivo.vida or 0)/max(1, objetivo.vida_max or 1)))
            pygame.draw.rect(lienzo, (175, 69, 59), (barra.x, barra.y, int(barra.w*proporcion), 4))
            ui.texto(lienzo, str(objetivo.indice), (r.right+2, r.y), ACENTO, ui.pequena)
            self.regiones.append(RegionEscena('enemigo', objetivo, r))
        for i, objetivo in enumerate(objetos):
            imagen = self.recursos.objeto(objetivo.clase_objeto)
            r = imagen.get_rect(center=(self.rect.x+int(self.rect.w*(0.18+i*0.09)),
                                       self.rect.y+int(self.rect.h*0.82)))
            if objetivo == seleccionado:
                pygame.draw.ellipse(lienzo, ACENTO, r.inflate(12, 8), 2)
            lienzo.blit(imagen, r)
            self.regiones.append(RegionEscena('suelo', objetivo, r.inflate(4, 4)))
        if animacion is not None:
            animacion.dibujar(lienzo, self, ui)
        return seleccionado

    @staticmethod
    def _sombra(lienzo, r, seleccionado=False):
        pie = pygame.Rect(r.centerx-r.w//2, r.bottom-9, max(24, r.w), 14)
        pygame.draw.ellipse(lienzo, (25, 22, 20), pie)
        if seleccionado:
            pygame.draw.ellipse(lienzo, ACENTO, pie.inflate(12, 6), 2)
