"""T030/T031: evidencia de alternativas sin cambiar las decisiones del juego."""
import platform
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar, _cronometrar, _comparar_copias
from adaptadores.copia_estado import TablaIdentidades
from adaptadores.estado_binario import IdentidadGuardado
from modelo.bench_linea_tiempo import _preparar, _resumen
from modelo.bench_modelo import ListaOrdenada
from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento
from comun.ordenamiento import ordenar


def _agenda(partida, acciones, rondas):
    """Registra operaciones reales, reproduce las mismas claves en ambas agendas."""
    agenda = partida.motor.agenda
    ids, datos, operaciones = TablaIdentidades(), [], []

    def registrar(evento):
        indice = ids.buscar(evento)
        if indice is None:
            indice = len(datos)
            ids.insertar(evento, indice)
            datos.append((evento.tiempo, evento.cancelado))
        return indice

    iniciales, _ = ordenar(list(agenda.heap), clave=lambda e: e.secuencia)
    iniciales = [registrar(e) for e in iniciales]
    insertar, cancelar, extraer = agenda.insertar, agenda.cancelar, agenda._extraer_raiz
    maximo = [len(agenda.heap)]

    def ins(evento, conservar_secuencia=False):
        assert not conservar_secuencia, 'la traza hacia adelante no restaura eventos'
        operaciones.append(('insertar', registrar(evento)))
        resultado = insertar(evento)
        maximo[0] = max(maximo[0], len(agenda.heap))
        return resultado

    def canc(evento):
        operaciones.append(('cancelar', registrar(evento)))
        return cancelar(evento)

    def ext():
        evento = extraer()
        operaciones.append(('extraer', None if evento is None else registrar(evento)))
        return evento

    agenda.insertar, agenda.cancelar, agenda._extraer_raiz = ins, canc, ext
    try:
        for paso in range(acciones):
            texto = 'esperar' if paso % 2 else (
                'ir N' if partida.jugador.sala_actual.sala_id == 1 else 'ir S')
            _ejecutar(partida, texto)
    finally:
        agenda.insertar, agenda.cancelar, agenda._extraer_raiz = insertar, cancelar, extraer

    def preparar(clase):
        eventos = [Evento(t, 'medicion', i) for i, (t, _) in enumerate(datos)]
        nueva = clase()
        for i in iniciales:
            nueva.insertar(eventos[i])
            eventos[i].cancelado = datos[i][1]
        return nueva, eventos

    def ejecutar(estado):
        nueva, eventos = estado
        extraidos = []
        for op, i in operaciones:
            if op == 'insertar':
                nueva.insertar(eventos[i])
            elif op == 'cancelar':
                nueva.cancelar(eventos[i])
            else:
                # La traza incluye extracción de cancelados; ambas alternativas
                # deben devolver la misma raíz bruta antes de filtrar cancelados.
                e = nueva._extraer_raiz() if isinstance(nueva, AgendaEventos) else (
                    nueva.eventos.pop(0) if nueva.eventos else None)
                obtenido = None if e is None else e.actor_id
                extraidos.append(obtenido)
        return extraidos

    esperado = [i for op, i in operaciones if op == 'extraer']
    tiempos = []
    for clase in (AgendaEventos, ListaOrdenada):
        muestras = []
        for _ in range(rondas):
            estado = preparar(clase)
            salida, ms = _cronometrar(lambda: ejecutar(estado))
            assert salida == esperado, 'la agenda cambia el orden de eventos'
            muestras.append(ms)
        tiempos.append(muestras)
    return {'operaciones': len(operaciones), 'eventos': len(datos),
            'maximo_eventos_en_agenda': maximo[0],
            'insertar': sum(op == 'insertar' for op, _ in operaciones),
            'cancelar': sum(op == 'cancelar' for op, _ in operaciones),
            'extraer': len(esperado), 'heap_ms': tiempos[0], 'lista_ms': tiempos[1],
            'equivalentes': True, 'alcance': 'Traza real, claves y cancelaciones; sin reglas ni copiado dentro del cronometro.'}


def _retroceso(cargador, partida, rondas):
    filas = []
    raiz = (partida, cargador.salas_ordenadas())
    for cantidad in (1, 3, 5):
        adelante, atras = [], []
        for _ in range(rondas):
            copia = cargador.copia_de_trabajo(SimpleNamespace(estado=raiz))
            esperado, azar = _resumen(copia), copia.motor.azar.getstate()
            # Deshacer se mide como alternativa técnica sin consumir pergaminos.
            # Solo se ensayan esperas: no hay efectos irreversibles de inventario.
            for _ in range(cantidad):
                _, ms = _cronometrar(lambda: _ejecutar(copia, 'esperar'))
                adelante.append(ms)
            bloques = copia.motor.historial.acciones[-cantidad:]
            deltas = sum(len(a.cambios) for a in bloques)
            memoria = sum(sys.getsizeof(a) + sys.getsizeof(a.__dict__) +
                          sys.getsizeof(a.cambios) + sum(sys.getsizeof(d) for d in a.cambios)
                          for a in bloques)
            for _ in range(cantidad):
                resultado, ms = _cronometrar(copia.motor.deshacer_ultima_accion)
                assert resultado
                atras.append(ms)
            assert _resumen(copia) == esperado and copia.motor.azar.getstate() == azar
        filas.append({'acciones': cantidad, 'adelante_ms': adelante, 'atras_ms': atras,
                      'deltas': deltas, 'contenedores_deltas_bytes': memoria,
                      'restaura_estado': True})
    return filas


def medir_decisiones(salas=(200, 300, 1000), cazadores=(0, 8, 32), acciones=100, rondas=3, semilla=2026):
    if acciones < 3 or rondas < 1 or not salas or any(s < 3 for s in salas):
        raise ValueError('acciones/salas >=3 y rondas positivas')
    filas = []
    with tempfile.TemporaryDirectory(prefix='cripta-decisiones-') as temporal:
        raiz = Path(temporal)
        for n in salas:
            for c in cazadores:
                print(f'DECISIONES: {n} salas, {c} cazadores', flush=True)
                p = raiz / f'datos-{n}-{c}'
                _paquete(p, n, semilla, cazadores=c)
                cargador = _cargador(p, raiz / f'cache-{n}-{c}')
                partida, _ = _preparar(cargador, acciones, 25, c, semilla, [1])
                retroceso = _retroceso(cargador, partida, rondas)
                identidad = IdentidadGuardado(partida.id_cripta, partida.version_cripta,
                                              cargador.servicio.cache.version)
                copias, codec = _comparar_copias((partida, cargador.salas_ordenadas()), identidad, rondas)
                agenda = _agenda(partida, acciones, rondas)
                filas.append({'salas': n, 'cazadores': c, 'retroceso': retroceso,
                              'registro_activo': len(partida.linea_tiempo.ordenes) > acciones,
                              'codec': {'copia_ms': copias, 'ida_vuelta_ms': codec, 'equivalentes': True},
                              'agenda': agenda})
    return {'semilla': semilla, 'rondas': rondas, 'acciones_preparacion_y_traza': acciones,
            'python': platform.python_version(), 'plataforma': platform.platform(), 'escenarios': filas,
            'alcance': 'Comparacion de componentes con carga P2, registro historico activo. '
                       'Deltas: contenedores reales de hasta cinco acciones, sin contar objetos referenciados; '
                       'no es memoria total ni implementar historia inversa ilimitada. '
                       'El costo de copia inicial no se incluye en costo por accion. Sin HTTP/vista. '
                       'No cambia decisiones ni pretende resolver limites de 20/50 ms.'}


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--salida-json', required=True)
    args = parser.parse_args()
    from adaptadores.resumen_mediciones import resumir_mediciones
    Path(args.salida_json).write_text(json.dumps(resumir_mediciones(medir_decisiones()), ensure_ascii=False, indent=2), encoding='utf-8')
