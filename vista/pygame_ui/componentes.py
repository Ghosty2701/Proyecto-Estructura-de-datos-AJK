"""Controles inmediatos: solo eventos y píxeles, sin acceso a la partida."""
from dataclasses import dataclass
import pygame

FONDO = (8, 12, 28)
PANEL = (21, 37, 91)
TEXTO = (247, 246, 238)
TENUE = (176, 191, 222)
ACENTO = (255, 217, 116)
BORDE = (165, 188, 231)
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
    seleccionado: bool = False


class Componentes:
    def __init__(self):
        self.fuente = pygame.font.SysFont('consolas', 20)
        self.pequena = pygame.font.SysFont('consolas', 16)
        self.titulo = pygame.font.SysFont('consolas', 30, bold=True)
        self.botones = []
        self.campos = []
        self.foco = None

    def comenzar(self):
        self.botones.clear()
        self.campos.clear()

    def texto(self, lienzo, texto, posicion, color=TEXTO, fuente=None):
        fuente = fuente or self.fuente
        lienzo.blit(fuente.render(str(texto), False, color), posicion)

    def panel(self, lienzo, rect, titulo=None):
        r = pygame.Rect(rect)
        pygame.draw.rect(lienzo, (2, 5, 16), r.move(4, 4))
        for y in range(r.h):
            t = y/max(1, r.h)
            pygame.draw.line(lienzo, (19, int(46-18*t), int(112-42*t)),
                             (r.x, r.y+y), (r.right-1, r.y+y))
        pygame.draw.rect(lienzo, (23, 35, 65), r, 2)
        pygame.draw.rect(lienzo, BORDE, r.inflate(-4, -4), 2)
        pygame.draw.rect(lienzo, (238, 240, 247), r.inflate(-8, -8), 1)
        # Remates metálicos y luz en la arista superior, sin tapar el contenido.
        pygame.draw.line(lienzo, (211, 226, 255), (r.x+14, r.y+4), (r.right-15, r.y+4))
        for x, y, dx, dy in ((r.x+5, r.y+5, 1, 1), (r.right-6, r.y+5, -1, 1),
                              (r.x+5, r.bottom-6, 1, -1), (r.right-6, r.bottom-6, -1, -1)):
            pygame.draw.line(lienzo, ACENTO, (x, y), (x+dx*9, y), 2)
            pygame.draw.line(lienzo, ACENTO, (x, y), (x, y+dy*9), 2)
        if titulo:
            self.texto(lienzo, titulo, (r.x+24, r.y+18), ACENTO)

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

    def boton(self, lienzo, rect, texto, accion, habilitado=True, seleccionado=False):
        rect = pygame.Rect(rect)
        hover = habilitado and rect.collidepoint(pygame.mouse.get_pos())
        iluminado = hover or seleccionado
        color = (48, 73, 142) if iluminado else (25, 44, 103) if habilitado else (20, 30, 66)
        pygame.draw.rect(lienzo, (2, 5, 17), rect.move(2, 3))
        for y in range(rect.h):
            luz = int(12*(1-y/max(1, rect.h)))
            pygame.draw.line(lienzo, tuple(c+luz for c in color), (rect.x, rect.y+y), (rect.right-1, rect.y+y))
        borde = ACENTO if iluminado else BORDE if habilitado else (64, 78, 117)
        pygame.draw.rect(lienzo, borde, rect, 1)
        pygame.draw.line(lienzo, (157, 184, 235) if habilitado else (53, 65, 99),
                         (rect.x+2, rect.y+2), (rect.right-3, rect.y+2))
        pygame.draw.line(lienzo, (8, 17, 52), (rect.x+2, rect.bottom-3), (rect.right-3, rect.bottom-3), 2)
        pygame.draw.line(lienzo, (8, 17, 52), (rect.right-3, rect.y+3), (rect.right-3, rect.bottom-3))
        if iluminado:
            pygame.draw.rect(lienzo, (142, 126, 89), rect.inflate(-4, -4), 1)
            pygame.draw.polygon(lienzo, ACENTO, ((rect.x+7, rect.centery-4), (rect.x+7, rect.centery+4), (rect.x+12, rect.centery)))
        previo = lienzo.get_clip()
        lienzo.set_clip(rect.inflate(-8, -2))
        fuente = self.pequena if self.fuente.size(texto)[0] > rect.w - 12 else self.fuente
        imagen = fuente.render(texto, False, TEXTO if habilitado else (111, 130, 167))
        lienzo.blit(imagen, imagen.get_rect(center=rect.center))
        lienzo.set_clip(previo)
        self.botones.append(Boton(rect, texto, accion, habilitado, seleccionado))

    def campo(self, lienzo, campo, rect, habilitado=True):
        campo.rect = pygame.Rect(rect)
        self.texto(lienzo, campo.etiqueta, (campo.rect.x, campo.rect.y - 24), TENUE, self.pequena)
        pygame.draw.rect(lienzo, (10, 22, 62), campo.rect)
        pygame.draw.rect(lienzo, ACENTO if self.foco is campo else BORDE, campo.rect, 1)
        previo = lienzo.get_clip()
        lienzo.set_clip(campo.rect.inflate(-12, -4))
        imagen = self.fuente.render(campo.valor or ' ', False, TEXTO)
        x = min(campo.rect.x + 8, campo.rect.right - 8 - imagen.get_width()) if self.foco is campo else campo.rect.x + 8
        lienzo.blit(imagen, (x, campo.rect.y + 8))
        lienzo.set_clip(previo)
        if habilitado:
            self.campos.append(campo)

    def evento(self, evento, ocupado=False):
        if ocupado:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                return next((b.accion for b in self.botones if b.habilitado and
                             b.accion in ('salir', 'detener', 'pausa', 'mapa', 'inventario_panel', 'cerrar_local')
                             and b.rect.collidepoint(evento.pos)), None)
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
