"""Arte ilustrado local: catálogo vectorial y escalas de la escena activa."""
from dataclasses import dataclass
from pathlib import Path
import pygame


@dataclass
class Recurso:
    clave: str
    fuente: object
    imagen: object = None


def _atlas(ruta, columnas, filas, claves):
    atlas = pygame.image.load(str(ruta)).convert_alpha()
    w, h = atlas.get_size()
    registros = []
    for i, clave in enumerate(claves):
        x, y = i % columnas, i // columnas
        rect = pygame.Rect(x*w//columnas, y*h//filas,
                           (x+1)*w//columnas-x*w//columnas,
                           (y+1)*h//filas-y*h//filas)
        celda = atlas.subsurface(rect)
        contenido = celda.get_bounding_rect(min_alpha=12)
        registros.append(Recurso(clave, celda.subsurface(contenido).copy()))
    return registros


def _ajustar(imagen, caja):
    razon = min(caja[0]/imagen.get_width(), caja[1]/imagen.get_height())
    return pygame.transform.scale(imagen, (max(1, round(imagen.get_width()*razon)),
                                                max(1, round(imagen.get_height()*razon))))


class Recursos:
    def __init__(self):
        carpeta = Path(__file__).with_name('assets')
        self._fondo = pygame.transform.scale(pygame.image.load(str(carpeta/'sala_16bits.png')).convert(), (400, 280))
        self.actores = _atlas(carpeta/'actores_16bits.png', 3, 2,
                             ('jugador', 'guardian', 'errante', 'rastreador', 'cazador', 'otro'))
        self.elementos = _atlas(carpeta/'elementos_16bits.png', 4, 3,
                               ('cerrada', 'abierta', 'arma', 'armadura', 'llave',
                                'pergamino_retroceso', 'pocion', 'antidoto', 'antorcha',
                                'amuleto', 'otro', 'contenedor'))
        self.clave = None
        self.fondo = None
        self.puertas = []
        self.puertas_fuente = _atlas(carpeta/'puertas_16bits.png', 4, 2,
                                    ('N_cerrada', 'S_cerrada', 'E_cerrada', 'O_cerrada',
                                     'N_abierta', 'S_abierta', 'E_abierta', 'O_abierta'))
        for recurso in self.actores:
            recurso.fuente = _ajustar(recurso.fuente, (32, 40))
        for recurso in self.elementos:
            recurso.fuente = _ajustar(recurso.fuente, (20, 24))
        for recurso in self.puertas_fuente:
            recurso.fuente = _ajustar(recurso.fuente, (64, 48) if recurso.clave[0] in ('N', 'S') else (40, 64))

    def preparar(self, tamano, alto_actor=None):
        alto = alto_actor or max(64, int(tamano[1]*0.26))
        clave = (tuple(tamano), alto)
        if clave == self.clave:
            return
        self.clave = clave
        self.fondo = pygame.transform.scale(self._fondo, tamano)
        for r in self.actores:
            tamano_actor = max(72, int(tamano[1]*0.20)) if r.clave == 'jugador' else min(alto, int(tamano[1]*0.22))
            r.imagen = _ajustar(r.fuente, (tamano_actor, tamano_actor))
        item = max(30, min(52, int(tamano[1]*0.1)))
        for r in self.elementos:
            r.imagen = _ajustar(r.fuente, (item, item))
        self.puertas.clear()
        for r in self.puertas_fuente:
            caja = (int(tamano[0]*0.20), int(tamano[1]*0.17)) if r.clave[0] in ('N', 'S') else (int(tamano[0]*0.085), int(tamano[1]*0.26))
            self.puertas.append(_ajustar(r.fuente, caja))

    def actor(self, tipo):
        tipo = 'guardian' if tipo == 'guardián' else tipo
        return next((r.imagen for r in self.actores if r.clave == tipo), self.actores[-1].imagen)

    def objeto(self, clase):
        return next((r.imagen for r in self.elementos[2:] if r.clave == clase), self.elementos[-2].imagen)

    def puerta(self, abierta, direccion):
        return self.puertas[(4 if abierta else 0)+('N', 'S', 'E', 'O').index(direccion)]
