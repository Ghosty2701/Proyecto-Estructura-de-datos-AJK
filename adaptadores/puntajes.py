"""Tabla local de partidas terminadas, almacenada como una lista JSON."""

import json
import os
from pathlib import Path
import tempfile


class ErrorPuntajes(Exception):
    pass


def registrar_resultado(ruta, resultado):
    ruta = Path(ruta)
    registros = []
    if ruta.exists():
        try:
            registros = json.loads(ruta.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as error:
            raise ErrorPuntajes("La tabla de puntajes no contiene JSON valido; se conserva el archivo.") from error
        if not isinstance(registros, list) or not all(isinstance(fila, dict) for fila in registros):
            raise ErrorPuntajes("La tabla de puntajes debe ser una lista de resultados; se conserva el archivo.")
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
