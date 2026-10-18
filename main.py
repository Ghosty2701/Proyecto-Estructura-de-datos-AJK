"""Primera partida de consola: python main.py --cripta <id> --semilla 2026."""

import argparse
import sys
from contextlib import nullcontext

from adaptadores.cache_catalogo import CacheCatalogo, ErrorCatalogo
from adaptadores.cliente_http import ClienteHTTP, ErrorHTTP, PresupuestoAgotado
from adaptadores.modo_offline import ModoOffline, ErrorOffline
from adaptadores.guardado_binario import ErrorGuardado
from adaptadores.servicio_cripta import ErrorCripta, ServicioCripta
from adaptadores.puntajes import ErrorPuntajes, registrar_resultado
from adaptadores.bitacora_partida import (
    ErrorBitacora, EscritorBitacora, leer_bitacora, reproducir_bitacora,
)
from controlador.cargar_partida import CargadorPartida, ErrorDatosPartida
from controlador.controlador import Controlador, ejecutar_accion_replay
from vista.vista_consola import VistaConsola


def _entero_positivo(texto):
    valor = int(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return valor


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Cripta: primera partida de consola con datos oficiales.")
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--listar", action="store_true", help="mostrar las criptas oficiales disponibles")
    parser.add_argument("--bench", action="store_true", help="medir subsistemas y, con --cripta, ciclos reales")
    parser.add_argument("--repeticiones", type=_entero_positivo, default=5, help="repeticiones del benchmark")
    seleccion.add_argument("--cripta", help="ID de la cripta que se jugara")
    seleccion.add_argument("--cargar", metavar="ARCHIVO", help="reanudar una partida binaria sin grabar bitacora")
    parser.add_argument("--archivo-guardado", help="ruta usada por los comandos guardar y cargar")
    seleccion.add_argument("--replay", help="reproducir una bitacora sin interfaz ni interaccion")
    parser.add_argument("--sin-interfaz", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--bitacora", help="ruta de una nueva bitacora; no sobrescribe archivos existentes")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--nombre", help="nombre para la tabla de puntajes")
    parser.add_argument("--puntajes", default="puntajes.json", help="archivo JSON de resultados")
    parser.add_argument("--cache-size", type=_entero_positivo, default=25)
    parser.add_argument("--cache-dir", default=".cache_cripta")
    parser.add_argument("--offline", nargs="?", const="datos_offline", metavar="CARPETA",
                        help="leer el paquete local sin HTTP; carpeta predeterminada: datos_offline")
    opciones = parser.parse_args(argumentos)
    if not (opciones.listar or opciones.cripta or opciones.cargar or opciones.replay or opciones.bench):
        parser.error("indica --listar, --cripta, --cargar, --replay o --bench")
    if opciones.bench and (opciones.listar or opciones.cargar or opciones.replay or opciones.bitacora):
        parser.error("--bench solo se combina con --cripta para medir ciclos")
    if opciones.bitacora and not opciones.cripta:
        parser.error("--bitacora requiere --cripta")
    if opciones.sin_interfaz and not opciones.replay:
        parser.error("--sin-interfaz requiere --replay")
    if opciones.nombre is not None and not opciones.nombre.strip():
        parser.error("el nombre del jugador no puede estar vacio")
    if opciones.bench:
        from modelo.bench_modelo import ejecutar_bench_completo
        ejecutar_bench_completo(opciones.repeticiones, opciones.semilla, opciones.cache_size)
        if not opciones.cripta:
            return 0
    fuente = ModoOffline(opciones.offline) if opciones.offline is not None else ClienteHTTP(reservar_imprevistos=True)
    try:
        if opciones.listar:
            for cripta in fuente.listar_criptas()["criptas"]:
                print(f"{cripta['id']}: {cripta['nombre']} ({cripta['salas']} salas)")
            return 0
        cache = CacheCatalogo(fuente, carpeta=opciones.cache_dir, tope=opciones.cache_size)
        servicio = ServicioCripta(fuente, cache)
        cargador = CargadorPartida(servicio)
        if opciones.bench:
            from modelo.bench_modelo import medir_cripta_cargada
            partida = cargador.crear(opciones.cripta, opciones.semilla)
            try:
                resultado = medir_cripta_cargada(cargador, partida, opciones.repeticiones)
            except RuntimeError as error:
                print(f"No se pudo medir el ciclo completo: {error}", file=sys.stderr)
                return 1
            return 0 if resultado["excedidos"] == 0 else 1
        if opciones.replay:
            encabezado, _ = leer_bitacora(opciones.replay)
            partida = cargador.crear(encabezado.id_cripta, encabezado.semilla, encabezado_log=encabezado)
            partida = reproducir_bitacora(
                opciones.replay, id_cripta_actual=partida.id_cripta,
                version_cripta_actual=partida.version_cripta, version_catalogo_actual=cache.version,
                crear_partida=lambda encabezado: partida, ejecutar_accion=ejecutar_accion_replay,
            )
            print(f"Replay completado: sala {partida.jugador.sala_actual.sala_id}, "
                  f"vida {partida.jugador.vida}, reloj {partida.motor.reloj}, "
                  f"acciones {partida.acciones_ejecutadas}; resultado: {partida.estado().resultado or 'en curso'}.")
            return 0
        if opciones.cargar:
            partida = cargador.reanudar(opciones.cargar)
        else:
            partida = cargador.crear(opciones.cripta, opciones.semilla)
        if opciones.nombre is not None:
            partida.nombre_jugador = opciones.nombre.strip()
        if opciones.archivo_guardado is not None:
            partida.ruta_guardado = opciones.archivo_guardado
        vista = VistaConsola()
        vista.permitir_cargar = not bool(opciones.bitacora)
        vista.agregar_mensajes([
            f"Cripta {partida.id_cripta}; semilla {partida.motor.semilla}.",
            f"Guardar/cargar: {partida.ruta_guardado}. Cargar requiere no estar registrando bitacora.",
        ])
        if opciones.bitacora:
            cache.obtener_varias(())
            contexto_log = EscritorBitacora(
                opciones.bitacora, partida.id_cripta, partida.version_cripta,
                cache.version, opciones.semilla,
            )
        else:
            contexto_log = nullcontext(None)
        with contexto_log as escritor:
            partida.bitacora_activa = escritor is not None
            try:
                Controlador(
                    partida, vista, registrar_accion=escritor.registrar_accion if escritor else None,
                ).ejecutar()
            finally:
                partida.bitacora_activa = False
        vista.mostrar_resumen_red(
            fuente.solicitudes_realizadas, fuente.presupuesto_solicitudes, cache.aciertos, cache.fallos,
        )
        resultado = partida.resultado_final()
        if resultado is not None:
            try:
                registrar_resultado(opciones.puntajes, resultado)
            except (OSError, ErrorPuntajes) as error:
                print(f"No se pudo guardar el resultado: {error}", file=sys.stderr)
                return 1
            print(f"Resultado guardado en {opciones.puntajes}.")
    except (ErrorHTTP, PresupuestoAgotado, ErrorOffline, ErrorCatalogo, ErrorCripta, ErrorDatosPartida, ErrorBitacora, ErrorGuardado, OSError) as error:
        print(f"No se pudo continuar la partida: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nPartida interrumpida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
