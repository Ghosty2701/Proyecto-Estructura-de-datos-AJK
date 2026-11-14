"""Primera partida de consola: python main.py --cripta <id> --semilla 2026."""

import argparse
import sys
from contextlib import nullcontext

from adaptadores.cache_catalogo import CacheCatalogo, ErrorCatalogo
from adaptadores.cliente_http import ClienteHTTP, ErrorHTTP, PresupuestoAgotado
from adaptadores.modo_offline import ModoOffline, ErrorOffline
from adaptadores.guardado_binario import ErrorGuardado
from adaptadores.servicio_cripta import ErrorCripta, ServicioCripta
from adaptadores.puntajes import ErrorPuntajes, consultar_puntajes, registrar_resultado
from adaptadores.bitacora_partida import (
    ErrorBitacora, EscritorBitacora, leer_bitacora, reproducir_bitacora,
)
from controlador.cargar_partida import CargadorPartida, ErrorDatosPartida
from controlador.controlador import Controlador, ejecutar_accion_replay
from vista.vista_consola import VistaConsola, lineas_historia
from modelo.verificacion import verificar


from vista.informes import informe_verificacion
from controlador.sesion import abrir_partida, guardar_resultado


def _entero_positivo(texto):
    valor = int(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return valor


def _entero_positivo_estricto(texto):
    if not texto or any(c not in "0123456789" for c in texto) or int(texto) < 1:
        raise argparse.ArgumentTypeError("debe ser un entero mayor o igual que 1")
    return int(texto)


def _entero_no_negativo(texto):
    if not texto or any(c not in "0123456789" for c in texto):
        raise argparse.ArgumentTypeError("debe ser un entero mayor o igual que 0")
    return int(texto)


def informe_hasta(partida, hasta):
    """Resumen histórico de --replay --hasta sin instanciar la vista (FR-LT-010)."""
    reloj = partida.motor.reloj
    if hasta < reloj:
        return "\n".join(lineas_historia(partida.historia(("t", hasta))))
    lineas = lineas_historia(partida.historia(("t", reloj)))
    if hasta > reloj:
        if partida.estado().terminada:
            lineas.append(f"La partida terminó en t={reloj}, antes de {hasta}.")
        else:
            lineas.append(f"El registro termina en t={reloj}, antes de {hasta}; la partida seguía en curso.")
    return "\n".join(lineas)


def _resumen_red(fuente, cache):
    presupuesto = fuente.presupuesto_solicitudes
    print(f"Solicitudes: {fuente.solicitudes_realizadas}/{presupuesto}; "
          f"cache: {cache.aciertos} aciertos, {cache.fallos} fallos, "
          f"{cache.lecturas_disco} lecturas de disco.")


def _iniciar_grafica(opciones):
    try:
        import pygame
    except ModuleNotFoundError as error:
        if error.name != 'pygame':
            raise
        # AC-IG-022: explicar instalación y entorno; pygame 2.6.1 no publica paquetes para 3.14+.
        version = f'{sys.version_info.major}.{sys.version_info.minor}'
        print('Instala la interfaz opcional: python -m pip install -r '
              'documentacion/requirements-pygame.txt', file=sys.stderr)
        print(f'Requiere Python 3.11 a 3.13 (estás usando {version}); pygame 2.6.1 no se '
              'instala en 3.14 o posterior. En Windows: py -3.13 -m venv .venv', file=sys.stderr)
        return 1
    from vista.pygame_ui.aplicacion import ejecutar
    try:
        return ejecutar(opciones)
    except pygame.error as error:
        print(f'No se pudo abrir la pantalla de Pygame: {error}', file=sys.stderr)
        return 1


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Cripta: primera partida de consola con datos oficiales.")
    parser.add_argument('--interfaz', choices=('consola', 'pygame'), default='consola',
                        help='interfaz opcional; pygame sin cripta abre el menú')
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument("--listar", action="store_true", help="mostrar las criptas oficiales disponibles")
    seleccion.add_argument("--ver-puntajes", action="store_true", help="consultar resultados locales ordenados")
    parser.add_argument("--orden-puntajes", choices=("tiempo", "acciones", "enemigos", "nombre"),
                        default="tiempo", help="criterio para --ver-puntajes")
    parser.add_argument("--bench", action="store_true", help="medir todos los bloques de P2 (varios minutos); con --cripta, referencia real")
    parser.add_argument('--bench-linea-tiempo', action='store_true',
                        help='alias compatible: --bench ya incluye la línea de tiempo')
    parser.add_argument('--salida-bench', metavar='CARPETA',
                        help='con --bench: carpeta de resultados (predeterminada: resultados/bench)')
    parser.add_argument("--repeticiones", type=_entero_positivo, default=5, help="repeticiones del benchmark")
    seleccion.add_argument("--cripta", help="ID de la cripta que se jugara")
    seleccion.add_argument('--verificar', metavar='CRIPTA', help='verificar resolubilidad sin vista ni partida')
    parser.add_argument('--forzar', action='store_true', help='iniciar una cripta no resoluble explícitamente')
    seleccion.add_argument("--cargar", metavar="ARCHIVO", help="reanudar una partida binaria sin grabar bitacora")
    parser.add_argument("--archivo-guardado", help="ruta usada por los comandos guardar y cargar")
    seleccion.add_argument("--replay", help="reproducir una bitacora sin interfaz ni interaccion")
    parser.add_argument("--sin-interfaz", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--checkpoint-cada", type=_entero_positivo_estricto, metavar="K",
                        help="copia completa del estado como mucho cada K acciones (línea de tiempo)")
    parser.add_argument("--hasta", type=_entero_no_negativo, metavar="T",
                        help="con --replay: imprimir el estado en el instante T sin vista")
    parser.add_argument("--bitacora", help="ruta de una nueva bitacora; no sobrescribe archivos existentes")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--nombre", help="nombre para la tabla de puntajes")
    parser.add_argument("--puntajes", default="puntajes.json", help="archivo JSON de resultados")
    parser.add_argument("--cache-size", type=_entero_positivo, default=25)
    parser.add_argument("--cache-dir", default=".cache_cripta")
    parser.add_argument("--offline", nargs="?", const="datos_offline", metavar="CARPETA",
                        help="leer el paquete local sin HTTP; carpeta predeterminada: datos_offline")
    opciones = parser.parse_args(argumentos)
    grafica = opciones.interfaz == 'pygame'
    if grafica and (opciones.listar or opciones.verificar or opciones.replay or
                    opciones.ver_puntajes or opciones.bench or opciones.bench_linea_tiempo or
                    opciones.salida_bench is not None or opciones.hasta is not None or opciones.sin_interfaz):
        parser.error('--interfaz pygame no se combina con modos sin vista')
    if opciones.bench_linea_tiempo and not opciones.bench:
        parser.error('--bench-linea-tiempo requiere --bench')
    if opciones.salida_bench is not None and not opciones.bench:
        parser.error('--salida-bench requiere --bench')
    if not (grafica or opciones.listar or opciones.cripta or opciones.cargar or opciones.replay or opciones.bench or opciones.ver_puntajes or opciones.verificar):
        parser.error("indica --listar, --cripta, --cargar, --replay, --bench o --ver-puntajes")
    if opciones.bench and (opciones.listar or opciones.cargar or opciones.replay or opciones.bitacora or opciones.ver_puntajes or opciones.verificar):
        parser.error("--bench solo se combina con --cripta para medir ciclos")
    if opciones.forzar and (not opciones.cripta or opciones.bench):
        parser.error('--forzar requiere --cripta en una partida nueva')
    if opciones.bitacora and not opciones.cripta:
        parser.error("--bitacora requiere --cripta")
    if opciones.checkpoint_cada is not None and (
            opciones.bench or not (opciones.cripta or opciones.cargar or opciones.replay)):
        parser.error("--checkpoint-cada solo se usa con --cripta, --cargar o --replay")
    if opciones.hasta is not None and not opciones.replay:
        parser.error("--hasta requiere --replay")
    if opciones.sin_interfaz and not opciones.replay:
        parser.error("--sin-interfaz requiere --replay")
    if opciones.nombre is not None and not opciones.nombre.strip():
        parser.error("el nombre del jugador no puede estar vacio")
    if grafica:
        return _iniciar_grafica(opciones)
    if opciones.ver_puntajes:
        try:
            registros = consultar_puntajes(opciones.puntajes, opciones.orden_puntajes)
        except (OSError, ErrorPuntajes) as error:
            print(f"No se pudo consultar los puntajes: {error}", file=sys.stderr)
            return 1
        if not registros:
            print("No hay resultados registrados.")
        for fila in registros:
            print(f"{fila['id_cripta']} ({fila['version_cripta']}) | {fila['nombre_jugador']} | "
                  f"{fila['resultado']} | tiempo {fila['tiempo_final']} | "
                  f"acciones {fila['acciones_jugador']} | enemigos {fila['enemigos_derrotados']}")
        return 0
    if opciones.bench:
        from modelo.bench_modelo import ejecutar_bench_completo
        from modelo.bench_cierre import ejecutar_cierre
        try:
            subsistemas = ejecutar_bench_completo(opciones.repeticiones, opciones.semilla, opciones.cache_size)
            ejecutar_cierre(opciones.repeticiones, opciones.semilla,
                           carpeta=opciones.salida_bench or 'resultados/bench',
                           decisiones=subsistemas.get('decisiones_linea_tiempo'))
        except (OSError, ValueError, RuntimeError, AssertionError) as error:
            print(f'No se pudo completar --bench: {error}', file=sys.stderr)
            return 1
        if not opciones.cripta:
            return 0
    fuente = ModoOffline(opciones.offline) if opciones.offline is not None else ClienteHTTP(reservar_imprevistos=True)
    try:
        if opciones.listar:
            for cripta in fuente.listar_criptas()["criptas"]:
                print(f"{cripta['id']}: {cripta['nombre']} ({cripta['salas']} salas)")
            return 0
        if opciones.verificar:
            servicio = ServicioCripta(fuente, None)
            resultado = verificar(servicio.preparar_verificacion(opciones.verificar))
            print(informe_verificacion(resultado))
            print(f'Solicitudes: {fuente.solicitudes_realizadas}/{fuente.presupuesto_solicitudes}.')
            return 0 if resultado.resoluble else 1
        cache = CacheCatalogo(fuente, carpeta=opciones.cache_dir, tope=opciones.cache_size)
        servicio = ServicioCripta(fuente, cache)
        mapa = None
        if opciones.cripta and not opciones.bench:
            mapa = servicio.preparar_verificacion(opciones.cripta)
            resultado = verificar(mapa)
            print(informe_verificacion(resultado))
            if not resultado.resoluble and not opciones.forzar:
                print('La partida no inicia; usa --forzar para iniciar explícitamente.')
                return 1
        cargador = CargadorPartida(servicio)
        if opciones.bench:
            from modelo.bench_modelo import medir_cripta_cargada
            from modelo.bench_resolubilidad import medir_entrada
            mapa = servicio.preparar_verificacion(opciones.cripta)
            _, generales, salas, _ = servicio._preparada
            ubicaciones = {'llaves': [
                {'id': llave.id, 'sala': mapa.salas[u.sala].sala_id, 'enemigo': u.enemigo}
                for llave in mapa.llaves for u in llave.ubicaciones]}
            resolubilidad = medir_entrada(generales, salas, ubicaciones,
                                         opciones.repeticiones, informe_verificacion)
            print(f"RESOLUBILIDAD OFICIAL: {mapa.id_cripta}; máximo "
                  f"{resolubilidad['maximo_ms']:.4f} ms; "
                  + ('CUMPLE <200 ms.' if not resolubilidad['excedidos_200ms'] else 'NO CUMPLE <200 ms.'))
            partida = cargador.crear(opciones.cripta, opciones.semilla, datos_verificados=mapa)
            try:
                resultado = medir_cripta_cargada(cargador, partida, opciones.repeticiones)
            except RuntimeError as error:
                print(f"No se pudo medir el ciclo completo: {error}", file=sys.stderr)
                return 1
            _resumen_red(fuente, cache)
            return 0 if (resultado["excedidos"] == 0 and resultado['niebla']['excedidos_5ms'] == 0
                         and not resolubilidad['excedidos_200ms']) else 1
        if opciones.replay:
            encabezado, _ = leer_bitacora(opciones.replay)
            partida = cargador.crear(encabezado.id_cripta, encabezado.semilla, encabezado_log=encabezado,
                                     checkpoint_cada=opciones.checkpoint_cada)
            partida = reproducir_bitacora(
                opciones.replay, id_cripta_actual=partida.id_cripta,
                version_cripta_actual=partida.version_cripta, version_catalogo_actual=cache.version,
                crear_partida=lambda encabezado: partida, ejecutar_accion=ejecutar_accion_replay,
            )
            print(f"Replay completado: sala {partida.jugador.sala_actual.sala_id}, "
                  f"vida {partida.jugador.vida}, reloj {partida.motor.reloj}, "
                  f"acciones {partida.acciones_ejecutadas}; resultado: {partida.estado().resultado or 'en curso'}.")
            if opciones.hasta is not None:
                print(informe_hasta(partida, opciones.hasta))
            _resumen_red(fuente, cache)
            return 0
        partida = abrir_partida(cargador, opciones, mapa)
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
                guardar_resultado(partida, opciones.puntajes, registrar_resultado)
            except (OSError, ErrorPuntajes) as error:
                print(f"No se pudo guardar el resultado: {error}", file=sys.stderr)
                return 1
            print(f"Resultado guardado en {opciones.puntajes}.")
    except (ErrorHTTP, PresupuestoAgotado, ErrorOffline, ErrorCatalogo, ErrorCripta, ErrorDatosPartida, ErrorBitacora, ErrorGuardado, OSError) as error:
        print(f"Error: no se pudo continuar la partida o verificación: {error}", file=sys.stderr)
        return 2 if opciones.verificar else 1
    except KeyboardInterrupt:
        print("\nPartida interrumpida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
