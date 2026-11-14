"""Ventana principal. Pygame vive aquí; la sesión pertenece al trabajador."""
from dataclasses import replace
import pygame

from controlador.controlador_grafico import ControladorGrafico
from controlador.sesion import ConfiguracionSesion
from controlador.proyeccion_grafica import IntencionGrafica, salas_visuales
from vista.vista_consola import lineas_historia
from vista.pygame_ui.componentes import Campo, Componentes, FONDO, PANEL, TEXTO, TENUE, ACENTO, PELIGRO
from vista.pygame_ui.mapa import Mapa


class Aplicacion:
    def __init__(self, opciones, controlador=None):
        pygame.display.init()
        pygame.font.init()
        self.ventana = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
        pygame.display.set_caption('Cripta · Mapa y turnos')
        pygame.key.set_repeat()
        self.ui = Componentes()
        self.mapa = Mapa()
        self.mapa_historia = Mapa()
        self.foto_historia = None
        self.historia = Campo('historia', 'Consultar pasado: t o #acción', '0')
        self.historia_scroll = 0
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
                self.panel_local = None
            elif accion == 'continuar':
                self.menu = False
            elif accion == 'detener':
                self.controlador.detener_viaje()
            elif accion == 'consultar_historia':
                self.accion(('juego', 'historia', self.historia.valor.strip(), None))
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
                self.puntajes = None
            elif accion == 'puntajes':
                self.controlador.puntajes(self.config)
                self.error = ''
            elif accion == 'mensajes':
                self.panel_local, self.panel_scroll = 'mensajes', 0
            elif accion == 'cerrar_local':
                self.panel_local = None
            elif accion == 'centrar':
                self.mapa.centrar(self.controlador.respuesta.presentacion.sala_id)
            elif accion in ('zoom_mas', 'zoom_menos'):
                self.mapa.zoom(1.15 if accion == 'zoom_mas' else 1/1.15)
            elif isinstance(accion, tuple) and accion[0] == 'cripta':
                self.campo('cripta').valor = accion[1]
            elif isinstance(accion, tuple) and accion[0] == 'tab':
                self.tab, self.lista_inicio = accion[1], 0
            elif isinstance(accion, tuple) and accion[0] == 'objetivo':
                self.objetivo = accion[1]
                self.tab = 'enemigos' if self.objetivo.clase == 'enemigo' else 'suelo'
            elif isinstance(accion, tuple) and accion[0] in ('juego', 'seleccionar'):
                foto = self.controlador.respuesta.presentacion
                if foto is not None and (not self.controlador.ocupado or self.controlador.viajando):
                    if accion[0] == 'seleccionar':
                        op, arg, objetivo = 'seleccionar', None, accion[1]
                    else:
                        _, op, arg, objetivo = accion
                    if op == 'inventario':
                        self.tab = 'inventario'
                    self.controlador.enviar(IntencionGrafica(foto.generacion, foto.revision, op, arg, objetivo))
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
        elif respuesta.fase == 'PUNTAJES':
            self.puntajes = respuesta.datos
            self.catalogo_inicio = 0
        elif respuesta.presentacion is not None:
            self.menu = False
            self.error = ''
            self.objetivo = None

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
        bw = (w-64)//5
        for i, (texto, accion) in enumerate((('Nueva partida', 'nueva'), ('Cargar .bin', 'cargar'),
                                            ('Listar criptas', 'listar'), ('Puntajes', 'puntajes'), ('Salir', 'salir'))):
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

    def dibujar_juego(self):
        u, v = self.ui, self.ventana
        w, h = v.get_size()
        foto = self.controlador.respuesta.presentacion
        if self.panel_local == 'mensajes':
            u.texto(v, 'Mensajes de la partida', (28, 24), ACENTO, u.titulo)
            u.parrafo(v, '\n'.join(foto.mensajes), (28, 100, w-56, h-190), desplazamiento=self.panel_scroll)
            u.boton(v, (28, h-62, 220, 40), 'Volver', 'cerrar_local')
            return
        if foto.terminada:
            u.texto(v, f'RESULTADO · {foto.resultado}', (40, 40), ACENTO, u.titulo)
            u.parrafo(v, f'{foto.nombre_jugador}\nCripta {foto.id_cripta} · Semilla {foto.semilla}\n'
                         f'Tiempo final: {foto.reloj}\nAcciones: {foto.acciones}\nVida: {foto.vida}/{foto.vida_max}\n\n'
                         + (self.error or '\n'.join(foto.mensajes[-5:])), (40, 120, w-80, h-240))
            u.boton(v, (40, h-80, 230, 40), 'Volver al menú', 'menu')
            u.boton(v, (292, h-80, 180, 40), 'Cerrar', 'salir')
            return
        if foto.panel == 'historia' and foto.historia is not None:
            self.dibujar_historia(foto)
            return
        u.texto(v, f'Cripta {foto.id_cripta}', (32, 24), ACENTO, u.titulo)
        u.texto(v, f'{foto.nombre_jugador} · Sala {foto.sala_id} · Reloj {foto.reloj} · Vida {foto.vida}/{foto.vida_max}', (32, 78))
        u.texto(v, f'Ataque {foto.ataque} · Defensa {foto.defensa} · Efectos: ' + (', '.join(str(e) for e in foto.efectos) or 'ninguno') +
                f' · Red {foto.red[0]}/{foto.red[1]}', (330, 36), TENUE, u.pequena)
        self.mapa.dibujar(v, (24, 116, w-410, h-430), foto, u)
        u.texto(v, '? avistada · tú: verde · rojo: cerrada · ~: esquemático · tenue: recuerdo', (30, h-337), TENUE, u.pequena)
        u.boton(v, (30, 124, 88, 28), 'Centrar', 'centrar')
        u.boton(v, (126, 124, 40, 28), '+', 'zoom_mas')
        u.boton(v, (174, 124, 40, 28), '−', 'zoom_menos')
        activo = (not self.controlador.ocupado or self.controlador.viajando) and not foto.terminada
        ancho = (w-440)//4
        for i, direccion in enumerate(('N', 'S', 'E', 'O')):
            x = 24+i*(ancho+8)
            actual = next(s for s in foto.salas if s.actual)
            salida = next((s for s in actual.salidas if s.direccion == direccion), None)
            etiqueta = f'Ir {direccion}' + (f' · {salida.costo}' if salida else '')
            u.boton(v, (x, h-304, ancho, 38), etiqueta, ('juego', 'mover', direccion, None), activo)
            u.boton(v, (x, h-258, ancho, 36), f'Abrir {direccion}', ('juego', 'abrir', direccion, None), activo)
        for i, (texto, op) in enumerate((('Esperar [espacio]', 'esperar'), ('Retroceder', 'retroceder'), ('Ayuda', 'ayuda'), ('Inventario', 'inventario'))):
            u.boton(v, (24+i*(ancho+8), h-212, ancho, 36), texto, ('juego', op, None, None), activo)
        u.campo(v, self.historia, (24, h-150, 170, 36), not self.controlador.ocupado)
        u.boton(v, (204, h-150, 120, 36), 'Consultar', 'consultar_historia', not self.controlador.ocupado)
        u.boton(v, (334, h-150, 112, 36), 'Guardar', ('juego', 'guardar', None, None), activo)
        u.boton(v, (456, h-150, 112, 36), 'Cargar', ('juego', 'cargar', None, None), activo and foto.permitir_cargar)
        u.boton(v, (w-520, 124, 100, 28), 'Mensajes', 'mensajes')
        u.parrafo(v, self.error or '\n'.join(foto.mensajes[-3:]), (30, h-100, w-430, 88), PELIGRO if self.error else TENUE)
        self.dibujar_objetos(foto, activo)
        sala = next((s for s in foto.salas if s.sala_id == self.mapa.seleccion), None)
        if self.controlador.viajando:
            u.boton(v, (240, 124, 230, 30), 'Detener viaje', 'detener')
        elif sala and sala.estado == 2:
            u.boton(v, (240, 124, 230, 30), f'Viajar a sala {sala.sala_id}', ('juego', 'viajar', str(sala.sala_id), None), activo)

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

    def dibujar_objetos(self, foto, activo):
        u, v = self.ui, self.ventana
        w, h = v.get_size()
        x = w-366
        for i, (texto, tab) in enumerate((('Enemigos', 'enemigos'), ('Suelo', 'suelo'), ('Inventario', 'inventario'))):
            u.boton(v, (x+i*112, 116, 106, 36), texto, ('tab', tab))
        items = foto.enemigos if self.tab == 'enemigos' else foto.objetos if self.tab == 'suelo' else foto.inventario
        if foto.panel == 'ayuda':
            u.parrafo(v, 'W/A/S/D: moverse. Espacio: esperar.\nCada activación ejecuta una acción.\nElige enemigo u objeto y pulsa su acción.\nClic en inventario: cambia el cursor sin turno.\nRueda sobre mapa: zoom; botón central: desplazar.\nLos iconos tenues son recuerdos: no posiciones remotas.\nEscudo: guardián; rombo: errante; mira: rastreador; bestia: cazador.', (x, 166, 332, h-380))
            u.boton(v, (x, h-224, 332, 36), 'Cerrar ayuda', ('juego', 'cerrar_panel', None, None))
        else:
            u.texto(v, f'{self.tab.capitalize()} · {len(items)}' + (f'/{foto.capacidad}' if self.tab == 'inventario' else ''), (x, 160), TENUE, u.pequena)
            visibles = max(1, (h-410)//42)
            self.lista_inicio = min(self.lista_inicio, max(0, len(items)-visibles))
            for i, objeto in enumerate(items[self.lista_inicio:self.lista_inicio+visibles]):
                seleccionado = objeto.seleccionado or objeto == self.objetivo
                etiqueta = ('▶ ' if seleccionado else '') + f'{objeto.indice}. {objeto.nombre}'
                if objeto.equipado: etiqueta += ' [equipado]'
                if objeto.vida is not None: etiqueta += f' {objeto.vida}/{objeto.vida_max}'
                accion = ('seleccionar', objeto) if self.tab == 'inventario' else ('objetivo', objeto)
                u.boton(v, (x, 188+i*42, 332, 36), etiqueta, accion, activo)
            if not items:
                u.texto(v, 'Sin elementos en esta sala.' if self.tab != 'inventario' else 'Inventario vacío.', (x, 195), TENUE, u.pequena)
            objetivo = self.objetivo
            if self.tab == 'enemigos':
                u.boton(v, (x, h-202, 332, 38), 'Atacar seleccionado', ('juego', 'atacar', None, objetivo), activo and objetivo is not None)
            elif self.tab == 'suelo':
                u.boton(v, (x, h-202, 332, 38), 'Recoger seleccionado', ('juego', 'recoger', None, objetivo), activo and objetivo is not None)
            else:
                for i, (texto, op) in enumerate((('Usar', 'usar'), ('Equipar', 'equipar'), ('Soltar', 'soltar'))):
                    u.boton(v, (x+i*112, h-202, 106, 38), texto, ('juego', op, None, None), activo and bool(items))
                for i, orden in enumerate(('nombre', 'peso', 'valor')):
                    u.boton(v, (x+i*112, h-156, 106, 34), orden.capitalize(), ('juego', 'orden', orden, None), activo)
        seleccion = next((s for s in foto.salas if s.sala_id == self.mapa.seleccion), None)
        if seleccion:
            detalle = f'Sala {seleccion.sala_id}: ' + (seleccion.nombre or 'avistada, contenido desconocido')
            if seleccion.recuerdo:
                detalle += f'\nÚltima observación: t={seleccion.recuerdo.reloj}'
                detalle += '\n' + (', '.join(f'{nombre} ×{n}' for _, nombre, n in seleccion.recuerdo.grupos) or 'Sin enemigos observados')
            u.parrafo(v, detalle, (x, h-112, 332, 56))
        if self.controlador.ocupado:
            u.texto(v, 'Procesando…', (x, h-112), ACENTO)
        u.boton(v, (x, h-48, 150, 36), 'Menú', 'menu', not self.controlador.ocupado)
        u.boton(v, (w-198, h-48, 150, 36), 'Cerrar', 'salir')

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
            self.teclas.clear()
            self.botones_pulsados.clear()
            self.ui.foco = None
            self.mapa.arrastrando = False
            self.controlador.detener_viaje(perder_foco=True)
            pygame.key.stop_text_input()
            return
        elif evento.type == pygame.KEYDOWN:
            if evento.key in self.teclas or getattr(evento, 'repeat', False):
                return
            self.teclas.append(evento.key)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button in self.botones_pulsados:
                return
            self.botones_pulsados.append(evento.button)
        if evento.type == pygame.QUIT:
            self.accion('salir')
        elif evento.type == pygame.VIDEORESIZE:
            self.ventana = pygame.display.set_mode((max(1024, evento.w), max(768, evento.h)), pygame.RESIZABLE)
        elif not self.saliendo:
            if not self.menu and self.controlador.respuesta.presentacion is not None:
                if self.controlador.respuesta.presentacion.panel == 'historia':
                    self.mapa_historia.evento(evento)
                else:
                    self.mapa.evento(evento)
            if evento.type == pygame.MOUSEWHEEL:
                if self.panel_local is not None:
                    self.panel_scroll = max(0, self.panel_scroll - evento.y*42)
                elif not self.menu and self.controlador.respuesta.presentacion.panel == 'historia':
                    self.historia_scroll = max(0, self.historia_scroll - evento.y*42)
                elif not self.menu and pygame.mouse.get_pos()[0] >= self.ventana.get_width()-390:
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
                for tecla, op, arg in ((pygame.K_w, 'mover', 'N'), (pygame.K_s, 'mover', 'S'),
                                       (pygame.K_a, 'mover', 'O'), (pygame.K_d, 'mover', 'E'),
                                       (pygame.K_SPACE, 'esperar', None), (pygame.K_i, 'inventario', None),
                                       (pygame.K_h, 'ayuda', None), (pygame.K_ESCAPE, 'cerrar_panel', None)):
                    if evento.key == tecla:
                        if op == 'inventario': self.tab = 'inventario'
                        self.accion(('juego', op, arg, None))
                        break

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
                if not self.saliendo and not self.menu:
                    self.controlador.continuar_viaje()
                reloj.tick(60)
        finally:
            self.controlador.cerrar(esperar=True)
            pygame.quit()
        return 0


def ejecutar(opciones):
    return Aplicacion(opciones).ejecutar()
