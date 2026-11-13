"""PR-LT-005/008: medición histórica estándar con resultados nuevos."""
import json
import sys
import platform
from datetime import datetime, timezone
from contextlib import redirect_stdout
from pathlib import Path

from adaptadores.bench_persistencia import medir_persistencia
from modelo.bench_linea_tiempo import medir_consultas
from modelo.bench_memoria import medir_memoria
from modelo.bench_decisiones import medir_decisiones
from modelo.linea_tiempo import K_POR_DEFECTO


class _SalidaDoble:
    def __init__(self, pantalla, archivo):
        self.pantalla, self.archivo = pantalla, archivo

    def write(self, texto):
        self.pantalla.write(texto)
        return self.archivo.write(texto)

    def flush(self):
        self.pantalla.flush()
        self.archivo.flush()


def ejecutar_cierre(rondas=1, semilla=2026, carpeta='resultados/bench', decisiones=None):
    """Puede tardar varios minutos. No reutiliza mediciones antiguas como nuevas."""
    raiz = Path(carpeta)
    raiz.mkdir(parents=True, exist_ok=True)
    with (raiz / 'bench_linea_tiempo.txt').open('w', encoding='utf-8') as archivo:
        with redirect_stdout(_SalidaDoble(sys.stdout, archivo)):
            resultado = {
                'entorno': {'python': platform.python_version(), 'plataforma': platform.platform(),
                            'fecha_utc': datetime.now(timezone.utc).isoformat(),
                            'k_por_defecto': K_POR_DEFECTO},
                'semilla': semilla, 'rondas': rondas,
                'consultas': medir_consultas(rondas=rondas, semilla=semilla),
                'memoria': medir_memoria(rondas=rondas, semilla=semilla),
                'persistencia': medir_persistencia(rondas=rondas, semilla=semilla),
                'decisiones': decisiones if decisiones is not None else medir_decisiones(rondas=rondas, semilla=semilla),
            }
    ruta = raiz / 'mediciones_linea_tiempo.json'
    # Publicar solo después de completar todas las mediciones.
    temporal = ruta.with_suffix('.json.tmp')
    from adaptadores.resumen_mediciones import resumir_mediciones
    temporal.write_text(json.dumps(resumir_mediciones(resultado), ensure_ascii=False, indent=2), encoding='utf-8')
    temporal.replace(ruta)
    print(f'Resultados de línea de tiempo: {ruta}')
    return resultado
