# Inventario (§4.5): lista doblemente enlazada de objetos.
#
# El "orden real" es el orden de la lista (el que ve equipar/soltar/guardar). Las
# vistas ordenadas por peso, valor o nombre se calculan aparte, con comun.ordenamiento,
# y nunca modifican este orden.
#
# Este modulo no conoce la forma exacta de un "objeto": no asume que tenga .peso,
# .valor o .clase. Cuando hace falta ordenar, quien llama entrega una funcion clave
# (ej. clave=lambda o: o.peso). Cuando hace falta equipar, quien llama indica el tipo
# ("arma" o "armadura") porque resolver la clase de un objeto depende del catalogo,
# que este modulo tampoco conoce.

from comun.ordenamiento import vista_ordenada as _vista_ordenada

TIPOS_EQUIPABLES = ("arma", "armadura")


class ErrorInventario(Exception):
    pass


class NodoInventario:
    def __init__(self, objeto):
        self.objeto = objeto
        self.anterior = None
        self.siguiente = None


class Inventario:
    def __init__(self, capacidad):
        if capacidad <= 0:
            raise ValueError("la capacidad del inventario debe ser mayor que 0")

        self.capacidad = capacidad
        self.frente = None
        self.final = None
        self.cantidad = 0
        # Nodo que el jugador esta viendo actualmente; None si el inventario esta vacio.
        self.cursor = None
        # Un objeto equipado por ranura. None si no hay nada puesto en esa ranura.
        self._arma_equipada = None
        self._armadura_equipada = None

    def esta_lleno(self):
        return self.cantidad >= self.capacidad

    def esta_vacio(self):
        return self.cantidad == 0

    # --- Insercion / remocion ---

    def recoger(self, objeto):
        # Con el inventario lleno, no cambia nada y devuelve False: quien llama decide
        # que la accion no se ejecuta ni consume tiempo (Apendice B del enunciado).
        if self.esta_lleno():
            return False

        nodo = NodoInventario(objeto)
        nodo.anterior = self.final
        if self.final is not None:
            self.final.siguiente = nodo
        else:
            self.frente = nodo
        self.final = nodo
        self.cantidad += 1

        if self.cursor is None:
            self.cursor = nodo

        return True

    def soltar_actual(self):
        # Suelta el objeto que el cursor esta viendo, sin importar la posicion: el
        # costo es O(1) porque ya se tiene la referencia directa al nodo (§4.5).
        if self.cursor is None:
            return None

        nodo = self.cursor
        objeto = nodo.objeto

        # El cursor pasa a un vecino antes de desligar el nodo que va a salir.
        vecino = nodo.siguiente if nodo.siguiente is not None else nodo.anterior
        self._desligar(nodo)
        self.cursor = vecino

        if self._arma_equipada is nodo:
            self._arma_equipada = None
        if self._armadura_equipada is nodo:
            self._armadura_equipada = None

        return objeto

    def _desligar(self, nodo):
        # Remueve el nodo por completo (sale del inventario): ajusta la cantidad.
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.frente = nodo.siguiente

        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.final = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = None
        self.cantidad -= 1

    # --- Recorrido bidireccional ---

    def actual(self):
        return self.cursor.objeto if self.cursor is not None else None

    def avanzar(self):
        # Mueve el cursor hacia el objeto siguiente. False si ya esta en el ultimo.
        if self.cursor is None or self.cursor.siguiente is None:
            return False
        self.cursor = self.cursor.siguiente
        return True

    def retroceder(self):
        # Mueve el cursor hacia el objeto anterior. False si ya esta en el primero.
        if self.cursor is None or self.cursor.anterior is None:
            return False
        self.cursor = self.cursor.anterior
        return True

    # --- Equipar ---

    def equipar_actual(self, tipo):
        # Mueve el objeto que se esta viendo al frente del orden real (O(1), sin
        # recorrer el resto) y lo marca como equipado en su ranura. Si ya habia algo
        # equipado ahi, queda desequipado pero permanece en el inventario (no se
        # suelta), tal como exige el enunciado. Devuelve el objeto desplazado, o None
        # si la ranura estaba vacia o ya tenia equipado este mismo objeto.
        if tipo not in TIPOS_EQUIPABLES:
            raise ErrorInventario(f"tipo de equipo invalido: {tipo}")
        if self.cursor is None:
            return None

        nodo = self.cursor
        equipado_previo = self._arma_equipada if tipo == "arma" else self._armadura_equipada

        if equipado_previo is nodo:
            return None  # ya era el equipado de esta ranura; nada que desplazar

        self._mover_al_frente(nodo)
        if tipo == "arma":
            self._arma_equipada = nodo
        else:
            self._armadura_equipada = nodo

        return equipado_previo.objeto if equipado_previo is not None else None

    def _mover_al_frente(self, nodo):
        if nodo is self.frente:
            return
        self._desligar_sin_remover(nodo)
        nodo.anterior = None
        nodo.siguiente = self.frente
        if self.frente is not None:
            self.frente.anterior = nodo
        else:
            self.final = nodo
        self.frente = nodo

    def _desligar_sin_remover(self, nodo):
        # Igual que _desligar, pero el nodo sigue perteneciendo al inventario
        # (se va a reinsertar de inmediato): no toca self.cantidad.
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.frente = nodo.siguiente
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.final = nodo.anterior

    @property
    def arma_equipada(self):
        return self._arma_equipada.objeto if self._arma_equipada is not None else None

    @property
    def armadura_equipada(self):
        return self._armadura_equipada.objeto if self._armadura_equipada is not None else None

    # --- Vistas ---

    def listar(self):
        # Orden real, del primero al ultimo. Base de las vistas ordenadas y de lo
        # que se muestra o se persiste tal cual esta.
        resultado = []
        nodo = self.frente
        while nodo is not None:
            resultado.append(nodo.objeto)
            nodo = nodo.siguiente
        return resultado

    def vista_ordenada(self, clave):
        # No altera frente, final ni cursor en ningun momento (§4.5).
        return _vista_ordenada(self.listar(), clave)
