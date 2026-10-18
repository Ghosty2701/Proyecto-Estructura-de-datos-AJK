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

from controlador.comandos import parsear


class AccionInvalida(Exception):
    pass


def ejecutar_comando_partida(partida, comando):
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
    if comando.argumento is None:
        return accion()
    return accion(comando.argumento)


def ejecutar_accion_replay(partida, texto):
    comando = parsear(texto)
    if comando is None or comando.nombre not in (
        "mover", "abrir", "atacar", "esperar", "recoger", "usar", "equipar",
        "soltar", "retroceder", "siguiente", "anterior",
    ):
        raise AccionInvalida("El registro no contiene una accion reproducible.")
    return ejecutar_comando_partida(partida, comando)


class Controlador:
    def __init__(self, partida, vista, registrar_accion=None):
        self.partida = partida
        self.vista = vista
        self._solo_consulta = False
        self.registrar_accion = registrar_accion

    def _registrar(self, texto):
        if self.registrar_accion is not None:
            self.registrar_accion(" ".join(texto.strip().lower().split()))

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
        # Devuelve False cuando el jugador pide salir, True en cualquier otro caso.
        self._solo_consulta = False
        comando = parsear(texto)
        if comando is None:
            self.vista.agregar_mensajes(["Comando no reconocido. Escribe 'ayuda'."])
            return True

        nombre = comando.nombre
        if nombre == "salir":
            return False
        if nombre == "ayuda":
            self._solo_consulta = True
            self.vista.mostrar_ayuda()
            return True
        if nombre in ("inventario", "siguiente", "anterior", "orden"):
            self._solo_consulta = True
            if self._navegar_inventario(comando) and nombre in ("siguiente", "anterior"):
                self._registrar(texto)
            return True

        try:
            mensajes = ejecutar_comando_partida(self.partida, comando)
        except AccionInvalida as error:
            mensajes = [str(error)]
        else:
            # Guardar no cambia la simulacion; cargar solo se permite sin bitacora.
            if nombre not in ("guardar", "cargar"):
                self._registrar(texto)
        self.vista.agregar_mensajes(mensajes)
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
