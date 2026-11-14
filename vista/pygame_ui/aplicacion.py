"""Ventana principal. Pygame vive aquí; la sesión pertenece al trabajador."""
from dataclasses import replace
from pathlib import Path
import pygame

from controlador.controlador_grafico import ControladorGrafico
from controlador.sesion import ConfiguracionSesion
from controlador.proyeccion_grafica import IntencionGrafica, salas_visuales
from vista.vista_consola import lineas_historia
from vista.pygame_ui.componentes import Campo, Componentes, FONDO, PANEL, TEXTO, TENUE, ACENTO, PELIGRO
from vista.pygame_ui.mapa import Mapa
from vista.pygame_ui.sala import EscenaSala
from vista.pygame_ui.animaciones import Animaciones


def elegir_archivo_guardado(actual):
    """Diálogo nativo opcional; cancelar no cambia el Campo de la aplicación."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as error:
        raise OSError('El selector no está disponible. Escribe la ruta del .bin en el campo.') from error
    raiz = None
    try:
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.attributes('-topmost', True)
        carpeta = Path(actual).expanduser().resolve().parent if actual else Path.cwd()
        return filedialog.askopenfilename(parent=raiz, title='Elige una partida guardada',
                                         initialdir=str(carpeta),
                                         filetypes=(('Partidas de Cripta', '*.bin'), ('Todos los archivos', '*.*')))
    except tk.TclError as error:
        raise OSError('No se pudo abrir el selector. Escribe la ruta del .bin en el campo.') from error
    finally:
        if raiz is not None:
            raiz.destroy()


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
        self.inicio_avanzado = False
        self.saliendo = False
        self.error = ''
        self.catalogo = ()
        self.puntajes = None
        self.panel_local = 'inicio_cargar' if c.cargar else None
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
        self.operacion_pendiente = 'Preparando partida'
        self.ocupado_desde = None
        if not self.menu:
            self.candidata = c
            self.controlador.iniciar(c)

    def campo(self, clave):
        return next(c for c in self.campos if c.clave == clave)

    def configurar(self, cargar=False):
        k = self.campo('checkpoint_cada').valor.strip()
        return replace(self.config,
                       nombre=None if cargar else self.campo('nombre').valor.strip(),
                       semilla=self.config.semilla if cargar else int(self.campo('semilla').valor),
                       cripta=None if cargar else self.campo('cripta').valor.strip(),
                       cargar=self.campo('cargar').valor.strip() if cargar else None,
                       offline=self.campo('offline').valor.strip() or None,
                       archivo_guardado=(self.campo('cargar').valor.strip() if cargar else
                                         self.campo('archivo_guardado').valor.strip()) or None,
                       checkpoint_cada=None if cargar else int(k) if k else None,
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
                self.panel_local = None
                self.ui.foco = None
            elif accion in ('pantalla_nueva', 'pantalla_cargar'):
                self.menu = True
                self.panel_local = 'inicio_cargar' if accion == 'pantalla_cargar' else None
                self.inicio_avanzado = False
                self.ui.foco = None
                self.error = ''
            elif accion == 'buscar_guardado':
                ruta = elegir_archivo_guardado(self.campo('cargar').valor.strip())
                if ruta:
                    self.campo('cargar').valor = ruta
                    self.error = ''
                self.teclas.clear(); self.botones_pulsados.clear()
                self.ui.foco = None
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
                self.ui.foco = None
            elif accion in ('nueva', 'cargar'):
                if accion == 'cargar' and not self.campo('cargar').valor.strip():
                    self.panel_local = 'inicio_cargar'
                    self.error = 'Elige un archivo .bin con Buscar o escribe su ruta.'
                    return
                config = self.configurar(cargar=accion == 'cargar')
                config.validar()
                if self.controlador.iniciar(config):
                    self.candidata = config
                    self.error = ''
                    self.indicar_operacion('Cargando partida' if accion == 'cargar' else 'Preparando y verificando la cripta')
            elif accion == 'forzar' and self.candidata is not None:
                self.controlador.iniciar(replace(self.candidata, forzar=True))
                self.indicar_operacion('Preparando la cripta')
                self.error = ''
            elif accion == 'listar':
                config = replace(self.config, offline=self.campo('offline').valor.strip() or None)
                self.controlador.catalogo(config)
                self.indicar_operacion('Buscando criptas disponibles')
                self.error = ''
                self.puntajes = None
            elif accion == 'puntajes':
                self.controlador.puntajes(self.config)
                self.indicar_operacion('Consultando puntajes')
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
                self.error = ''
                self.ui.foco = None
            elif isinstance(accion, tuple) and accion[0] == 'tab':
                self.tab, self.lista_inicio = accion[1], 0
                self.panel_local = 'inventario' if accion[1] == 'inventario' else 'objetivos'
            elif isinstance(accion, tuple) and accion[0] == 'elegir_objetivo':
                self.panel_local = None
                self.accion(('objetivo', accion[1]))
                if accion[1].clase == 'enemigo':
                    self.escena.pagina_enemigos = (accion[1].indice-1)//12
                else:
                    self.escena.pagina_objetos = (accion[1].indice-1)//8
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
                    if self.controlador.enviar(IntencionGrafica(foto.generacion, foto.revision, op, arg, objetivo)):
                        descripcion = next((texto for clave, texto in
                            (('guardar', 'Guardando partida'), ('cargar', 'Cargando partida'),
                             ('historia', 'Consultando historia'), ('orden', 'Ordenando la vista del inventario'),
                             ('retroceder', 'Reconstruyendo el pasado')) if clave == op), 'Procesando acción')
                        self.indicar_operacion(descripcion)
        except (ValueError, OSError) as error:
            self.error = str(error)

    def indicar_operacion(self, texto):
        self.operacion_pendiente = texto
        self.ocupado_desde = pygame.time.get_ticks()

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
            if anterior is None or anterior.generacion != foto.generacion:
                self.panel_local = None
                self.ui.foco = None
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
        u.texto(v, 'CRIPTA', (40, 30), ACENTO, u.titulo)
        u.texto(v, 'Tu aventura, un turno a la vez.', (40, 74), TENUE, u.pequena)
        cargar = self.panel_local == 'inicio_cargar'
        u.boton(v, (40, 108, 240, 40), 'Nueva partida', 'pantalla_nueva', not ocupado, not cargar)
        u.boton(v, (294, 108, 240, 40), 'Cargar partida', 'pantalla_cargar', not ocupado, cargar)
        if self.controlador.respuesta.presentacion:
            u.boton(v, (w-300, 38, 256, 38), 'Volver a la partida', 'continuar', not ocupado)
        if self.inicio_avanzado:
            u.texto(v, 'Opciones de datos y archivos', (40, 168), ACENTO)
            ancho = (w-112)//2
            for i, campo in enumerate(self.campos):
                u.campo(v, campo, (40+i%2*(ancho+32), 230+i//2*80, ancho, 42), not ocupado)
            u.parrafo(v, 'Estas opciones se conservan al volver. Los datos locales deben corresponder a la partida.\nAl cargar se recuperan nombre, semilla e historial desde el archivo guardado.',
                      (40, 566, w-80, h-658))
            u.boton(v, (40, h-78, 260, 42), 'Volver', 'avanzado', not ocupado)
            return
        if cargar:
            u.panel(v, (40, 168, w-80, h-274), '1. Elige una partida guardada')
            u.parrafo(v, 'Busca el archivo .bin que guardaste, o escribe su ruta completa.\nElegir un archivo todavía no reemplaza la partida actual.', (68, 226, w-136, 64), TEXTO)
            u.campo(v, self.campo('cargar'), (68, 322, w-382, 44), not ocupado)
            u.boton(v, (w-292, 322, 222, 44), 'Buscar archivo .bin', 'buscar_guardado', not ocupado)
            ruta = self.campo('cargar').valor.strip()
            u.parrafo(v, 'Archivo elegido: '+(Path(ruta).name if ruta else 'ninguno'), (68, 390, w-136, 30), ACENTO)
            u.parrafo(v, '2. Pulsa Cargar partida para continuar desde ese archivo.\nEl nombre, la semilla y el progreso se recuperan del guardado.', (68, 432, w-136, 56))
            if self.error:
                u.parrafo(v, self.error, (68, 510, w-136, h-636), PELIGRO, self.informe_scroll)
            else:
                u.parrafo(v, 'Fuente de datos: '+(self.campo('offline').valor.strip() or 'servicio por internet')+
                          '\nSi necesitas cambiarla, abre Opciones de datos.', (68, 510, w-136, h-636))
            u.boton(v, (40, h-78, 260, 42), 'Cargar partida', 'cargar', not ocupado and bool(ruta))
            u.boton(v, (316, h-78, 244, 42), 'Opciones de datos', 'avanzado', not ocupado)
            u.boton(v, (w-184, h-78, 140, 42), 'Salir', 'salir')
            return
        ancho = (w - 96) // 2
        for i, campo in enumerate(self.campos[:2]):
            u.campo(v, campo, (40+i*(ancho+16), 194, ancho-16, 42), not ocupado)
        elegida = self.campo('cripta').valor.strip()
        datos = next((fila for fila in self.catalogo if fila[0] == elegida), None)
        u.panel(v, (40, 258, w-80, 96), 'Cripta seleccionada')
        u.parrafo(v, (f'{datos[1]} | ID: {elegida} | {datos[2]} salas' if datos else f'ID: {elegida}' if elegida else
                    'Ninguna. Pulsa Buscar criptas y elige una de la lista.'), (66, 306, w-132, 28), TEXTO)
        u.boton(v, (40, 370, 220, 38), 'Buscar criptas', 'listar', not ocupado)
        u.boton(v, (274, 370, 230, 38), 'Opciones de datos', 'avanzado', not ocupado)
        u.boton(v, (518, 370, 168, 38), 'Puntajes', 'puntajes', not ocupado)
        u.texto(v, 'Selecciona una cripta y luego pulsa Empezar partida.', (44, 426), TENUE, u.pequena)
        if self.error:
            u.parrafo(v, self.error, (44, 464, w-88, h-566), PELIGRO, self.informe_scroll)
        elif self.puntajes is not None:
            filas = ['Cripta / versión · Jugador · Resultado · Tiempo · Acciones · Enemigos']
            filas.extend(f'{c} / {ver} · {nombre} · {resultado} · {tiempo} · {acciones} · {enemigos}'
                         for c, ver, nombre, resultado, tiempo, acciones, enemigos in self.puntajes)
            if not self.puntajes: filas.append('No hay resultados registrados.')
            u.parrafo(v, '\n'.join(filas), (44, 464, w-88, h-566), desplazamiento=self.catalogo_inicio*21)
        else:
            if not self.catalogo:
                u.parrafo(v, 'La lista aparecerá aquí. La fuente se configura en Opciones de datos.\nPuedes recorrerla con la rueda del ratón.', (44, 464, w-88, 76))
            for i, (identificador, nombre, salas) in enumerate(self.catalogo[self.catalogo_inicio:self.catalogo_inicio + max(1, (h-564)//44)]):
                u.boton(v, (44, 464+44*i, w-88, 38), f'{nombre} | {identificador} | {salas} salas',
                        ('cripta', identificador), not ocupado, identificador == elegida)
        forzar = self.controlador.respuesta.fase == 'VERIFICACION' and bool(self.error)
        u.boton(v, (40, h-78, 360 if forzar else 260, 42),
                'Iniciar de todos modos (forzar)' if forzar else 'Empezar partida',
                'forzar' if forzar else 'nueva', not ocupado and bool(elegida))
        u.boton(v, (w-184, h-78, 140, 42), 'Salir', 'salir')

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
        u.panel(v, (w-220, 90, 204, 286), 'Mapa')
        self.mapa.actualizar(foto)
        if self.mini_generacion != foto.generacion:
            self.mapa.escala = 0.60
            self.mini_generacion = foto.generacion
        if self.mini_sala != foto.sala_id:
            self.mapa.centrar(foto.sala_id); self.mini_sala = foto.sala_id
        self.mapa.dibujar(v, (w-212, 132, 188, 234), foto, u)
        u.panel(v, (w-220, 388, 204, h-548), 'Estado')
        u.parrafo(v, f'Ataque: {foto.ataque}\nDefensa: {foto.defensa}\nEnemigos: {len(foto.enemigos)}\nObjetos: {len(foto.objetos)}\n\n'
                         + ('\n'.join(str(e) for e in foto.efectos) if foto.efectos else 'Sin efectos activos'),
                  (w-202, 434, 168, h-610), TEXTO)
        u.texto(v, 'W A S D: moverse  |  H: controles', (34, h-188), TENUE, u.pequena)
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
                        ('Reanudar guardado actual', ('juego', 'cargar', None, None)),
                        ('Cargar otro archivo…', 'pantalla_cargar'),
                        ('Usar pergamino', ('juego', 'retroceder', None, None)),
                        ('Consultar historia', 'abrir_historia'), ('Registro de mensajes', 'mensajes'),
                        ('Opciones y ayuda', 'opciones_panel'), ('Volver al inicio', 'menu'))
        else:
            opciones = ((f'Animaciones: {self.animacion.modo}', 'modo_efectos'),
                        ('Controles y ayuda', ('juego', 'ayuda', None, None)), ('Cerrar juego', 'salir'))
        for i, (texto, accion) in enumerate(opciones):
            permiso = activo and (accion not in (('juego', 'cargar', None, None), 'pantalla_cargar') or foto.permitir_cargar)
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
        if inventario:
            u.texto(v, 'Selecciona un objeto para actuar. Rueda del ratón: recorrer.',
                    (r.x+28, r.y+55), TENUE, u.pequena)
        if not inventario:
            for i, (nombre, tab) in enumerate((('Enemigos', 'enemigos'), ('Objetos', 'suelo'))):
                u.boton(v, (r.x+24+i*192, r.y+48, 180, 34), nombre, ('tab', tab))
        items = foto.inventario if inventario else foto.enemigos if self.tab == 'enemigos' else foto.objetos
        inicio_y = r.y+90
        visibles = max(1, (r.h-(300 if inventario else 250))//38)
        self.lista_inicio = min(self.lista_inicio, max(0, len(items)-visibles))
        for i, o in enumerate(items[self.lista_inicio:self.lista_inicio+visibles]):
            elegido = o.seleccionado or o == self.objetivo
            texto = o.nombre+(' [equipado]' if o.equipado else '')
            if not inventario: texto = f'{o.indice}. '+texto
            if o.vida is not None: texto += f'  {o.vida}/{o.vida_max}'
            if inventario:
                texto += f' | Peso: {o.peso if o.peso is not None else "—"} | Valor: {o.valor if o.valor is not None else "—"}'
            accion = ('seleccionar', o) if inventario else ('elegir_objetivo', o)
            u.boton(v, (r.x+24, inicio_y+i*38, r.w-48, 32), texto, accion, activo, elegido)
        if not items:
            u.texto(v, 'No hay objetos.' if inventario or self.tab == 'suelo' else 'No hay enemigos.', (r.x+28, inicio_y+12), TENUE)
        if inventario:
            criterio = foto.orden_inventario
            sentido = 'A–Z' if criterio == 'nombre' else 'de menor a mayor'
            u.texto(v, 'Orden de la lista: '+(f'{criterio}, {sentido}' if criterio else 'orden original'),
                    (r.x+28, r.bottom-198), ACENTO, u.pequena)
            u.texto(v, 'Ordenar solo cambia esta lista; no gasta un turno.', (r.x+28, r.bottom-178), TENUE, u.pequena)
        else:
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
                ancho = (r.w-48)//3
                u.boton(v, (r.x+24+i*ancho, r.bottom-94, ancho-8, 34), 'Ordenar por '+orden,
                        ('juego', 'orden', orden, None), activo, foto.orden_inventario == orden)
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
        if self.controlador.ocupado or self.saliendo and not self.controlador.cerrada:
            self.dibujar_actividad()
        else:
            self.ocupado_desde = None

    def dibujar_actividad(self):
        """Actividad indeterminada. Este reloj nunca participa en la simulación."""
        ahora = pygame.time.get_ticks()
        if self.ocupado_desde is None:
            self.ocupado_desde = ahora
        transcurrido = max(0, ahora-self.ocupado_desde)
        u, v = self.ui, self.ventana
        if not self.menu and self.controlador.respuesta.presentacion is not None and not self.saliendo:
            if transcurrido < 150:
                return
            # Ocupa solo una esquina de la sala; no agrega controles ni bloquea dibujo.
            r = pygame.Rect(v.get_width()-406, 98, 160, 30)
            velo = pygame.Surface(r.size, pygame.SRCALPHA)
            velo.fill((8, 16, 37, 210)); v.blit(velo, r)
            fase = (transcurrido%1000)/1000*6.283
            pygame.draw.arc(v, ACENTO, (r.x+8, r.y+7, 16, 16), fase, fase+4.5, 2)
            u.texto(v, 'Cargando…', (r.x+32, r.y+7), TENUE, u.pequena)
            return
        r = pygame.Rect((v.get_width()-704)//2, 154, 704, 154)
        u.panel(v, r)
        texto = 'Cerrando la sesión' if self.saliendo else self.operacion_pendiente
        u.texto(v, texto+'…', (r.x+26, r.y+20), ACENTO)
        u.texto(v, f'{transcurrido//1000} s | Esperando la operación; el juego sigue por turnos.',
                (r.x+26, r.y+54), TEXTO, u.pequena)
        pista = pygame.Rect(r.x+28, r.y+86, r.w-56, 8)
        pygame.draw.rect(v, (7, 15, 43), pista)
        paso = (transcurrido//8) % (2*(pista.w-80))
        x = min(paso, 2*(pista.w-80)-paso)
        pygame.draw.rect(v, (144, 199, 255), (pista.x+x, pista.y, 80, 8))
        u.texto(v, 'La fuente de datos puede tardar. No hace falta volver a pulsar.',
                (r.x+26, r.y+110), TENUE, u.pequena)
        # Siempre hay una salida alcanzable, incluso cuando el trabajador tarda.
        u.boton(v, (v.get_width()-200, v.get_height()-64, 168, 36),
                'Cerrar juego', 'salir', not self.saliendo)

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
            if evento.key == pygame.K_ESCAPE and self.menu and self.ui.foco is None:
                if self.inicio_avanzado:
                    self.accion('avanzado')
                elif self.panel_local == 'inicio_cargar':
                    self.accion('pantalla_nueva')
                elif self.controlador.respuesta.presentacion is not None:
                    self.accion('continuar')
                return
            if evento.key == pygame.K_ESCAPE and not self.menu and self.controlador.respuesta.presentacion is not None:
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
                if self.menu and self.error:
                    self.informe_scroll = max(0, self.informe_scroll-evento.y*42)
                elif self.panel_local in ('inventario', 'objetivos'):
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
