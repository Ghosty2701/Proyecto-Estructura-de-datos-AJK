"""Convierte las respuestas del servicio en entidades del modelo.

Usa ServicioCripta y su estrategia de precarga sin modificar los adaptadores.
Los IDs de salas se resuelven con el AVL existente, elegido por Kendall.
"""

from adaptadores.cache_catalogo import ArbolAVL, ErrorCatalogo
from adaptadores.cliente_http import ErrorHTTP, PresupuestoAgotado
from adaptadores.modo_offline import ErrorOffline
from adaptadores.servicio_cripta import ErrorCripta
from adaptadores.estado_binario import ObjetoPartida
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

    def crear(self, cripta_id, semilla):
        if self.jugador is not None:
            raise ErrorDatosPartida("Usa un cargador nuevo para iniciar otra partida.")
        try:
            datos = self.servicio.cargar(cripta_id)
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
        return Partida(motor, jugador, self.enemigos, self.preparar_destino, self.servicio.fuente)

    def preparar_destino(self, sala):
        try:
            self.preparar_sala(sala)
        except (ErrorHTTP, PresupuestoAgotado, ErrorCatalogo, ErrorCripta,
                ErrorOffline, ErrorDatosPartida, OSError) as error:
            raise AccionInvalida(
                f"No se confirmo el movimiento: {str(error).rstrip('.')}. "
                "Sigues en la misma sala y el reloj no avanzo. Puedes elegir otra accion o salir."
            ) from error

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
