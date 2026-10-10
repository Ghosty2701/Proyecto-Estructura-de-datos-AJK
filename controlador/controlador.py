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


class Controlador:
    def __init__(self, partida, vista):
        self.partida = partida
        self.vista = vista

    def ejecutar(self):
        # Bucle principal. Termina al salir o cuando la partida acaba.
        while not self.partida.estado().terminada:
            self.vista.mostrar_estado(self.partida.estado())
            if not self.procesar(self.vista.leer_comando()):
                return
        self.vista.mostrar_estado(self.partida.estado())
        self.vista.mostrar_fin(self.partida.estado())

    def procesar(self, texto):
        # Devuelve False cuando el jugador pide salir, True en cualquier otro caso.
        comando = parsear(texto)
        if comando is None:
            self.vista.agregar_mensajes(["Comando no reconocido. Escribe 'ayuda'."])
            return True

        nombre = comando.nombre
        if nombre == "salir":
            return False
        if nombre == "ayuda":
            self.vista.mostrar_ayuda()
            return True
        if nombre in ("inventario", "siguiente", "anterior", "orden"):
            self._navegar_inventario(comando)
            return True

        accion = getattr(self.partida, nombre)
        try:
            if comando.argumento is None:
                mensajes = accion()
            else:
                mensajes = accion(comando.argumento)
        except AccionInvalida as error:
            mensajes = [str(error)]
        self.vista.agregar_mensajes(mensajes)
        return True

    def _navegar_inventario(self, comando):
        # Recorrer o consultar el inventario no consume tiempo virtual.
        inv = self.partida.inventario
        if comando.nombre == "siguiente":
            if not inv.avanzar():
                self.vista.agregar_mensajes(["Ya estás en el último objeto."])
                return
        elif comando.nombre == "anterior":
            if not inv.retroceder():
                self.vista.agregar_mensajes(["Ya estás en el primer objeto."])
                return

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
