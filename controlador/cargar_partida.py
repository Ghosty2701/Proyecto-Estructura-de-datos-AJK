"""Convierte las respuestas del servicio en entidades del modelo.

Usa ServicioCripta y su estrategia de precarga sin modificar los adaptadores.
Los IDs de salas se resuelven con el AVL existente, elegido por Kendall.
"""

import json

from adaptadores.cache_catalogo import ArbolAVL, ErrorCatalogo, ReferenciaFicha
from adaptadores.copia_estado import copiar_estado
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
from modelo.inventario_reversible import InventarioReversible, CambioInventario
from modelo.motor_eventos import ActorTurnos, MotorEventos
from modelo.rastro import Puerta, SalaRastro, SalidaRastro
from modelo.conocimiento import ConocimientoMapa
from modelo.linea_tiempo import K_POR_DEFECTO, LineaTiempo
from modelo.verificacion import agrupar_puertas


class ErrorDatosPartida(Exception):
    pass


class ErrorReconstruccion(Exception):
    """La línea de tiempo no puede reconstruir un estado sin pedir datos a la red."""


class _FichasConsulta:
    """Fichas de solo lectura para copias (T008; FR-LT-006, constitución V).

    Lee la ficha residente en el AVL de la caché o el archivo persistido, sin
    solicitudes, sin tocar la LRU ni los contadores y sin insertar ni desalojar.
    Ofrece referencia() con el contrato que usan los constructores de entidades.
    """

    def __init__(self, cache):
        self.cache = cache

    def ficha(self, id_ficha):
        nodo = self.cache.arbol.buscar(id_ficha)
        if nodo is not None:
            return nodo.ficha
        try:
            with open(self.cache._ruta_ficha(id_ficha), encoding="utf-8") as archivo:
                return json.load(archivo)
        except (OSError, ValueError, ErrorCatalogo) as error:
            raise ErrorReconstruccion(
                f"la ficha {id_ficha} no está disponible sin red") from error

    def referencia(self, id_ficha):
        return ReferenciaFicha(id_ficha, self.ficha(id_ficha))


class _GestorConsulta:
    """Gestor de guardado inerte para copias: las fichas ya se completaron."""

    def preparar_botin(self, enemigo):
        pass

    def preparar_retroceso(self, partida):
        pass

    def guardar_sesion(self, partida, ruta):
        raise ErrorGuardado("una copia de la línea de tiempo no se guarda")

    def leer_sesion(self, *argumentos):
        raise ErrorGuardado("una copia de la línea de tiempo no carga partidas")


class PreparadorConsulta:
    """Prepara salas de una copia con el contenido ya descargado, sin red ni precarga."""

    def __init__(self, servicio, partida):
        self.servicio = servicio
        self.partida = partida
        self.fichas = _FichasConsulta(servicio.cache)

    def preparar_sala(self, sala):
        if sala.contenido_cargado:
            return
        contenido = self.servicio.contenido.buscar(sala.sala_id)
        if contenido is None:
            raise ErrorReconstruccion(f"el contenido de la sala {sala.sala_id} no está disponible sin red")
        fichas = self.fichas
        try:
            enemigos = []
            for entrada in contenido["enemigos"]:
                ficha = fichas.ficha(entrada["tipo"])
                datos = {"instancia": entrada["instancia"], "vida": entrada.get("vida"), "ficha": ficha,
                         "suelta": [fichas.ficha(i) for i in ficha.get("suelta") or []]}
                enemigos.append(_crear_enemigo(datos, sala, fichas))
            objetos = [_crear_objeto(fichas.ficha(i), fichas) for i in contenido["objetos"]]
            trampas = [_crear_trampa({"instancia": t["instancia"], "ficha": fichas.ficha(t["tipo"])}, fichas)
                       for t in contenido["trampas"]]
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorReconstruccion(f"Sala {sala.sala_id}: datos incompatibles ({error}).") from error
        sala.enemigos = enemigos
        sala.objetos_suelo = objetos
        sala.trampas = trampas
        self.partida.enemigos.extend(enemigos)
        sala.contenido_cargado = True


def _recorrer_arbol(nodo):
    if nodo is not None:
        yield from _recorrer_arbol(nodo.izquierdo)
        yield nodo.valor
        yield from _recorrer_arbol(nodo.derecho)


def _crear_objeto(ficha, cache):
    return ObjetoPartida(
        id=ficha["id"], clase=ficha["clase"], nombre=ficha["nombre"],
        peso=ficha.get("peso", 0), valor=ficha.get("valor", 0),
        ataque_bonus=ficha.get("ataque_bonus", 0),
        defensa_bonus=ficha.get("defensa_bonus", 0), ficha=cache.referencia(ficha["id"]),
    )


def _crear_enemigo(entrada, sala, cache):
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
        rango=ficha.get("rango"),
    )
    enemigo.nombre = ficha["nombre"]
    enemigo.ficha = cache.referencia(ficha["id"])
    enemigo.sala_actual = sala
    enemigo.suelta = [_crear_objeto(f, cache) for f in entrada["suelta"]]
    return enemigo


def _crear_trampa(entrada, cache):
    ficha = entrada["ficha"]
    rearme = ficha.get("rearme")
    if rearme is None:
        rearme = 300
    # El contrato HTTP actual publica trampas de daño directo.
    trampa = Trampa(
        entrada["instancia"], "dano", ficha["daño"],
        rearme=rearme,
    )
    trampa.ficha = cache.referencia(ficha["id"])
    return trampa


class CargadorPartida:
    def __init__(self, servicio):
        self.servicio = servicio
        self.salas = ArbolAVL()
        self.enemigos = []
        self.jugador = None
        self._ids_preparando = []
        self.servicio.cache.esta_en_uso = self.ficha_en_uso

    def crear(self, cripta_id, semilla, *, encabezado_log=None, datos_verificados=None,
              checkpoint_cada=None):
        if self.jugador is not None:
            raise ErrorDatosPartida("Usa un cargador nuevo para iniciar otra partida.")
        try:
            if datos_verificados is not None:
                if (self.servicio._preparada is None or
                        self.servicio._preparada[3] is not datos_verificados):
                    raise ErrorDatosPartida('La carga verificada no corresponde al servicio')
                datos = self.servicio.cargar(cripta_id, usar_preparada=True)
            else:
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
            motor.conocimiento = ConocimientoMapa(list(_recorrer_arbol(self.salas.raiz)))
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
        self.iniciar_linea(partida, K_POR_DEFECTO if checkpoint_cada is None else checkpoint_cada)
        return partida

    # --- Línea de tiempo (T009) ---

    def iniciar_linea(self, partida, k):
        """Punto 0 en el estado actual; raíces iguales a las del guardado."""
        linea = LineaTiempo(k, copiar_estado)
        linea.iniciar(lambda: (partida, self.salas_ordenadas()), partida.motor.reloj)
        partida.linea_tiempo = linea
        partida.gestor_linea = self
        partida._reloj_linea = partida.motor.reloj
        partida._acciones_linea = partida.acciones_ejecutadas

    def copia_de_trabajo(self, punto):
        """Copia independiente de un punto, conectada a datos de solo lectura."""
        referencias = []
        copia, _ = copiar_estado(punto.estado, referencias)
        fichas = _FichasConsulta(self.servicio.cache)
        for referencia in referencias:
            if referencia.datos is None:
                referencia.datos = fichas.ficha(referencia.id_ficha)
        copia.preparar_sala = PreparadorConsulta(self.servicio, copia).preparar_sala
        copia.gestor_guardado = _GestorConsulta()
        return copia

    def salas_ordenadas(self):
        """Salas del esqueleto en orden de ID: las mismas raíces que el guardado."""
        return list(_recorrer_arbol(self.salas.raiz))

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
        # Las fichas desalojadas se leen solo para escribir el archivo completo;
        # no se reincorporan a la cache ni quedan retenidas por las entidades.
        for referencia in _recorrer_arbol(self.servicio.cache.referencias.raiz):
            ficha = referencia.datos
            if ficha is None:
                ficha = self.servicio.cache._leer_de_disco(referencia.id_ficha)
            if ficha is None:
                raise ErrorGuardado(f"Falta la ficha {referencia.id_ficha} en disco.")
            fichas.insertar(referencia.id_ficha, ficha)
        for sala in salas:
            entidades = list(sala.objetos_suelo) + list(sala.trampas)
            for enemigo in sala.enemigos:
                entidades.append(enemigo)
                entidades.extend(enemigo.suelta)
            for entidad in entidades:
                ficha = getattr(entidad, "ficha", None)
                if isinstance(ficha, ReferenciaFicha):
                    ficha = ficha.datos
                if ficha is not None:
                    fichas.insertar(ficha["id"], ficha)
        for objeto in partida.inventario.listar():
            ficha = getattr(objeto, "ficha", None)
            if isinstance(ficha, ReferenciaFicha):
                ficha = ficha.datos
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
        referencias = ArbolAVL()
        for referencia in cargada.referencias_fichas:
            existente = referencias.buscar(referencia.id_ficha)
            if existente is not None and existente is not referencia:
                raise ErrorGuardado("Referencias de ficha duplicadas en el guardado.")
            referencias.insertar(referencia.id_ficha, referencia)
        try:
            self._recuperar_fichas(self._entidades_activas(nueva))
        except AccionInvalida as error:
            raise ErrorGuardado(str(error)) from error
        for referencia in cargada.referencias_fichas:
            nodo = self.servicio.cache.arbol.buscar(referencia.id_ficha)
            referencia.datos = nodo.ficha if nodo is not None else None
        self.servicio.cache.referencias = referencias
        cargada.datos_extra["fichas"].clear()
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
                costo = conexion.get('costo')
                salida = SalidaRastro(destino, puerta=puerta, costo=100 if costo is None else costo)
                salida.direccion = direccion
                sala.salidas.append(salida)

        try:
            grupos, _ = agrupar_puertas(
                list(_recorrer_arbol(self.salas.raiz)), lambda salida: salida.destino,
                lambda salida: (not salida.abierta, salida.puerta.llave,
                                salida.puerta.cierre_automatico))
        except ValueError as error:
            raise ErrorDatosPartida(str(error)) from error
        for grupo in grupos:
            puerta = grupo[0].puerta
            for salida in grupo:
                salida.puerta = puerta

    def preparar_sala(self, sala):
        if sala.contenido_cargado:
            self._recuperar_fichas(sala.objetos_suelo + sala.trampas)
            return
        try:
            self.servicio.asegurar_contenido(sala.sala_id)
            self._ids_preparando = self.servicio._tipos_en_salas([sala.sala_id])
            self.servicio.cache.verificar_capacidad(self._ids_preparando)
            datos = self.servicio.sala_resuelta(sala.sala_id)
            cache = self.servicio.cache
            enemigos = [_crear_enemigo(e, sala, cache) for e in datos["enemigos"]]
            objetos = [_crear_objeto(o["ficha"], cache) for o in datos["objetos"]]
            trampas = [_crear_trampa(t, cache) for t in datos["trampas"]]
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorDatosPartida(f"Sala {sala.sala_id}: datos incompatibles ({error}).") from error
        finally:
            self._ids_preparando = []
        # Publicar solo despues de convertir todo el contenido. Cargar no activa.
        sala.enemigos = enemigos
        sala.objetos_suelo = objetos
        sala.trampas = trampas
        self.enemigos.extend(enemigos)
        sala.contenido_cargado = True

    def ficha_en_uso(self, id_ficha):
        if id_ficha in self._ids_preparando:
            return True
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

    @staticmethod
    def _entidades_activas(partida):
        sala = partida.jugador.sala_actual
        return (list(partida.inventario.listar()) + sala.objetos_suelo + sala.trampas
                + [enemigo for enemigo in partida.enemigos if enemigo.vida > 0])

    def _recuperar_fichas(self, entidades):
        ids = []
        for entidad in entidades:
            ficha = getattr(entidad, "ficha", None)
            if isinstance(ficha, ReferenciaFicha) and ficha.id_ficha not in ids:
                ids.append(ficha.id_ficha)
        anteriores = self._ids_preparando
        self._ids_preparando = anteriores + ids
        try:
            self.servicio.cache.verificar_capacidad(ids)
            # Estas fichas ya fueron descargadas y persistidas. No se consulta
            # la red para restaurarlas ni se cargan otras salas por anticipacion.
            for identificador in ids:
                cache = self.servicio.cache
                if cache._buscar_en_memoria(identificador) is None:
                    datos = cache._leer_de_disco(identificador)
                    if datos is None:
                        raise AccionInvalida(f"No se puede recuperar la ficha {identificador} del disco.")
                    cache._insertar_en_memoria(identificador, datos)
        except ErrorCatalogo as error:
            raise AccionInvalida(str(error)) from error
        finally:
            self._ids_preparando = anteriores

    def preparar_botin(self, enemigo):
        self._recuperar_fichas(enemigo.suelta)

    def preparar_retroceso(self, partida):
        entidades = []

        def incluir(valor):
            if isinstance(valor, SalaRastro):
                entidades.extend(valor.objetos_suelo + valor.trampas)
            elif isinstance(valor, CambioInventario):
                entidades.append(valor.nodo.objeto)
            elif isinstance(valor, (tuple, list)):
                for elemento in valor:
                    incluir(elemento)
            elif hasattr(valor, "ficha"):
                entidades.append(valor)

        # Solo se inspecciona el intervalo que se va a deshacer, antes de
        # consumir el pergamino. El historial conserva referencias ligeras.
        for tipo, objeto, anterior in partida.motor.historial.acciones[-1].cambios:
            if tipo == "vida":
                incluir(objeto)
            elif tipo == "atributo":
                incluir(objeto)
                incluir(anterior[1])
            elif tipo in ("inventario", "recogida", "objeto_soltado"):
                incluir(anterior)
        self._recuperar_fichas(entidades)
