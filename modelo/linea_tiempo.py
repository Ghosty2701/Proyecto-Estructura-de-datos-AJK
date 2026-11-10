"""Línea de tiempo con puntos de control (D-LT-01/02/03/05; FR-LT-003/004/008/012/013).

Tres arreglos que solo crecen al final:
- órdenes ejecutadas: cada orden reproducible, incluidas las revertidas;
- acciones vigentes: k → (instante de decisión, posición de su orden); el
  pergamino trunca el final;
- puntos de control: copia completa del estado cada K acciones ejecutadas.
Las búsquedas son binarias y propias (sin bisect). El módulo no importa
adaptadores: la función de copia se recibe por parámetro.
"""

ACCION = 'accion'
PERGAMINO = 'pergamino'
NAVEGACION = 'navegacion'

# D-LT-07 pendiente: valor provisional hasta que el usuario elija con mediciones (T034).
K_POR_DEFECTO = 25


class ErrorHistoria(ValueError):
    """Consulta rechazada: no altera la partida."""


class ErrorReconstruccion(Exception):
    """La línea de tiempo no puede reconstruir un estado sin pedir datos a la red."""


def validar_k(k):
    if type(k) is not int or k < 1:
        raise ValueError('K debe ser un entero mayor o igual que 1')
    return k


class OrdenEjecutada:
    __slots__ = ('texto', 'tipo', 'reloj')

    def __init__(self, texto, tipo, reloj):
        self.texto = texto
        self.tipo = tipo
        self.reloj = reloj


class AccionVigente:
    __slots__ = ('reloj', 'posicion')

    def __init__(self, reloj, posicion):
        self.reloj = reloj
        self.posicion = posicion


class PuntoControl:
    """posicion: primera orden por re-ejecutar desde la copia."""
    __slots__ = ('posicion', 'acciones', 'reloj', 'estado', 'k')

    def __init__(self, posicion, acciones, reloj, estado, k):
        self.posicion = posicion
        self.acciones = acciones
        self.reloj = reloj
        self.estado = estado
        self.k = k


class TramoK:
    __slots__ = ('k', 'posicion')

    def __init__(self, k, posicion):
        self.k = k
        self.posicion = posicion


class LineaTiempo:
    def __init__(self, k, copiar):
        self.copiar = copiar
        self.obtener_raiz = None
        self.ordenes = []
        self.acciones = []
        self.puntos = []
        self.tramos = [TramoK(validar_k(k), 0)]
        self.acciones_en_tramo = 0
        # Contadores de trabajo para pruebas de complejidad (PR-LT-002/004).
        self.trabajo_recorte = 0
        self.busquedas_puntos = 0

    @property
    def k(self):
        return self.tramos[-1].k

    @property
    def cantidad_acciones(self):
        return len(self.acciones)

    def iniciar(self, obtener_raiz, reloj):
        """obtener_raiz(): raíz del estado a copiar; solo se invoca al crear un punto."""
        if self.puntos or self.ordenes:
            raise RuntimeError('La línea de tiempo ya fue iniciada')
        self.obtener_raiz = obtener_raiz
        self.puntos.append(PuntoControl(0, 0, reloj, self.copiar(obtener_raiz()), self.k))

    def _crear_punto(self, reloj):
        self.puntos.append(PuntoControl(
            len(self.ordenes), len(self.acciones), reloj, self.copiar(self.obtener_raiz()), self.k))
        self.acciones_en_tramo = 0

    def registrar(self, texto, tipo, reloj_decision, reloj_actual, vigentes):
        """Agrega una orden aceptada. vigentes: acciones vigentes tras ejecutarla."""
        posicion = len(self.ordenes)
        self.ordenes.append(OrdenEjecutada(texto, tipo, reloj_decision))
        if tipo == ACCION:
            if vigentes != len(self.acciones) + 1:
                raise RuntimeError('Contador de acciones inconsistente con la línea')
            self.acciones.append(AccionVigente(reloj_decision, posicion))
            self.acciones_en_tramo += 1
            if self.acciones_en_tramo >= self.k:
                self._crear_punto(reloj_actual)
        elif tipo == PERGAMINO:
            if not 0 <= vigentes <= len(self.acciones):
                raise RuntimeError('Contador de acciones inconsistente con la línea')
            while len(self.acciones) > vigentes:
                self.acciones.pop()
                self.trabajo_recorte += 1
        elif tipo != NAVEGACION:
            raise ValueError(f'tipo de orden desconocido: {tipo!r}')

    def cambiar_k(self, k, reloj):
        """Nuevo K desde ahora (AC-LT-025); los puntos previos no cambian.

        Se conserva la cuenta del tramo: si ya alcanza el nuevo K, el punto se
        crea en este instante. Así la separación respeta el nuevo K y ninguna
        consulta del tramo anterior supera su propio K.
        """
        validar_k(k)
        if k == self.k:
            return
        self.tramos.append(TramoK(k, len(self.ordenes)))
        if self.acciones_en_tramo >= k:
            self._crear_punto(reloj)

    # --- Búsquedas binarias propias ---

    def _ultima_accion_hasta(self, t):
        """Índice de la última acción vigente con instante ≤ t, o -1."""
        bajo, alto = 0, len(self.acciones) - 1
        resultado = -1
        while bajo <= alto:
            medio = (bajo + alto) // 2
            if self.acciones[medio].reloj <= t:
                resultado = medio
                bajo = medio + 1
            else:
                alto = medio - 1
        return resultado

    def punto_para(self, posicion):
        """Último punto con posición ≤ posicion (O(log P))."""
        bajo, alto = 0, len(self.puntos) - 1
        resultado = 0
        while bajo <= alto:
            self.busquedas_puntos += 1
            medio = (bajo + alto) // 2
            if self.puntos[medio].posicion <= posicion:
                resultado = medio
                bajo = medio + 1
            else:
                alto = medio - 1
        return self.puntos[resultado]

    # --- Objetivos de consulta ---

    def objetivo_por_k(self, k):
        """(posición final exclusiva, límite) o None si k = N + 1 (estado actual)."""
        if type(k) is not int or not 1 <= k <= len(self.acciones) + 1:
            raise ErrorHistoria(
                f'número de acción inválido: usa historia #k con 1 ≤ k ≤ {len(self.acciones) + 1}')
        if k == len(self.acciones) + 1:
            return None
        return self.acciones[k - 1].posicion, None

    def objetivo_por_t(self, t, reloj_actual):
        if type(t) is not int or t < 0:
            raise ErrorHistoria('instante inválido: usa historia <t> con t entero ≥ 0')
        if t > reloj_actual:
            raise ErrorHistoria(f'el instante {t} es posterior al reloj actual {reloj_actual}')
        if t == reloj_actual:
            return None
        indice = self._ultima_accion_hasta(t)
        if indice < 0:
            raise ErrorHistoria(f'no hay estado registrado para t={t}')
        accion = self.acciones[indice]
        if accion.reloj == t:
            return accion.posicion, None
        return accion.posicion + 1, t

    def accion_en(self, t):
        """Número k de la última acción vigente decidida en un instante ≤ t (0 si no hay)."""
        return self._ultima_accion_hasta(t) + 1

    def acciones_ejecutadas_entre(self, desde, hasta):
        """Acciones ejecutadas (incluidas las revertidas) en órdenes [desde, hasta)."""
        return sum(1 for posicion in range(desde, hasta) if self.ordenes[posicion].tipo == ACCION)

    def ordenes_entre(self, desde, hasta):
        return [self.ordenes[posicion] for posicion in range(desde, hasta)]
