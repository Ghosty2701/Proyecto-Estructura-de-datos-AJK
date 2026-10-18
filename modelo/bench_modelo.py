"""Mediciones del rol A. Ejecutar: python -m modelo.bench_modelo.

Son cargas sinteticas de estructuras, no una partida completa. No demuestran
por si solas el limite de 20 ms entre decisiones del jugador.
"""

import argparse
import random
import sys
import time
import tempfile
from pathlib import Path

from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento
from modelo.rastro import SalaRastro, SalidaRastro, elegir_destino_rastreador
from modelo.retroceso import HistorialRetroceso
from modelo.inventario_reversible import InventarioReversible
from comun.ordenamiento import insertion_sort, merge_sort, ordenar


class ListaOrdenada:
    """Alternativa experimental propia, sin sorted ni list.sort."""

    def __init__(self):
        self.eventos = []
        self.siguiente_secuencia = 0

    def insertar(self, evento):
        evento.secuencia = self.siguiente_secuencia
        self.siguiente_secuencia += 1
        self.eventos.append(evento)
        i = len(self.eventos) - 1
        while i > 0:
            anterior = self.eventos[i - 1]
            if (anterior.tiempo, anterior.secuencia) <= (
                evento.tiempo, evento.secuencia
            ):
                break
            self.eventos[i] = anterior
            i -= 1
        self.eventos[i] = evento

    def cancelar(self, evento):
        evento.cancelado = True

    def extraer_minimo(self):
        while self.eventos:
            evento = self.eventos.pop(0)
            if not evento.cancelado:
                return evento
        return None


def medir(preparar, ejecutar, verificar, repeticiones):
    tiempos = []
    for _ in range(repeticiones):
        estado = preparar()  # Preparacion fuera del cronometro.
        inicio = time.perf_counter_ns()
        resultado = ejecutar(estado)
        tiempos.append(time.perf_counter_ns() - inicio)
        verificar(resultado)  # Verificacion fuera del cronometro.
    return min(tiempos) / 1_000_000


def comprobar(condicion, mensaje):
    if not condicion:
        raise RuntimeError(mensaje)


def medir_agenda(cantidad, repeticiones, semilla):
    azar = random.Random(semilla)
    tiempos = [
        azar.randrange(cantidad * 10)
        for _ in range(cantidad)
    ]

    # Orden esperado, calculado fuera del tiempo medido.
    esperados = []

    for i, tiempo in enumerate(tiempos):
        if i % 4 == 0:
            continue

        clave = (tiempo, i, i)
        esperados.append(clave)
        posicion = len(esperados) - 1

        while posicion > 0 and esperados[posicion - 1] > clave:
            esperados[posicion] = esperados[posicion - 1]
            posicion -= 1

        esperados[posicion] = clave

    def ejecutar(estado):
        agenda, eventos = estado

        for evento in eventos:
            agenda.insertar(evento)

        for i in range(0, cantidad, 4):
            agenda.cancelar(eventos[i])

        salida = []

        while True:
            evento = agenda.extraer_minimo()

            if evento is None:
                break

            salida.append(
                (evento.tiempo, evento.secuencia, evento.actor_id)
            )

        return salida

    def verificar(salida):
        comprobar(
            salida == esperados,
            "La agenda devolvio un orden incorrecto",
        )

    print(
        f"\nAGENDA: {cantidad} inserciones, "
        f"{(cantidad + 3) // 4} cancelaciones"
    )
    print(f"Eventos activos extraidos: {len(esperados)}")

    alternativas = (
        ("Heap propio", AgendaEventos),
        ("Lista ordenada", ListaOrdenada),
    )

    for nombre, clase in alternativas:
        def preparar(clase=clase):
            eventos = [
                Evento(t, "accion", i)
                for i, t in enumerate(tiempos)
            ]
            return clase(), eventos

        ms = medir(
            preparar,
            ejecutar,
            verificar,
            repeticiones,
        )

        print(f"{nombre}: {ms:.3f} ms")


class ActorMedicion:
    def __init__(self):
        self.vida = 100


def preparar_retroceso(cantidad):
    historial = HistorialRetroceso()
    actor = ActorMedicion()
    sala = SalaRastro(1)
    sala.ultimo_rastro = 0
    historial.iniciar_accion(50)
    for i in range(cantidad):
        historial.registrar_vida(actor)
        actor.vida = 99 if i % 2 == 0 else 100
        historial.registrar_rastro(sala, i + 1)
    return historial, actor, sala


def medir_retroceso(cantidad, repeticiones):
    estado = preparar_retroceso(cantidad)
    accion = estado[0].acciones[-1]
    # Estimacion parcial: contenedores del registro, sin sumar actores, salas
    # ni valores referenciados. No es el consumo total del proceso.
    bytes_registro = (
        sys.getsizeof(accion)
        + sys.getsizeof(accion.__dict__)
        + sys.getsizeof(accion.cambios)
        + sum(sys.getsizeof(delta) for delta in accion.cambios)
    )

    def ejecutar(estado):
        historial, actor, sala = estado
        reloj = historial.deshacer_ultima()
        return reloj, actor.vida, sala.ultimo_rastro, len(historial.acciones)

    def verificar(resultado):
        comprobar(resultado == (50, 100, 0, 0), "El retroceso no restauro el estado")

    ms = medir(lambda: preparar_retroceso(cantidad), ejecutar, verificar, repeticiones)
    print(f"\nRETROCESO: {cantidad * 2} deltas de vida y rastro")
    print(f"Deshacer un intervalo: {ms:.3f} ms")
    print(f"Contenedores del registro (estimacion parcial): {bytes_registro} bytes")


def medir_rastro(salas, rastreadores, vueltas, repeticiones):
    mapa = [SalaRastro(i) for i in range(salas)]
    for sala in mapa:
        sala.ultimo_rastro = 50
        sala.salidas = [
            SalidaRastro(mapa[(sala.sala_id + paso) % salas])
            for paso in range(1, 5)
        ]

    print(f"\nRASTRO: mapa de {salas} salas; 4 salidas abiertas por rastreador")
    for cantidad in (1, rastreadores):
        actores = mapa[:cantidad]
        # Todos los rastros empatan: gana el menor ID conectado.
        esperado = sum(0 if i >= salas - 4 else i + 1 for i in range(cantidad))
        esperado *= vueltas

        def ejecutar(actores):
            suma = 0
            for _ in range(vueltas):
                for sala in actores:
                    suma += elegir_destino_rastreador(sala, 100)
            return suma

        def verificar(suma, esperado=esperado):
            comprobar(suma == esperado, "El rastreador eligio un destino incorrecto")

        ms = medir(lambda: actores, ejecutar, verificar, repeticiones)
        decisiones = cantidad * vueltas
        print(f"{cantidad} rastreadores; {decisiones} decisiones: {ms:.3f} ms")
        print(f"Promedio de esta carga: {ms * 1000 / decisiones:.3f} us/decision")


def medir_inventario(cantidad, repeticiones):
    def ejecutar(inventario):
        for numero in range(cantidad):
            inventario.recoger(numero)
        for _ in range(cantidad // 2):
            inventario.avanzar()
        inventario.equipar_actual("arma")
        equipado = inventario.arma_equipada
        retirados = 0
        suma = 0
        while not inventario.esta_vacio():
            suma += inventario.soltar_actual()
            retirados += 1
        return inventario, equipado, retirados, suma

    def verificar(resultado):
        inventario, equipado, retirados, suma = resultado
        comprobar(equipado == cantidad // 2 and retirados == cantidad and suma == cantidad * (cantidad - 1) // 2,
                  "El recorrido, equipamiento o retiro de objetos fue incorrecto")
        comprobar(inventario.cantidad == 0 and inventario.frente is None and inventario.final is None,
                  "El inventario no quedo vacio")
        comprobar(inventario.frente_reversible is None and inventario.final_reversible is None,
                  "El orden reversible no quedo vacio")

    ms = medir(lambda: InventarioReversible(cantidad), ejecutar, verificar, repeticiones)
    print(f"\nINVENTARIO: {cantidad} inserciones, recorrido al centro, equipar y {cantidad} retiros")
    print(f"Carga completa: {ms:.3f} ms")


def medir_ordenamientos(tamanos, repeticiones, semilla):
    def clave_costosa(numero):
        acumulado = 0
        for _ in range(20):
            acumulado += numero
        return acumulado // 20

    print("\nORDENAMIENTOS: milisegundos por lista; clave costosa sintetica de 20 sumas")
    for cantidad in tamanos:
        for caso in ("mezclados", "casi ordenados", "clave costosa"):
            datos = list(range(cantidad))
            if caso == "casi ordenados":
                centro = cantidad // 2
                datos[centro], datos[centro + 1] = datos[centro + 1], datos[centro]
            else:
                random.Random(semilla).shuffle(datos)
            costosa = caso == "clave costosa"
            clave = clave_costosa if costosa else lambda numero: numero
            esperado = list(range(cantidad))

            def verificar(resultado):
                comprobar(resultado == esperado, "El ordenamiento produjo un resultado incorrecto")

            print(f"  n={cantidad}; {caso}")
            for algoritmo in (insertion_sort, merge_sort):
                ms = medir(lambda: datos, lambda lista: algoritmo(lista, clave), verificar, repeticiones)
                print(f"    {algoritmo.__name__}: {ms:.3f} ms")
            _, elegido = ordenar(datos, clave, comparacion_costosa=costosa)
            ms = medir(lambda: datos, lambda lista: ordenar(lista, clave, comparacion_costosa=costosa)[0],
                       verificar, repeticiones)
            print(f"    Seleccion automatica ({elegido}): {ms:.3f} ms")


def ejecutar_bench_completo(repeticiones=5, semilla=2026, tope_cache=25):
    from adaptadores.bench_adaptadores import ejecutar_bench

    print(f"Python {sys.version.split()[0]}; plataforma {sys.platform}; semilla {semilla}")
    print(f"Repeticiones: {repeticiones}; menor tiempo observado, sin garantia de rendimiento.")
    medir_agenda(2000, repeticiones, semilla)
    medir_retroceso(1000, repeticiones)
    medir_rastro(4000, 100, 100, repeticiones)
    medir_inventario(1000, repeticiones)
    medir_ordenamientos((16, 256), repeticiones, semilla)
    ejecutar_bench(rondas=repeticiones, semilla=semilla, tope=tope_cache)


def _accion_para_medir(partida, sala_anterior):
    if partida._enemigos_presentes():
        return "atacar 1"
    objeto = partida.inventario.actual()
    tipo = getattr(objeto, "clase", None)
    if tipo == "arma" and objeto is not partida.inventario.arma_equipada:
        return "equipar"
    if tipo == "armadura" and objeto is not partida.inventario.armadura_equipada:
        return "equipar"
    if tipo in ("pocion", "antidoto", "antorcha"):
        return "usar"
    sala = partida.jugador.sala_actual
    if sala.objetos_suelo and not partida.inventario.esta_lleno():
        return "recoger 1"
    for salida in sala.salidas:
        if not salida.abierta and any(
            getattr(objeto, "clase", None) == "llave"
            and getattr(objeto, "id", None) == salida.puerta.llave
            for objeto in partida.inventario.listar()
        ):
            return f"abrir {salida.direccion.lower()}"
    abiertas = [salida for salida in sala.salidas if salida.abierta]
    for salida in abiertas:
        if salida.destino.sala_id != sala_anterior:
            return f"ir {salida.direccion.lower()}"
    if abiertas:
        return f"ir {abiertas[0].direccion.lower()}"
    return "esperar"


def medir_ciclos_partida(partida, cantidad=100):
    """Mide acciones reales con los datos ya incorporados al modelo, sin vista."""
    from controlador.controlador import ejecutar_accion_replay

    if cantidad <= 0:
        raise ValueError("La cantidad de ciclos debe ser positiva")
    tiempos = []
    terminales = []
    sala_anterior = None
    for _ in range(cantidad):
        if partida.estado().terminada:
            break
        accion = _accion_para_medir(partida, sala_anterior)
        origen = partida.jugador.sala_actual.sala_id
        solicitudes = getattr(partida.fuente, "solicitudes_realizadas", 0)
        inicio = time.perf_counter_ns()
        ejecutar_accion_replay(partida, accion)
        duracion = (time.perf_counter_ns() - inicio) / 1_000_000
        comprobar(getattr(partida.fuente, "solicitudes_realizadas", 0) == solicitudes,
                  "Se realizo HTTP durante un ciclo: la medicion no es valida")
        if partida.estado().terminada:
            terminales.append(duracion)
        else:
            turno = partida.motor.consultar_siguiente_evento()
            comprobar(turno is partida.jugador.proxima_accion and turno.tiempo == partida.motor.reloj,
                      "El ciclo no termino en la siguiente decision del jugador")
            tiempos.append(duracion)
        if partida.jugador.sala_actual.sala_id != origen:
            sala_anterior = origen
    return tiempos, terminales


def medir_cripta_cargada(cargador, partida, repeticiones=5, ciclos=100):
    if repeticiones <= 0 or ciclos <= 0:
        raise ValueError("Las cantidades de la medicion deben ser positivas")
    from controlador.cargar_partida import _recorrer_arbol

    for sala in _recorrer_arbol(cargador.salas.raiz):
        cargador.preparar_sala(sala)
    tiempos = []
    terminales = []
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "inicio_bench.bin"
        # Un guardado inicial repite la carga experimental; no se usa para retroceso.
        cargador.guardar_sesion(partida, ruta)
        for _ in range(repeticiones):
            estado = cargador.leer_sesion(ruta, partida.id_cripta, partida.version_cripta)
            cargador.aplicar_sesion(partida, estado)
            ciclos_medidos, finales = medir_ciclos_partida(partida, ciclos)
            tiempos.extend(ciclos_medidos)
            terminales.extend(finales)
    comprobar(bool(tiempos), "No se completo ningun ciclo entre decisiones")
    maximo = max(tiempos)
    excedidos = sum(tiempo >= 20 for tiempo in tiempos)
    print(f"\nCICLO COMPLETO: cripta {partida.id_cripta}; version {partida.version_cripta}; semilla {partida.motor.semilla}")
    print(f"Datos precargados; sin HTTP ni renderizado; {repeticiones} repeticiones desde el mismo estado.")
    print("Recorrido automatico: combate, recogida, uso/equipo, puertas con llave y movimiento.")
    print(f"Ciclos entre decisiones: {len(tiempos)}; intervalos terminales separados: {len(terminales)}")
    print(f"Minimo: {min(tiempos):.3f} ms; promedio: {sum(tiempos) / len(tiempos):.3f} ms; maximo: {maximo:.3f} ms")
    if terminales:
        print(f"Maximo del intervalo de victoria/derrota: {max(terminales):.3f} ms")
    print(f"Ciclos con tiempo >= 20 ms: {excedidos}/{len(tiempos)}")
    print(f"Limite de 20 ms en los ciclos medidos: {'CUMPLE' if excedidos == 0 else 'NO CUMPLE'}")
    return {"ciclos": len(tiempos), "maximo_ms": maximo, "excedidos": excedidos}


def positivo(valor):
    numero = int(valor)
    if numero <= 0:
        raise argparse.ArgumentTypeError("Debe ser un entero positivo")
    return numero


def main():
    parser = argparse.ArgumentParser(description="Benchmarks sinteticos del rol A")
    parser.add_argument("--eventos", type=positivo, default=2000)
    parser.add_argument("--cambios", type=positivo, default=1000)
    parser.add_argument("--salas", type=positivo, default=4000)
    parser.add_argument("--rastreadores", type=positivo, default=100)
    parser.add_argument("--vueltas", type=positivo, default=100)
    parser.add_argument("--repeticiones", type=positivo, default=5)
    parser.add_argument("--semilla", type=int, default=2026)
    args = parser.parse_args()
    if args.salas < 5 or args.rastreadores > args.salas:
        parser.error("Se necesitan al menos 5 salas y rastreadores <= salas")

    print(f"Python {sys.version.split()[0]}; plataforma {sys.platform}")
    print(f"Semilla: {args.semilla}; repeticiones: {args.repeticiones}")
    print("Se informa el menor tiempo de las repeticiones; no un limite garantizado.")
    medir_agenda(args.eventos, args.repeticiones, args.semilla)
    medir_retroceso(args.cambios, args.repeticiones)
    medir_rastro(args.salas, args.rastreadores, args.vueltas, args.repeticiones)
    print("\nComprobaciones funcionales de todas las cargas: OK")


if __name__ == "__main__":
    main()
