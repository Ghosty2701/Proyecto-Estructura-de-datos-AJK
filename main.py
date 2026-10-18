"""Primera partida de consola: python main.py --cripta <id> --semilla 2026."""

import argparse
import sys

from adaptadores.cache_catalogo import CacheCatalogo, ErrorCatalogo
from adaptadores.cliente_http import ClienteHTTP, ErrorHTTP, PresupuestoAgotado
from adaptadores.servicio_cripta import ErrorCripta, ServicioCripta
from controlador.cargar_partida import CargadorPartida, ErrorDatosPartida
from controlador.controlador import Controlador
from vista.vista_consola import VistaConsola


def _entero_positivo(texto):
    valor = int(texto)
    if valor <= 0:
        raise argparse.ArgumentTypeError("debe ser un entero positivo")
    return valor


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Cripta: primera partida de consola con datos oficiales.")
    seleccion = parser.add_mutually_exclusive_group(required=True)
    seleccion.add_argument("--listar", action="store_true", help="mostrar las criptas oficiales disponibles")
    seleccion.add_argument("--cripta", help="ID de la cripta que se jugara")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--cache-size", type=_entero_positivo, default=25)
    parser.add_argument("--cache-dir", default=".cache_cripta")
    opciones = parser.parse_args(argumentos)
    fuente = ClienteHTTP(reservar_imprevistos=True)
    try:
        if opciones.listar:
            for cripta in fuente.listar_criptas()["criptas"]:
                print(f"{cripta['id']}: {cripta['nombre']} ({cripta['salas']} salas)")
            return 0
        cache = CacheCatalogo(fuente, carpeta=opciones.cache_dir, tope=opciones.cache_size)
        servicio = ServicioCripta(fuente, cache)
        cargador = CargadorPartida(servicio)
        partida = cargador.crear(opciones.cripta, opciones.semilla)
        vista = VistaConsola()
        vista.agregar_mensajes([
            f"Cripta {opciones.cripta}; semilla {opciones.semilla}.",
            "Comandos: w/a/s/d, atacar 1, recoger 1, abrir n, inv, sig, ant, usar, equipar, esperar, ayuda y salir.",
            "Soltar, retroceso, guardado y victoria aun pendientes de integracion.",
        ])
        Controlador(partida, vista).ejecutar()
    except (ErrorHTTP, PresupuestoAgotado, ErrorCatalogo, ErrorCripta, ErrorDatosPartida, OSError) as error:
        print(f"No se pudo continuar la partida: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nPartida interrumpida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
