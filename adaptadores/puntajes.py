"""Tabla local de partidas terminadas, almacenada como una lista JSON."""

import json
import os
from pathlib import Path
import tempfile

from comun.ordenamiento import ordenar


class ErrorPuntajes(Exception):
    pass


def _leer_resultados(ruta):
    ruta = Path(ruta)
    registros = []
    if ruta.exists():
        try:
            registros = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as error:
            raise ErrorPuntajes("La tabla de puntajes no contiene JSON valido; se conserva el archivo.") from error
        if not isinstance(registros, list) or not all(isinstance(fila, dict) for fila in registros):
            raise ErrorPuntajes("La tabla de puntajes debe ser una lista de resultados; se conserva el archivo.")
    return registros


def consultar_puntajes(ruta, criterio="tiempo"):
    """Vista estable; cada cripta/version se compara por separado."""
    if criterio not in ("tiempo", "acciones", "enemigos", "nombre"):
        raise ErrorPuntajes("Criterio desconocido: usa tiempo, acciones, enemigos o nombre.")
    registros = _leer_resultados(ruta)
    for fila in registros:
        for campo in ("nombre_jugador", "id_cripta", "version_cripta", "resultado"):
            if type(fila.get(campo)) is not str:
                raise ErrorPuntajes(f"Resultado sin {campo} valido; se conserva el archivo.")
        for campo in ("acciones_jugador", "enemigos_derrotados", "tiempo_final"):
            if type(fila.get(campo)) is not int or fila[campo] < 0:
                raise ErrorPuntajes(f"Resultado sin {campo} valido; se conserva el archivo.")

    def clave(fila):
        if criterio == "nombre":
            valor = fila["nombre_jugador"].casefold()
        elif criterio == "enemigos":
            valor = -fila["enemigos_derrotados"]
        elif criterio == "acciones":
            valor = fila["acciones_jugador"]
        else:
            valor = fila["tiempo_final"]
        return fila["id_cripta"], fila["version_cripta"], fila["resultado"], valor

    return ordenar(registros, clave=clave, comparacion_costosa=criterio == "nombre")[0]


def registrar_resultado(ruta, resultado):
    ruta = Path(ruta)
    registros = _leer_resultados(ruta)
    registros.append(resultado)
    # Publicar de una vez para conservar la tabla anterior si falla la escritura.
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ruta.parent,
                                         delete=False, suffix=".tmp") as archivo:
            temporal = Path(archivo.name)
            json.dump(registros, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
        os.replace(temporal, ruta)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
