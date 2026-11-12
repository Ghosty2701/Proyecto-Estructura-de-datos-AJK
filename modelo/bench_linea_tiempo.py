"""T029: consultas históricas deterministas, sin red ni renderizado.

Reutiliza D-LT-01 a 06 y el paquete sintético de persistencia. La alternativa
sin puntos periódicos usa K mayor que la carga y conserva solo el punto inicial.
Los diccionarios son registros de medición, no índices de las estructuras.
"""
import gc
import platform
import random
import tempfile
from dataclasses import replace
from pathlib import Path

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar, _cronometrar, _metadatos
from adaptadores.estado_binario import IdentidadGuardado, codificar_punto
from comun.ordenamiento import ordenar


def _comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def estadisticas(tiempos):
    """Mediana usual y p95 de rango más cercano; conserva máximos y excedidos."""
    if not tiempos:
        raise ValueError("la muestra no puede estar vacia")
    valores, _ = ordenar(tiempos)
    n = len(valores)
    mediana = valores[n // 2] if n % 2 else (valores[n // 2 - 1] + valores[n // 2]) / 2
    return {"cantidad": n, "minimo_ms": valores[0], "mediana_ms": mediana,
            "p95_ms": valores[(95 * n + 99) // 100 - 1], "maximo_ms": valores[-1],
            "excedidos_50ms": sum(t >= 50 for t in tiempos)}


def _resumen(partida):
    return partida.resumen_historico("")


def _preparar(cargador, acciones, k, cazadores, semilla, indices, instrumentar=None, ejecutar=None):
    """Captura resúmenes en vivo en decisiones elegidas; nunca estados completos."""
    from adaptadores.bench_persistencia import ID

    partida = cargador.crear(ID, semilla, checkpoint_cada=k)
    salas = cargador.salas_ordenadas()
    for sala in salas:
        cargador.preparar_sala(sala)
    if cazadores:
        # Preparación experimental: vida suficiente y activación anticipada.
        partida.jugador.vida = partida.jugador.vida_max = 10**9
        for enemigo in partida.enemigos:
            partida.motor.programar_accion(enemigo, 100)
            enemigo.activo = True
    cargador.iniciar_linea(partida, k)
    if instrumentar is not None:
        instrumentar(partida)
    capturas = [None] * len(indices)

    def capturar():
        numero = partida.acciones_ejecutadas + 1
        for i, indice in enumerate(indices):
            if numero == indice:
                capturas[i] = _resumen(partida)

    def aplicar(texto):
        if texto != "retroceder":
            capturar()
        (ejecutar or _ejecutar)(partida, texto)

    aplicar("recoger 1")
    aplicar("ir N")
    aplicar("retroceder")
    azar = random.Random(semilla)
    while partida.acciones_ejecutadas < acciones:
        texto = "esperar" if azar.randrange(3) == 0 else (
            "ir N" if partida.jugador.sala_actual.sala_id == 1 else "ir S")
        aplicar(texto)
    capturar()
    _comprobar(all(c is not None for c in capturas), "faltan capturas en vivo")
    return partida, capturas


def _consultas(indices, capturas, reloj):
    """Alterna #k, instante exacto e instante intermedio, incluyendo el actual."""
    consultas = []
    for i, (indice, captura) in enumerate(zip(indices, capturas)):
        if i % 3 == 0:
            argumento, esperado = ("k", indice), captura
        elif i % 3 == 1:
            argumento, esperado = ("t", captura.reloj), captura
        else:
            t = min(captura.reloj + 1, reloj)
            argumento = ("t", t)
            # Los intermedios se contrastan entre K y contra el replay desde el inicio.
            esperado = captura if t == captura.reloj else None
        consultas.append((argumento, esperado))
    return consultas


def _firma(partida, cargador):
    """Fuera del cronómetro: estado persistible, retroceso, azar, línea y contadores."""
    identidad = IdentidadGuardado(partida.id_cripta, partida.version_cripta,
                                  cargador.servicio.cache.version)
    estado = codificar_punto(partida.motor, partida.jugador, cargador.salas_ordenadas(),
                             identidad, {"partida": partida})
    cache = cargador.servicio.cache
    return (estado, _metadatos(partida.linea_tiempo),
            cache.aciertos, cache.fallos, cache.lecturas_disco,
            partida.fuente.solicitudes_realizadas)


def _trabajo(linea, argumento, reloj):
    clase, valor = argumento
    objetivo = linea.objetivo_por_k(valor) if clase == "k" else linea.objetivo_por_t(valor, reloj)
    if objetivo is None:
        return 0
    posicion, limite = objetivo
    punto = linea.punto_para(posicion if limite is None else posicion - 1)
    return linea.acciones_ejecutadas_entre(punto.posicion, posicion)


def _indices(acciones, muestras):
    return [1, 2] + [max(3, (acciones - 1) * (i + 1) // (muestras - 3))
                     for i in range(muestras - 3)] + [acciones + 1]


def _medir(partida, consultas, rondas, k, referencias):
    muestras, obtenidos = [], [None] * len(consultas)
    linea = partida.linea_tiempo
    for ronda in range(rondas):
        # Rota el orden de consulta sin cambiar los destinos; GC se mantiene habilitado.
        gc.collect()
        for paso in range(len(consultas)):
            i = (paso + ronda) % len(consultas)
            argumento, esperado = consultas[i]
            trabajo = _trabajo(linea, argumento, partida.motor.reloj)
            if k is not None:
                _comprobar(trabajo <= k, "la consulta supera K acciones")
            busquedas = linea.busquedas_puntos
            resumen, ms = _cronometrar(lambda: partida.historia(argumento))
            comparaciones = linea.busquedas_puntos - busquedas
            _comprobar(comparaciones <= len(linea.puntos).bit_length(),
                       "la busqueda del punto no es logaritmica")
            resumen = replace(resumen, titulo="")
            if esperado is not None:
                _comprobar(resumen == esperado, "la consulta difiere del estado capturado en vivo")
            if referencias is not None:
                _comprobar(resumen == referencias[i], "los resumenes difieren entre K")
            if obtenidos[i] is not None:
                _comprobar(resumen == obtenidos[i], "consultas repetidas dieron estados diferentes")
            obtenidos[i] = resumen
            muestras.append({"ronda": ronda + 1, "argumento": list(argumento), "tiempo_ms": ms,
                             "acciones_reaplicadas": trabajo, "comparaciones_puntos": comparaciones})
    return muestras, obtenidos


def medir_consultas(acciones=5000, cantidad_salas=200, valores_k=(10, 25, 50, 100),
                    cazadores=(0, 32), muestras=12, rondas=3, semilla=2026, informar=True):
    """Consulta completa (validación, copia, re-simulación y resumen), sin imprimir.

    La alternativa k=None no cambia producción: usa K > acciones ejecutadas.
    Se mide en la misma carga y se contrasta con los puntos periódicos. No mide
    memoria total, E/S, creación de puntos o ciclos de eventos; no elige K.
    """
    if (type(acciones) is not int or acciones < 3 or type(cantidad_salas) is not int
            or cantidad_salas < 3 or type(rondas) is not int or rondas < 1
            or type(muestras) is not int or muestras < 6 or not valores_k or not cazadores
            or any(type(k) is not int or k < 1 for k in valores_k)
            or any(type(c) is not int or c < 0 for c in cazadores)):
        raise ValueError("usa acciones/salas >= 3, muestras >= 6, rondas y K positivos, cazadores >= 0")
    # Destinos comunes entre K: incluye extremos y la penúltima acción, cuyo
    # intervalo suele requerir casi K acciones. No se consulta solo en puntos.
    indices = _indices(acciones, muestras)
    escenarios = []
    with tempfile.TemporaryDirectory(prefix="cripta-bench-consultas-") as temporal:
        raiz = Path(temporal)
        for cantidad in cazadores:
            paquete = raiz / f"datos-{cantidad}"
            _paquete(paquete, cantidad_salas, semilla, cazadores=cantidad)
            referencias = None
            for k in (*valores_k, None):
                if informar:
                    print(f"CONSULTAS: {acciones} acciones, {cantidad_salas} salas, "
                          f"{cantidad} cazadores, K={k if k is not None else 'solo inicial'}", flush=True)
                cargador = _cargador(paquete, raiz / f"cache-{cantidad}-{k}")
                partida, capturas = _preparar(cargador, acciones, acciones + 2 if k is None else k,
                                              cantidad, semilla, indices)
                consultas = _consultas(indices, capturas, partida.motor.reloj)
                firma = _firma(partida, cargador)
                muestras_medidas, resultados = _medir(partida, consultas, rondas, k, referencias)
                _comprobar(_firma(partida, cargador) == firma, "las consultas alteraron la partida")
                if referencias is None:
                    referencias = resultados
                linea = partida.linea_tiempo
                fila = {"k": k, "cazadores": cantidad, "salas": cantidad_salas,
                        "acciones_vigentes": partida.acciones_ejecutadas, "puntos": len(linea.puntos),
                        "cazadores_activos_final": sum(e.activo and e.vida > 0 for e in partida.enemigos),
                        "estadisticas": estadisticas([m["tiempo_ms"] for m in muestras_medidas]),
                        "maximo_acciones_reaplicadas": max(m["acciones_reaplicadas"] for m in muestras_medidas),
                        "maximo_comparaciones_puntos": max(m["comparaciones_puntos"] for m in muestras_medidas),
                        "destinos_con_captura_en_vivo": sum(e is not None for _, e in consultas),
                        "equivalente_en_vivo": True, "equivalente_entre_k": True,
                        "partida_intacta": True, "http": partida.fuente.solicitudes_realizadas,
                        "vista": False, "muestras": muestras_medidas}
                escenarios.append(fila)
                if informar:
                    e = fila["estadisticas"]
                    print(f"  mediana {e['mediana_ms']:.3f} ms; p95 {e['p95_ms']:.3f} ms; "
                          f"max {e['maximo_ms']:.3f} ms; >=50 ms: {e['excedidos_50ms']}/{e['cantidad']}; "
                          f"reaplica hasta {fila['maximo_acciones_reaplicadas']} acciones", flush=True)
                del partida, cargador, linea
                gc.collect()
    return {"semilla": semilla, "rondas": rondas, "muestras_por_ronda": muestras,
            "python": platform.python_version(), "plataforma": platform.platform(),
            "referencia_oficial_verificada": False, "escenarios": escenarios,
            "alcance": "Carga sintetica: costos variables, un pergamino, movimientos entre salas 1/2 "
                       "y esperas. Cazadores con vida 100, ataque 2, velocidad 100 y rango 2000; "
                       "activados antes del punto inicial; jugador con vida experimental 10^9. "
                       "Los cazadores convergen y siguen activos. GC habilitado. "
                       "Consultas #k/t exacto contrastadas con capturas en vivo; intermedios "
                       "contrastados entre K y con la alternativa desde el inicio. "
                       "Sin red/renderizado. No mide memoria ni certifica cualquier consulta o cripta oficial."}


def medir_cripta_consultas(cargador, partida, acciones=5000, muestras=12, rondas=3,
                          cazadores_objetivo=32, checkpoint_cada=None):
    """Tramo de T033: K provisional, datos externos precargados, sin red al consultar.

    No altera estadísticas/posiciones de los enemigos. La preparación experimental
    aumenta la vida del jugador y activa cazadores, según la tarea aprobada.
    El llamador elige la cripta publicada; aquí se conservan identidad y versión.
    """
    from modelo.linea_tiempo import K_POR_DEFECTO, validar_k

    if acciones < 3 or muestras < 6 or rondas < 1 or cazadores_objetivo < 0:
        raise ValueError("acciones >= 3, muestras >= 6, rondas >= 1 y cazadores >= 0")
    k = K_POR_DEFECTO if checkpoint_cada is None else validar_k(checkpoint_cada)
    for sala in cargador.salas_ordenadas():
        cargador.preparar_sala(sala)
    partida.jugador.vida = partida.jugador.vida_max = 10**9
    cazadores = [e for e in partida.enemigos if e.comportamiento == "cazador" and e.vida > 0]
    activos = sum(e.activo for e in cazadores)
    for enemigo in cazadores:
        if activos >= cazadores_objetivo:
            break
        if not enemigo.activo:
            partida.motor.programar_accion(enemigo, 100)
            enemigo.activo = True
            if enemigo.regeneracion_cantidad > 0:
                partida.motor.iniciar_regeneracion(enemigo)
            activos += 1
    cargador.iniciar_linea(partida, k)
    indices = _indices(acciones, muestras)
    capturas = [None] * len(indices)

    def capturar():
        for i, indice in enumerate(indices):
            if partida.acciones_ejecutadas + 1 == indice:
                capturas[i] = _resumen(partida)

    solicitudes = partida.fuente.solicitudes_realizadas
    print(f"CONSULTAS SERVICIO: {partida.id_cripta}, version {partida.version_cripta}, "
          f"K={k}, cazadores activos iniciales={activos}", flush=True)
    for paso in range(acciones):
        if partida.estado().terminada:
            break
        capturar()
        salidas = [s for s in partida.jugador.sala_actual.salidas
                   if s.abierta and s.destino.sala_id != partida.sala_salida]
        texto = "esperar" if paso % 2 or not salidas else (
            f"ir {salidas[(paso // 2) % len(salidas)].direccion}")
        _ejecutar(partida, texto)
    capturar()
    _comprobar(partida.fuente.solicitudes_realizadas == solicitudes,
               "la preparacion de 5000 acciones requirio HTTP inesperado")
    # Si terminó antes, conservar solo destinos alcanzados y declarar la cantidad.
    pares = [(i, c) for i, c in zip(indices, capturas) if c is not None]
    consultas = _consultas([i for i, _ in pares], [c for _, c in pares], partida.motor.reloj)
    firma = _firma(partida, cargador)
    mediciones, _ = _medir(partida, consultas, rondas, k, None)
    _comprobar(_firma(partida, cargador) == firma, "las consultas alteraron la partida")
    _comprobar(partida.fuente.solicitudes_realizadas == solicitudes, "una consulta realizo HTTP")
    resumen = estadisticas([m["tiempo_ms"] for m in mediciones])
    print(f"  {partida.acciones_ejecutadas} acciones; {resumen['cantidad']} consultas; "
          f"max {resumen['maximo_ms']:.3f} ms; >=50 ms: {resumen['excedidos_50ms']}", flush=True)
    return {"id_cripta": partida.id_cripta, "version_cripta": partida.version_cripta,
            "version_catalogo": cargador.servicio.cache.version, "salas": cargador.salas.cantidad,
            "k": k, "acciones_objetivo": acciones,
            "acciones_vigentes": partida.acciones_ejecutadas,
            "semilla": partida.motor.semilla, "rondas": rondas,
            "cazadores_totales": len(cazadores), "cazadores_activos_inicio": activos,
            "estadisticas": resumen, "muestras": mediciones,
            "maximo_acciones_reaplicadas": max(m["acciones_reaplicadas"] for m in mediciones),
            "partida_intacta": True, "http_consultas": 0, "vista": False,
            "solicitudes": solicitudes, "presupuesto": partida.fuente.presupuesto_solicitudes,
            "python": platform.python_version(), "plataforma": platform.platform(),
            "alcance": "K provisional; vida experimental del jugador 10^9; movimiento por salidas "
                       "abiertas evitando la salida, alternado con esperas. Enemigos originales "
                       "sin alterar estadisticas/posiciones. Solo certifica las consultas muestreadas; "
                       "no mide memoria ni ciclos. Intermedios sin oraculo independiente en este ensayo."}
