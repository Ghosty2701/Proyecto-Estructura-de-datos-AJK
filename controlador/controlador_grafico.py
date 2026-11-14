"""Coordinador de sesión con un propietario y un buzón de capacidad uno.

No conoce Pygame. La pantalla solo entrega intenciones y recibe snapshots;
la preparación, los comandos, el registro y las consultas pertenecen al trabajador.
"""
from dataclasses import dataclass
from threading import Condition, Event, Thread

from controlador.controlador import Controlador, ResultadoOperacion
from controlador.memoria_visual import MemoriaVisual
from controlador.proyeccion_grafica import (
    IntencionGrafica, congelar_historia, congelar_mapa, proyectar, validar_intencion,
)


@dataclass(frozen=True)
class RespuestaGrafica:
    resultado: ResultadoOperacion
    presentacion: object = None
    error: str | None = None
    fase: str = 'INICIO'
    datos: tuple = ()


class ReceptorValores:
    """Implementa el protocolo de vista sin dibujar ni retener modelos vivos."""
    def __init__(self):
        self.mensajes = []
        self.panel = 'juego'
        self.historia = None
        self.mapa = ()
        self.interrupcion_detectada = False
        self.permitir_cargar = True

    def comenzar(self):
        self.mensajes = []

    def agregar_mensajes(self, mensajes):
        self.mensajes.extend(str(m) for m in mensajes)

    def mostrar_mapa(self, mapa):
        self.panel, self.mapa = 'mapa', congelar_mapa(mapa)

    def mostrar_historia(self, resumen):
        self.panel, self.historia = 'historia', congelar_historia(resumen)

    def mostrar_inventario(self, objetos, **opciones):
        # El proyector obtiene luego los valores y posiciones bajo el mismo dueño.
        self.panel = 'inventario'

    def mostrar_ayuda(self):
        self.panel = 'ayuda'

    def mostrar_estado(self, estado):
        self.panel, self.historia = 'juego', None

    def mostrar_fin(self, estado):
        self.panel = 'resultado'

    def hay_interrupcion(self):
        return self.interrupcion_detectada


class ControladorGrafico:
    def __init__(self, preparar_sesion=None):
        self._preparar_sesion = preparar_sesion
        self.cancelar = Event()
        self._condicion = Condition()
        self._pendiente = None
        self._ocupado = False
        self._cerrando = False
        self._sesion = None
        self._controlador = None
        self._receptor = ReceptorValores()
        self._generacion, self._revision = 0, 0
        self._mensajes = []
        self._memoria = None
        self._orden_inventario = None
        self._respuesta = RespuestaGrafica(ResultadoOperacion('consulta', True))
        self._hilo = Thread(target=self._bucle, name='Cripta-sesion', daemon=False)
        self._hilo.start()

    @property
    def ocupado(self):
        with self._condicion:
            return self._ocupado

    @property
    def respuesta(self):
        with self._condicion:
            return self._respuesta

    @property
    def cerrada(self):
        return not self._hilo.is_alive()

    def _ofrecer(self, operacion, argumento):
        with self._condicion:
            if self._cerrando or self._ocupado:
                return False
            self._ocupado = True
            self._pendiente = (operacion, argumento)
            self._condicion.notify_all()
            return True

    def iniciar(self, configuracion):
        return self._ofrecer('iniciar', configuracion)

    def catalogo(self, configuracion):
        return self._ofrecer('catalogo', configuracion)

    def enviar(self, intencion):
        if not isinstance(intencion, IntencionGrafica):
            raise TypeError('Se requiere una intención gráfica de valores.')
        if self.respuesta.presentacion is None:
            return False
        return self._ofrecer('orden', intencion)

    def esperar(self, segundos=5):
        """Solo para pruebas/ejecutores; el bucle de ventana no espera al trabajador."""
        with self._condicion:
            return self._condicion.wait_for(lambda: not self._ocupado, segundos)

    def cerrar(self, *, esperar=False, timeout=12):
        with self._condicion:
            self._cerrando = True
            self.cancelar.set()
            self._condicion.notify_all()
        if esperar:
            self._hilo.join(timeout)
            if self._hilo.is_alive():
                raise TimeoutError('La sesión todavía está cerrando una operación aceptada.')

    def _publicar(self, respuesta):
        with self._condicion:
            self._respuesta = respuesta

    def _bucle(self):
        try:
            while True:
                with self._condicion:
                    self._condicion.wait_for(lambda: self._cerrando or self._pendiente is not None)
                    if self._cerrando:
                        break
                    operacion, argumento = self._pendiente
                    self._pendiente = None
                try:
                    if operacion == 'iniciar':
                        self._iniciar(argumento)
                    elif operacion == 'catalogo':
                        from controlador.sesion import listar_criptas
                        datos = listar_criptas(argumento, self.cancelar)
                        self._publicar(RespuestaGrafica(ResultadoOperacion('consulta', True),
                                       self.respuesta.presentacion, fase='CATALOGO', datos=datos))
                    else:
                        self._ejecutar(argumento)
                except Exception as error:
                    anterior = self.respuesta
                    from controlador.sesion import CriptaNoResoluble
                    self._publicar(RespuestaGrafica(
                        ResultadoOperacion('rechazo', False), anterior.presentacion,
                        str(error), 'VERIFICACION' if isinstance(error, CriptaNoResoluble) else anterior.fase,
                    ))
                finally:
                    with self._condicion:
                        self._ocupado = False
                        self._condicion.notify_all()
        finally:
            try:
                if self._sesion is not None:
                    self._sesion.cerrar()
            finally:
                with self._condicion:
                    self._ocupado = False
                    self._pendiente = None
                    anterior = self._respuesta
                    self._respuesta = RespuestaGrafica(
                        ResultadoOperacion('salida', True, continuar=False),
                        anterior.presentacion, anterior.error, 'CERRADA',
                    )
                    self._condicion.notify_all()

    def _iniciar(self, configuracion):
        fabrica = self._preparar_sesion
        if fabrica is None:
            from controlador.sesion import preparar_sesion
            fabrica = lambda config: preparar_sesion(config, cancelar=self.cancelar)
        nueva = fabrica(configuracion)
        if self.cancelar.is_set():
            nueva.cerrar()
            return
        receptor = ReceptorValores()
        controlador = Controlador(nueva.partida, receptor,
                                  registrar_accion=getattr(nueva, 'registrar_accion', None))
        # Construir y validar la presentación antes de reemplazar la sesión activa.
        generacion = self._generacion + 1
        try:
            memoria = MemoriaVisual(nueva.partida)
            foto = proyectar(nueva.partida, generacion, 0,
                             mensajes=getattr(nueva, 'mensajes', ()), memoria=memoria)
        except Exception:
            nueva.cerrar()
            raise
        if self._sesion is not None:
            self._sesion.cerrar()
        self._sesion, self._controlador, self._receptor = nueva, controlador, receptor
        self._generacion, self._revision = generacion, 0
        self._mensajes = list(getattr(nueva, 'mensajes', ()))
        self._memoria = memoria
        self._orden_inventario = None
        self._publicar(RespuestaGrafica(ResultadoOperacion('inicio', True), foto, fase='JUGANDO'))

    def _ejecutar(self, intencion):
        foto = self.respuesta.presentacion
        indice = validar_intencion(foto, intencion)
        partida = self._sesion.partida
        op, arg = intencion.operacion, intencion.argumento
        self._receptor.comenzar()
        if op == 'cerrar_panel':
            self._receptor.panel, self._receptor.historia = 'juego', None
            resultado = ResultadoOperacion('consulta', True)
        elif op == 'seleccionar':
            if intencion.objetivo is None or intencion.objetivo.clase != 'inventario':
                raise ValueError('Selecciona un objeto del inventario vigente.')
            objetos = partida.inventario.listar()
            actual = next(i for i, o in enumerate(objetos, 1) if o is partida.inventario.actual())
            distancia = indice - actual
            ordenes = []
            for _ in range(abs(distancia)):
                self._controlador.procesar('sig' if distancia > 0 else 'ant')
                ordenes.extend(self._controlador.ultimo_resultado.ordenes)
            self._receptor.panel = 'inventario'
            resultado = ResultadoOperacion('navegacion', True, tuple(ordenes))
        else:
            if op == 'mover':
                texto = f'ir {arg}'
            elif op == 'viajar':
                texto = f'ir a {arg}'
            elif op in ('atacar', 'recoger'):
                clase = 'enemigo' if op == 'atacar' else 'suelo'
                if intencion.objetivo is not None and intencion.objetivo.clase != clase:
                    raise ValueError('El objetivo no corresponde a esa acción.')
                texto = f'{op} {indice if indice is not None else arg or 1}'
            elif op == 'comando':
                texto = str(arg)
            else:
                texto = op + (f' {arg}' if arg is not None else '')
            self._controlador.procesar(texto)
            resultado = self._controlador.ultimo_resultado
            if op == 'orden' and resultado.aceptada:
                self._orden_inventario = arg
            if not self._controlador._solo_consulta:
                self._receptor.panel, self._receptor.historia = 'juego', None
        if resultado.aceptada and resultado.clase == 'accion':
            self._memoria.observar(partida)
        elif resultado.aceptada and resultado.clase in ('retroceso', 'carga'):
            # La restauración de deltas y memoria persistida se integra en US5/US6.
            self._memoria = MemoriaVisual(partida)
        self._mensajes.extend(self._receptor.mensajes)
        del self._mensajes[:-20]
        self._revision += 1
        nueva = proyectar(partida, self._generacion, self._revision,
                          mensajes=self._mensajes, memoria=self._memoria,
                          panel=self._receptor.panel, historia=self._receptor.historia,
                          orden_inventario=self._orden_inventario)
        fase = 'RESULTADO' if nueva.terminada else 'JUGANDO'
        self._publicar(RespuestaGrafica(resultado, nueva, fase=fase))
