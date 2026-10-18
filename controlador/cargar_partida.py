"""Convierte las respuestas del servicio en entidades del modelo.

Usa ServicioCripta y su estrategia de precarga sin modificar los adaptadores.
Los IDs de salas se resuelven con el AVL existente, elegido por Kendall.
"""

from adaptadores.cache_catalogo import ArbolAVL, ErrorCatalogo
from adaptadores.cliente_http import ErrorHTTP, PresupuestoAgotado
from adaptadores.modo_offline import ErrorOffline
from adaptadores.servicio_cripta import ErrorCripta
from adaptadores.estado_binario import (
    ObjetoPartida, guardar_partida, cargar_partida, leer_identidad_guardada,
)
from adaptadores.guardado_binario import ErrorGuardado
from adaptadores.bitacora_partida import verificar_compatibilidad
from controlador.partida import Partida
from controlador.controlador import AccionInvalida
from modelo.efectos import Trampa
from modelo.inventario_reversible import InventarioReversible
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import Puerta, SalaRastro, SalidaRastro


class ErrorDatosPartida(Exception):
    pass


def _recorrer_arbol(nodo):
    if nodo is not None:
        yield from _recorrer_arbol(nodo.izquierdo)
        yield nodo.valor
        yield from _recorrer_arbol(nodo.derecho)


def _crear_objeto(ficha):
    return ObjetoPartida(
        id=ficha["id"], clase=ficha["clase"], nombre=ficha["nombre"],
        peso=ficha.get("peso", 0), valor=ficha.get("valor", 0),
        ataque_bonus=ficha.get("ataque_bonus", 0),
        defensa_bonus=ficha.get("defensa_bonus", 0), ficha=ficha,
    )


def _crear_enemigo(entrada, sala):
    ficha = entrada["ficha"]
    comportamiento = ficha["comportamiento"]
    if comportamiento == "guardián":
        comportamiento = "guardian"
    vida = entrada["vida"]
    if vida is None:
        vida = ficha["vida_max"]
    enemigo = ActorTurnos(
        entrada["instancia"], vida, ficha["velocidad"],
        vida_max=ficha["vida_max"], ataque=ficha["ataque"], defensa=ficha["defensa"],
        comportamiento=comportamiento, regeneracion=ficha.get("regeneracion", 0),
    )
    enemigo.nombre = ficha["nombre"]
    enemigo.ficha = ficha
    enemigo.sala_actual = sala
    enemigo.suelta = [_crear_objeto(f) for f in entrada["suelta"]]
    return enemigo


def _crear_trampa(entrada):
    ficha = entrada["ficha"]
    rearme = ficha.get("rearme")
    if rearme is None:
        rearme = 300
    # El contrato HTTP actual publica trampas de daño directo.
    trampa = Trampa(
        entrada["instancia"], "dano", ficha["daño"],
        rearme=rearme,
    )
    trampa.ficha = ficha
    return trampa


class CargadorPartida:
    def __init__(self, servicio):
        self.servicio = servicio
        self.salas = ArbolAVL()
        self.enemigos = []
        self.jugador = None

    def crear(self, cripta_id, semilla, *, encabezado_log=None):
        if self.jugador is not None:
            raise ErrorDatosPartida("Usa un cargador nuevo para iniciar otra partida.")
        try:
            datos = self.servicio.cargar(cripta_id)
            if encabezado_log is not None:
                # Valida versiones antes de construir entidades o ejecutar acciones.
                self.servicio.cache.obtener_varias(())
                verificar_compatibilidad(
                    encabezado_log, cripta_id, datos["version"], self.servicio.cache.version,
                )
            self._construir_esqueleto()
            inicial = self.salas.buscar(datos["sala_inicial"])
            if inicial is None:
                raise ErrorDatosPartida("La sala inicial no existe en el esqueleto.")
            self.preparar_sala(inicial)
            estadisticas = datos["jugador"]
            jugador = ActorTurnos(
                "jugador", estadisticas["vida_max"], estadisticas["velocidad"],
                ataque=estadisticas["ataque"], defensa=estadisticas["defensa"],
            )
            jugador.inventario = InventarioReversible(datos["inventario_max"])
            motor = MotorEventos(semilla)
            motor.iniciar_partida(jugador, inicial)
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorDatosPartida(f"Datos incompatibles de {cripta_id}: {error}") from error
        self.jugador = jugador
        self.servicio.cache.esta_en_uso = self.ficha_en_uso
        partida = Partida(
            motor, jugador, self.enemigos, self.preparar_destino, self.servicio.fuente,
            sala_salida=datos["sala_salida"], llave_salida=datos["llave_salida"],
            id_cripta=cripta_id, version_cripta=datos["version"],
        )
        partida.gestor_guardado = self
        return partida

    def preparar_destino(self, sala):
        try:
            self.preparar_sala(sala)
        except (ErrorHTTP, PresupuestoAgotado, ErrorCatalogo, ErrorCripta,
                ErrorOffline, ErrorDatosPartida, OSError) as error:
            raise AccionInvalida(
                f"No se confirmo el movimiento: {str(error).rstrip('.')}. "
                "Sigues en la misma sala y el reloj no avanzo. Puedes elegir otra accion o salir."
            ) from error

    def guardar_sesion(self, partida, ruta):
        self.servicio.cache.obtener_varias(())
        salas = list(_recorrer_arbol(self.salas.raiz))
        fichas = ArbolAVL()
        for nodo in _recorrer_arbol(self.servicio.cache.arbol.raiz):
            ficha = nodo.ficha
            fichas.insertar(ficha["id"], ficha)
        for sala in salas:
            entidades = list(sala.objetos_suelo) + list(sala.trampas)
            for enemigo in sala.enemigos:
                entidades.append(enemigo)
                entidades.extend(enemigo.suelta)
            for entidad in entidades:
                ficha = getattr(entidad, "ficha", None)
                if ficha is not None:
                    fichas.insertar(ficha["id"], ficha)
        for objeto in partida.inventario.listar():
            ficha = getattr(objeto, "ficha", None)
            if ficha is not None:
                fichas.insertar(ficha["id"], ficha)
        guardar_partida(
            ruta, partida.motor, partida.jugador, salas,
            id_cripta=partida.id_cripta, version_cripta=partida.version_cripta,
            version_catalogo=self.servicio.cache.version,
            datos_extra={
                "partida": partida,
                "contenido": list(_recorrer_arbol(self.servicio.contenido.raiz)),
                "fichas": list(_recorrer_arbol(fichas.raiz)),
            },
        )

    def leer_sesion(self, ruta, id_cripta, version_cripta):
        self.servicio.cache.obtener_varias(())
        cargada = cargar_partida(
            ruta, id_cripta=id_cripta, version_cripta=version_cripta,
            version_catalogo=self.servicio.cache.version,
        )
        extra = cargada.datos_extra
        if type(extra) is not dict or type(extra.get("partida")) is not Partida:
            raise ErrorGuardado("El archivo no contiene una sesion de consola completa.")
        partida = extra["partida"]
        if (
            partida.motor is not cargada.motor or partida.jugador is not cargada.jugador
            or partida.id_cripta != cargada.identidad.id_cripta
            or partida.version_cripta != cargada.identidad.version_cripta
        ):
            raise ErrorGuardado("La sesion no coincide con las raices del guardado.")
        if partida.victoria or partida.jugador.vida <= 0:
            raise ErrorGuardado("El guardado corresponde a una partida terminada.")
        if len(cargada.salas) != self.servicio.esqueleto.cantidad:
            raise ErrorGuardado("Las salas del guardado no coinciden con el esqueleto actual.")
        for sala in cargada.salas:
            if self.servicio.esqueleto.buscar(sala.sala_id) is None:
                raise ErrorGuardado("El guardado contiene una sala desconocida.")
        for campo in ("contenido", "fichas"):
            if type(extra.get(campo)) is not list:
                raise ErrorGuardado(f"Falta la lista de {campo} del guardado.")
        for datos in extra["contenido"]:
            if type(datos) is not dict or self.servicio.esqueleto.buscar(datos.get("sala")) is None:
                raise ErrorGuardado("Contenido guardado incompatible con el esqueleto.")
        for ficha in extra["fichas"]:
            if type(ficha) is not dict or type(ficha.get("id")) is not str:
                raise ErrorGuardado("Ficha guardada invalida.")
        return cargada

    def aplicar_sesion(self, actual, cargada):
        nueva = cargada.datos_extra["partida"]
        salas = ArbolAVL()
        for sala in cargada.salas:
            salas.insertar(sala.sala_id, sala)
        # Mantener el objeto de sesion que conocen main y el controlador.
        # Los deltas de sus contadores deben apuntar a ese mismo objeto.
        for accion in nueva.motor.historial.acciones:
            for indice, (tipo, objeto, anterior) in enumerate(accion.cambios):
                if objeto is nueva:
                    accion.cambios[indice] = (tipo, actual, anterior)
        # Los datos de infraestructura no retroceden al cargar un guardado.
        for datos in cargada.datos_extra["contenido"]:
            if self.servicio.contenido.buscar(datos["sala"]) is None:
                self.servicio.contenido.insertar(datos["sala"], datos)
        for ficha in cargada.datos_extra["fichas"]:
            self.servicio.cache._guardar_en_disco(ficha)
        for campo in (
            "motor", "jugador", "enemigos", "sala_salida", "llave_salida", "id_cripta",
            "version_cripta", "nombre_jugador", "acciones_ejecutadas", "victoria",
        ):
            setattr(actual, campo, getattr(nueva, campo))
        actual.preparar_sala = self.preparar_destino
        actual.fuente = self.servicio.fuente
        actual.gestor_guardado = self
        actual._mensajes = []
        actual._inicio_pendiente = False
        actual._ataque_pendiente = None
        self.salas = salas
        self.enemigos = actual.enemigos
        self.jugador = actual.jugador
        self.servicio.cache.esta_en_uso = self.ficha_en_uso

    def reanudar(self, ruta):
        if self.jugador is not None:
            raise ErrorGuardado("Usa un cargador nuevo para reanudar otra partida.")
        identidad = leer_identidad_guardada(ruta)
        datos = self.servicio.cargar(identidad.id_cripta)
        cargada = self.leer_sesion(ruta, identidad.id_cripta, datos["version"])
        partida = cargada.datos_extra["partida"]
        partida.ruta_guardado = str(ruta)
        partida.bitacora_activa = False
        self.aplicar_sesion(partida, cargada)
        return partida

    def _construir_esqueleto(self):
        for datos in _recorrer_arbol(self.servicio.esqueleto.raiz):
            sala = SalaRastro(datos["id"])
            sala.nombre = datos["nombre"]
            sala.objetos_suelo = []
            self.salas.insertar(sala.sala_id, sala)
        for datos in _recorrer_arbol(self.servicio.esqueleto.raiz):
            sala = self.salas.buscar(datos["id"])
            for direccion in ("N", "S", "E", "O"):
                conexion = datos.get("salidas", {}).get(direccion)
                if conexion is None:
                    continue
                destino = self.salas.buscar(conexion["sala"])
                if destino is None:
                    raise ErrorDatosPartida(f"Sala {sala.sala_id}: destino inexistente {conexion['sala']}.")
                puerta = Puerta(
                    abierta=not conexion.get("cerrada", False), llave=conexion.get("llave"),
                    cierre_automatico=conexion.get("cierre_automatico"),
                )
                salida = SalidaRastro(destino, puerta=puerta)
                salida.direccion = direccion
                sala.salidas.append(salida)

    def preparar_sala(self, sala):
        if sala.contenido_cargado:
            return
        try:
            datos = self.servicio.sala_resuelta(sala.sala_id)
            enemigos = [_crear_enemigo(e, sala) for e in datos["enemigos"]]
            objetos = [_crear_objeto(o["ficha"]) for o in datos["objetos"]]
            trampas = [_crear_trampa(t) for t in datos["trampas"]]
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorDatosPartida(f"Sala {sala.sala_id}: datos incompatibles ({error}).") from error
        # Publicar solo despues de convertir todo el contenido. Cargar no activa.
        sala.enemigos = enemigos
        sala.objetos_suelo = objetos
        sala.trampas = trampas
        self.enemigos.extend(enemigos)
        sala.contenido_cargado = True

    def ficha_en_uso(self, id_ficha):
        for enemigo in self.enemigos:
            if enemigo.vida > 0 and enemigo.ficha["id"] == id_ficha:
                return True
        if self.jugador is None:
            return False
        for objeto in self.jugador.inventario.listar():
            if objeto.id == id_ficha:
                return True
        sala = self.jugador.sala_actual
        for objeto in sala.objetos_suelo:
            if objeto.id == id_ficha:
                return True
        for trampa in sala.trampas:
            if trampa.ficha["id"] == id_ficha:
                return True
        return False
