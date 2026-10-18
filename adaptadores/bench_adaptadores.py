"""Mediciones sinteticas: python -m adaptadores.bench_adaptadores."""

import argparse
import json
import platform
import random
import tempfile
import time
from pathlib import Path

from adaptadores.cache_catalogo import ArbolAVL, CacheCatalogo
from adaptadores.guardado_binario import escribir_guardado, leer_globales, leer_sala
from adaptadores.modo_offline import ModoOffline
import adaptadores.estado_binario as estado_binario
from adaptadores.guardado_binario import leer_guardado

SEMILLA_BENCH = 2042

class NodoSimple:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None


class ArbolSimple:
    def __init__(self):
        self.raiz = None
        self.altura = 0

    def insertar(self, clave, valor):
        nuevo = NodoSimple(clave, valor)
        if self.raiz is None:
            self.raiz = nuevo
            self.altura = 1
            return

        actual = self.raiz
        nivel = 1
        while True:
            if clave == actual.clave:
                actual.valor = valor
                return
            nivel += 1
            if clave < actual.clave:
                if actual.izquierdo is None:
                    actual.izquierdo = nuevo
                    break
                actual = actual.izquierdo
            else:
                if actual.derecho is None:
                    actual.derecho = nuevo
                    break
                actual = actual.derecho

        if nivel > self.altura:
            self.altura = nivel

    def buscar(self, clave):
        nodo = self.raiz
        while nodo is not None:
            if clave == nodo.clave:
                return nodo.valor
            if clave < nodo.clave:
                nodo = nodo.izquierdo
            else:
                nodo = nodo.derecho
        return None

def comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def positivo(valor):
    numero = int(valor)
    if numero <= 0:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return numero


def medir(funcion, repeticiones, rondas=5):
    if type(repeticiones) is not int or repeticiones <= 0:
        raise ValueError("repeticiones debe ser un entero positivo")
    if type(rondas) is not int or rondas <= 0:
        raise ValueError("rondas debe ser un entero positivo")
    mejor = None
    for _ in range(rondas):
        inicio = time.perf_counter_ns()
        for _ in range(repeticiones):
            funcion()
        promedio = (time.perf_counter_ns() - inicio) / repeticiones / 1000
        if mejor is None or promedio < mejor:
            mejor = promedio
    return mejor


def mostrar(nombre, microsegundos):
    print(f"  {nombre:<48} {microsegundos:12.3f} us/operacion")


def generar_ids(cantidad, mezclados, semilla=SEMILLA_BENCH):
    ids = [f"ficha_{numero:06d}" for numero in range(cantidad)]
    if mezclados:
        random.Random(semilla).shuffle(ids)
    return ids


def construir(clase_arbol, ids):
    arbol = clase_arbol()
    for posicion, clave in enumerate(ids):
        arbol.insertar(clave, posicion)
    return arbol


def verificar_busquedas(arbol, ids):
    comprobar(bool(ids), "la carga de busqueda no puede estar vacia")
    for posicion, clave in enumerate(ids):
        comprobar(arbol.buscar(clave) == posicion, f"busqueda incorrecta: {clave}")
    comprobar(arbol.buscar("ficha_ausente") is None, "una clave ausente debe devolver None")


def microsegundos_por_busqueda(arbol, ids, repeticiones, rondas=5):
    verificar_busquedas(arbol, ids)

    def buscar_todos():
        for clave in ids:
            arbol.buscar(clave)

    tiempo = medir(buscar_todos, repeticiones, rondas) / len(ids)
    verificar_busquedas(arbol, ids)
    return tiempo


def microsegundos_por_insercion(clase_arbol, ids, repeticiones, rondas=5):
    verificar_busquedas(construir(clase_arbol, ids), ids)
    # Incluye construir y liberar el arbol; se divide por las fichas insertadas.
    return medir(lambda: construir(clase_arbol, ids), repeticiones, rondas) / len(ids)


def bench_busqueda_cache(rondas=5, semilla=SEMILLA_BENCH, tamanos=(25, 100, 1000)):
    print("\nIndice: AVL vs arbol simple (tiempos en us/ficha)")
    print(f"  {'n':<7}{'orden':<12}{'altura AVL/simple':<20}{'buscar AVL/simple':<23}construir AVL/simple")
    for cantidad in tamanos:
        for mezclados in (False, True):
            ids = generar_ids(cantidad, mezclados, semilla)
            repeticiones = max(2, 5000 // cantidad)
            avl = construir(ArbolAVL, ids)
            simple = construir(ArbolSimple, ids)
            buscar_avl = microsegundos_por_busqueda(avl, ids, repeticiones, rondas)
            buscar_simple = microsegundos_por_busqueda(simple, ids, repeticiones, rondas)
            insertar_avl = microsegundos_por_insercion(ArbolAVL, ids, repeticiones, rondas)
            insertar_simple = microsegundos_por_insercion(ArbolSimple, ids, repeticiones, rondas)
            orden = "mezclados" if mezclados else "ordenados"
            alturas = f"{avl.raiz.altura} / {simple.altura}"
            buscar = f"{buscar_avl:.3f} / {buscar_simple:.3f}"
            insertar = f"{insertar_avl:.3f} / {insertar_simple:.3f}"
            print(f"  {cantidad:<7}{orden:<12}{alturas:<20}{buscar:<23}{insertar}")


def escribir_json(ruta, datos):
    # Ambos formatos codifican en memoria antes de escribir: no comparar un
    # json.dump de muchas escrituras pequenas con un unico bloque binario.
    texto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(texto)


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


class FuenteBench(ModoOffline):
    """Paquete sintetico local: cuenta accesos al catalogo, sin HTTP."""
    def __init__(self, carpeta):
        super().__init__(carpeta)
        self.consultas_catalogo = 0
        self.solo_cache = False

    def catalogo(self, ids):
        comprobar(not self.solo_cache, "una ficha persistida se volvio a pedir a la fuente")
        self.consultas_catalogo += 1
        return super().catalogo(ids)


def verificar_cache(cache, ids):
    fichas = cache.obtener_varias(ids)
    comprobar([ficha["id"] for ficha in fichas] == ids, "cache: resultado fuera de orden")
    comprobar(cache.lista.cantidad == cache.arbol.cantidad, "cache: indices inconsistentes")
    comprobar(cache.lista.cantidad <= cache.tope, "cache: se excedio el tope sin fichas en uso")


def bench_cache(rondas=5, tope=25):
    print(f"\nCacheCatalogo real: capacidad {tope}, fuente local sin HTTP")
    with tempfile.TemporaryDirectory(prefix="cripta-bench-cache-") as carpeta:
        raiz = Path(carpeta)
        catalogo = raiz / "catalogo"
        catalogo.mkdir()
        escribir_json(raiz / "catalogo_version.json", {"version": "bench-v1"})
        ids = generar_ids(2 * tope, False)
        for clave in ids:
            escribir_json(catalogo / (clave + ".json"), {
                "id": clave, "clase": "arma", "nombre": "Ficha " + clave,
                "peso": 2, "valor": 15, "ataque_bonus": 3,
            })

        fuente = FuenteBench(carpeta)
        cache = CacheCatalogo(fuente, carpeta=str(raiz / "caliente"), tope=tope)
        residentes = ids[:tope]
        verificar_cache(cache, residentes)
        fuente.solo_cache = True
        repeticiones = max(2, 5000 // tope)
        aciertos = cache.aciertos
        lecturas = cache.lecturas_disco
        tiempo = medir(lambda: cache.obtener_varias(residentes), repeticiones, rondas) / tope
        comprobar(cache.aciertos - aciertos == tope * repeticiones * rondas,
                  "la carga caliente no fueron exclusivamente aciertos")
        comprobar(cache.lecturas_disco == lecturas, "la carga caliente leyo del disco")
        verificar_cache(cache, residentes)
        mostrar("Acierto en memoria, incluye AVL y LRU", tiempo)

        fuente = FuenteBench(carpeta)
        cache = CacheCatalogo(fuente, carpeta=str(raiz / "liberadas"), tope=tope)
        verificar_cache(cache, ids)
        comprobar(cache.arbol.buscar(ids[0]) is None, "la ficha inicial no fue liberada")
        fuente.solo_cache = True
        repeticiones = max(1, 100 // len(ids))
        lecturas = cache.lecturas_disco
        aciertos = cache.aciertos
        tiempo = medir(lambda: cache.obtener_varias(ids), repeticiones, rondas) / len(ids)
        recuperaciones = cache.lecturas_disco - lecturas
        comprobar(recuperaciones == len(ids) * repeticiones * rondas,
                  "la carga de recuperacion incluyo fichas residentes")
        comprobar(cache.aciertos == aciertos, "la carga de disco tuvo aciertos en memoria")
        verificar_cache(cache, ids)
        comprobar(fuente.solicitudes_realizadas == 0, "el benchmark realizo HTTP")
        mostrar("Ficha liberada: leer JSON, reinsertar y desalojar", tiempo)
        print(f"  Recuperaciones cronometradas: {recuperaciones}; solicitudes HTTP: 0")
        print("  Disco con cache del sistema operativo; no se fuerza una lectura fisica fria.")


def codificar(datos):
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def bench_guardado(rondas=5, cantidad_salas=200, semilla=SEMILLA_BENCH):
    print(f"\nGuardado/carga: {cantidad_salas} salas sinteticas")
    print("  Mismos datos: contenedor binario existente con bloques JSON UTF-8 vs JSON compacto.")
    print("  Comparacion del contenedor original; el codec por campos se mide despues.")
    globales = {"semilla": semilla, "reloj": 1200, "version_cripta": "bench-v1"}
    salas = [
        {"id": numero, "nombre": f"Sala {numero}", "ultimo_rastro": numero * 10,
         "enemigos": [{"instancia": f"e-{numero}", "vida": 12, "tipo": "ent_rata"}],
         "objetos": ["itm_antorcha", "itm_daga"], "trampas": []}
        for numero in range(1, cantidad_salas + 1)
    ]
    documento = {"globales": globales, "salas": salas}
    id_objetivo = (cantidad_salas + 1) // 2

    with tempfile.TemporaryDirectory(prefix="cripta-bench-guardado-") as carpeta:
        ruta_bin = Path(carpeta) / "partida.bin"
        ruta_json = Path(carpeta) / "partida.json"

        def guardar_binario():
            escribir_guardado(ruta_bin, codificar(globales),
                              [(sala["id"], codificar(sala)) for sala in salas])

        def cargar_binario():
            datos_globales, bloques = leer_guardado(ruta_bin)
            return {"globales": json.loads(datos_globales),
                    "salas": [json.loads(datos) for _, datos in bloques]}

        def sala_binaria():
            return json.loads(leer_sala(ruta_bin, id_objetivo))

        def sala_json():
            datos = leer_json(ruta_json)
            for sala in datos["salas"]:
                if sala["id"] == id_objetivo:
                    return sala
            return None

        guardar_binario()
        escribir_json(ruta_json, documento)
        comprobar(cargar_binario() == documento, "binario: ida y vuelta incorrecta")
        comprobar(leer_json(ruta_json) == documento, "JSON: ida y vuelta incorrecta")
        comprobar(sala_binaria() == sala_json() == salas[id_objetivo - 1],
                  "lectura selectiva: sala incorrecta")

        mostrar("Guardar completo, binario", medir(guardar_binario, 2, rondas))
        mostrar("Guardar completo, JSON", medir(lambda: escribir_json(ruta_json, documento), 2, rondas))
        mostrar("Cargar completo, binario (una apertura)", medir(cargar_binario, 2, rondas))
        mostrar("Cargar completo, JSON", medir(lambda: leer_json(ruta_json), 2, rondas))
        mostrar("Recuperar una sala, binario con indice", medir(sala_binaria, 10, rondas))
        mostrar("Recuperar una sala, JSON completo y recorrido", medir(sala_json, 10, rondas))
        comprobar(cargar_binario() == leer_json(ruta_json) == documento,
                  "los archivos cambiaron durante la medicion")
        print(f"  Tamano binario: {ruta_bin.stat().st_size} bytes; JSON: {ruta_json.stat().st_size} bytes")
        print("  Incluye codificacion/decodificacion. Carga completa con una apertura del archivo.")
        print("  Escrituras con cierre de archivo, sin fsync; lecturas con cache del sistema operativo.")


def _valor_json_comparable(valor):
    # Registros de datos para la alternativa JSON del benchmark, no indices.
    if type(valor) is estado_binario._Referencia:
        return {"ref": valor.numero}
    if type(valor) is tuple:
        return {"tupla": [_valor_json_comparable(elemento) for elemento in valor]}
    if type(valor) is bytes:
        return {"bytes_hex": valor.hex()}
    if type(valor) is list:
        return [_valor_json_comparable(elemento) for elemento in valor]
    return valor


def _registros_comparables(registros):
    resultado = []
    for datos in registros:
        numero, esquema, valores = estado_binario._leer_registro(datos)
        resultado.append({"id": numero, "tipo": esquema[0], "campos": _valor_json_comparable(valores)})
    return resultado


def _estado_comparable(ruta):
    globales, bloques = leer_guardado(ruta)
    identidad, raices, salas, registros = estado_binario._leer_globales_modelo(globales)
    documentos_salas = []
    for numero, bloque in bloques:
        raiz, vista, datos = estado_binario._leer_bloque_sala(bloque)
        resumen = (vista.sala_id, vista.nombre, vista.ultimo_rastro, vista.contenido_cargado,
                   vista.salidas, vista.actores, vista.objetos, vista.trampas)
        documentos_salas.append({"sala": numero, "raiz": raiz,
                                "vista": _valor_json_comparable(resumen),
                                "entidades": _registros_comparables(datos)})
    return {"version_modelo": estado_binario.VERSION_MODELO,
            "identidad": [identidad.id_cripta, identidad.version_cripta, identidad.version_catalogo],
            "raices": list(raices), "salas": [list(par) for par in salas],
            "entidades_globales": _registros_comparables(registros), "bloques": documentos_salas}


def bench_estado_real(rondas=5, cantidad_salas=200, semilla=SEMILLA_BENCH):
    from modelo.inventario import Inventario
    from modelo.motor_eventos import ActorTurnos, MotorEventos
    from modelo.rastro import SalaRastro

    print(f"\nModelo real: esquema explicito binario, {cantidad_salas} salas e historial de dos acciones")
    motor = MotorEventos(semilla)
    jugador = ActorTurnos("jugador", 10000, 100, ataque=6, defensa=1)
    jugador.inventario = Inventario(5)
    jugador.inventario.recoger(estado_binario.ObjetoPartida("itm_daga", "arma", "Daga", ataque_bonus=3))
    salas = [SalaRastro(numero) for numero in range(1, cantidad_salas + 1)]
    for sala in salas:
        sala.nombre = f"Sala {sala.sala_id}"
        sala.contenido_cargado = True
    enemigo = ActorTurnos("e-1", 100, 150, ataque=3, comportamiento="guardian")
    enemigo.sala_actual = salas[0]
    salas[0].enemigos.append(enemigo)
    motor.iniciar_partida(jugador, salas[0])
    motor.aplicar_veneno(jugador, 1)
    for _ in range(2):
        motor.esperar_jugador(jugador, lambda evento: motor.ejecutar_evento(evento, jugador))

    with tempfile.TemporaryDirectory(prefix="cripta-bench-modelo-") as carpeta:
        ruta_bin = Path(carpeta) / "estado.bin"
        ruta_json = Path(carpeta) / "estado.json"

        def guardar_modelo():
            estado_binario.guardar_partida(ruta_bin, motor, jugador, salas, id_cripta="bench",
                                           version_cripta="v1", version_catalogo="cat-bench")

        guardar_modelo()
        globales, bloques = leer_guardado(ruta_bin)
        documento = _estado_comparable(ruta_bin)
        json_preparado = codificar(documento)
        ruta_json.write_bytes(json_preparado)
        comprobar(leer_json(ruta_json) == documento, "el JSON no conserva todos los campos del modelo")
        cargada = estado_binario.cargar_partida(ruta_bin)
        comprobar(cargada.motor.azar.getstate() == motor.azar.getstate() and
                  cargada.jugador.vida == jugador.vida and cargada.motor.reloj == motor.reloj,
                  "carga del modelo real incorrecta")

        mostrar("Guardar modelo completo (captura, valida y publica)", medir(guardar_modelo, 1, rondas))
        mostrar("Restaurar modelo completo y sus referencias",
                medir(lambda: estado_binario.cargar_partida(ruta_bin), 1, rondas))
        print("  Comparacion de escritura con ambas representaciones ya preparadas:")
        mostrar("Escribir bloques binarios preparados",
                medir(lambda: escribir_guardado(ruta_bin, globales, bloques), 2, rondas))
        mostrar("Escribir JSON completo preparado",
                medir(lambda: ruta_json.write_bytes(json_preparado), 2, rondas))
        print("  Lectura/decodificacion al mismo esquema de datos; sin reconstruir entidades:")
        mostrar("Binario por campos -> registros comparables", medir(lambda: _estado_comparable(ruta_bin), 2, rondas))
        mostrar("JSON equivalente -> registros comparables", medir(lambda: leer_json(ruta_json), 2, rondas))
        comprobar(_estado_comparable(ruta_bin) == leer_json(ruta_json),
                  "los formatos no contienen el mismo estado explicito")
        vista = estado_binario.leer_sala_guardada(ruta_bin, cantidad_salas)
        comprobar(vista.sala_id == cantidad_salas, "lectura selectiva del modelo incorrecta")
        mostrar("Vista de una sala sin cargar el modelo",
                medir(lambda: estado_binario.leer_sala_guardada(ruta_bin, cantidad_salas), 10, rondas))
        print(f"  Tamano modelo binario: {ruta_bin.stat().st_size} bytes; JSON equivalente: {ruta_json.stat().st_size} bytes")
        print("  JSON es la alternativa de medicion: incluye entidades, IDs, eventos, azar e historial.")
        print("  Restaurar entidades es una medicion adicional, distinta de leer/decodificar registros.")


def ejecutar_bench(rondas=5, semilla=SEMILLA_BENCH, tope=25, cantidad_salas=200,
                   solo="todos", tamanos=(25, 100, 1000)):
    if rondas <= 0 or tope <= 0 or cantidad_salas <= 0 or any(n <= 0 for n in tamanos):
        raise ValueError("las cantidades del benchmark deben ser positivas")
    if solo not in ("todos", "indice", "cache", "guardado"):
        raise ValueError("subsistema desconocido")
    print(f"Python {platform.python_version()} | {platform.system()} | semilla {semilla}")
    print(f"Tiempo reportado: menor promedio de {rondas} rondas; validaciones fuera del cronometro.")
    print("Cargas sinteticas locales; no validan una partida completa ni el limite de 20 ms.")
    if solo in ("todos", "indice"):
        bench_busqueda_cache(rondas, semilla, tamanos)
    if solo in ("todos", "cache"):
        bench_cache(rondas, tope)
    if solo in ("todos", "guardado"):
        bench_guardado(rondas, cantidad_salas, semilla)
        bench_estado_real(rondas, cantidad_salas, semilla)
    print("\nComprobaciones funcionales: OK")


def main():
    parser = argparse.ArgumentParser(description="Benchmarks sinteticos de adaptadores, sin HTTP.")
    parser.add_argument("--rondas", type=positivo, default=5)
    parser.add_argument("--semilla", type=int, default=SEMILLA_BENCH)
    parser.add_argument("--cache-size", type=positivo, default=25)
    parser.add_argument("--salas", type=positivo, default=200)
    parser.add_argument("--tamanos", type=positivo, nargs="+", default=[25, 100, 1000])
    parser.add_argument("--solo", choices=("todos", "indice", "cache", "guardado"), default="todos")
    args = parser.parse_args()
    ejecutar_bench(args.rondas, args.semilla, args.cache_size, args.salas, args.solo, args.tamanos)


if __name__ == "__main__":
    main()
