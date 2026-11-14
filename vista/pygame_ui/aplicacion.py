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
            elif accion == 'mapa':
                self.panel_local = 'mapa'
                self.mapa.centrar(self.controlador.respuesta.presentacion.sala_id)
            elif accion == 'cerrar_local':
                self.panel_local = None
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
            elif isinstance(accion, tuple) and accion[0] == 'objetivo':
                self.objetivo = accion[1]
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
        if self.panel_local == 'mapa':
            u.texto(v, 'Mapa conocido de la cripta', (28, 24), ACENTO, u.titulo)
            self.mapa.dibujar(v, (24, 90, w-48, h-210), foto, u)
            u.texto(v, '? avistada · tenue: recuerdo · rojo: cerrada · ~ enlace esquemático', (30, h-110), TENUE)
            sala = next((s for s in foto.salas if s.sala_id == self.mapa.seleccion), None)
            if self.controlador.viajando:
                u.boton(v, (300, h-62, 230, 40), 'Detener viaje', 'detener')
            elif sala and sala.estado == 2:
                u.boton(v, (300, h-62, 230, 40), f'Viajar a sala {sala.sala_id}', ('juego', 'viajar', str(sala.sala_id), None), not self.controlador.ocupado)
            u.boton(v, (28, h-62, 230, 40), 'Volver a la habitación', 'cerrar_local')
            return
        if foto.terminada and not self.animacion.activa:
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
        activo = (not self.controlador.ocupado or self.controlador.viajando) and not foto.terminada and not self.animacion.activa
        u.texto(v, 'CRIPTA', (24, 14), ACENTO, u.titulo)
        u.texto(v, f'{foto.sala_nombre} · Sala {foto.sala_id}', (185, 21))
        u.texto(v, f'{foto.nombre_jugador}   Vida {foto.vida}/{foto.vida_max}   Ataque {foto.ataque}   Defensa {foto.defensa}', (24, 61), TEXTO)
        u.texto(v, f'Turno {foto.acciones} · t={foto.reloj} · Red {foto.red[0]}/{foto.red[1]}', (w-316, 26), TENUE, u.pequena)
        visual = self.animacion.foto_para_dibujo(foto)
        self.escena.dibujar(v, (20, 96, w-350, h-348), visual, u, self.objetivo, self.puerta, self.animacion)
        if self.animacion.activa:
            u.boton(v, (32, 104, 190, 28), 'Saltar efecto [espacio]', 'saltar_efecto')
        self.mapa.actualizar(foto)
        if self.mini_generacion != foto.generacion:
            self.mapa.escala = 0.45
            self.mini_generacion = foto.generacion
        if self.mini_sala != foto.sala_id:
            self.mapa.centrar(foto.sala_id)
            self.mini_sala = foto.sala_id
        self.mapa.dibujar(v, (w-314, 96, 294, 156), foto, u)
        u.boton(v, (w-314, 258, 142, 28), 'Ampliar mapa', 'mapa')
        u.boton(v, (w-164, 258, 144, 28), 'Centrar', 'centrar')
        ancho = (w-374)//4
        actual = next(s for s in foto.salas if s.actual)
        for i, direccion in enumerate(('N', 'S', 'E', 'O')):
            x = 20+i*(ancho+6)
            salida = next((s for s in actual.salidas if s.direccion == direccion), None)
            texto = f'Ir {direccion}' + (f' · {salida.costo}' if salida else '')
            u.boton(v, (x, h-240, ancho, 32), texto, ('juego', 'mover', direccion, None), activo)
            u.boton(v, (x, h-202, ancho, 30), f'Abrir {direccion}', ('juego', 'abrir', direccion, None), activo)
        for i, (texto, op) in enumerate((('Esperar [espacio]', 'esperar'), ('Retroceder', 'retroceder'), ('Ayuda', 'ayuda'), ('Inventario', 'inventario'))):
            u.boton(v, (20+i*(ancho+6), h-166, ancho, 32), texto, ('juego', op, None, None), activo)
        u.campo(v, self.historia, (20, h-101, 114, 32), not self.controlador.ocupado)
        u.boton(v, (142, h-101, 100, 32), 'Consultar', 'consultar_historia', not self.controlador.ocupado)
        u.boton(v, (250, h-101, 92, 32), 'Guardar', ('juego', 'guardar', None, None), activo)
        u.boton(v, (350, h-101, 92, 32), 'Cargar', ('juego', 'cargar', None, None), activo and foto.permitir_cargar)
        u.boton(v, (450, h-101, 100, 32), 'Mensajes', 'mensajes')
        u.boton(v, (w-314, h-112, 160, 30), f'Efectos: {self.animacion.modo}', 'modo_efectos')
        if self.controlador.viajando:
            u.boton(v, (20, 102, 170, 30), 'Detener viaje', 'detener')
        u.parrafo(v, self.error or '\n'.join(foto.mensajes[-2:]), (24, h-59, w-374, 52), PELIGRO if self.error else TENUE)
        self.dibujar_objetos(foto, activo)
        if self.objetivo is not None:
            u.texto(v, self.objetivo.nombre, (32, h-280), ACENTO, u.pequena)
        elif self.puerta:
            salida = next((s for s in actual.salidas if s.direccion == self.puerta), None)
            if salida:
                u.texto(v, f'Puerta {salida.direccion} · costo {salida.costo} · usa Ir/Abrir', (32, h-280), ACENTO, u.pequena)
        # Páginas de la escena: conservan cada objetivo, sin agregar enemigos.
        for lado, cantidad, pagina, limite, x in (('enemigos', len(foto.enemigos), self.escena.pagina_enemigos, 12, 20),
                                                ('objetos', len(foto.objetos), self.escena.pagina_objetos, 8, 270)):
            if cantidad > limite:
                u.boton(v, (x, 102, 36, 26), '‹', ('pagina', lado, -1))
                u.boton(v, (x+42, 102, 36, 26), '›', ('pagina', lado, 1))
                u.texto(v, f'{lado} {pagina+1}/{(cantidad+limite-1)//limite}', (x+84, 106), TENUE, u.pequena)


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
        x = w-314
        for i, (texto, tab) in enumerate((('Enemigos', 'enemigos'), ('Suelo', 'suelo'), ('Inventario', 'inventario'))):
            u.boton(v, (x+i*100, 300, 94, 36), texto, ('tab', tab))
        items = foto.enemigos if self.tab == 'enemigos' else foto.objetos if self.tab == 'suelo' else foto.inventario
        if foto.panel == 'ayuda':
            u.parrafo(v, 'W/A/S/D: moverse. Espacio: esperar.\nClic en personaje, enemigo, objeto o puerta para seleccionar.\nUsa los botones para actuar.\nCada activación ejecuta una acción.\nRueda sobre mapa: zoom; botón central: desplazar.\nEl minimapa muestra recuerdos, no posiciones remotas.', (x, 348, 294, h-560))
            u.boton(v, (x, h-224, 294, 36), 'Cerrar ayuda', ('juego', 'cerrar_panel', None, None))
        else:
            u.texto(v, f'{self.tab.capitalize()} · {len(items)}' + (f'/{foto.capacidad}' if self.tab == 'inventario' else ''), (x, 342), TENUE, u.pequena)
            visibles = max(1, (h-574)//38)
            self.lista_inicio = min(self.lista_inicio, max(0, len(items)-visibles))
            for i, objeto in enumerate(items[self.lista_inicio:self.lista_inicio+visibles]):
                seleccionado = objeto.seleccionado or objeto == self.objetivo
                etiqueta = ('> ' if seleccionado else '') + f'{objeto.indice}. {objeto.nombre}'
                if objeto.equipado: etiqueta += ' [equipado]'
                if objeto.vida is not None: etiqueta += f' {objeto.vida}/{objeto.vida_max}'
                accion = ('seleccionar', objeto) if self.tab == 'inventario' else ('objetivo', objeto)
                u.boton(v, (x, 366+i*38, 294, 32), etiqueta, accion, activo)
            if not items:
                u.texto(v, 'Sin elementos en esta sala.' if self.tab != 'inventario' else 'Inventario vacío.', (x, 376), TENUE, u.pequena)
            objetivo = self.objetivo
            if self.tab == 'enemigos':
                u.boton(v, (x, h-202, 294, 38), 'Atacar seleccionado', ('juego', 'atacar', None, objetivo), activo and objetivo is not None)
            elif self.tab == 'suelo':
                u.boton(v, (x, h-202, 294, 38), 'Recoger seleccionado', ('juego', 'recoger', None, objetivo), activo and objetivo is not None)
            else:
                for i, (texto, op) in enumerate((('Usar', 'usar'), ('Equipar', 'equipar'), ('Soltar', 'soltar'))):
                    u.boton(v, (x+i*100, h-202, 94, 38), texto, ('juego', op, None, None), activo and bool(items))
                for i, orden in enumerate(('nombre', 'peso', 'valor')):
                    u.boton(v, (x+i*100, h-156, 94, 34), orden.capitalize(), ('juego', 'orden', orden, None), activo)
        seleccion = next((s for s in foto.salas if s.sala_id == self.mapa.seleccion), None)
        if seleccion:
            detalle = f'Sala {seleccion.sala_id}: ' + (seleccion.nombre or 'avistada, contenido desconocido')
            if seleccion.recuerdo:
                detalle += f'\nÚltima observación: t={seleccion.recuerdo.reloj}'
                detalle += '\n' + (', '.join(f'{nombre} ×{n}' for _, nombre, n in seleccion.recuerdo.grupos) or 'Sin enemigos observados')
            u.parrafo(v, detalle, (x, h-75, 294, 23))
        if self.controlador.ocupado:
            u.texto(v, 'Procesando…', (x, h-112), ACENTO)
        u.boton(v, (x, h-48, 140, 36), 'Menú', 'menu', not self.controlador.ocupado)
        u.boton(v, (x+150, h-48, 144, 36), 'Cerrar', 'salir')

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
                else:
                    self.mapa.evento(evento)
            if evento.type == pygame.MOUSEWHEEL:
                if self.panel_local is not None:
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
                if not self.saliendo and not self.menu and not self.animacion.activa:
                    self.controlador.continuar_viaje()
                reloj.tick(60)
        finally:
            self.controlador.cerrar(esperar=True)
            pygame.quit()
        return 0


def ejecutar(opciones):
    return Aplicacion(opciones).ejecutar()
