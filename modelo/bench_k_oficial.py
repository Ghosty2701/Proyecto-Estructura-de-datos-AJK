"""K oficiales en procesos separados; observador opcional de memoria con psutil.

psutil solo se usa en este ejecutor de mediciones, no en el juego. La consulta
corre sin tracemalloc ni perfilador. Los archivos intermedios son temporales.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def medir(valores_k=(5, 10, 25)):
    import psutil

    if not valores_k or any(type(k) is not int or k < 1 for k in valores_k):
        raise ValueError('K positivos')
    filas = []
    with tempfile.TemporaryDirectory(prefix='cripta-k-oficial-') as temporal:
        carpeta = Path(temporal)
        for k in valores_k:
            print(f'OFICIAL + MEMORIA: K={k}, 5000 acciones, proceso independiente', flush=True)
            salida, registro = carpeta/f'k-{k}.json', carpeta/f'k-{k}.log'
            comando = [sys.executable, '-X', 'utf8', '-u', '-m', 'adaptadores.bench_adaptadores',
                       '--solo', 'consultas', '--cripta', 'cripta-06', '--acciones', '5000',
                       '--rondas', '3', '--muestras', '12', '--semilla', '2026',
                       '--checkpoint-cada', str(k), '--salida-json', str(salida)]
            pico = 0
            with registro.open('w', encoding='utf-8') as log:
                proceso = subprocess.Popen(comando, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                observador = psutil.Process(proceso.pid)
                while proceso.poll() is None:
                    try:
                        memoria = observador.memory_info()
                        pico = max(pico, getattr(memoria, 'peak_wset', memoria.rss))
                    except psutil.NoSuchProcess:
                        break
                    time.sleep(0.1)
                codigo = proceso.wait()
            print(registro.read_text(encoding='utf-8'), flush=True)
            if codigo != 0:
                raise RuntimeError(f'benchmark K={k} termino con codigo {codigo}')
            fila = json.loads(salida.read_text(encoding='utf-8'))
            fila['pico_residente_observado_bytes'] = pico
            filas.append(fila)
            print(f'  pico residente observado: {pico / 2**20:.2f} MiB', flush=True)
    # No comparar K sobre versiones externas diferentes sin declararlo.
    identidad = [(f['version_cripta'], f['version_catalogo']) for f in filas]
    if any(i != identidad[0] for i in identidad):
        raise RuntimeError('las versiones del servicio cambiaron entre K')
    return {'escenarios': filas, 'psutil_observador': psutil.__version__,
            'intervalo_observador_s': 0.1,
            'alcance_memoria': 'Pico residente del proceso completo, observado desde otro proceso; '
                              'Windows informa peak_wset; otros sistemas maximo RSS muestreado. '
                              'Incluye Python, HTTP, cache, partida e historia; no memoria solo '
                              'de puntos ni memoria virtual/commit. No cambia K del juego.'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--valores-k', type=int, nargs='+', default=[5, 10, 25])
    parser.add_argument('--salida-json', required=True)
    args = parser.parse_args()
    Path(args.salida_json).write_text(json.dumps(medir(args.valores_k), ensure_ascii=False, indent=2),
                                     encoding='utf-8')
