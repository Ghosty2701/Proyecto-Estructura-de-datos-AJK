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
    return pygame.transform.smoothscale(imagen, (max(1, round(imagen.get_width()*razon)),
                                                max(1, round(imagen.get_height()*razon))))


class Recursos:
    def __init__(self):
        carpeta = Path(__file__).with_name('assets')
        self._fondo = pygame.image.load(str(carpeta/'sala.png')).convert()
        self.actores = _atlas(carpeta/'actores.png', 3, 2,
                             ('jugador', 'guardian', 'errante', 'rastreador', 'cazador', 'otro'))
        self.elementos = _atlas(carpeta/'elementos.png', 4, 3,
                               ('cerrada', 'abierta', 'arma', 'armadura', 'llave',
                                'pergamino_retroceso', 'pocion', 'antidoto', 'antorcha',
                                'amuleto', 'otro', 'contenedor'))
        self.clave = None
        self.fondo = None
        self.puertas = []

    def preparar(self, tamano, alto_actor=None):
        alto = alto_actor or max(64, int(tamano[1]*0.26))
        clave = (tuple(tamano), alto)
        if clave == self.clave:
            return
        self.clave = clave
        self.fondo = pygame.transform.smoothscale(self._fondo, tamano)
        for r in self.actores:
            tamano_actor = max(alto, int(tamano[1]*0.30)) if r.clave == 'jugador' else alto
            r.imagen = _ajustar(r.fuente, (tamano_actor, tamano_actor))
        item = max(30, min(52, int(tamano[1]*0.1)))
        for r in self.elementos:
            r.imagen = _ajustar(r.fuente, (item, item))
        self.puertas.clear()
        for r in self.elementos[:2]:
            puerta = _ajustar(r.fuente, (max(50, int(tamano[0]*0.11)), max(64, int(tamano[1]*0.20))))
            self.puertas.append(tuple(pygame.transform.rotate(puerta, angulo) for angulo in (0, 180, -90, 90)))

    def actor(self, tipo):
        tipo = 'guardian' if tipo == 'guardián' else tipo
        return next((r.imagen for r in self.actores if r.clave == tipo), self.actores[-1].imagen)

    def objeto(self, clase):
        return next((r.imagen for r in self.elementos[2:] if r.clave == clase), self.elementos[-2].imagen)

    def puerta(self, abierta, direccion):
        return self.puertas[1 if abierta else 0][('N', 'S', 'E', 'O').index(direccion)]
