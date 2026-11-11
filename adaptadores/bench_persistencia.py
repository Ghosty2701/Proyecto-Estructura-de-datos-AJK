"""Carga local de Juan para T029/T030: persistencia y copia de puntos.

Reutiliza el formato 6, el cargador y el copiador aprobados en D-LT-04/06.
No mide consultas con cazadores ni el ciclo del motor: esas mediciones siguen
en el cierre del equipo. Los diccionarios son datos de entrada y resultados.
"""
import gc
import json
import platform
import random
import tempfile
from pathlib import Path
from time import perf_counter_ns

from adaptadores.cache_catalogo import CacheCatalogo
from adaptadores.copia_estado import copiar_estado
from adaptadores.estado_binario import (
    VERSION_MODELO, IdentidadGuardado, codificar_punto, decodificar_punto,
)
from adaptadores.modo_offline import ModoOffline
from adaptadores.servicio_cripta import ServicioCripta
from controlador.cargar_partida import CargadorPartida
from controlador.controlador import ejecutar_accion_replay


ID = "bench-persistencia"


def _comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def _paquete(carpeta, cantidad_salas, semilla, cazadores=0):
    """Escribe una cripta sintética; nunca usa datos de una cripta publicada."""
    def escribir(nombre, datos):
        ruta = carpeta / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    azar = random.Random(semilla)
    costos = [azar.choice((100, 150, 250)) for _ in range(cantidad_salas - 1)]
    salas = []
    for numero in range(1, cantidad_salas + 1):
        salidas = {}
        if numero > 1:
            salidas["S"] = {"sala": numero - 1, "costo": costos[numero - 2]}
        if numero < cantidad_salas:
            salidas["N"] = {"sala": numero + 1, "costo": costos[numero - 1]}
        salas.append({"id": numero, "nombre": f"Sala sintetica {numero}", "salidas": salidas})
        escribir(f"criptas/{ID}/contenido/{numero}.json", {
            "sala": numero, "enemigos": [
                {"instancia": f"c-bench-{i:03d}", "tipo": "cazador", "vida": None}
                for i in range(cazadores) if numero == 2 + i % min(8, cantidad_salas - 2)
            ], "trampas": [],
            "objetos": ["pergamino"] if numero == 1 else [],
        })
    escribir("catalogo_version.json", {"version": "cat-bench-persistencia"})
    escribir("catalogo/pergamino.json", {
        "id": "pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino",
    })
    if cazadores:
        escribir("catalogo/cazador.json", {
            "id": "cazador", "clase": "enemigo", "nombre": "Cazador sintetico",
            "vida_max": 100, "ataque": 2, "defensa": 0, "velocidad": 100,
            "comportamiento": "cazador", "rango": 2000, "suelta": [],
        })
    escribir(f"criptas/{ID}/general.json", {
        "id": ID, "version": "v1", "paginas": 1, "salas_total": cantidad_salas,
        "sala_inicial": 1, "sala_salida": cantidad_salas, "llave_salida": "llave_salida",
        "presupuesto_solicitudes": 10000, "inventario_max": 5,
        "jugador": {"vida_max": 100, "ataque": 6, "defensa": 1, "velocidad": 100},
    })
    escribir(f"criptas/{ID}/salas_1.json", {"pagina": 1, "salas": salas})


def _cargador(carpeta, cache_dir):
    fuente = ModoOffline(str(carpeta))
    cache = CacheCatalogo(fuente, carpeta=str(cache_dir), tope=25)
    return CargadorPartida(ServicioCripta(fuente, cache))


def _ejecutar(partida, texto):
    ejecutar_accion_replay(partida, texto)
    partida.registrar_orden(texto)


def _jugar(cargador, acciones, k, semilla):
    partida = cargador.crear(ID, semilla, checkpoint_cada=k)
    # Preparación local fuera de todos los cronómetros.
    for sala in cargador.salas_ordenadas():
        cargador.preparar_sala(sala)
    cargador.iniciar_linea(partida, k)
    _ejecutar(partida, "recoger 1")
    _ejecutar(partida, "ir N")
    _ejecutar(partida, "retroceder")
    azar = random.Random(semilla)
    while partida.acciones_ejecutadas < acciones:
        if azar.randrange(3) == 0:
            texto = "esperar"
        else:
            texto = "ir N" if partida.jugador.sala_actual.sala_id == 1 else "ir S"
        _ejecutar(partida, texto)
    return partida


def _metadatos(linea):
    """Compara todo el registro, no solo el estado actual del jugador."""
    return (
        [(o.texto, o.tipo, o.reloj) for o in linea.ordenes],
        [(a.reloj, a.posicion) for a in linea.acciones],
        [(p.posicion, p.acciones, p.reloj, p.k) for p in linea.puntos],
        [(t.k, t.posicion) for t in linea.tramos], linea.acciones_en_tramo,
    )


def _cronometrar(funcion):
    inicio = perf_counter_ns()
    resultado = funcion()
    return resultado, (perf_counter_ns() - inicio) / 1e6


def _comparar_copias(raiz, identidad, rondas):
    """Copia del estado base, sin copiar recursivamente la línea ni hacer E/S."""
    partida, salas = raiz

    def codec():
        bloque = codificar_punto(partida.motor, partida.jugador, salas, identidad,
                                 {"partida": partida})
        cargada = decodificar_punto(bloque, identidad)
        return cargada.datos_extra["partida"], cargada.salas

    tiempos_copia, tiempos_codec = [], []
    esperado = partida.resumen_historico("comparacion")
    for _ in range(rondas):
        gc.collect()  # Limpieza previa fuera del cronómetro; GC permanece habilitado.
        copia, tiempo = _cronometrar(lambda: copiar_estado(raiz))
        tiempos_copia.append(tiempo)
        reconstruida, tiempo = _cronometrar(codec)
        tiempos_codec.append(tiempo)
        for nueva, nuevas_salas in (copia, reconstruida):
            # La infraestructura es transitoria: el codec no la restaura.
            nueva.fuente = None
            _comprobar(nueva.resumen_historico("comparacion") == esperado,
                       "las alternativas de copia cambiaron el estado observable")
            _comprobar(nueva.motor.azar.getstate() == partida.motor.azar.getstate(),
                       "la copia no conserva el generador aleatorio")
            _comprobar(len(nuevas_salas) == len(salas), "faltan salas en la copia")
        del copia, reconstruida, nueva, nuevas_salas
    return tiempos_copia, tiempos_codec


def medir_persistencia(acciones=5000, cantidad_salas=200, valores_k=(10, 25, 50, 100),
                       rondas=3, semilla=2026, informar=True):
    """Mide la sesión completa y verifica historia/continuación fuera del cronómetro.

    Cargar incluye decodificar todos los puntos, validar y reenlazar la sesión.
    El servicio offline y su esqueleto se preparan antes de medir cada carga.
    Se conservan todas las muestras, sin seleccionar únicamente el mejor tiempo.
    """
    if (type(acciones) is not int or acciones < 3 or type(cantidad_salas) is not int
            or cantidad_salas < 3 or type(rondas) is not int or rondas < 1
            or not valores_k or any(type(k) is not int or k < 1 for k in valores_k)):
        raise ValueError("usa acciones >= 3, salas >= 3, rondas >= 1 y valores K positivos")
    filas = []
    esperado_entre_k = None
    with tempfile.TemporaryDirectory(prefix="cripta-bench-persistencia-") as temporal:
        raiz = Path(temporal)
        paquete = raiz / "datos"
        _paquete(paquete, cantidad_salas, semilla)
        for k in valores_k:
            if informar:
                print(f"PERSISTENCIA: preparando {acciones} acciones, {cantidad_salas} salas, K={k}",
                      flush=True)
            cargador = _cargador(paquete, raiz / f"cache-{k}")
            partida = _jugar(cargador, acciones, k, semilla)
            estado_final = partida.resumen_historico("final")
            if esperado_entre_k is None:
                esperado_entre_k = estado_final
            _comprobar(estado_final == esperado_entre_k, "K cambio la partida sintetica")
            linea = partida.linea_tiempo
            metadata = _metadatos(linea)
            consultas = (("t", 0), ("k", 2), ("k", acciones // 2),
                         ("t", max(0, partida.motor.reloj - 1)), ("k", acciones + 1))
            historias = [partida.historia(q) for q in consultas]
            ruta = raiz / f"sesion-{k}.bin"
            guardar_ms, cargar_ms = [], []
            for ronda in range(rondas):
                gc.collect()
                _, tiempo = _cronometrar(lambda: cargador.guardar_sesion(partida, ruta))
                guardar_ms.append(tiempo)
                destino = _cargador(paquete, raiz / f"carga-{k}-{ronda}")
                destino.servicio.cargar(ID)
                destino.servicio.cache.obtener_varias(())

                def cargar():
                    datos = destino.leer_sesion(ruta, ID, "v1")
                    nueva = datos.datos_extra["partida"]
                    destino.aplicar_sesion(nueva, datos)
                    return nueva

                restaurada, tiempo = _cronometrar(cargar)
                cargar_ms.append(tiempo)
                _comprobar(_metadatos(restaurada.linea_tiempo) == metadata,
                           "el guardado cambio ordenes, acciones, puntos o tramos")
                _comprobar([restaurada.historia(q) for q in consultas] == historias,
                           "la historia cambio despues de cargar")
                # Continuación de una copia para no alterar la carga de las siguientes rondas.
                copia = cargador.copia_de_trabajo(linea.puntos[-1])
                for orden in linea.ordenes[linea.puntos[-1].posicion:]:
                    ejecutar_accion_replay(copia, orden.texto)
                ejecutar_accion_replay(copia, "esperar")
                _ejecutar(restaurada, "esperar")
                _comprobar(copia.resumen_historico("continuacion") ==
                           restaurada.resumen_historico("continuacion"), "continuacion diferente")
                _comprobar(copia.motor.azar.getstate() == restaurada.motor.azar.getstate(),
                           "el azar cambio al continuar")
                _comprobar(destino.servicio.fuente.solicitudes_realizadas == 0, "hubo HTTP")
                del restaurada, destino, copia
            identidad = IdentidadGuardado(ID, "v1", cargador.servicio.cache.version)
            copia_ms, codec_ms = _comparar_copias(
                (partida, cargador.salas_ordenadas()), identidad, rondas)
            fila = {"k": k, "puntos": len(linea.puntos), "ordenes": len(linea.ordenes),
                    "acciones_ejecutadas": sum(o.tipo == "accion" for o in linea.ordenes),
                    "archivo_bytes": ruta.stat().st_size, "guardar_ms": guardar_ms,
                    "cargar_ms": cargar_ms, "copiador_ms": copia_ms,
                    "codec_ida_vuelta_ms": codec_ms, "historia_equivalente": True,
                    "continuacion_equivalente": True, "copias_equivalentes": True}
            filas.append(fila)
            _comprobar(cargador.servicio.fuente.solicitudes_realizadas == 0, "hubo HTTP")
            if informar:
                print(f"  {fila['puntos']} puntos; {fila['archivo_bytes']} bytes; "
                      f"guardar max {max(guardar_ms):.3f} ms; cargar max {max(cargar_ms):.3f} ms; "
                      f"copia max {max(copia_ms):.3f} ms; codec max {max(codec_ms):.3f} ms", flush=True)
            del partida, cargador, linea
            gc.collect()
    return {"semilla": semilla, "rondas": rondas, "python": platform.python_version(),
            "plataforma": platform.platform(), "version_modelo": VERSION_MODELO,
            "acciones_vigentes": acciones, "salas": cantidad_salas, "cazadores": 0,
            "http": 0, "vista": False, "carga_equivalente_entre_k": True, "filas": filas,
            "alcance": "Persistencia y copia con movimiento ponderado y un pergamino; "
                       "sin cazadores. No certifica 20 ms de ciclo ni 50 ms de historia. "
                       "Disco con cache del sistema, sin fsync; sin medir memoria residente."}
