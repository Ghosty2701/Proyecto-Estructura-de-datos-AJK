"""PR-RS-001/002/003: mediciones locales, sin vista ni HTTP dentro del reloj."""
import hashlib
import platform
import random
import sys
from pathlib import Path
from time import perf_counter_ns
from modelo.verificacion import normalizar, cerrar, resultado_de_cierre, _diagnosticar


def _datos(cantidad, llave, salida):
    return ({'id': 'sintetica-bench', 'version': 'sintetica-1',
             'sala_inicial': 1, 'sala_salida': salida, 'llave_salida': llave},
            [{'id': i + 1, 'nombre': str(i + 1), 'salidas': {}}
             for i in range(cantidad)], {'llaves': []})


def _conectar(salas, a, b, ida, vuelta, llave, costo):
    salas[a - 1]['salidas'][ida] = {'sala': b, 'cerrada': llave is not None,
                                   'llave': llave, 'costo': costo}
    salas[b - 1]['salidas'][vuelta] = {'sala': a, 'cerrada': llave is not None,
                                     'llave': llave, 'costo': costo}


def generar_cadena(cantidad, semilla):
    azar = random.Random(semilla)
    general, salas, ubicaciones = _datos(cantidad, f'k{cantidad-2}', cantidad)
    for i in range(1, cantidad):
        llave = f'k{i-1}'
        _conectar(salas, i, i + 1, 'E', 'O', llave, azar.randrange(1, 400))
        ubicaciones['llaves'].append({'id': llave, 'sala': i})
    return general, salas, ubicaciones


def generar_grupos(cantidad, semilla):
    azar = random.Random(semilla)
    general, salas, ubicaciones = _datos(2 * cantidad + 1, 'k0', cantidad + 2)
    for i in range(1, cantidad + 1):
        _conectar(salas, i, i + 1, 'N', 'S', None, 100)
        hoja = cantidad + 1 + i
        llave = f'k{i-1}'
        _conectar(salas, i, hoja, 'E', 'O', llave, azar.randrange(1, 400))
        ubicaciones['llaves'].append({'id': llave, 'sala': hoja})
    return general, salas, ubicaciones


def generar_alternativas(cantidad, semilla):
    general, salas, llaves = generar_grupos(cantidad, semilla)
    # Cada región bloqueada admite A O B y contiene ambas llaves.
    for i in range(1, cantidad + 1):
        hoja = cantidad + 1 + i
        llave = f'alternativa{i}'
        _conectar(salas, i, hoja, 'O', 'N', llave, 100)
        llaves['llaves'].append({'id': llave, 'sala': hoja})
        llaves['llaves'].append({'id': llave, 'sala': hoja})
    return general, salas, llaves


def referencia(mapa):
    """Alternativa deliberadamente repetida, solo para validación/bench."""
    obtenidas = [False] * len(mapa.llaves)
    operaciones = 0
    while True:
        alcanzadas, cola = [False] * len(mapa.salas), [mapa.inicial]
        alcanzadas[mapa.inicial] = True
        cursor = 0
        while cursor < len(cola):
            posicion = cola[cursor]
            cursor += 1
            operaciones += 1
            for salida in mapa.salas[posicion].salidas:
                operaciones += 1
                if (not salida.cerrada or
                        (salida.llave >= 0 and obtenidas[salida.llave])):
                    if not alcanzadas[salida.destino]:
                        alcanzadas[salida.destino] = True
                        cola.append(salida.destino)
        cambio = False
        for posicion, sala in enumerate(mapa.salas):
            operaciones += 1
            if alcanzadas[posicion]:
                for k in sala.llaves:
                    operaciones += 1
                    if not obtenidas[k]:
                        obtenidas[k], cambio = True, True
        if not cambio:
            break
    gana = obtenidas[mapa.llave_salida] and any(
        alcanzadas[i] and salida.destino == mapa.salida and salida.llave == mapa.llave_salida
        and (not salida.cerrada or obtenidas[salida.llave])
        for i, sala in enumerate(mapa.salas) for salida in sala.salidas)
    return gana, operaciones


def medir_entrada(general, salas, llaves, repeticiones=5, formatear=None):
    muestras = []
    for _ in range(repeticiones):
        inicio = perf_counter_ns()
        mapa = normalizar(general, salas, llaves)
        preparado = perf_counter_ns()
        cierre = cerrar(mapa)
        cerrado = perf_counter_ns()
        resultado = resultado_de_cierre(mapa, cierre)
        reportado = perf_counter_ns()
        if not resultado.resoluble:
            _diagnosticar(resultado)
        diagnosticado = perf_counter_ns()
        if formatear is not None:
            formatear(resultado)  # Construir texto, sin imprimirlo en la región medida.
        fin = perf_counter_ns()
        referencia_inicio = perf_counter_ns()
        esperado, operaciones = referencia(mapa)
        referencia_fin = perf_counter_ns()
        if esperado != resultado.resoluble:
            raise RuntimeError('Referencia e incremental difieren')
        muestras.append({'preparacion_ms': (preparado - inicio) / 1e6,
                         'cierre_ms': (cerrado - preparado) / 1e6,
                         'resultado_ms': (reportado - cerrado) / 1e6,
                         'diagnostico_ms': (diagnosticado - reportado) / 1e6,
                         'texto_ms': (fin - diagnosticado) / 1e6,
                         'total_ms': (fin - inicio) / 1e6,
                         'referencia_cierre_ms': (referencia_fin - referencia_inicio) / 1e6,
                         'operaciones_incremental': cierre.operaciones,
                         'operaciones_referencia': operaciones})
    return {'id_cripta': mapa.id_cripta, 'version': mapa.version,
            'salas': len(mapa.salas), 'salidas': sum(len(s.salidas) for s in mapa.salas),
            'llaves': len(mapa.llaves), 'ubicaciones': len(llaves['llaves']),
            'resoluble': resultado.resoluble, 'grupos': len(resultado.certificados),
            'sondeos': mapa.indice.sondeos + mapa.indice_llaves.sondeos,
            'texto_incluido': formatear is not None, 'coinciden': True,
            'muestras': muestras, 'maximo_ms': max(m['total_ms'] for m in muestras),
            'minimo_ms': min(m['total_ms'] for m in muestras),
            'excedidos_200ms': sum(m['total_ms'] >= 200 for m in muestras)}


def entorno():
    raiz = Path(__file__).resolve().parents[1]
    rutas = ('modelo/verificacion.py', 'modelo/indice_llaves.py', 'modelo/conocimiento.py',
             'modelo/tabla_hash.py', 'modelo/bench_resolubilidad.py', 'modelo/bench_modelo.py',
             'adaptadores/servicio_cripta.py', 'adaptadores/cliente_http.py',
             'adaptadores/modo_offline.py', 'controlador/cargar_partida.py', 'main.py')
    return {'python': sys.version, 'plataforma': platform.platform(),
            'procesador': platform.processor(),
            'fuentes': [{'ruta': ruta, 'sha256': hashlib.sha256((raiz / ruta).read_bytes()).hexdigest()}
                        for ruta in rutas]}


def medir_resolubilidad(repeticiones=5, semilla=2026, formatear=None):
    resultados = []
    for cantidad in (40, 160, 640):
        entrada = generar_cadena(cantidad, semilla)
        resultado = medir_entrada(*entrada, repeticiones, formatear)
        resultado['escenario'] = 'cadena'
        resultados.append(resultado)
    for generador, nombre in ((generar_grupos, 'grupos'),
                              (generar_alternativas, 'alternativas')):
        for cantidad in (20, 80, 320):
            resultado = medir_entrada(*generador(cantidad, semilla), repeticiones, formatear)
            resultado['escenario'] = nombre
            resultados.append(resultado)
    for fila in resultados:
        print(f"RESOLUBILIDAD {fila['escenario']}: {fila['salas']} salas, "
              f"{fila['llaves']} llaves; total máximo {fila['maximo_ms']:.4f} ms; "
              f"cierre repetido máximo {max(m['referencia_cierre_ms'] for m in fila['muestras']):.4f} ms.")
    return {'semilla': semilla, 'repeticiones': repeticiones, 'entorno': entorno(),
            'sinteticos': resultados,
            'nota': 'Referencia compara cierre/veredicto; no genera certificados. '
                    'El total incremental incluye preparación y diagnóstico, y texto si se indica.'}
