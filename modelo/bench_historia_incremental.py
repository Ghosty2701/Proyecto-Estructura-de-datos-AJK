"""Piloto optativo de historias: observar órdenes, conservar versiones y consultar.

Solo este arnés instala adaptadores en la instancia creada para medir. La
consola y los cargadores productivos conservan su capturador predeterminado.
"""
import gc
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter_ns
from types import ModuleType

from adaptadores.bench_persistencia import _paquete, _cargador, _ejecutar, _metadatos
from adaptadores.captura_incremental import CapturadorIncremental, PuntoIncremental
from adaptadores.frontera_incremental import FronteraIncremental
from adaptadores.estado_binario import codificar_punto
from controlador.controlador import ejecutar_accion_replay
from modelo.bench_linea_tiempo import _preparar, _indices, _consultas, _medir, _firma
from modelo.bench_presupuestos import _tiempos
from modelo.linea_tiempo import PuntoControl


def _firma_puntos(partida, cargador):
    digest = hashlib.sha256()
    identidad = cargador._identidad(partida)
    for punto in partida.linea_tiempo.puntos:
        creados = []
        try:
            copia, salas = punto.estado.reconstruir(creados=creados)
            datos = codificar_punto(copia.motor, copia.jugador, salas, identidad, {'partida': copia})
            digest.update(len(datos).to_bytes(8, 'little'))
            digest.update(datos)
        finally:
            # Como el gestor de consultas, retirar los ciclos temporales sin
            # conservar modelos reconstruidos durante la medición siguiente.
            for objeto in reversed(creados):
                if type(objeto) in (list, dict):
                    objeto.clear()
                elif hasattr(objeto, '__dict__'):
                    objeto.__dict__.clear()
    return digest.hexdigest()


def medir(acciones=5000, salas=300, cazadores=32, valores_k=(5, 10, 25),
          rondas=3, muestras=12, comparar=True, verificar_puntos=False):
    if (acciones < 3 or salas < 3 or cazadores < 0 or muestras < 6 or rondas < 1
            or not valores_k or any(type(k) is not int or k < 1 for k in valores_k)
            or not gc.isenabled()):
        raise ValueError('carga inválida o GC deshabilitado')
    escenarios = []
    referencias = None
    control_firma = control_meta = None
    # Para K=25, A B B A; el resto son exploraciones de K sin intercalación.
    orden = ([('completo', 25)] if comparar else [])
    orden += [('incremental', k) for k in valores_k]
    if comparar:
        orden += [('incremental', 25), ('completo', 25)]
    with tempfile.TemporaryDirectory(prefix='cripta-piloto-historia-') as temporal:
        base = Path(temporal)
        _paquete(base/'datos', salas, 2026, cazadores=cazadores)
        for numero, (tipo, k) in enumerate(orden):
            gc.collect()
            print(f'PILOTO {tipo} K={k}: {acciones} acciones', flush=True)
            cargador = _cargador(base/'datos', base/f'cache-{numero}')
            captura = CapturadorIncremental() if tipo == 'incremental' else None
            frontera = None
            ciclos, ordenes, copias, codificados, campos = [], [], [], [], []
            inicio_ms = 0

            def conectar(partida):
                nonlocal frontera, inicio_ms
                linea = partida.linea_tiempo
                original = linea.copiar
                if captura:
                    inicio = perf_counter_ns()
                    linea.puntos[0].estado = captura.capturar(
                        (partida, cargador.salas_ordenadas()), verificar=verificar_puntos)
                    inicio_ms = (perf_counter_ns()-inicio)/1e6
                    frontera = FronteraIncremental(captura, partida)
                    copia_original = cargador.copia_de_trabajo

                    def copia_de_trabajo(punto):
                        # Conversión incluida dentro de historia y su cronómetro.
                        if isinstance(punto.estado, PuntoIncremental):
                            punto = PuntoControl(punto.posicion, punto.acciones, punto.reloj,
                                                 punto.estado.a_inmutable(), punto.k)
                        return copia_original(punto)
                    cargador.copia_de_trabajo = copia_de_trabajo

                def copiar(raiz):
                    inicio = perf_counter_ns()
                    punto = (captura.capturar(raiz, verificar=verificar_puntos)
                             if captura else original(raiz))
                    copias.append((perf_counter_ns()-inicio)/1e6)
                    if captura:
                        codificados.append(captura.estadisticas['objetos_codificados'])
                        campos.append(captura.estadisticas['campos_leidos'])
                    return punto
                linea.copiar = copiar

            def ejecutar(partida, texto):
                antes = partida.acciones_ejecutadas
                inicio = perf_counter_ns()
                if captura:
                    frontera.ejecutar(lambda: ejecutar_accion_replay(partida, texto))
                    # Capturar después del finally del observador, no antes.
                    partida.registrar_orden(texto)
                else:
                    _ejecutar(partida, texto)
                ms = (perf_counter_ns()-inicio)/1e6
                ordenes.append(ms)
                if partida.acciones_ejecutadas > antes:
                    ciclos.append(ms)

            try:
                partida, capturas = _preparar(cargador, acciones, k, cazadores, 2026,
                    _indices(acciones, muestras), instrumentar=conectar, ejecutar=ejecutar)
                if captura:
                    captura.capturar((partida, cargador.salas_ordenadas()))  # oráculo final
                print(f'  validando bytes v6 de {len(partida.linea_tiempo.puntos)} puntos', flush=True)
                firma_puntos = _firma_puntos(partida, cargador)
                meta = _metadatos(partida.linea_tiempo)
                if k == 25 and comparar:
                    if control_firma is None:
                        control_firma, control_meta = firma_puntos, meta
                    assert firma_puntos == control_firma and meta == control_meta
                consultas = _consultas(_indices(acciones, muestras), capturas, partida.motor.reloj)
                firma = _firma(partida, cargador)
                medidas, obtenidos = _medir(partida, consultas, rondas, k, referencias)
                assert _firma(partida, cargador) == firma
                if referencias is None:
                    referencias = obtenidos
                assert partida.fuente.solicitudes_realizadas == 0
                bytes_vectores = bytes_pares = None
                if captura:
                    registro = captura._identidades
                    bytes_vectores = sys.getsizeof(registro.casillas)
                    inverso = getattr(registro, 'por_id', None)
                    bytes_pares = 0
                    if inverso is not None:
                        bytes_vectores += sys.getsizeof(inverso.casillas)
                        bytes_pares = sum(sys.getsizeof(e) for e in inverso.casillas if e)
                fila = {'tipo': tipo, 'k': k, 'inicio_incremental_ms': inicio_ms if captura else None,
                        'ciclos': _tiempos(ciclos, 20), 'ordenes_incluido_undo': _tiempos(ordenes, 20),
                        'capturas': _tiempos(copias, 20),
                        'consultas': _tiempos([m['tiempo_ms'] for m in medidas], 50),
                        'maximo_acciones_reaplicadas': max(m['acciones_reaplicadas'] for m in medidas),
                        'objetos_codificados_min_max': [min(codificados), max(codificados)] if codificados else None,
                        'campos_leidos_min_max': [min(campos), max(campos)] if campos else None,
                        'indices_finales': ({nombre: captura.estadisticas.get(nombre)
                            for nombre in ('registros_vivos', 'capacidad_version',
                                'capacidad_identidades', 'capacidad_inverso',
                                'reserva_identidades',
                                'tumbas_identidades', 'tumbas_inverso',
                                'recomposiciones_identidades', 'recomposiciones_inverso')}
                            if captura else None),
                        'bytes_superficiales_vectores_indices': bytes_vectores,
                        'bytes_superficiales_pares_inversos': bytes_pares,
                        'puntos': len(partida.linea_tiempo.puntos), 'sha256_bytes_v6_puntos': firma_puntos,
                        'partida_intacta': True, 'http': 0}
                escenarios.append(fila)
                print(f"  ciclos >=20: {fila['ciclos']['excedidos']}; consultas >=50: "
                      f"{fila['consultas']['excedidos']}", flush=True)
            finally:
                if captura:
                    captura.cerrar()
                # Romper los closures instalados exclusivamente en esta instancia.
                cargador.copia_de_trabajo = type(cargador).copia_de_trabajo.__get__(cargador)
            del partida, cargador, frontera, captura
            gc.collect()
    return {'acciones': acciones, 'salas': salas, 'cazadores': cazadores, 'semilla': 2026,
            'python': platform.python_version(), 'gc_habilitado': True,
            'oraculo_dentro_de_capturas': verificar_puntos, 'escenarios': escenarios,
            'alcance': 'Piloto sintético, sin activación productiva. Ciclos incluyen observar '
            'fronteras/deltas, registro y captura con retiro/GC. Consultas incluyen convertir '
            'IDs, copiar, replay y resumen. Verificación completa final y SHA256 de bytes '
            'v6 de TODOS los puntos fuera de cronómetros; entre variantes de K25 y consultas '
            'entre todos los escenarios. Sin RSS ni red ni renderizado. No elige K ni '
            'certifica referencia oficial; conserva todos los picos en estadísticas.'}


def comparar_indice(revision, acciones=5000, salas=300, cazadores=32, rondas=3, muestras=12):
    """Misma historia K25, antiguo/actual/actual/antiguo, todos los puntos v6."""
    codigo = subprocess.check_output(
        ['git', 'show', f'{revision}:adaptadores/captura_incremental.py'], encoding='utf-8')
    nombre = '_captura_indice_referencia'
    anterior = ModuleType(nombre)
    original = globals()['CapturadorIncremental']
    sys.modules[nombre] = anterior
    try:
        exec(compile(codigo, f'{revision}:captura_incremental.py', 'exec'), anterior.__dict__)
        # Mismo formato de versión: el adaptador de consultas debe reconocerlo.
        anterior.PuntoIncremental = PuntoIncremental
        escenarios = []
        firma = None
        for variante, clase in (('anterior', anterior.CapturadorIncremental),
                                ('inverso', original), ('inverso', original),
                                ('anterior', anterior.CapturadorIncremental)):
            globals()['CapturadorIncremental'] = clase
            resultado = medir(acciones=acciones, salas=salas, cazadores=cazadores,
                             valores_k=(25,), comparar=False, rondas=rondas, muestras=muestras)
            fila = resultado['escenarios'][0]
            fila['variante_indice'] = variante
            if firma is None:
                firma = fila['sha256_bytes_v6_puntos']
            assert fila['sha256_bytes_v6_puntos'] == firma
            escenarios.append(fila)
        resultado['escenarios'] = escenarios
        resultado['revision_referencia'] = revision
        resultado['orden'] = 'ABBA K25 contiguo, historias independientes'
        resultado['alcance'] += (' Comparación exclusiva de índices del piloto; '
                                 'no compara contra producción. Todos los puntos v6 '
                                 'coinciden entre las cuatro historias.')
        return resultado
    finally:
        globals()['CapturadorIncremental'] = original
        sys.modules.pop(nombre, None)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--acciones', type=int, default=5000)
    p.add_argument('--solo-k25', action='store_true')
    p.add_argument('--comparar-indice', help='revisión Git del piloto anterior, para ABBA K25')
    p.add_argument('--salida-json', required=True)
    args = p.parse_args()
    resultado = (comparar_indice(args.comparar_indice, acciones=args.acciones)
                 if args.comparar_indice else medir(acciones=args.acciones,
                     valores_k=(25,) if args.solo_k25 else (5, 10, 25)))
    Path(args.salida_json).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
