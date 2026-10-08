"""Mediciones del rol A. Ejecutar: python -m modelo.bench_modelo.

Son cargas sinteticas de estructuras, no una partida completa. No demuestran
por si solas el limite de 20 ms entre decisiones del jugador.
"""

import argparse
import random
import sys
import time

from modelo.agenda_eventos import AgendaEventos
from modelo.evento import Evento
from modelo.rastro import SalaRastro, SalidaRastro, elegir_destino_rastreador
from modelo.retroceso import HistorialRetroceso


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
    print("Estas mediciones no validan los 20 ms del bucle completo del juego.")


if __name__ == "__main__":
    main()
