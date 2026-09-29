def rastro_fresco(ultimo_rastro, reloj_actual):
    # Un rastro ausente o con 400 unidades de tiempo cumplidas ya no es fresco.
    if ultimo_rastro is None:
        return False

    return reloj_actual - ultimo_rastro < 400
    
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
