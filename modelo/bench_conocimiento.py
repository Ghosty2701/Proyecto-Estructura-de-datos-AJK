"""Mediciones reproducibles de conocimiento, índices y rutas; sin vista ni HTTP."""
import random
import sys
from time import perf_counter_ns

from modelo.conocimiento import ConocimientoMapa, IndiceSalas
from modelo.motor_eventos import MotorEventos
from modelo.rastro import Puerta, SalaRastro, SalidaRastro


def _mapa(cantidad, semilla):
    azar = random.Random(semilla)
    salas = [SalaRastro(i * 100003 + 7) for i in range(cantidad)]
    for i, sala in enumerate(salas):
        sala.nombre = f'Sala {i}'
        sala.objetos_suelo = []
    for a, b in zip(salas, salas[1:]):
        puerta, costo = Puerta(), azar.randrange(1, 401)
        for origen, destino, direccion in ((a, b, 'N'), (b, a, 'S')):
            salida = SalidaRastro(destino, puerta=puerta, costo=costo)
            salida.direccion = direccion
            origen.salidas.append(salida)
    return salas


def _indice_alternativo(ids, porcentaje, gradual):
    # Solo comparación: la aplicación siempre usa reserva estática al 70 %.
    indice = object.__new__(IndiceSalas)
    indice.capacidad, indice.sondeos = (32 if gradual else 2), 0
    if not gradual:
        while len(ids) * 100 > indice.capacidad * porcentaje:
            indice.capacidad *= 2
    indice.claves = [None] * indice.capacidad
    indice.posiciones = [None] * indice.capacidad
    ampliaciones = 0
    for posicion, clave in enumerate(ids):
        if (posicion + 1) * 100 > indice.capacidad * porcentaje:
            anteriores = indice.claves
            posiciones = indice.posiciones
            indice.capacidad *= 2
            indice.claves = [None] * indice.capacidad
            indice.posiciones = [None] * indice.capacidad
            ampliaciones += 1
            for anterior, valor in zip(anteriores, posiciones):
                if anterior is not None:
                    celda, _ = indice._localizar(anterior)
                    indice.claves[celda], indice.posiciones[celda] = anterior, valor
        celda, _ = indice._localizar(clave)
        indice.claves[celda], indice.posiciones[celda] = clave, posicion
    return indice, ampliaciones


def medir_rutas_mapa(conocimiento, repeticiones=5, informar=True):
    if repeticiones <= 0 or not conocimiento.salas:
        raise ValueError('La medicion requiere salas y repeticiones positivas')
    # Preparación experimental: conocimiento completo, sin activar contenido.
    for sala in conocimiento.salas:
        conocimiento.entrar(sala.sala, False, setattr)
    tiempos, encontradas, escenarios = [], 0, []
    cantidad = len(conocimiento.salas)
    for modo in ('puertas_observadas', 'recuerdos_abiertos'):
        if modo == 'recuerdos_abiertos':
            # Preparación de estrés: recuerdos abiertos, puertas físicas intactas.
            # El mapa conocido puede recordar abiertas puertas cerradas a distancia.
            for sala in conocimiento.salas:
                for salida in sala.salidas:
                    salida.puerta.observada = True
        muestra, exitos = [], 0
        for _ in range(repeticiones):
            for i, origen in enumerate(conocimiento.salas):
                destino = conocimiento.salas[(i + cantidad // 2) % cantidad]
                inicio = perf_counter_ns()
                resultado = conocimiento.ruta(origen.sala, destino)
                muestra.append((perf_counter_ns() - inicio) / 1_000_000)
                exitos += int(resultado.encontrada)
        escenarios.append({'modo': modo, 'consultas': len(muestra), 'encontradas': exitos,
                           'maximo_ms': max(muestra), 'excedidos_5ms': sum(t >= 5 for t in muestra)})
        tiempos.extend(muestra)
        encontradas += exitos
    salida = {'salas': cantidad, 'consultas': len(tiempos), 'encontradas': encontradas,
              'minimo_ms': min(tiempos), 'promedio_ms': sum(tiempos) / len(tiempos),
              'maximo_ms': max(tiempos), 'excedidos_5ms': sum(t >= 5 for t in tiempos),
              'tiempos_ms': tiempos, 'conocimiento_completo': True}
    salida['escenarios'] = escenarios
    if informar:
        print(f"IR A: {len(tiempos)} calculos sobre {cantidad} salas conocidas; "
              f"maximo {max(tiempos):.4f} ms; >=5 ms: {salida['excedidos_5ms']}")
    return salida


def medir_conocimiento(repeticiones=5, semilla=2026, tamanos=(80, 8000), informar=True):
    if repeticiones <= 0 or not tamanos or min(tamanos) < 5:
        raise ValueError('Cargas positivas y al menos cinco salas')
    regiones, indices = [], []
    for cantidad in tamanos:
        salas = _mapa(cantidad, semilla)
        k, motor = ConocimientoMapa(salas), MotorEventos(semilla)
        k.entrar(salas[0], False, motor._cambiar)
        revelacion, inversion, trabajo, memoria_deltas = [], [], [], []
        for _ in range(repeticiones):
            motor.iniciar_accion()
            anterior = k.actualizaciones
            inicio = perf_counter_ns()
            k.entrar(salas[1], True, motor._cambiar)
            revelacion.append((perf_counter_ns() - inicio) / 1_000_000)
            trabajo.append(k.actualizaciones - anterior)
            cambios = motor.historial.acciones[-1].cambios
            memoria_deltas.append(sys.getsizeof(cambios) + sum(sys.getsizeof(c) for c in cambios))
            inicio = perf_counter_ns()
            motor.historial.acciones.pop().deshacer()
            inversion.append((perf_counter_ns() - inicio) / 1_000_000)
            assert [s.estado for s in k.salas[:4]] == [2, 1, 0, 0]
        assert min(trabajo) == max(trabajo)
        inicio = perf_counter_ns()
        for _ in range(1000):
            assert k.salas[0].estado == 2
            assert k.salas[0].salidas[0].puerta.observada is True
        consulta_ns = (perf_counter_ns() - inicio) / 1000
        regiones.append({'salas': cantidad, 'trabajo_revelacion': max(trabajo),
                         'revelacion_max_ms': max(revelacion), 'inversion_max_ms': max(inversion),
                         'consulta_estado_puerta_ns': consulta_ns,
                         'memoria_parcial_indices_bytes': sum(sys.getsizeof(v) for v in
                           (k.salas, k.indice.claves, k.indice.posiciones, k.registros.datos)),
                         'memoria_parcial_deltas_bytes': max(memoria_deltas)})
        ids = [s.sala_id for s in salas]
        for nombre, porcentaje, gradual in (('reserva70', 70, False), ('reserva50', 50, False),
                                             ('gradual70', 70, True)):
            tiempos = []
            for _ in range(repeticiones):
                inicio = perf_counter_ns()
                indice, ampliaciones = _indice_alternativo(ids, porcentaje, gradual)
                tiempos.append((perf_counter_ns() - inicio) / 1_000_000)
            sondeos_inicio = indice.sondeos
            inicio = perf_counter_ns()
            for posicion, clave in enumerate(ids):
                assert indice.obtener(clave) == posicion
                assert indice.obtener(clave + 1) is None
            consulta_ms = (perf_counter_ns() - inicio) / 1_000_000
            indices.append({'salas': cantidad, 'alternativa': nombre, 'capacidad': indice.capacidad,
                            'construccion_max_ms': max(tiempos), 'ampliaciones': ampliaciones,
                            'consultas_ms': consulta_ms, 'sondeos_consultas': indice.sondeos - sondeos_inicio,
                            'memoria_parcial_bytes': sys.getsizeof(indice.claves) + sys.getsizeof(indice.posiciones),
                            'equivalentes': True})
    assert all(r['trabajo_revelacion'] == regiones[0]['trabajo_revelacion'] for r in regiones)
    # Carga independiente y pequeña; la referencia real se mide por separado.
    k = ConocimientoMapa(_mapa(tamanos[0], semilla))
    rutas = medir_rutas_mapa(k, repeticiones, informar=informar)
    assert rutas['encontradas'] == rutas['consultas']
    resultado = {'regiones': regiones, 'indices': indices, 'rutas_sinteticas': rutas,
                 'semilla': semilla, 'repeticiones': repeticiones,
                 'referencia_oficial_verificada': False}
    if informar:
        print('NIEBLA: consultas, revelacion e inversion; sin vista ni HTTP.')
        for fila in regiones:
            print(f"  salas={fila['salas']}; trabajo={fila['trabajo_revelacion']}; "
                  f"revelacion maxima={fila['revelacion_max_ms']:.4f} ms")
        for fila in indices:
            print(f"  {fila['alternativa']}; salas={fila['salas']}; capacidad={fila['capacidad']}; "
                  f"construccion maxima={fila['construccion_max_ms']:.4f} ms; "
                  f"ampliaciones={fila['ampliaciones']}")
    return resultado
