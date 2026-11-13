"""Observación experimental por orden, sin modificar clases ni la consola.

Conserva deltas antes/después para observar undo y acciones desalojadas; las
marcas se acumulan fuera del historial. No cubre escrituras externas a ejecutar.
El capturador debe conservar su oráculo habilitado durante la validación.
"""
from modelo.inventario_reversible import CambioInventario


class FronteraIncremental:
    def __init__(self, captura, partida):
        self.captura = captura
        self.partida = partida

    def _marcar(self, objeto):
        # Nuevos objetos se descubrirán desde los enlaces registrados. No retener
        # aquí todo objeto temporal que aparece en deltas y luego desaparece.
        if (objeto is None or type(objeto) in (bool, int, float, str, bytes, tuple)):
            return
        if self.captura._identidades.obtener(objeto) is not None:
            self.captura.marcar(objeto)

    def _delta(self, cambio):
        tipo, objeto, anterior = cambio
        self._marcar(objeto)
        if tipo in ('azar', 'atributo', 'vida', 'rastro'):
            # Estado anterior de Random: 625 números, todos inmutables. Los
            # atributos restaurados los cubre su destinatario, no el valor viejo.
            return
        if tipo not in ('evento_programado', 'evento_cancelado', 'evento_extraido',
                        'recogida', 'inventario', 'objeto_soltado', 'botin'):
            raise RuntimeError(f'delta no cubierto por el piloto: {tipo}')
        self._referencias_delta(anterior)

    def _referencias_delta(self, valor):
        pendientes = [valor]
        while pendientes:
            actual = pendientes.pop()
            if type(actual) is tuple:
                pendientes.extend(actual)
                continue
            self._marcar(actual)
            if type(actual) is CambioInventario:
                for nombre in ('inventario', 'nodo', 'anterior', 'siguiente',
                               'anterior_reversible', 'siguiente_reversible',
                               'cursor', 'arma', 'armadura'):
                    self._marcar(getattr(actual, nombre))

    def _frontera(self):
        p = self.partida
        motor = p.motor
        for objeto in (p, p.jugador, p.enemigos, motor, motor.azar,
                       motor.agenda, motor.agenda.heap,
                       motor.historial, motor.historial.acciones):
            self._marcar(objeto)
        inventario = p.inventario
        self._marcar(inventario)
        nodo = inventario.frente
        while nodo is not None:
            self._marcar(nodo)
            self._marcar(nodo.objeto)
            self._marcar(getattr(nodo.objeto, 'ficha', None))
            nodo = nodo.siguiente
        sala = p.jugador.sala_actual
        self._marcar(sala)
        if sala is not None:
            for nombre in ('salidas', 'enemigos', 'trampas', 'objetos_suelo'):
                contenedor = getattr(sala, nombre, ())
                self._marcar(contenedor)
                if nombre != 'salidas':
                    for entidad in contenedor:
                        self._marcar(getattr(entidad, 'ficha', None))
        # Copiar referencias conserva lo que undo vaciará. No visitar otra vez
        # los destinatarios de deltas inalterados en cada navegación/acción.
        return [(accion, tuple(accion.cambios)) for accion in motor.historial.acciones]

    def _diferencia(self, accion, antes, despues):
        prefijo = 0
        limite = min(len(antes), len(despues))
        while prefijo < limite and antes[prefijo] is despues[prefijo]:
            prefijo += 1
        if prefijo == len(antes) == len(despues):
            return
        self._marcar(accion)
        self._marcar(accion.cambios)
        for cambio in antes[prefijo:]:
            self._delta(cambio)
        for cambio in despues[prefijo:]:
            self._delta(cambio)

    def ejecutar(self, operacion):
        anteriores = self._frontera()
        try:
            return operacion()
        finally:
            posteriores = self._frontera()
            for accion, antes in anteriores:
                # Una acción expulsada puede seguir intacta; la deshecha estará
                # vacía. Leer su lista permite distinguir ambos casos.
                self._diferencia(accion, antes, tuple(accion.cambios))
            for accion, despues in posteriores:
                if all(accion is not anterior for anterior, _ in anteriores):
                    self._diferencia(accion, (), despues)
