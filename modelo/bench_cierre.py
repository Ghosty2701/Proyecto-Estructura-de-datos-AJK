"""T032: ejecución conjunta optativa, con salida visible y evidencia nueva."""
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

from adaptadores.bench_persistencia import medir_persistencia
from modelo.bench_linea_tiempo import medir_consultas
from modelo.bench_memoria import medir_memoria
from modelo.bench_decisiones import medir_decisiones


class _SalidaDoble:
    def __init__(self, pantalla, archivo):
        self.pantalla, self.archivo = pantalla, archivo

    def write(self, texto):
        self.pantalla.write(texto)
        return self.archivo.write(texto)

    def flush(self):
        self.pantalla.flush()
        self.archivo.flush()


def ejecutar_cierre(rondas=1, semilla=2026, carpeta='documentacion/evidencia', decisiones=None):
    """Puede tardar varios minutos. No reutiliza mediciones antiguas como nuevas."""
    raiz = Path(carpeta)
    raiz.mkdir(parents=True, exist_ok=True)
    with (raiz / 'bench_linea_tiempo.txt').open('w', encoding='utf-8') as archivo:
        with redirect_stdout(_SalidaDoble(sys.stdout, archivo)):
            resultado = {
                'semilla': semilla, 'rondas': rondas,
                'consultas': medir_consultas(rondas=rondas, semilla=semilla),
                'memoria': medir_memoria(rondas=rondas, semilla=semilla),
                'persistencia': medir_persistencia(rondas=rondas, semilla=semilla),
                'decisiones': decisiones if decisiones is not None else medir_decisiones(rondas=rondas, semilla=semilla),
            }
    ruta = raiz / 'mediciones_linea_tiempo.json'
    # Publicar solo después de completar todas las mediciones.
    temporal = ruta.with_suffix('.json.tmp')
    temporal.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    temporal.replace(ruta)
    return resultado
