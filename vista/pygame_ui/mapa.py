"""Cámara y mapa de conocimiento: ninguna referencia al modelo físico."""
import pygame
from controlador.disposicion_mapa import construir_croquis
from modelo.conocimiento import IndiceSalas
from vista.pygame_ui.componentes import PANEL, TEXTO, TENUE, ACENTO, BORDE
from vista.pygame_ui.sprites import Sprites


class Mapa:
    def __init__(self):
        self.sprites = Sprites()
        self.croquis = None
        self.indice = None
        self.clave = None
        self.foto_actualizada = None
        self.generacion = None
        self.ancla = None
        self.centro = [0.0, 0.0]
        self.escala = 1.0
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.casillas = []
        self.seleccion = None
        self.arrastrando = False

    def actualizar(self, foto):
        if self.foto_actualizada is foto:
            return
        if self.generacion != foto.generacion:
            self.generacion, self.ancla = foto.generacion, foto.sala_id
            self.clave = None
            self.seleccion = None
            self.centro[:] = (0, 0)
            self.escala = 1.0
        clave = tuple((s.sala_id, s.estado, s.salidas) for s in foto.salas)
        if clave != self.clave:
            self.croquis = construir_croquis(foto.salas, foto.sala_id, self.ancla)
            self.indice = IndiceSalas([c.sala_id for c in self.croquis.casillas])
            self.clave = clave
            if self.seleccion is not None and self.croquis.casilla(self.seleccion) is None:
                self.seleccion = None
            self.limitar()
        self.foto_actualizada = foto

    def limitar(self):
        if self.croquis is None:
            return
        x0, y0, x1, y1 = self.croquis.limites
        self.centro[0] = max(x0 * 140 - 100, min(x1 * 140 + 100, self.centro[0]))
        self.centro[1] = max(y0 * 140 - 100, min(y1 * 140 + 100, self.centro[1]))

    def punto(self, posicion):
        return (int(self.rect.centerx + (posicion[0]*140 - self.centro[0])*self.escala),
                int(self.rect.centery + (posicion[1]*140 - self.centro[1])*self.escala))

    def centrar(self, sala_id):
        casilla = self.croquis.casilla(sala_id) if self.croquis else None
        if casilla:
            self.centro[:] = (casilla.posicion[0]*140, casilla.posicion[1]*140)

    def zoom(self, factor, posicion=None):
        posicion = posicion or self.rect.center
        anterior = self.escala
        nueva = max(0.45, min(1.8, anterior * factor))
        self.centro[0] += (posicion[0] - self.rect.centerx) * (1/anterior - 1/nueva)
        self.centro[1] += (posicion[1] - self.rect.centery) * (1/anterior - 1/nueva)
        self.escala = nueva
        self.limitar()

    def evento(self, evento):
        if evento.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.zoom(1.15 ** evento.y, pygame.mouse.get_pos())
        elif evento.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(evento.pos):
            if evento.button == 2:
                self.arrastrando = True
            elif evento.button == 1:
                self.seleccion = next((ident for ident, r in self.casillas if r.collidepoint(evento.pos)), None)
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 2:
            self.arrastrando = False
        elif evento.type == pygame.MOUSEMOTION and self.arrastrando:
            self.centro[0] -= evento.rel[0] / self.escala
            self.centro[1] -= evento.rel[1] / self.escala
            self.limitar()
        elif evento.type == pygame.WINDOWFOCUSLOST:
            self.arrastrando = False

    def dibujar(self, lienzo, rect, foto, ui):
        self.rect = pygame.Rect(rect)
        self.actualizar(foto)
        pygame.draw.rect(lienzo, (18, 26, 37), self.rect, border_radius=8)
        clip = lienzo.get_clip()
        lienzo.set_clip(self.rect)
        for enlace in self.croquis.enlaces:
            a, b = self.punto(enlace.desde), self.punto(enlace.hasta)
            color = ((208, 157, 87) if enlace.esquematico else
                     (179, 98, 103) if enlace.conexion.observada is False else
                     (88, 136, 133) if enlace.conexion.observada is True else BORDE)
            pygame.draw.line(lienzo, color, a, b, 2)
            if enlace.esquematico:
                ui.texto(lienzo, '~', ((a[0]+b[0])//2, (a[1]+b[1])//2), color, ui.pequena)
            if enlace.conexion.observada is False:
                p = ((a[0]+b[0])//2, (a[1]+b[1])//2)
                pygame.draw.rect(lienzo, color, (p[0]-4, p[1]-4, 8, 8))
        self.casillas.clear()
        # Las salas y las casillas están ordenadas por ID; índice propio ya resuelto.
        for sala in foto.salas:
            casilla = self.croquis.casillas[self.indice.obtener(sala.sala_id)]
            x, y = self.punto(casilla.posicion)
            tamano = max(52, int(104*self.escala))
            r = pygame.Rect(x-tamano//2, y-tamano//2, tamano, tamano)
            if not self.rect.colliderect(r):
                continue
            self.casillas.append((sala.sala_id, r))
            pygame.draw.rect(lienzo, PANEL if sala.estado == 2 else (28, 32, 42), r, border_radius=6)
            color = ACENTO if sala.actual else (231, 210, 139) if sala.sala_id == self.seleccion else BORDE
            pygame.draw.rect(lienzo, color, r, 3 if sala.actual else 2, border_radius=6)
            previo = lienzo.get_clip()
            lienzo.set_clip(r.clip(self.rect).inflate(-2, -2))
            ui.texto(lienzo, f'{sala.sala_id}' + (' · tú' if sala.actual else ''), (r.x+6, r.y+3), color, ui.pequena)
            if sala.estado == 1:
                ui.texto(lienzo, '?', (x-8, y-8), TENUE, ui.titulo)
            else:
                if self.escala >= 0.8:
                    ui.texto(lienzo, sala.nombre or '', (r.x+6, r.y+23), TEXTO, ui.pequena)
                observado = sala.recuerdo
                grupos = observado.grupos if observado else ()
                for i, (tipo, nombre, cantidad) in enumerate(grupos[:4]):
                    px, py = r.x + 6 + (i%2)*43, r.y + 46 + (i//2)*23
                    lienzo.blit(self.sprites.obtener(tipo, not sala.actual), (px, py))
                    ui.texto(lienzo, str(cantidad), (px+24, py), TENUE, ui.pequena)
                if self.escala >= 0.8 and not sala.actual:
                    etiqueta = ('sin observación' if observado is None else
                                f'recuerdo t={observado.reloj}' if grupos else f'vacía t={observado.reloj}')
                    ui.texto(lienzo, etiqueta, (r.x+4, r.bottom-21), TENUE, ui.pequena)
            lienzo.set_clip(previo)
        lienzo.set_clip(clip)
        return self.seleccion
