"""Prototipo aislado de D-LT-04: plantilla compartida y estado mutable separado.

No se conecta a partidas ni cambia el formato 6. Solo se comparte una tupla
de metadatos escalares y enlaces por posición; ningún nodo mutable vivo.
"""
from dataclasses import dataclass

from adaptadores.copia_estado import TablaIdentidades, copiar_estado
from modelo.rastro import SalaRastro, SalidaRastro, Puerta
from modelo.conocimiento import SalaConocida, RecuerdoPuerta

# tipo, metadatos, enlaces, campos mutables. El costo puede cambiar: se copia.
_TIPOS = (
    (SalaRastro, ('sala_id', 'nombre'), ('salidas',),
     ('ultimo_rastro', 'enemigos', 'trampas', 'contenido_cargado', 'objetos_suelo', 'posicion_conocimiento')),
    (SalidaRastro, ('direccion',), ('destino', 'puerta'), ('costo',)),
    (Puerta, ('llave', 'cierre_automatico'), ('recuerdo',), ('abierta', 'abierta_con_llave')),
    (RecuerdoPuerta, (), (), ('observada',)),
    (SalaConocida, ('sala_id', 'posicion'), ('sala',), ('estado', 'nombre', 'salidas')),
)
_AUSENTE = ('campo-ausente',)


def _tipo(objeto):
    for i, datos in enumerate(_TIPOS):
        if type(objeto) is datos[0]:
            return i
    raise TypeError('nodo sin esquema de plantilla')


@dataclass(frozen=True, slots=True)
class PuntoCompartido:
    plantilla: tuple
    tokens: tuple
    _datos: tuple

    def reconstruir(self, referencias=None):
        nodos = [_TIPOS[tipo][0].__new__(_TIPOS[tipo][0]) for tipo, _, _ in self.plantilla]
        for nodo, (_, metadatos, enlaces) in zip(nodos, self.plantilla):
            for nombre, valor in metadatos:
                setattr(nodo, nombre, valor)
            for nombre, lista, destinos in enlaces:
                valor = [nodos[i] for i in destinos] if lista else (
                    None if destinos is None else nodos[destinos])
                setattr(nodo, nombre, valor)
        raiz, registros = copiar_estado(self._datos, referencias, sustituciones=zip(self.tokens, nodos),
                                         reconstruir=False, capacidad=4 * len(nodos))
        for nodo, campos, (tipo, _, _) in zip(nodos, registros, self.plantilla):
            for nombre, valor in zip(_TIPOS[tipo][3], campos):
                if valor is not _AUSENTE:
                    setattr(nodo, nombre, valor)
        partida, salas = raiz
        if partida.motor.conocimiento is not None:
            partida.motor.conocimiento.reconstruir()
        return partida, salas


class ContextoCompartido:
    """Solo el capturador retiene nodos vivos, nunca la plantilla compartida."""
    def __init__(self, partida, salas):
        self.nodos = []
        self.indice = TablaIdentidades()

        def agregar(nodo):
            if nodo is not None and self.indice.buscar(nodo) is None:
                self.indice.insertar(nodo, len(self.nodos))
                self.nodos.append(nodo)

        for sala in salas:
            agregar(sala)
            for salida in sala.salidas:
                agregar(salida)
                agregar(salida.puerta)
                agregar(salida.puerta.recuerdo)
        if partida.motor.conocimiento is not None:
            for conocida in partida.motor.conocimiento.salas:
                agregar(conocida)
        self.salas = salas
        self.tokens = tuple(('nodo-compartido', i) for i in range(len(self.nodos)))
        self.plantilla = self._plantilla()
        self.tipos = tuple(fila[0] for fila in self.plantilla)

    def _validar(self):
        # Comparación directa con las identidades ya registradas, sin construir
        # otra plantilla ni volver a buscar cada enlace en la tabla hash.
        for nodo, (_, metadatos, enlaces) in zip(self.nodos, self.plantilla):
            for nombre, esperado in metadatos:
                actual = getattr(nodo, nombre)
                if type(actual) is not type(esperado) or actual != esperado:
                    raise ValueError('cambio de plantilla')
            for nombre, lista, destinos in enlaces:
                actual = getattr(nodo, nombre)
                if lista:
                    if (type(actual) is not list or len(actual) != len(destinos)
                            or any(v is not self.nodos[i] for v, i in zip(actual, destinos))):
                        raise ValueError('cambio de plantilla')
                elif actual is not (None if destinos is None else self.nodos[destinos]):
                    raise ValueError('cambio de plantilla')

    def _plantilla(self):
        filas = []
        for nodo in self.nodos:
            tipo = _tipo(nodo)
            metadatos = tuple((n, getattr(nodo, n)) for n in _TIPOS[tipo][1])
            if any(type(v) not in (type(None), bool, int, float, str) for _, v in metadatos):
                raise TypeError('metadato mutable en plantilla')
            enlaces = []
            for nombre in _TIPOS[tipo][2]:
                valor = getattr(nodo, nombre)
                if type(valor) is list:
                    destino = tuple(self.indice.buscar(v) for v in valor)
                    if any(i is None for i in destino):
                        raise ValueError('plantilla con destino desconocido')
                    enlaces.append((nombre, True, destino))
                else:
                    destino = None if valor is None else self.indice.buscar(valor)
                    if valor is not None and destino is None:
                        raise ValueError('plantilla con destino desconocido')
                    enlaces.append((nombre, False, destino))
            filas.append((tipo, metadatos, tuple(enlaces)))
        return tuple(filas)

    def capturar(self, partida):
        self._validar()
        # Los nombres de campo ya están en el esquema compartido. Repetir pares
        # (nombre, valor) por captura anulaba el ahorro de memoria del prototipo.
        registros = tuple(tuple(getattr(nodo, n, _AUSENTE) for n in _TIPOS[tipo][3])
                          for nodo, tipo in zip(self.nodos, self.tipos))
        datos = copiar_estado(((partida, self.salas), registros),
                               sustituciones=zip(self.nodos, self.tokens), reconstruir=False,
                               capacidad=4 * len(self.nodos))
        return PuntoCompartido(self.plantilla, self.tokens, datos)


def medir_prototipo(repeticiones=20, acciones=500, cantidad_salas=300, cazadores=32):
    """Ensayo exploratorio; aun no es aceptacion con 5 000 acciones ni replay."""
    import gc
    import json
    import tempfile
    import tracemalloc
    from pathlib import Path
    from dataclasses import replace
    from adaptadores.bench_persistencia import _paquete, _cargador, _cronometrar
    from modelo.bench_linea_tiempo import _preparar, estadisticas

    with tempfile.TemporaryDirectory() as temporal:
        p = Path(temporal)
        _paquete(p/'datos', cantidad_salas, 2026, cazadores=cazadores)
        cargador = _cargador(p/'datos', p/'cache')
        partida, _ = _preparar(cargador, acciones, 25, cazadores, 2026, [1])
        salas = cargador.salas_ordenadas()
        raiz = (partida, salas)
        contexto = ContextoCompartido(partida, salas)
        punto = contexto.capturar(partida)
        resultados = {'normal': [], 'captura_compartida': [], 'restauracion_compartida': []}
        for i in range(repeticiones):
            operaciones = [('normal', lambda: copiar_estado(raiz)),
                           ('captura_compartida', lambda: contexto.capturar(partida)),
                           ('restauracion_compartida', punto.reconstruir)]
            for j in range(3):
                nombre, operar = operaciones[(j+i)%3]
                copia, tiempo = _cronometrar(operar)
                resultados[nombre].append(tiempo)
                if nombre != 'captura_compartida':
                    assert copia[0].resumen_historico('') == partida.resumen_historico('')
                    assert copia[0].motor.azar.getstate() == partida.motor.azar.getstate()
                del copia
        memoria = {}
        for modo in ('normal', 'compartido'):
            gc.collect()
            tracemalloc.start()
            try:
                ctx = ContextoCompartido(partida, salas) if modo == 'compartido' else None
                puntos = [ctx.capturar(partida) if ctx else copiar_estado(raiz)
                          for _ in range(repeticiones)]
                gc.collect()
                retenida, pico = tracemalloc.get_traced_memory()
                memoria[modo] = {'retenida_bytes': retenida, 'pico_bytes': pico}
            finally:
                tracemalloc.stop()
            del puntos, ctx
            gc.collect()
        return {'semilla': 2026, 'acciones': acciones, 'salas': cantidad_salas,
                'cazadores': cazadores, 'repeticiones': repeticiones,
                'tiempos': {n: estadisticas(t) for n, t in resultados.items()},
                'muestras_ms': resultados, 'memoria': memoria, 'equivalentes': True,
                'alcance': 'Prototipo sin integracion en checkpoints/replay/guardado; '
                           'no elige K. Memoria incremental de capturas de un mismo estado; '
                           'incluye una plantilla nueva en modo compartido. No RSS. '
                           'Tiempos rotados, GC habilitado, sin trazado; no certifica limites.'}


def medir_historia_compartida(acciones=5000):
    """Comparación experimental de historia completa; no modifica el cargador del juego."""
    import gc
    import tempfile
    from pathlib import Path
    from adaptadores.bench_persistencia import _paquete, _cargador
    from modelo.bench_linea_tiempo import _preparar, _indices, _consultas, _medir, estadisticas, _firma
    from controlador.cargar_partida import PreparadorConsulta, _GestorConsulta, _FichasConsulta

    filas = []
    referencias = None
    with tempfile.TemporaryDirectory() as temporal:
        p = Path(temporal)
        _paquete(p/'datos', 300, 2026, cazadores=32)
        for modo in ('normal', 'compartido'):
            c = _cargador(p/'datos', p/modo)

            def conectar(partida):
                contexto = ContextoCompartido(partida, c.salas_ordenadas())
                linea = partida.linea_tiempo
                linea.copiar = lambda raiz: contexto.capturar(raiz[0])
                linea.puntos[0].estado = contexto.capturar(partida)

                def copia_de_trabajo(punto):
                    refs = []
                    copia, _ = punto.estado.reconstruir(refs)
                    fichas = _FichasConsulta(c.servicio.cache)
                    for ref in refs:
                        if ref.datos is None:
                            ref.datos = fichas.ficha(ref.id_ficha)
                    copia.preparar_sala = PreparadorConsulta(c.servicio, copia).preparar_sala
                    copia.gestor_guardado = _GestorConsulta()
                    return copia

                c.copia_de_trabajo = copia_de_trabajo

            a, capturas = _preparar(c, acciones, 25, 32, 2026, _indices(acciones, 12),
                                    instrumentar=conectar if modo == 'compartido' else None)
            consultas = _consultas(_indices(acciones, 12), capturas, a.motor.reloj)
            firma = _firma(a, c)
            muestras, resumenes = _medir(a, consultas, 3, 25, referencias)
            assert _firma(a, c) == firma
            if referencias is None:
                referencias = resumenes
            filas.append({'modo': modo, 'puntos': len(a.linea_tiempo.puntos),
                          'estadisticas': estadisticas([m['tiempo_ms'] for m in muestras]),
                          'muestras': muestras, 'equivalentes': True, 'partida_intacta': True})
            # Evitar conservar el contexto de un modo al ejecutar el siguiente.
            del a, c, capturas
            gc.collect()
    return {'acciones': acciones, 'salas': 300, 'cazadores': 32, 'k': 25,
            'semilla': 2026, 'escenarios': filas,
            'alcance': 'Historia sintetica experimental con puntos compartidos; '
                       'no modifica CLI de juego ni formato 6. Sin validar guardado/replay. '
                       'Comparacion contra capturas en vivo y modo normal; sin HTTP ni vista.'}


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Medir prototipo de plantilla compartida')
    parser.add_argument('--salida-json', required=True)
    parser.add_argument('--historia', action='store_true')
    parser.add_argument('--acciones', type=int, default=5000)
    args = parser.parse_args()
    if args.acciones < 3:
        parser.error('--acciones debe ser >=3')
    datos = medir_historia_compartida(args.acciones) if args.historia else medir_prototipo()
    from adaptadores.resumen_mediciones import resumir_mediciones
    Path(args.salida_json).write_text(json.dumps(resumir_mediciones(datos), ensure_ascii=False, indent=2), encoding='utf-8')
    if args.historia:
        for fila in datos['escenarios']:
            print(fila['modo'], fila['estadisticas'])
    else:
        print(json.dumps(datos['tiempos'], ensure_ascii=False, indent=2))
        print(json.dumps(datos['memoria'], indent=2))
