# Controlador: traduce comandos del jugador en operaciones de la partida y coordina
# el flujo (mostrar estado -> leer comando -> ejecutar). No contiene reglas del juego.
#
# CONTRATO que debe cumplir el objeto `partida` (lo construye quien arme el modelo):
#
#   partida.estado()  -> objeto con estos campos (solo lectura, para la vista):
#       sala_id, sala_nombre, reloj, vida, vida_max, ataque, defensa,
#       efectos (lista de str), salidas (lista de (dir, destino_id, cerrada)),
#       enemigos (lista de (nombre_con_instancia, vida, vida_max)),
#       objetos_suelo (lista de str), terminada (bool), resultado ("victoria"|"derrota"|None)
#   partida.inventario -> modelo.inventario.Inventario del jugador
#   Acciones; cada una devuelve una lista de mensajes (str) y, si la accion se
#   rechaza (sin llave, inventario lleno, etc.), lanza AccionInvalida SIN consumir tiempo:
#       mover(direccion), abrir(direccion), atacar(indice), esperar(), recoger(indice),
#       usar(), equipar(), soltar(), retroceder(), guardar(), cargar()
#   Los indices que recibe (atacar/recoger) son base 1, tal como los ve el jugador.
#   `usar/equipar/soltar` actuan sobre el objeto que el cursor del inventario esta viendo.

from dataclasses import dataclass

from controlador.comandos import parsear


@dataclass(frozen=True)
class ResultadoOperacion:
    clase: str
    aceptada: bool
    ordenes: tuple = ()
    continuar: bool = True


class AccionInvalida(Exception):
    pass


def ejecutar_comando_partida(partida, comando, *, observar=None):
    """Operaciones compartidas por la consola y el replay, sin usar una vista."""
    if partida.estado().terminada:
        raise AccionInvalida("La partida ya termino.")
    if comando.nombre == "siguiente":
        if not partida.inventario.avanzar():
            raise AccionInvalida("Ya estás en el último objeto.")
        return []
    if comando.nombre == "anterior":
        if not partida.inventario.retroceder():
            raise AccionInvalida("Ya estás en el primer objeto.")
        return []
    accion = getattr(partida, comando.nombre)
    opciones = ({'observar': observar} if observar is not None and comando.nombre in
                ('mover', 'abrir', 'atacar', 'esperar', 'recoger', 'usar', 'equipar', 'soltar') else {})
    if comando.argumento is None:
        return accion(**opciones)
    return accion(comando.argumento, **opciones)


def ejecutar_accion_replay(partida, texto):
    comando = parsear(texto)
    if comando is None or comando.nombre not in (
        "mover", "abrir", "atacar", "esperar", "recoger", "usar", "equipar",
        "soltar", "retroceder", "siguiente", "anterior",
    ):
        raise AccionInvalida("El registro no contiene una accion reproducible.")
    return ejecutar_comando_partida(partida, comando)


class Controlador:
    def __init__(self, partida, vista, registrar_accion=None, *, observar=None):
        self.partida = partida
        self.vista = vista
        self._solo_consulta = False
        self.registrar_accion = registrar_accion
        self.observar = observar
        self.ultimo_resultado = ResultadoOperacion('consulta', True)
        self._ordenes_emitidas = []

    def _registrar(self, texto):
        # Misma orden normalizada para el log y la línea de tiempo (FR-LT-013).
        normalizado = texto if texto.startswith('#') else " ".join(texto.strip().lower().split())
        self._ordenes_emitidas.append(normalizado)
        if self.registrar_accion is not None:
            self.registrar_accion(normalizado)
        registrar_orden = getattr(self.partida, "registrar_orden", None)
        if registrar_orden is not None and not normalizado.startswith('#'):
            registrar_orden(normalizado)

    def ejecutar(self):
        # Bucle principal. Termina al salir o cuando la partida acaba.
        self.vista.mostrar_estado(self.partida.estado())
        while not self.partida.estado().terminada:
            if not self.procesar(self.vista.leer_comando()):
                return
            # Las consultas quedan debajo de la sala hasta la proxima accion.
            if not self._solo_consulta:
                self.vista.mostrar_estado(self.partida.estado())
        self.vista.mostrar_fin(self.partida.estado())

    def procesar(self, texto):
        """Mantiene el bool de consola y publica un resultado sin depender de una vista."""
        antes = getattr(self.partida, 'acciones_ejecutadas', 0)
        self._ordenes_emitidas = []
        self._clase_resultado, self._aceptada = 'consulta', True
        continuar = self._procesar(texto)
        diferencia = getattr(self.partida, 'acciones_ejecutadas', 0) - antes
        clase = self._clase_resultado
        if self._aceptada and clase == 'accion':
            if diferencia < 0:
                clase = 'retroceso'
        self.ultimo_resultado = ResultadoOperacion(
            clase, self._aceptada, tuple(self._ordenes_emitidas), continuar,
        )
        return continuar

    def _procesar(self, texto):
        # Devuelve False cuando el jugador pide salir, True en cualquier otro caso.
        self._solo_consulta = False
        comando = parsear(texto)
        if comando is None:
            self._clase_resultado, self._aceptada = 'rechazo', False
            self.vista.agregar_mensajes(["Comando no reconocido. Escribe 'ayuda'."])
            return True

        nombre = comando.nombre
        if nombre == 'mapa':
            self._solo_consulta = True
            self.vista.mostrar_mapa(self.partida.mapa())
            return True
        if nombre == 'historia':
            # Consulta: sin tiempo, sin log ni retroceso (FR-LT-006).
            try:
                resumen = self.partida.historia(comando.argumento)
            except AccionInvalida as error:
                self._clase_resultado, self._aceptada = 'rechazo', False
                # El rechazo se ve al redibujar la sala; nada del juego cambia.
                self.vista.agregar_mensajes([str(error)])
                return True
            self._solo_consulta = True
            self.vista.mostrar_historia(resumen)
            return True
        if nombre == "salir":
            self._clase_resultado = 'salida'
            return False
        if nombre == "ayuda":
            self._solo_consulta = True
            self.vista.mostrar_ayuda()
            return True
        if nombre in ("inventario", "siguiente", "anterior", "orden"):
            self._solo_consulta = True
            if self._navegar_inventario(comando):
                if nombre in ("siguiente", "anterior"):
                    self._clase_resultado = 'navegacion'
                    self._registrar(texto)
            else:
                self._clase_resultado, self._aceptada = 'rechazo', False
            return True

        try:
            if nombre == 'viajar':
                mensajes = self.partida.viajar(
                    comando.argumento, registrar=self._registrar, comentar=self._registrar,
                    interrumpir=self.vista.hay_interrupcion,
                    mostrar_paso=lambda: self.vista.mostrar_estado(self.partida.estado()),
                )
            else:
                mensajes = ejecutar_comando_partida(self.partida, comando, observar=self.observar)
        except AccionInvalida as error:
            self._clase_resultado, self._aceptada = 'rechazo', False
            mensajes = [str(error)]
        else:
            self._clase_resultado = (
                'guardado' if nombre == 'guardar' else 'carga' if nombre == 'cargar'
                else 'viaje' if nombre == 'viajar' else 'accion')
            # Guardar no cambia la simulacion; cargar solo se permite sin bitacora.
            if nombre not in ("guardar", "cargar", "viajar"):
                self._registrar(texto)
        self.vista.agregar_mensajes(mensajes)
        if nombre == 'viajar' and self.vista.interrupcion_detectada:
            self.vista.interrupcion_detectada = False
            return self._procesar(self.vista.leer_comando())
        return True

    def _navegar_inventario(self, comando):
        # Recorrer o consultar el inventario no consume tiempo virtual.
        inv = self.partida.inventario
        if comando.nombre in ("siguiente", "anterior"):
            try:
                ejecutar_comando_partida(self.partida, comando)
            except AccionInvalida as error:
                self.vista.agregar_mensajes([str(error)])
                return False

        if comando.nombre == "orden":
            clave = lambda objeto: getattr(objeto, comando.argumento)
            try:
                ordenados = inv.vista_ordenada(clave)
            except AttributeError:
                self.vista.agregar_mensajes([f"No se puede ordenar por {comando.argumento}."])
                return
            self.vista.mostrar_inventario(
                ordenados,
                actual=inv.actual(),
                arma=inv.arma_equipada,
                armadura=inv.armadura_equipada,
                titulo=f"Inventario por {comando.argumento}",
            )
        else:
            self.vista.mostrar_inventario(
                inv.listar(),
                actual=inv.actual(),
                arma=inv.arma_equipada,
                armadura=inv.armadura_equipada,
            )
        return True
