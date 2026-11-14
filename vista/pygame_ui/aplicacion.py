"""Ventana principal. Pygame vive aquí; la sesión pertenece al trabajador."""
from dataclasses import replace
import pygame

from controlador.controlador_grafico import ControladorGrafico
from controlador.sesion import ConfiguracionSesion
from controlador.proyeccion_grafica import IntencionGrafica, salas_visuales
from vista.vista_consola import lineas_historia
from vista.pygame_ui.componentes import Campo, Componentes, FONDO, PANEL, TEXTO, TENUE, ACENTO, PELIGRO
from vista.pygame_ui.mapa import Mapa
from vista.pygame_ui.sala import EscenaSala
from vista.pygame_ui.animaciones import Animaciones


class Aplicacion:
    def __init__(self, opciones, controlador=None):
        pygame.display.init()
        pygame.font.init()
        self.ventana = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        pygame.display.set_caption('Cripta · Habitaciones y turnos')
        pygame.key.set_repeat()
        self.ui = Componentes()
        self.mapa = Mapa()
        self.escena = EscenaSala()
        self.animacion = Animaciones()
        self.puerta = None
        self.mini_generacion = None
        self.mini_sala = None
        self.mapa_historia = Mapa()
        self.foto_historia = None
        self.historia = Campo('historia', 'Consultar pasado: t o #acción', '0')
        self.historia_scroll = 0
        self.controlador = controlador or ControladorGrafico()
        self.config = ConfiguracionSesion.desde_opciones(opciones)
        c = self.config
        self.campos = [
            Campo('nombre', 'Jugador', c.nombre or 'Explorador'),
            Campo('semilla', 'Semilla (código de partida)', str(c.semilla)),
            Campo('cripta', 'Cripta elegida', c.cripta or ''),
            Campo('offline', 'Datos locales (vacío = internet)', c.offline or ''),
            Campo('cargar', 'Archivo de partida para cargar', c.cargar or ''),
            Campo('archivo_guardado', 'Guardar partidas en', c.archivo_guardado or 'partida.bin'),
            Campo('checkpoint_cada', 'Frecuencia del historial (opcional)', str(c.checkpoint_cada or '')),
            Campo('bitacora', 'Archivo de repetición (opcional)', c.bitacora or ''),
        ]
        self.menu = not bool(c.cripta or c.cargar)
        self.inicio_avanzado = bool(c.cargar)
        self.saliendo = False
        self.error = ''
        self.catalogo = ()
        self.puntajes = None
        self.panel_local = None
        self.panel_scroll = 0
        self.catalogo_inicio = 0
        self.informe_scroll = 0
        self.ultima = None
        self.candidata = None
        self.tab = 'suelo'
        self.lista_inicio = 0
        self.objetivo = None
        self.teclas = []
        self.botones_pulsados = []
        self.tiene_foco = True
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
                self.animacion.saltar()
                self.saliendo = True
                self.controlador.cerrar()
            elif accion == 'menu':
                self.animacion.saltar()
                self.menu = True
                self.error = ''
                self.panel_local = None
            elif accion == 'continuar':
                self.menu = False
            elif accion in ('pausa', 'inventario_panel', 'objetivos_panel', 'opciones_panel', 'abrir_historia'):
                if accion != 'opciones_panel':
                    self.controlador.detener_viaje()
                self.animacion.saltar()
                self.ui.foco = None
                self.lista_inicio = 0
                self.panel_local = next(panel for nombre, panel in
                    (('pausa', 'pausa'), ('inventario_panel', 'inventario'), ('objetivos_panel', 'objetivos'),
                     ('opciones_panel', 'opciones'), ('abrir_historia', 'historia_formulario')) if nombre == accion)
                if accion == 'inventario_panel': self.tab = 'inventario'
                if accion == 'objetivos_panel':
                    self.tab = 'enemigos' if self.controlador.respuesta.presentacion.enemigos else 'suelo'
            elif accion == 'detener':
                self.controlador.detener_viaje()
            elif accion == 'consultar_historia':
                self.accion(('juego', 'historia', self.historia.valor.strip(), None))
            elif accion == 'avanzado':
                self.inicio_avanzado = not self.inicio_avanzado
            elif accion in ('nueva', 'cargar'):
                if accion == 'cargar' and not self.campo('cargar').valor.strip():
                    self.inicio_avanzado = True
                    self.error = 'Indica el archivo de partida y vuelve a pulsar Cargar partida.'
                    return
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
                self.puntajes = None
            elif accion == 'puntajes':
                self.controlador.puntajes(self.config)
                self.error = ''
            elif accion == 'mensajes':
                self.panel_local, self.panel_scroll = 'mensajes', 0
            elif accion == 'mapa':
                self.panel_local = 'mapa'
                self.mapa.centrar(self.controlador.respuesta.presentacion.sala_id)
            elif accion == 'cerrar_local':
                self.panel_local = None
                self.ui.foco = None
            elif accion == 'saltar_efecto':
                self.animacion.saltar()
            elif accion == 'modo_efectos':
                modos = ('normal', 'reducida', 'sin')
                self.animacion.modo = modos[(modos.index(self.animacion.modo)+1)%3]
                self.animacion.saltar()
            elif accion == 'centrar':
                self.mapa.centrar(self.controlador.respuesta.presentacion.sala_id)
            elif accion in ('zoom_mas', 'zoom_menos'):
                self.mapa.zoom(1.15 if accion == 'zoom_mas' else 1/1.15)
            elif isinstance(accion, tuple) and accion[0] == 'cripta':
                self.campo('cripta').valor = accion[1]
            elif isinstance(accion, tuple) and accion[0] == 'tab':
                self.tab, self.lista_inicio = accion[1], 0
                self.panel_local = 'inventario' if accion[1] == 'inventario' else 'objetivos'
            elif isinstance(accion, tuple) and accion[0] == 'elegir_objetivo':
                self.panel_local = None
                self.accion(('objetivo', accion[1]))
            elif isinstance(accion, tuple) and accion[0] == 'objetivo':
                self.objetivo = accion[1]
                self.puerta = None
                self.tab = 'enemigos' if self.objetivo.clase == 'enemigo' else 'suelo'
            elif isinstance(accion, tuple) and accion[0] == 'puerta':
                self.puerta = accion[1]
                self.objetivo = None
            elif isinstance(accion, tuple) and accion[0] == 'pagina':
                campo = 'pagina_enemigos' if accion[1] == 'enemigos' else 'pagina_objetos'
                setattr(self.escena, campo, max(0, getattr(self.escena, campo)+accion[2]))
            elif isinstance(accion, tuple) and accion[0] in ('juego', 'seleccionar'):
                if self.animacion.activa:
                    if accion[0] == 'juego' and accion[1] in ('cargar', 'retroceder'):
                        self.animacion.saltar()
                    else:
                        return
                foto = self.controlador.respuesta.presentacion
                if foto is not None and (not self.controlador.ocupado or self.controlador.viajando):
                    if accion[0] == 'seleccionar':
                        op, arg, objetivo = 'seleccionar', None, accion[1]
                    else:
                        _, op, arg, objetivo = accion
                    if op == 'inventario':
                        self.tab = 'inventario'
                        self.panel_local = 'inventario'
                    if op == 'cerrar_panel':
                        self.panel_local = None
                        self.ui.foco = None
                    self.controlador.enviar(IntencionGrafica(foto.generacion, foto.revision, op, arg, objetivo))
        except (ValueError, OSError) as error:
            self.error = str(error)

    def actualizar(self):
        respuesta = self.controlador.respuesta
        if respuesta is self.ultima:
            return
        anterior = self.ultima.presentacion if self.ultima else None
        self.animacion.incorporar(respuesta, anterior)
        if not self.tiene_foco:
            self.animacion.saltar()
        self.ultima = respuesta
        if respuesta.error:
            self.error = respuesta.error
        elif respuesta.fase == 'CATALOGO':
            self.catalogo = respuesta.datos
            self.catalogo_inicio = 0
        elif respuesta.fase == 'PUNTAJES':
            self.puntajes = respuesta.datos
            self.catalogo_inicio = 0
        elif respuesta.presentacion is not None:
            self.menu = False
            foto = respuesta.presentacion
            self.error = '' if respuesta.resultado.aceptada else (foto.mensajes[-1] if foto.mensajes else '')
            if foto.panel == 'historia':
                self.panel_local = None
                self.ui.foco = None
            elif foto.panel == 'ayuda': self.panel_local = 'ayuda'
            if anterior is None or anterior.generacion != foto.generacion or anterior.sala_id != foto.sala_id:
                self.objetivo = None; self.puerta = None
            elif self.objetivo is not None:
                self.objetivo = (next((e for e in foto.enemigos if e.identificador == self.objetivo.identificador), None)
                                 if self.objetivo.clase == 'enemigo' else None)

    def dibujar_menu(self):
        w, h = self.ventana.get_size()
        u, v = self.ui, self.ventana
        ocupado = self.controlador.ocupado
        u.panel(v, (20, 16, w-40, h-32))
        u.texto(v, 'CRIPTA', (32, 22), ACENTO, u.titulo)
        u.texto(v, 'Una acción, un turno. El tiempo espera por ti.', (32, 66), TENUE)
        ancho = (w - 96) // 2
        for i, campo in enumerate(self.campos if self.inicio_avanzado else self.campos[:4]):
            u.campo(v, campo, (32 + i % 2 * (ancho + 32), 128 + i // 2 * 80, ancho, 42), not ocupado)
        y = 440
        if not self.inicio_avanzado:
            u.parrafo(v, 'Elige una cripta con el botón Elegir cripta y comienza tu aventura.\nLas rutas de guardado, carga y opciones del historial están en Avanzado.',
                      (40, 300, w-80, 100), TENUE)
        bw = (w-64)//6
        for i, (texto, accion) in enumerate((('Nueva partida', 'nueva'), ('Cargar partida', 'cargar'),
                                            ('Elegir cripta', 'listar'), ('Puntajes', 'puntajes'),
                                            ('Avanzado', 'avanzado'), ('Salir', 'salir'))):
            u.boton(v, (32 + i*bw, y, bw-12, 40), texto, accion, not ocupado or accion == 'salir')
        if self.controlador.respuesta.presentacion:
            u.boton(v, (w - 300, 494, 268, 40), 'Volver a la partida', 'continuar', not ocupado)
        if ocupado:
            u.texto(v, 'Preparando datos… puedes cerrar la ventana.', (32, 494), ACENTO)
        elif self.controlador.respuesta.fase == 'VERIFICACION':
            u.boton(v, (32, 494, 350, 40), 'Iniciar de todos modos (forzar)', 'forzar')
        if self.error:
            u.parrafo(v, self.error, (32, 544, w - 64, h - 566), PELIGRO, self.informe_scroll)
        elif self.puntajes is not None:
            filas = ['Cripta / versión · Jugador · Resultado · Tiempo · Acciones · Enemigos']
            filas.extend(f'{c} / {ver} · {nombre} · {resultado} · {tiempo} · {acciones} · {enemigos}'
                         for c, ver, nombre, resultado, tiempo, acciones, enemigos in self.puntajes)
            if not self.puntajes: filas.append('No hay resultados registrados.')
            u.parrafo(v, '\n'.join(filas), (32, 548, w-64, h-572), desplazamiento=self.catalogo_inicio*21)
        else:
            for i, (identificador, nombre, salas) in enumerate(self.catalogo[self.catalogo_inicio:self.catalogo_inicio + max(1, (h-550)//40)]):
                u.boton(v, (32, 530 + 40 * i, w - 64, 34),
                        f'{identificador} · {nombre} · {salas} salas', ('cripta', identificador), not ocupado)

    def contexto(self, foto):
        if self.objetivo is not None:
            if self.objetivo.clase == 'enemigo':
                return 'Atacar', ('juego', 'atacar', None, self.objetivo), self.objetivo.nombre
            if self.objetivo.clase == 'suelo':
                return 'Recoger', ('juego', 'recoger', None, self.objetivo), self.objetivo.nombre
        actual = next(s for s in foto.salas if s.actual)
        salida = next((s for s in actual.salidas if s.direccion == self.puerta), None)
        if salida:
            nombre = next(n for d, n in (('N', 'Norte'), ('S', 'Sur'), ('E', 'Este'), ('O', 'Oeste')) if d == salida.direccion)
            abierta = salida.observada is not False
            return ('Entrar' if abierta else 'Abrir puerta',
                    ('juego', 'mover' if abierta else 'abrir', salida.direccion, None),
                    f'Puerta {nombre} | Paso: {salida.costo} | ' + ('Abierta' if abierta else 'Cerrada'))
        return None, None, 'Elige una puerta, un enemigo o un objeto con el ratón.'

    def dibujar_juego(self):
        u, v = self.ui, self.ventana
        w, h = v.get_size()
        foto = self.controlador.respuesta.presentacion
        if foto.terminada and not self.animacion.activa:
            u.panel(v, (40, 48, w-80, h-96), 'Fin de la aventura')
            u.texto(v, str(foto.resultado).upper(), (72, 110), ACENTO, u.titulo)
            u.parrafo(v, f'{foto.nombre_jugador}\nTiempo: {foto.reloj} | Turnos: {foto.acciones}\n\n'
                         + (self.error or '\n'.join(foto.mensajes[-5:])), (72, 170, w-144, h-310))
            u.boton(v, (72, h-110, 240, 42), 'Volver al inicio', 'menu')
            u.boton(v, (332, h-110, 180, 42), 'Cerrar juego', 'salir')
            return
        if foto.panel == 'historia' and foto.historia is not None:
            self.dibujar_historia(foto)
            return
        u.panel(v, (16, 12, w-32, 66))
        u.texto(v, 'CRIPTA', (32, 22), ACENTO, u.titulo)
        u.parrafo(v, foto.sala_nombre, (194, 23, w-490, 26), TEXTO)
        u.texto(v, f'{foto.nombre_jugador} | Turnos: {foto.acciones}', (194, 49), TENUE, u.pequena)
        u.texto(v, f'Vida {foto.vida}/{foto.vida_max}', (w-255, 28))
        barra = pygame.Rect(w-255, 56, 210, 8)
        pygame.draw.rect(v, (10, 16, 43), barra)
        pygame.draw.rect(v, (99, 213, 160), (barra.x, barra.y, int(barra.w*max(0, foto.vida)/max(1, foto.vida_max)), barra.h))
        visual = self.animacion.foto_para_dibujo(foto)
        self.escena.dibujar(v, (16, 90, w-252, h-250), visual, u, self.objetivo, self.puerta, self.animacion)
        u.panel(v, (w-220, 90, 204, 156))
        self.mapa.actualizar(foto)
        if self.mini_generacion != foto.generacion:
            self.mapa.escala = 0.45
            self.mini_generacion = foto.generacion
        if self.mini_sala != foto.sala_id:
            self.mapa.centrar(foto.sala_id); self.mini_sala = foto.sala_id
        self.mapa.dibujar(v, (w-212, 98, 188, 140), foto, u)
        u.panel(v, (w-220, 258, 204, h-418), 'Estado')
        u.parrafo(v, f'Ataque: {foto.ataque}\nDefensa: {foto.defensa}\nEnemigos: {len(foto.enemigos)}\nObjetos: {len(foto.objetos)}\n\n'
                         + ('\n'.join(str(e) for e in foto.efectos) if foto.efectos else 'Sin efectos activos'),
                  (w-202, 304, 168, h-480), TEXTO)
        principal, orden, detalle = self.contexto(foto)
        u.panel(v, (16, h-144, w-32, 128))
        controles = []
        if principal:
            controles.append((principal, orden))
        controles.extend((('Detener viaje', 'detener') if self.controlador.viajando else
                          ('Esperar', ('juego', 'esperar', None, None)),
                          ('Inventario', 'inventario_panel'), ('Mapa', 'mapa'), ('Menú', 'pausa')))
        if self.animacion.activa:
            controles.append(('Saltar efecto', 'saltar_efecto'))
        elif len(foto.enemigos) > 12 or len(foto.objetos) > 8:
            controles.append(('Objetivos', 'objetivos_panel'))
        bw = (w-64)//len(controles)
        activo = (not self.controlador.ocupado or self.controlador.viajando) and not self.animacion.activa
        for i, (texto, accion) in enumerate(controles):
            libre = accion in ('pausa', 'mapa', 'inventario_panel', 'objetivos_panel', 'detener', 'saltar_efecto')
            u.boton(v, (32+i*bw, h-128, bw-8, 36), texto, accion, libre or activo)
        mensaje = self.error or (foto.mensajes[-1] if foto.mensajes else 'W/A/S/D: moverse | Espacio: esperar | Esc: menú')
        u.parrafo(v, detalle+'\n'+mensaje, (34, h-80, w-70, 54), PELIGRO if self.error else TEXTO)
        if self.panel_local is not None:
            # Se ocultan también las regiones de comandos del fondo para evitar clics a través.
            u.comenzar()
            sombra = pygame.Surface(v.get_size(), pygame.SRCALPHA)
            sombra.fill((2, 5, 18, 155)); v.blit(sombra, (0, 0))
            self.dibujar_panel(foto)

    def dibujar_panel(self, foto):
        u, v = self.ui, self.ventana
        w, h = v.get_size()
        r = pygame.Rect((w-620)//2, 92, 620, h-184)
        activo = not self.controlador.ocupado and not self.animacion.activa
        if self.panel_local == 'mapa':
            u.panel(v, (24, 24, w-48, h-48), 'Mapa conocido')
            self.mapa.dibujar(v, (40, 78, w-80, h-214), foto, u)
            u.texto(v, '? Sin visitar | tenue: recuerdo | ~ conexión esquemática', (44, h-116), TENUE, u.pequena)
            sala = next((s for s in foto.salas if s.sala_id == self.mapa.seleccion), None)
            if self.controlador.viajando:
                u.boton(v, (300, h-84, 230, 40), 'Detener viaje', 'detener')
            elif sala and sala.estado == 2:
                u.boton(v, (300, h-84, 250, 40), f'Viajar a sala {sala.sala_id}', ('juego', 'viajar', str(sala.sala_id), None), activo)
            u.boton(v, (44, h-84, 236, 40), 'Volver', 'cerrar_local')
            return
        if self.panel_local in ('inventario', 'objetivos'):
            self.dibujar_objetos(foto, activo)
            return
        if self.panel_local == 'mensajes':
            u.panel(v, (40, 48, w-80, h-96), 'Registro de la aventura')
            u.parrafo(v, '\n'.join(foto.mensajes), (64, 108, w-128, h-240), desplazamiento=self.panel_scroll)
            u.boton(v, (64, h-110, 210, 40), 'Volver', 'cerrar_local')
            return
        if self.panel_local == 'historia_formulario':
            u.panel(v, r, 'Consultar historia')
            u.parrafo(v, 'Vuelve a ver un instante de la partida sin cambiar el presente.\nEscribe el tiempo o # seguido del número de acción.', (r.x+28, r.y+65, r.w-56, 90))
            u.campo(v, self.historia, (r.x+28, r.y+198, r.w-56, 42), activo)
            u.boton(v, (r.x+28, r.y+260, 240, 42), 'Consultar', 'consultar_historia', activo)
            u.boton(v, (r.x+28, r.bottom-64, 240, 40), 'Volver', 'cerrar_local')
            if self.error: u.parrafo(v, self.error, (r.x+28, r.y+326, r.w-56, 100), PELIGRO)
            return
        if self.panel_local == 'ayuda':
            u.panel(v, r, 'Controles')
            u.parrafo(v, 'Clic: seleccionar puerta, objeto o enemigo.\nEl botón principal cambia según lo elegido.\n\nW/A/S/D: moverse por las salidas.\nEspacio: esperar o saltar una animación.\nI: inventario. M: mapa. Esc: menú o volver.\n\nCada acción confirmada conserva su costo.\nLos enemigos del minimapa son recuerdos.\nNo hay movimiento ni turnos por esperar en pantalla.', (r.x+28, r.y+60, r.w-56, r.h-140), TEXTO)
            u.boton(v, (r.x+28, r.bottom-64, 240, 40), 'Volver', ('juego', 'cerrar_panel', None, None))
            return
        u.panel(v, r, 'Menú de pausa' if self.panel_local == 'pausa' else 'Opciones')
        if self.panel_local == 'pausa':
            opciones = (('Guardar partida', ('juego', 'guardar', None, None)),
                        ('Cargar partida', ('juego', 'cargar', None, None)),
                        ('Usar pergamino', ('juego', 'retroceder', None, None)),
                        ('Consultar historia', 'abrir_historia'), ('Registro de mensajes', 'mensajes'),
                        ('Opciones y ayuda', 'opciones_panel'), ('Volver al inicio', 'menu'))
        else:
            opciones = ((f'Animaciones: {self.animacion.modo}', 'modo_efectos'),
                        ('Controles y ayuda', ('juego', 'ayuda', None, None)), ('Cerrar juego', 'salir'))
        for i, (texto, accion) in enumerate(opciones):
            permiso = activo and (accion != ('juego', 'cargar', None, None) or foto.permitir_cargar)
            u.boton(v, (r.x+28, r.y+56+i*48, r.w-56, 40), texto, accion, permiso or accion == 'salir')
        if self.error:
            u.parrafo(v, self.error, (r.x+28, r.bottom-112, r.w-56, 40), PELIGRO)
        elif foto.mensajes:
            u.parrafo(v, foto.mensajes[-1], (r.x+28, r.bottom-112, r.w-56, 40), TENUE)
        u.boton(v, (r.x+28, r.bottom-60, 240, 36), 'Volver', 'cerrar_local')

    def dibujar_objetos(self, foto, activo):
        u, v = self.ui, self.ventana
        w, h = v.get_size()
        r = pygame.Rect((w-min(w-64, 860))//2, 64, min(w-64, 860), h-128)
        inventario = self.panel_local == 'inventario'
        titulo = f'Inventario {len(foto.inventario)}/{foto.capacidad}' if inventario else 'Elegir objetivo'
        u.panel(v, r, titulo)
        if not inventario:
            for i, (nombre, tab) in enumerate((('Enemigos', 'enemigos'), ('Objetos', 'suelo'))):
                u.boton(v, (r.x+24+i*192, r.y+48, 180, 34), nombre, ('tab', tab))
        items = foto.inventario if inventario else foto.enemigos if self.tab == 'enemigos' else foto.objetos
        inicio_y = r.y+90
        visibles = max(1, (r.h-250)//38)
        self.lista_inicio = min(self.lista_inicio, max(0, len(items)-visibles))
        for i, o in enumerate(items[self.lista_inicio:self.lista_inicio+visibles]):
            elegido = o.seleccionado or o == self.objetivo
            texto = ('> ' if elegido else '')+o.nombre+(' [equipado]' if o.equipado else '')
            if o.vida is not None: texto += f'  {o.vida}/{o.vida_max}'
            accion = ('seleccionar', o) if inventario else ('elegir_objetivo', o)
            u.boton(v, (r.x+24, inicio_y+i*38, r.w-48, 32), texto, accion, activo)
        if not items:
            u.texto(v, 'No hay objetos.' if inventario or self.tab == 'suelo' else 'No hay enemigos.', (r.x+28, inicio_y+12), TENUE)
        u.texto(v, 'Rueda del ratón para recorrer la lista.', (r.x+28, r.bottom-158), TENUE, u.pequena)
        if inventario:
            elegido = next((o for o in foto.inventario if o.seleccionado), None)
            acciones = []
            if elegido:
                if elegido.clase_objeto in ('arma', 'armadura'):
                    acciones.append(('Equipar', 'equipar'))
                elif elegido.clase_objeto in ('pocion', 'antidoto', 'antorcha', 'pergamino_retroceso'):
                    acciones.append(('Usar', 'usar'))
                acciones.append(('Soltar', 'soltar'))
            for i, (texto, op) in enumerate(acciones):
                u.boton(v, (r.x+24+i*174, r.bottom-138, 162, 36), texto, ('juego', op, None, None), activo)
            for i, orden in enumerate(('nombre', 'peso', 'valor')):
                u.boton(v, (r.x+24+i*174, r.bottom-94, 162, 32), orden.capitalize(), ('juego', 'orden', orden, None), activo)
        u.boton(v, (r.right-216, r.bottom-50, 190, 32), 'Volver', 'cerrar_local')


    def dibujar_historia(self, foto):
        h = foto.historia
        u, v = self.ui, self.ventana
        w, alto = v.get_size()
        u.texto(v, f'PASADO · {h.titulo}', (28, 24), ACENTO, u.titulo)
        u.texto(v, f'Consulta t={h.reloj} · El presente sigue en t={foto.reloj}. No consume turno.', (28, 76), TENUE)
        self.foto_historia = replace(foto, sala_id=h.sala_id,
                                    salas=salas_visuales(h.mapa, h.sala_id), mensajes=(), enemigos=())
        self.mapa_historia.dibujar(v, (24, 120, w-440, alto-200), self.foto_historia, u)
        u.parrafo(v, '\n'.join(lineas_historia(h)), (w-392, 124, 364, alto-210), desplazamiento=self.historia_scroll)
        u.boton(v, (28, alto-62, 230, 40), 'Volver al presente', ('juego', 'cerrar_panel', None, None), not self.controlador.ocupado)

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
        if evento.type == pygame.KEYUP:
            if evento.key in self.teclas: self.teclas.remove(evento.key)
        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button in self.botones_pulsados: self.botones_pulsados.remove(evento.button)
        elif evento.type == pygame.WINDOWFOCUSLOST:
            self.tiene_foco = False
            self.teclas.clear()
            self.botones_pulsados.clear()
            self.ui.foco = None
            self.animacion.saltar()
            self.mapa.arrastrando = False
            self.controlador.detener_viaje(perder_foco=True)
            pygame.key.stop_text_input()
            return
        elif evento.type == pygame.WINDOWFOCUSGAINED:
            self.tiene_foco = True
        elif evento.type == pygame.KEYDOWN:
            if evento.key in self.teclas or getattr(evento, 'repeat', False):
                return
            self.teclas.append(evento.key)
            if evento.key == pygame.K_ESCAPE and not self.menu:
                self.ui.foco = None
                if self.panel_local is not None:
                    self.panel_local = None
                elif self.controlador.respuesta.presentacion.panel == 'historia':
                    self.accion(('juego', 'cerrar_panel', None, None))
                else:
                    self.accion('pausa')
                return
            if self.animacion.activa:
                if evento.key == pygame.K_SPACE:
                    self.animacion.saltar()
                return
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button in self.botones_pulsados:
                return
            self.botones_pulsados.append(evento.button)
        if evento.type == pygame.QUIT:
            self.accion('salir')
        elif evento.type == pygame.VIDEORESIZE:
            self.ventana = pygame.display.set_mode((max(1024, evento.w), max(768, evento.h)), pygame.RESIZABLE)
        elif not self.saliendo:
            if (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and not self.menu
                    and self.panel_local is None and not self.controlador.ocupado and not self.animacion.activa):
                foto = self.controlador.respuesta.presentacion
                if foto and foto.panel != 'historia' and self.escena.rect.collidepoint(evento.pos):
                    seleccion = self.escena.seleccionar(evento.pos)
                    if seleccion:
                        self.accion(seleccion)
                        return
            if not self.menu and self.controlador.respuesta.presentacion is not None:
                if self.controlador.respuesta.presentacion.panel == 'historia':
                    self.mapa_historia.evento(evento)
                elif self.panel_local == 'mapa':
                    self.mapa.evento(evento)
                elif self.panel_local is None and evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.mapa.rect.collidepoint(evento.pos):
                    self.accion('mapa'); return
            if evento.type == pygame.MOUSEWHEEL:
                if self.panel_local in ('inventario', 'objetivos'):
                    self.lista_inicio = max(0, self.lista_inicio-evento.y)
                elif self.panel_local is not None:
                    self.panel_scroll = max(0, self.panel_scroll - evento.y*42)
                elif not self.menu and self.controlador.respuesta.presentacion.panel == 'historia':
                    self.historia_scroll = max(0, self.historia_scroll - evento.y*42)
                elif not self.menu and self.mapa.rect.collidepoint(pygame.mouse.get_pos()):
                    pass  # El mapa ya consumió su zoom; no desplazar también la lista.
                elif not self.menu and pygame.mouse.get_pos()[0] >= self.ventana.get_width()-314:
                    self.lista_inicio = max(0, self.lista_inicio-evento.y)
                elif self.error:
                    self.informe_scroll = max(0, self.informe_scroll - evento.y * 42)
                else:
                    cantidad = len(self.puntajes) if self.puntajes is not None else len(self.catalogo)
                    self.catalogo_inicio = max(0, min(max(0, cantidad-1), self.catalogo_inicio - evento.y))
            accion = self.ui.evento(evento, self.controlador.ocupado and not self.controlador.viajando)
            if accion is not None:
                self.accion(accion)
            elif (evento.type == pygame.KEYDOWN and not self.menu and self.ui.foco is None
                  and (not self.controlador.ocupado or self.controlador.viajando)):
                if self.panel_local is not None:
                    if evento.key == pygame.K_ESCAPE:
                        self.panel_local = None
                    return
                for tecla, op, arg in ((pygame.K_w, 'mover', 'N'), (pygame.K_s, 'mover', 'S'),
                                       (pygame.K_a, 'mover', 'O'), (pygame.K_d, 'mover', 'E'),
                                       (pygame.K_SPACE, 'esperar', None), (pygame.K_i, 'inventario', None),
                                       (pygame.K_h, 'ayuda', None), (pygame.K_ESCAPE, 'cerrar_panel', None)):
                    if evento.key == tecla:
                        if op == 'inventario':
                            self.accion('inventario_panel'); break
                        self.accion(('juego', op, arg, None))
                        break
                if evento.key == pygame.K_m: self.accion('mapa')

    def ejecutar(self, reloj=None):
        reloj = reloj or pygame.time.Clock()
        try:
            while not (self.saliendo and self.controlador.cerrada):
                self.actualizar()
                self.dibujar()
                for evento in pygame.event.get():
                    self.evento(evento)
                pygame.display.flip()
                # Una publicación y un ciclo de eventos completos entre pasos.
                if not self.saliendo and not self.menu and self.panel_local in (None, 'mapa') and not self.animacion.activa:
                    self.controlador.continuar_viaje()
                reloj.tick(60)
        finally:
            self.controlador.cerrar(esperar=True)
            pygame.quit()
        return 0


def ejecutar(opciones):
    return Aplicacion(opciones).ejecutar()
