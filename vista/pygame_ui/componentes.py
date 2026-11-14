"""Controles inmediatos: solo eventos y píxeles, sin acceso a la partida."""
from dataclasses import dataclass
import pygame

FONDO = (17, 17, 20)
PANEL = (29, 28, 29)
TEXTO = (229, 235, 241)
TENUE = (172, 167, 157)
ACENTO = (221, 182, 112)
BORDE = (76, 69, 57)
PELIGRO = (244, 139, 122)


@dataclass
class Campo:
    clave: str
    etiqueta: str
    valor: str = ''
    rect: object = None


@dataclass(frozen=True)
class Boton:
    rect: object
    texto: str
    accion: object
    habilitado: bool = True


class Componentes:
    def __init__(self):
        self.fuente = pygame.font.SysFont('segoeui', 18)
        self.pequena = pygame.font.SysFont('segoeui', 15)
        self.titulo = pygame.font.SysFont('segoeui', 32, bold=True)
        self.botones = []
        self.campos = []
        self.foco = None

    def comenzar(self):
        self.botones.clear()
        self.campos.clear()

    def texto(self, lienzo, texto, posicion, color=TEXTO, fuente=None):
        fuente = fuente or self.fuente
        lienzo.blit(fuente.render(str(texto), True, color), posicion)

    def parrafo(self, lienzo, texto, rect, color=TENUE, desplazamiento=0):
        """Recorte y ajuste de líneas sin alterar ni consultar datos del juego."""
        rect = pygame.Rect(rect)
        previo = lienzo.get_clip()
        lienzo.set_clip(rect)
        y = rect.y - desplazamiento
        for original in str(texto).splitlines():
            linea = ''
            for palabra in original.split():
                propuesta = (linea + ' ' + palabra).strip()
                if self.pequena.size(propuesta)[0] > rect.w and linea:
                    self.texto(lienzo, linea, (rect.x, y), color, self.pequena)
                    y += 21
                    linea = palabra
                else:
                    linea = propuesta
            self.texto(lienzo, linea, (rect.x, y), color, self.pequena)
            y += 21
        lienzo.set_clip(previo)
        return y + desplazamiento - rect.y

    def boton(self, lienzo, rect, texto, accion, habilitado=True):
        rect = pygame.Rect(rect)
        color = (55, 47, 37) if habilitado else PANEL
        if habilitado and rect.collidepoint(pygame.mouse.get_pos()):
            color = (77, 61, 40)
        pygame.draw.rect(lienzo, color, rect, border_radius=6)
        pygame.draw.rect(lienzo, BORDE, rect, 1, border_radius=6)
        previo = lienzo.get_clip()
        lienzo.set_clip(rect.inflate(-8, -2))
        fuente = self.pequena if self.fuente.size(texto)[0] > rect.w - 12 else self.fuente
        imagen = fuente.render(texto, True, TEXTO if habilitado else TENUE)
        lienzo.blit(imagen, imagen.get_rect(center=rect.center))
        lienzo.set_clip(previo)
        self.botones.append(Boton(rect, texto, accion, habilitado))

    def campo(self, lienzo, campo, rect, habilitado=True):
        campo.rect = pygame.Rect(rect)
        self.texto(lienzo, campo.etiqueta, (campo.rect.x, campo.rect.y - 24), TENUE, self.pequena)
        pygame.draw.rect(lienzo, PANEL, campo.rect, border_radius=5)
        pygame.draw.rect(lienzo, ACENTO if self.foco is campo else BORDE, campo.rect, 1, border_radius=5)
        previo = lienzo.get_clip()
        lienzo.set_clip(campo.rect.inflate(-12, -4))
        imagen = self.fuente.render(campo.valor or ' ', True, TEXTO)
        x = min(campo.rect.x + 8, campo.rect.right - 8 - imagen.get_width()) if self.foco is campo else campo.rect.x + 8
        lienzo.blit(imagen, (x, campo.rect.y + 8))
        lienzo.set_clip(previo)
        if habilitado:
            self.campos.append(campo)

    def evento(self, evento, ocupado=False):
        if ocupado:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                return next((b.accion for b in self.botones if b.habilitado and
                             b.accion in ('salir', 'detener') and b.rect.collidepoint(evento.pos)), None)
            return None
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.foco = next((c for c in self.campos if c.rect.collidepoint(evento.pos)), None)
            if self.foco is not None:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()
            for boton in self.botones:
                if boton.habilitado and boton.rect.collidepoint(evento.pos):
                    return boton.accion
        elif evento.type == pygame.TEXTINPUT and self.foco is not None:
            self.foco.valor = (self.foco.valor + evento.text)[:1024]
        elif evento.type == pygame.KEYDOWN and self.foco is not None:
            if evento.key == pygame.K_BACKSPACE:
                self.foco.valor = self.foco.valor[:-1]
            elif evento.key == pygame.K_TAB and self.campos:
                self.foco = self.campos[(self.campos.index(self.foco) + 1) % len(self.campos)]
            elif evento.key == pygame.K_ESCAPE:
                self.foco = None
                pygame.key.stop_text_input()
        return None
