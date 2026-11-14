"""Ventana principal. Pygame vive aquí; la sesión pertenece al trabajador."""
from dataclasses import replace
import pygame

from controlador.controlador_grafico import ControladorGrafico
from controlador.sesion import ConfiguracionSesion
from vista.pygame_ui.componentes import Campo, Componentes, FONDO, PANEL, TEXTO, TENUE, ACENTO, PELIGRO


class Aplicacion:
    def __init__(self, opciones, controlador=None):
        pygame.display.init()
        pygame.font.init()
        self.ventana = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        pygame.display.set_caption('Cripta · Mapa y turnos')
        pygame.key.set_repeat()
        self.ui = Componentes()
        self.controlador = controlador or ControladorGrafico()
        self.config = ConfiguracionSesion.desde_opciones(opciones)
        c = self.config
        self.campos = [
            Campo('nombre', 'Jugador', c.nombre or 'Explorador'),
            Campo('semilla', 'Semilla', str(c.semilla)),
            Campo('cripta', 'ID de cripta', c.cripta or ''),
            Campo('offline', 'Carpeta offline (vacía: servicio oficial)', c.offline or ''),
            Campo('cargar', 'Archivo .bin para reanudar', c.cargar or ''),
            Campo('archivo_guardado', 'Archivo .bin para guardar', c.archivo_guardado or 'partida.bin'),
            Campo('checkpoint_cada', 'Checkpoint cada K acciones (vacío: predeterminado)', str(c.checkpoint_cada or '')),
            Campo('bitacora', 'Nueva bitácora (opcional; solo partida nueva)', c.bitacora or ''),
        ]
        self.menu = not bool(c.cripta or c.cargar)
        self.saliendo = False
        self.error = ''
        self.catalogo = ()
        self.catalogo_inicio = 0
        self.informe_scroll = 0
        self.ultima = None
        self.candidata = None
        if not self.menu:
            self.candidata = c
            self.controlador.iniciar(c)

    def campo(self, clave):
        return next(c for c in self.campos if c.clave == clave)

    def configurar(self, cargar=False):
        k = self.campo('checkpoint_cada').valor.strip()
        return replace(self.config,
                       nombre=self.campo('nombre').valor.strip(),
                       semilla=int(self.campo('semilla').valor),
                       cripta=None if cargar else self.campo('cripta').valor.strip(),
                       cargar=self.campo('cargar').valor.strip() if cargar else None,
                       offline=self.campo('offline').valor.strip() or None,
                       archivo_guardado=self.campo('archivo_guardado').valor.strip() or None,
                       checkpoint_cada=int(k) if k else None,
                       bitacora=None if cargar else self.campo('bitacora').valor.strip() or None,
                       forzar=False)

    def accion(self, accion):
        try:
            if accion == 'salir':
                self.saliendo = True
                self.controlador.cerrar()
            elif accion == 'menu':
                self.menu = True
                self.error = ''
            elif accion == 'continuar':
                self.menu = False
            elif accion in ('nueva', 'cargar'):
                config = self.configurar(cargar=accion == 'cargar')
                config.validar()
                if self.controlador.iniciar(config):
                    self.candidata = config
                    self.error = ''
            elif accion == 'forzar' and self.candidata is not None:
                self.controlador.iniciar(replace(self.candidata, forzar=True))
                self.error = ''
            elif accion == 'listar':
                config = replace(self.config, offline=self.campo('offline').valor.strip() or None)
                self.controlador.catalogo(config)
                self.error = ''
            elif isinstance(accion, tuple) and accion[0] == 'cripta':
                self.campo('cripta').valor = accion[1]
        except (ValueError, OSError) as error:
            self.error = str(error)

    def actualizar(self):
        respuesta = self.controlador.respuesta
        if respuesta is self.ultima:
            return
        self.ultima = respuesta
        if respuesta.error:
            self.error = respuesta.error
        elif respuesta.fase == 'CATALOGO':
            self.catalogo = respuesta.datos
            self.catalogo_inicio = 0
        elif respuesta.presentacion is not None:
            self.menu = False
            self.error = ''

    def dibujar_menu(self):
        w, h = self.ventana.get_size()
        u, v = self.ui, self.ventana
        ocupado = self.controlador.ocupado
        u.texto(v, 'CRIPTA', (32, 22), ACENTO, u.titulo)
        u.texto(v, 'Una acción, un turno. El tiempo espera por ti.', (32, 66), TENUE)
        ancho = (w - 96) // 2
        for i, campo in enumerate(self.campos):
            u.campo(v, campo, (32 + i % 2 * (ancho + 32), 128 + i // 2 * 80, ancho, 42), not ocupado)
        y = 440
        for i, (texto, accion) in enumerate((('Nueva partida', 'nueva'), ('Cargar .bin', 'cargar'),
                                            ('Listar criptas', 'listar'), ('Salir', 'salir'))):
            u.boton(v, (32 + i * 180, y, 168, 40), texto, accion, not ocupado or accion == 'salir')
        if self.controlador.respuesta.presentacion:
            u.boton(v, (w - 242, y, 210, 40), 'Volver a la partida', 'continuar', not ocupado)
        if ocupado:
            u.texto(v, 'Preparando datos… puedes cerrar la ventana.', (32, 494), ACENTO)
        elif self.controlador.respuesta.fase == 'VERIFICACION':
            u.boton(v, (32, 494, 350, 40), 'Iniciar de todos modos (forzar)', 'forzar')
        if self.error:
            u.parrafo(v, self.error, (32, 544, w - 64, h - 566), PELIGRO, self.informe_scroll)
        else:
            for i, (identificador, nombre, salas) in enumerate(self.catalogo[self.catalogo_inicio:self.catalogo_inicio + max(1, (h-550)//40)]):
                u.boton(v, (32, 530 + 40 * i, w - 64, 34),
                        f'{identificador} · {nombre} · {salas} salas', ('cripta', identificador), not ocupado)

    def dibujar_juego(self):
        # Escena de sesión inicial; el mapa y controles se incorporan en US2/US3.
        u, v = self.ui, self.ventana
        foto = self.controlador.respuesta.presentacion
        u.texto(v, f'Cripta {foto.id_cripta}', (32, 24), ACENTO, u.titulo)
        u.texto(v, f'{foto.nombre_jugador} · Sala {foto.sala_id} · Reloj {foto.reloj} · Vida {foto.vida}/{foto.vida_max}', (32, 78))
        u.texto(v, 'Sesión preparada. Mapa y acciones en desarrollo.', (32, 128), TENUE)
        u.parrafo(v, '\n'.join(foto.mensajes), (32, 190, v.get_width()-64, 360))
        u.boton(v, (32, v.get_height()-72, 200, 40), 'Menú', 'menu', not self.controlador.ocupado)
        u.boton(v, (250, v.get_height()-72, 200, 40), 'Cerrar', 'salir')

    def dibujar(self):
        self.ventana.fill(FONDO)
        self.ui.comenzar()
        if self.saliendo:
            self.ui.texto(self.ventana, 'Cerrando la sesión…', (40, 60), TEXTO, self.ui.titulo)
            self.ui.texto(self.ventana, 'La operación aceptada termina antes de liberar los recursos.', (40, 120), TENUE)
        elif self.menu or self.controlador.respuesta.presentacion is None:
            self.dibujar_menu()
        else:
            self.dibujar_juego()

    def evento(self, evento):
        if evento.type == pygame.QUIT:
            self.accion('salir')
        elif evento.type == pygame.VIDEORESIZE:
            self.ventana = pygame.display.set_mode((max(1024, evento.w), max(768, evento.h)), pygame.RESIZABLE)
        elif not self.saliendo:
            if evento.type == pygame.MOUSEWHEEL:
                if self.error:
                    self.informe_scroll = max(0, self.informe_scroll - evento.y * 42)
                else:
                    self.catalogo_inicio = max(0, min(max(0, len(self.catalogo)-1), self.catalogo_inicio - evento.y))
            accion = self.ui.evento(evento, self.controlador.ocupado)
            if accion is not None:
                self.accion(accion)

    def ejecutar(self):
        reloj = pygame.time.Clock()
        try:
            while not (self.saliendo and self.controlador.cerrada):
                self.actualizar()
                self.dibujar()
                for evento in pygame.event.get():
                    self.evento(evento)
                pygame.display.flip()
                reloj.tick(60)
        finally:
            self.controlador.cerrar(esperar=True)
            pygame.quit()
        return 0


def ejecutar(opciones):
    return Aplicacion(opciones).ejecutar()
