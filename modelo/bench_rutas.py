"""Mediciones sinteticas de P2; usa hash y heap propios, sin red ni vista."""
import platform
import random
import sys
from time import perf_counter_ns
from modelo.rastro import SalaRastro, SalidaRastro, Puerta
from modelo.motor_eventos import MotorEventos, ActorTurnos
from modelo.rutas import buscar_ruta
from modelo.tabla_hash import TablaDistancias, RegistroBusqueda
from modelo.heap_rutas import HeapRutas


def _mapa(cantidad, semilla):
    azar = random.Random(semilla)
    salas = [SalaRastro(i) for i in range(cantidad)]
    for sala in salas:
        sala.nombre = f'Sintetica {sala.sala_id}'
        sala.objetos_suelo = []
        sala.contenido_cargado = True
    for a, b in zip(salas, salas[1:]):
        costo, puerta = azar.randrange(20, 51), Puerta()
        ida = SalidaRastro(b, puerta=puerta, costo=costo)
        vuelta = SalidaRastro(a, puerta=puerta, costo=costo)
        ida.direccion, vuelta.direccion = 'E', 'O'
        a.salidas.append(ida)
        b.salidas.append(vuelta)
    return salas


def _distancias_compartidas(objetivo, rango):
    # Alternativa de medicion, no estrategia del juego. Mismas estructuras aprobadas.
    tabla, heap = TablaDistancias(), HeapRutas()
    registro = RegistroBusqueda(objetivo, 0, objetivo)
    tabla.insertar(registro)
    heap.insertar(registro)
    while heap.datos:
        actual = heap.extraer_minimo()
        for salida in actual.sala.salidas:
            distancia = actual.distancia + salida.costo
            if not salida.abierta or distancia > rango:
                continue
            previa = tabla.obtener(salida.destino.sala_id)
            if previa is None:
                nueva = RegistroBusqueda(salida.destino, distancia, objetivo)
                tabla.insertar(nueva)
                heap.insertar(nueva)
            elif not previa.definitivo and distancia < previa.distancia:
                heap.mejorar(previa, distancia, objetivo)
    return tabla


def _decision_compartida(origen, objetivo, rango, tabla):
    if origen is objetivo:
        return None, 0
    registro = tabla.obtener(origen.sala_id)
    if registro is None or registro.distancia > rango:
        return None, None
    primero = None
    for salida in origen.salidas:
        restante = tabla.obtener(salida.destino.sala_id)
        if (salida.abierta and restante is not None
                and salida.costo + restante.distancia == registro.distancia):
            if primero is None or salida.destino.sala_id < primero:
                primero = salida.destino.sala_id
    return primero, registro.distancia


def _firma(resultado):
    paso = resultado.primer_paso
    return None if paso is None else paso.destino.sala_id, resultado.costo_total


def _consultas(cantidad, cazadores, rango, inestables, repeticiones, semilla):
    salas = _mapa(cantidad, semilla)
    motor, jugador = MotorEventos(semilla), ActorTurnos('j', 1000000, 100)
    jugador.sala_actual = salas[40]
    actores = [ActorTurnos(f'c-{i}', 100, 100, comportamiento='cazador', rango=rango)
               for i in range(cazadores)]
    for i, actor in enumerate(actores):
        actor.sala_actual = salas[i]
        motor.ruta_cazador(actor, jugador)
    individuales_ms, compartidas_ms, reuso_ms = [], [], []
    for _ in range(repeticiones):
        if inestables:
            puerta = salas[25].salidas[-1].puerta
            motor._cambiar(puerta, 'abierta', not puerta.abierta)
        inicio = perf_counter_ns()
        individuales = [buscar_ruta(a.sala_actual, jugador.sala_actual, a.rango) for a in actores]
        individuales_ms.append((perf_counter_ns() - inicio) / 1e6)
        inicio = perf_counter_ns()
        tabla = _distancias_compartidas(jugador.sala_actual, rango)
        compartidas = [_decision_compartida(a.sala_actual, jugador.sala_actual, a.rango, tabla)
                       for a in actores]
        compartidas_ms.append((perf_counter_ns() - inicio) / 1e6)
        inicio = perf_counter_ns()
        reutilizadas = [motor.ruta_cazador(a, jugador) for a in actores]
        reuso_ms.append((perf_counter_ns() - inicio) / 1e6)
        esperadas = [_firma(r) for r in individuales]
        if esperadas != compartidas or esperadas != [_firma(r) for r in reutilizadas]:
            raise RuntimeError('Las alternativas producen decisiones distintas')
    # Diccionarios de salida: registros de medicion, no indices/caches del algoritmo.
    return {'salas_mapa': cantidad, 'cazadores': cazadores, 'rango': rango,
            'puertas_inestables': inestables, 'equivalentes': True,
            'individual_ms': min(individuales_ms), 'compartida_ms': min(compartidas_ms),
            'reutilizacion_ms': min(reuso_ms), 'maximo_individual_ms': max(individuales_ms),
            'salas_examinadas': sum(r.salas_examinadas for r in individuales),
            'salidas_examinadas': sum(r.salidas_examinadas for r in individuales),
            'sondeos': sum(r.sondeos for r in individuales),
            'ampliaciones': sum(r.ampliaciones for r in individuales)}


def _ciclos(semilla, repeticiones, ciclos):
    from controlador.partida import Partida
    tiempos, retrocesos = [], []
    for _ in range(repeticiones):
        salas = _mapa(80, semilla)
        motor, jugador = MotorEventos(semilla), ActorTurnos('j', 1000000, 100)
        enemigos = []
        for i in range(32):
            actor = ActorTurnos(f'c-{i}', 100, 100, comportamiento='cazador', rango=2000)
            actor.nombre = 'Cazador sintetico'
            actor.sala_actual = salas[i]
            salas[i].enemigos.append(actor)
            enemigos.append(actor)
        motor.iniciar_partida(jugador, salas[40])
        for enemigo in enemigos:
            motor.programar_accion(enemigo, 100)
            enemigo.activo = True
        partida = Partida(motor, jugador, enemigos, lambda sala: None)
        for _ in range(ciclos):
            inicio = perf_counter_ns()
            partida.esperar()
            tiempos.append((perf_counter_ns() - inicio) / 1e6)
        inicio = perf_counter_ns()
        motor.deshacer_ultima_accion()
        retrocesos.append((perf_counter_ns() - inicio) / 1e6)
    return {'cantidad': len(tiempos), 'cazadores': 32, 'salas': 80,
            'maximo_ms': max(tiempos), 'minimo_ms': min(tiempos),
            'excedidos': sum(t >= 20 for t in tiempos),
            'retroceso_maximo_ms': max(retrocesos),
            'incluye_agenda_y_preparacion': True, 'http': 0, 'vista': False}


def medir_terreno_cazadores(repeticiones=5, ciclos=100, semilla=2026, informar=True):
    if repeticiones < 1 or ciclos < 1:
        raise ValueError('Repeticiones y ciclos deben ser positivos')
    filas = [_consultas(n, c, r, puertas, repeticiones, semilla)
             for n in (80, 800) for c in (1, 32) for r in (100, 2000)
             for puertas in (False, True)]
    resultado = {'semilla': semilla, 'repeticiones': repeticiones,
                 'python': sys.version.split()[0], 'plataforma': platform.platform(),
                 'rutas': filas, 'ciclos': _ciclos(semilla, repeticiones, ciclos),
                 'referencia_oficial_verificada': False,
                 'alcance': 'Sintetico: no certifica la cripta de referencia oficial.'}
    if informar:
        print('\nTERRENO Y CAZADORES: 16 cargas sinteticas, alternativas verificadas')
        print('Individual / compartida / reutilizacion, ms por lote (minimos):')
        for f in filas:
            print(f"  salas={f['salas_mapa']}, cazadores={f['cazadores']}, rango={f['rango']}, "
                  f"inestables={f['puertas_inestables']}: {f['individual_ms']:.4f} / "
                  f"{f['compartida_ms']:.4f} / {f['reutilizacion_ms']:.4f}")
        c = resultado['ciclos']
        print(f"Ciclo completo sintetico, 32 cazadores: {c['cantidad']} ciclos; "
              f"maximo {c['maximo_ms']:.4f} ms; >=20 ms: {c['excedidos']}")
        print('Sin HTTP ni vista. Referencia oficial pendiente; no certifica su limite.')
    return resultado
