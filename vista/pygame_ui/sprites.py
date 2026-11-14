"""Sprites originales de 24 px, dibujados localmente; sin descargas ni fuentes externas."""
import pygame


class Sprites:
    def __init__(self):
        self.tipos = ('guardian', 'errante', 'rastreador', 'cazador')
        self.imagenes = tuple(self._crear(tipo) for tipo in self.tipos)
        self.desconocido = self._crear('otro')

    def _crear(self, tipo):
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        if tipo == 'guardian':
            pygame.draw.polygon(s, (238, 185, 88), ((5, 4), (19, 4), (18, 16), (12, 22), (6, 16)))
            pygame.draw.line(s, (91, 65, 37), (12, 6), (12, 18), 2)
        elif tipo == 'cazador':
            pygame.draw.polygon(s, (232, 113, 107), ((3, 5), (11, 8), (21, 4), (19, 18), (8, 20), (4, 14)))
            pygame.draw.rect(s, (255, 241, 209), (15, 10, 3, 3))
        elif tipo == 'rastreador':
            pygame.draw.circle(s, (178, 153, 231), (12, 12), 9, 3)
            pygame.draw.line(s, (178, 153, 231), (1, 12), (23, 12), 2)
            pygame.draw.line(s, (178, 153, 231), (12, 1), (12, 23), 2)
        elif tipo == 'errante':
            pygame.draw.polygon(s, (106, 174, 232), ((12, 2), (21, 12), (12, 22), (3, 12)))
        else:
            pygame.draw.circle(s, (182, 188, 198), (12, 12), 9)
        if tipo != 'rastreador':
            pygame.draw.circle(s, (21, 25, 34), (9, 10), 2)
            pygame.draw.circle(s, (21, 25, 34), (15, 10), 2)
        return s

    def obtener(self, comportamiento, recuerdo=False):
        tipo = 'guardian' if comportamiento == 'guardián' else comportamiento
        i = self.tipos.index(tipo) if tipo in self.tipos else None
        imagen = self.imagenes[i] if i is not None else self.desconocido
        if recuerdo:
            imagen = imagen.copy()
            imagen.set_alpha(115)
        return imagen
