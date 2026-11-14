"""Payload primitivo opcional; nunca modifica el esquema binario de juego v6."""
import hashlib
import json

from controlador.memoria_visual import MemoriaVisual, DeltaVisual
from controlador.proyeccion_grafica import ObservacionEnemigos


def _huella(partida):
    huella = hashlib.sha256()
    for orden in partida.linea_tiempo.ordenes:
        dato = json.dumps((orden.texto, orden.tipo, orden.reloj), ensure_ascii=False,
                          separators=(',', ':')).encode('utf-8')
        huella.update(len(dato).to_bytes(8, 'little'))
        huella.update(dato)
    return huella.hexdigest()


def _marca(partida, version_catalogo):
    return (partida.id_cripta, partida.version_cripta, version_catalogo,
            partida.motor.semilla, partida.motor.reloj, partida.acciones_ejecutadas,
            partida.jugador.sala_actual.sala_id, _huella(partida))


def _observacion_a_datos(observacion):
    return ((observacion.sala_id, observacion.reloj, observacion.grupos)
            if observacion is not None else None)


def exportar_memoria(memoria, partida, version_catalogo):
    return (1, _marca(partida, version_catalogo), memoria.origen,
            tuple(_observacion_a_datos(o) for o in memoria.observaciones if o is not None),
            tuple((d.posicion, d.acciones_antes, d.acciones_despues, d.reloj_antes,
                   d.reloj_despues, tuple((s, _observacion_a_datos(o)) for s, o in d.anteriores))
                  for d in memoria.deltas))


def _exigir(condicion, texto):
    if not condicion:
        raise ValueError(texto)


def _entero(n, minimo=0, maximo=None):
    return type(n) is int and n >= minimo and (maximo is None or n <= maximo)


def _tupla(dato, longitud=None):
    return type(dato) is tuple and (longitud is None or len(dato) == longitud)


def _leer_observacion(dato, memoria, partida, hasta):
    _exigir(_tupla(dato, 3), 'observación mal formada')
    sala, reloj, grupos = dato
    _exigir(_entero(sala), 'ID inválido')
    posicion = memoria.indice.obtener(sala)
    _exigir(posicion is not None, 'sala inexistente')
    _exigir(partida.motor.conocimiento.salas[posicion].estado == 2, 'sala no explorada')
    _exigir(_entero(reloj, maximo=hasta) and _tupla(grupos), 'instante o grupos inválidos')
    claves = []
    for grupo in grupos:
        _exigir(_tupla(grupo, 3), 'grupo mal formado')
        comportamiento, nombre, cantidad = grupo
        _exigir(type(comportamiento) is str and type(nombre) is str and _entero(cantidad),
                'tipo o cantidad inválidos')
        _exigir(grupo[:2] not in claves, 'grupo repetido')
        claves.append(grupo[:2])
    return ObservacionEnemigos(sala, reloj, grupos)


def importar_memoria(datos, partida, version_catalogo):
    """Devuelve candidato y aviso. Un error visual no invalida el juego decodificado."""
    memoria = MemoriaVisual(partida)
    if datos is None:
        return memoria, 'El guardado no incluye recuerdos gráficos; se observa la sala actual.'
    try:
        _exigir(_tupla(datos, 5), 'formato visual inválido')
        version, marca, origen, observaciones, deltas = datos
        _exigir(type(version) is int and version == 1, 'versión visual desconocida')
        esperada = _marca(partida, version_catalogo)
        _exigir(_tupla(marca, 8) and all(type(a) is type(b) and a == b for a, b in zip(marca, esperada)),
                'recuerdos de otra sesión o línea temporal')
        _exigir(_tupla(origen, 2) and _entero(origen[0], maximo=len(partida.linea_tiempo.ordenes))
                and _entero(origen[1], maximo=partida.acciones_ejecutadas), 'origen fuera de rango')
        _exigir(_tupla(observaciones) and len(observaciones) <= len(memoria.ids), 'demasiadas observaciones')
        recibidas = [None] * len(memoria.ids)
        for dato in observaciones:
            observacion = _leer_observacion(dato, memoria, partida, partida.motor.reloj)
            posicion = memoria.indice.obtener(observacion.sala_id)
            _exigir(recibidas[posicion] is None, 'ID repetido')
            recibidas[posicion] = observacion
        _exigir(_tupla(deltas) and len(deltas) <= 5, 'demasiados deltas')
        m = len(deltas)
        vigentes, historial = partida.linea_tiempo.acciones, partida.motor.historial.acciones
        _exigir(m <= len(vigentes) and m <= len(historial), 'sufijo no reversible')
        cambios = []
        for i, dato in enumerate(deltas):
            _exigir(_tupla(dato, 6), 'delta mal formado')
            posicion, antes, despues, reloj_antes, reloj_despues, anteriores = dato
            _exigir(all(_entero(v) for v in dato[:5]), 'tipos de delta inválidos')
            accion = vigentes[-m+i]
            _exigir(posicion == accion.posicion and reloj_antes == accion.reloj == historial[-m+i].reloj_anterior,
                    'ancla de delta no vigente')
            _exigir(antes == partida.acciones_ejecutadas-m+i and despues == antes+1 and antes >= origen[1]
                    and posicion >= origen[0], 'contadores de delta inconsistentes')
            proximo_reloj = deltas[i+1][3] if i+1 < m and _tupla(deltas[i+1], 6) else partida.motor.reloj
            _exigir(reloj_antes <= reloj_despues == proximo_reloj, 'relojes de delta inconsistentes')
            _exigir(_tupla(anteriores) and 0 < len(anteriores) <= len(memoria.ids), 'cambios inválidos')
            vistos, valores = [], []
            for entrada in anteriores:
                _exigir(_tupla(entrada, 2), 'cambio mal formado')
                sala, previo = entrada
                _exigir(_entero(sala) and memoria.indice.obtener(sala) is not None and sala not in vistos, 'ID de cambio inválido')
                vistos.append(sala)
                observacion = None if previo is None else _leer_observacion(previo, memoria, partida, reloj_antes)
                _exigir(observacion is None or observacion.sala_id == sala, 'observación de otra sala')
                valores.append((sala, observacion))
            cambios.append(DeltaVisual(posicion, antes, despues, reloj_antes, reloj_despues, tuple(valores)))
        memoria.observaciones[:] = recibidas
        memoria.deltas[:] = cambios
        memoria.origen = origen
        memoria.observar(partida)
        return memoria, None
    except (ValueError, TypeError, IndexError) as error:
        return MemoriaVisual(partida), f'Se descartaron recuerdos gráficos inválidos: {error}.'
