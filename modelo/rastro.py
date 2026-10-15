class SalaRastro:
    def __init__(self, sala_id):
        self.sala_id = sala_id
        self.ultimo_rastro = None
        self.salidas = []
        self.enemigos = []
        self.trampas = []
        self.contenido_cargado = False

class Puerta:
    def __init__(
        self,
        abierta=True,
        llave=None,
        *,
        cierre_automatico=None,
    ):
        if cierre_automatico is not None and (
            not isinstance(cierre_automatico, int)
            or cierre_automatico <= 0
        ):
            raise ValueError(
                "El cierre automático debe ser un entero positivo"
            )

        self.abierta = abierta
        self.llave = llave
        self.cierre_automatico = cierre_automatico

class SalidaRastro:
    def __init__(
        self, destino, abierta=True, *, llave=None, puerta=None
    ):
        self.destino = destino
        self.puerta = (
            puerta
            if puerta is not None
            else Puerta(abierta=abierta, llave=llave)
        )

    @property
    def abierta(self):
        return self.puerta.abierta

    @abierta.setter
    def abierta(self, valor):
        self.puerta.abierta = valor
        
def elegir_destino_rastreador(sala, reloj_actual):
    vecinos_abiertos = (
        (salida.destino.sala_id, salida.destino.ultimo_rastro)
        for salida in sala.salidas
        if salida.abierta
    )

    return elegir_vecino(vecinos_abiertos, reloj_actual)

def rastro_fresco(ultimo_rastro, reloj_actual):
    if ultimo_rastro is None:
        return False

    antiguedad = reloj_actual - ultimo_rastro
    return 0 <= antiguedad < 400
    
def elegir_vecino(vecinos, reloj_actual):
    # Recibe pares (sala_id, ultimo_rastro); devuelve None si no hay rastro fresco.
    mejor_id = None
    mejor_tiempo = None

    for sala_id, ultimo_rastro in vecinos:
        if not rastro_fresco(ultimo_rastro, reloj_actual):
            continue

        # Prefiere el rastro mas reciente; en un empate, el menor ID de sala.
        if (
            mejor_tiempo is None
            or ultimo_rastro > mejor_tiempo
            or (ultimo_rastro == mejor_tiempo and sala_id < mejor_id)
        ):
            mejor_id = sala_id
            mejor_tiempo = ultimo_rastro

    return mejor_id


def registrar_rastro(sala, reloj_actual):
    # Actualiza el rastro y devuelve el anterior para poder restaurarlo.
    valor_anterior = sala.ultimo_rastro
    sala.ultimo_rastro = reloj_actual
    return valor_anterior

def restaurar_rastro(sala, valor_anterior):
    # Recupera el rastro guardado antes de la actualizacion.
    sala.ultimo_rastro = valor_anterior
