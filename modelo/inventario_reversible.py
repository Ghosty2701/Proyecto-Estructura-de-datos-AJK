"""Inventario con operaciones inversas y un segundo orden sin pergaminos.

El historial y el guardado deben integrar este contrato antes de usar esta
extension en una partida completa. El inventario existente conserva su API.
"""

from modelo.inventario import ErrorInventario, Inventario, NodoInventario, TIPOS_EQUIPABLES


class NodoReversible(NodoInventario):
    def __init__(self, objeto):
        super().__init__(objeto)
        self.reversible = getattr(objeto, "clase", None) != "pergamino_retroceso"
        self.anterior_reversible = None
        self.siguiente_reversible = None


class CambioInventario:
    """Numero constante de referencias locales; no copia objetos ni listas."""

    def __init__(self, inventario, tipo, nodo=None):
        self.inventario = inventario
        self.tipo = tipo
        self.nodo = nodo
        self.anterior = nodo.anterior if nodo else None
        self.siguiente = nodo.siguiente if nodo else None
        self.anterior_reversible = nodo.anterior_reversible if nodo else None
        self.siguiente_reversible = nodo.siguiente_reversible if nodo else None
        self.cursor = inventario.cursor
        self.arma = inventario._arma_equipada
        self.armadura = inventario._armadura_equipada
        self.deshecho = False


class InventarioReversible(Inventario):
    def __init__(self, capacidad):
        super().__init__(capacidad)
        self.frente_reversible = None
        self.final_reversible = None

    def _crear_nodo(self, objeto):
        return NodoReversible(objeto)

    def recoger(self, objeto):
        if not super().recoger(objeto):
            return False
        nodo = self.final
        if nodo.reversible:
            self._insertar_reversible(nodo, self.final_reversible, None)
        return True

    def _insertar_reversible(self, nodo, anterior, siguiente):
        nodo.anterior_reversible = anterior
        nodo.siguiente_reversible = siguiente
        if anterior is None:
            self.frente_reversible = nodo
        else:
            anterior.siguiente_reversible = nodo
        if siguiente is None:
            self.final_reversible = nodo
        else:
            siguiente.anterior_reversible = nodo

    def _desligar_reversible(self, nodo):
        anterior, siguiente = nodo.anterior_reversible, nodo.siguiente_reversible
        if anterior is None:
            self.frente_reversible = siguiente
        else:
            anterior.siguiente_reversible = siguiente
        if siguiente is None:
            self.final_reversible = anterior
        else:
            siguiente.anterior_reversible = anterior
        nodo.anterior_reversible = nodo.siguiente_reversible = None

    def _desligar(self, nodo):
        if nodo.reversible:
            self._desligar_reversible(nodo)
        super()._desligar(nodo)

    def _mover_al_frente(self, nodo):
        if nodo is self.frente:
            return
        if nodo.reversible:
            self._desligar_reversible(nodo)
            self._insertar_reversible(nodo, None, self.frente_reversible)
        super()._mover_al_frente(nodo)

    def equipar_actual(self, tipo):
        if tipo not in TIPOS_EQUIPABLES:
            raise ErrorInventario(f"tipo de equipo invalido: {tipo}")
        if self.cursor is not None and not self.cursor.reversible:
            raise ErrorInventario("un pergamino de retroceso no es equipable")
        return super().equipar_actual(tipo)

    # Cada operacion devuelve (resultado habitual, registro o None).
    def recoger_reversible(self, objeto):
        if self.esta_lleno():
            return False, None
        cambio = CambioInventario(self, "recoger")
        self.recoger(objeto)
        cambio.nodo = self.final
        return True, cambio if cambio.nodo.reversible else None

    def soltar_actual_reversible(self):
        if self.cursor is None:
            return None, None
        nodo = self.cursor
        cambio = CambioInventario(self, "retirar", nodo) if nodo.reversible else None
        return self._quitar_nodo(nodo), cambio

    def consumir_primero_reversible(self, cumple):
        nodo = self.frente
        while nodo is not None:
            if cumple(nodo.objeto):
                cambio = CambioInventario(self, "retirar", nodo) if nodo.reversible else None
                self._quitar_nodo(nodo)
                return True, cambio
            nodo = nodo.siguiente
        return False, None

    def equipar_actual_reversible(self, tipo):
        if tipo not in TIPOS_EQUIPABLES:
            raise ErrorInventario(f"tipo de equipo invalido: {tipo}")
        nodo = self.cursor
        if nodo is None:
            return None, None
        if not nodo.reversible:
            raise ErrorInventario("un pergamino de retroceso no es equipable")
        equipado = self._arma_equipada if tipo == "arma" else self._armadura_equipada
        if equipado is nodo:
            return None, None
        cambio = CambioInventario(self, "equipar", nodo)
        return self.equipar_actual(tipo), cambio

    def _contiene(self, buscado):
        if buscado is None:
            return False
        nodo = self.frente
        while nodo is not None:
            if nodo is buscado:
                return True
            nodo = nodo.siguiente
        return False

    def _hueco_real(self, cambio):
        """Busca los vecinos originales dentro del hueco del orden reversible.

        Si desaparecieron, se inserta antes del siguiente objeto reversible
        (o al final si no existe). Los pergaminos presentes mantienen su orden.
        """
        anterior = cambio.anterior_reversible
        limite = cambio.siguiente_reversible
        if anterior is not None and cambio.anterior is anterior:
            return anterior, anterior.siguiente
        nodo = anterior.siguiente if anterior else self.frente
        siguiente_original = None
        while nodo is not limite:
            if nodo is None:
                raise ErrorInventario("los cambios deben deshacerse en orden inverso")
            if nodo is cambio.anterior:
                return nodo, nodo.siguiente
            if nodo is cambio.siguiente:
                siguiente_original = nodo
            nodo = nodo.siguiente
        if siguiente_original is not None:
            return siguiente_original.anterior, siguiente_original
        if limite is not None:
            return limite.anterior, limite
        return self.final, None

    def _insertar_real(self, nodo, anterior, siguiente):
        nodo.anterior, nodo.siguiente = anterior, siguiente
        if anterior is None:
            self.frente = nodo
        else:
            anterior.siguiente = nodo
        if siguiente is None:
            self.final = nodo
        else:
            siguiente.anterior = nodo
        self.cantidad += 1

    def deshacer_cambio(self, cambio):
        """El consumidor garantiza LIFO y conserva solo cambios exitosos.

        Operaciones sin registro sobre objetos ordinarios invalidan el contrato.
        Un conflicto de capacidad se rechaza antes de modificar el inventario.
        No deshace suelo, atributos del actor, reloj ni eventos.
        """
        if not isinstance(cambio, CambioInventario) or cambio.inventario is not self:
            raise ErrorInventario("el cambio no pertenece a este inventario")
        if cambio.deshecho:
            raise ErrorInventario("el cambio ya fue deshecho")
        if cambio.tipo not in ("recoger", "retirar", "equipar"):
            raise ErrorInventario("tipo de cambio desconocido")
        presente = self._contiene(cambio.nodo)
        if cambio.tipo == "retirar":
            if presente:
                raise ErrorInventario("el objeto ya esta en el inventario")
            if self.esta_lleno():
                raise ErrorInventario("no hay espacio para restaurar el objeto")
        elif not presente:
            raise ErrorInventario("el objeto del cambio no esta en el inventario")
        for vecino in (cambio.anterior_reversible, cambio.siguiente_reversible):
            if vecino is not None and not self._contiene(vecino):
                raise ErrorInventario("los cambios deben deshacerse en orden inverso")
        if cambio.tipo != "recoger":
            anterior = cambio.anterior_reversible
            siguiente = anterior.siguiente_reversible if anterior else self.frente_reversible
            if siguiente is cambio.nodo:
                siguiente = siguiente.siguiente_reversible
            if siguiente is not cambio.siguiente_reversible:
                raise ErrorInventario("los cambios deben deshacerse en orden inverso")

        if cambio.tipo == "recoger":
            self._quitar_nodo(cambio.nodo)
        else:
            if cambio.tipo == "equipar":
                self._quitar_nodo(cambio.nodo)
            anterior, siguiente = self._hueco_real(cambio)
            self._insertar_real(cambio.nodo, anterior, siguiente)
            self._insertar_reversible(
                cambio.nodo, cambio.anterior_reversible, cambio.siguiente_reversible
            )
        self._arma_equipada = cambio.arma if self._contiene(cambio.arma) else None
        self._armadura_equipada = cambio.armadura if self._contiene(cambio.armadura) else None
        if self._contiene(cambio.cursor):
            self.cursor = cambio.cursor
        elif not self._contiene(self.cursor):
            self.cursor = self.frente
        cambio.deshecho = True
