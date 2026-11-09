"""Conocimiento reversible; índices propios, separado de la información física."""
from modelo.tabla_hash import _mezclar, RegistroBusqueda


class IndiceSalas:
    def __init__(self, identificadores):
        self.capacidad = 2
        while len(identificadores) * 10 > self.capacidad * 7:
            self.capacidad *= 2
        self.claves = [None] * self.capacidad
        self.posiciones = [None] * self.capacidad
        self.sondeos = 0
        for posicion, clave in enumerate(identificadores):
            indice, encontrada = self._localizar(clave)
            if encontrada:
                raise ValueError('ID de sala duplicado')
            self.claves[indice], self.posiciones[indice] = clave, posicion

    def _inicio(self, clave):
        return _mezclar(clave) & (self.capacidad - 1)

    def _paso(self, clave):
        return (_mezclar(clave + 0x9e3779b97f4a7c15) & (self.capacidad - 1)) | 1

    def _localizar(self, clave):
        if type(clave) is not int:
            raise ValueError('El ID debe ser entero')
        indice, paso = self._inicio(clave), self._paso(clave)
        for _ in range(self.capacidad):
            self.sondeos += 1
            if self.claves[indice] is None:
                return indice, False
            if self.claves[indice] == clave:
                return indice, True
            indice = (indice + paso) & (self.capacidad - 1)
        raise ValueError('Indice de salas sin casilla libre')

    def obtener(self, clave):
        indice, encontrada = self._localizar(clave)
        return self.posiciones[indice] if encontrada else None


class RecuerdoPuerta:
    def __init__(self):
        self.observada = None

    @property
    def abierta(self):
        return self.observada is True


class SalaConocida:
    def __init__(self, sala, posicion):
        self.sala = sala
        self.sala_id = sala.sala_id
        self.posicion = posicion
        self.estado = 0  # desconocida=0, avistada=1, explorada=2
        self.nombre = None
        self.salidas = []


class SalidaConocida:
    def __init__(self, destino, puerta, costo, direccion):
        self.destino = destino
        self.puerta = puerta
        self.costo = costo
        self.direccion = direccion

    @property
    def abierta(self):
        return self.puerta.abierta and self.destino.estado == 2


class RegistrosViaje:
    def __init__(self, cantidad):
        self.datos = [None] * cantidad
        self.generacion = 0

    def iniciar(self):
        self.generacion += 1

    def obtener(self, sala):
        registro = self.datos[sala.posicion]
        if registro is None or registro.generacion != self.generacion:
            return None
        return registro

    def crear(self, sala, distancia, primero=None):
        registro = self.datos[sala.posicion]
        if registro is None:
            registro = RegistroBusqueda(sala, distancia, primero)
            self.datos[sala.posicion] = registro
        registro.distancia, registro.primer_salto = distancia, primero
        registro.definitivo, registro.posicion_heap = False, -1
        registro.generacion = self.generacion
        return registro


class ConocimientoMapa:
    def __init__(self, salas):
        self.salas = [SalaConocida(sala, i) for i, sala in enumerate(salas)]
        self.jugador = None
        for i, sala in enumerate(salas):
            sala.posicion_conocimiento = i
            for salida in sala.salidas:
                if salida.puerta.recuerdo is None:
                    salida.puerta.recuerdo = RecuerdoPuerta()
        self.reconstruir()

    def reconstruir(self):
        self.indice = IndiceSalas([s.sala_id for s in self.salas])
        self.registros = RegistrosViaje(len(self.salas))
        self.actualizaciones = 0

    def de_sala(self, sala):
        conocida = self.salas[sala.posicion_conocimiento]
        if conocida.sala is not sala:
            raise ValueError('Sala fuera del conocimiento de esta partida')
        return conocida

    def observar(self, sala, cambiar):
        conocida = self.de_sala(sala)
        self.actualizaciones += 1
        if conocida.estado != 2:
            cambiar(conocida, 'estado', 2)
            cambiar(conocida, 'nombre', sala.nombre)
            salidas = [SalidaConocida(self.de_sala(s.destino), s.puerta.recuerdo,
                                      s.costo, s.direccion) for s in sala.salidas]
            cambiar(conocida, 'salidas', salidas)
        for salida in sala.salidas:
            self.actualizaciones += 1
            destino = self.de_sala(salida.destino)
            if destino.estado == 0:
                cambiar(destino, 'estado', 1)
            cambiar(salida.puerta.recuerdo, 'observada', salida.abierta)

    def entrar(self, sala, antorcha, cambiar):
        self.observar(sala, cambiar)
        if antorcha:
            for salida in sala.salidas:
                self.observar(salida.destino, cambiar)

    def resolver(self, texto):
        if type(texto) is int or (type(texto) is str and texto.isdecimal()):
            posicion = self.indice.obtener(int(texto))
            if posicion is not None and self.salas[posicion].estado == 2:
                return self.salas[posicion]
        else:
            encontrada = None
            for sala in self.salas:
                if sala.estado == 2 and sala.nombre == texto:
                    if encontrada is not None:
                        raise ValueError('Nombre repetido; indica el ID de sala.')
                    encontrada = sala
            if encontrada is not None:
                return encontrada
        raise ValueError('El destino no es una sala explorada.')

    def ruta(self, origen, destino):
        from modelo.rutas import buscar_ruta_conocida
        return buscar_ruta_conocida(self, self.de_sala(origen), destino)

    def proyeccion(self):
        # Registros de presentación: no contienen referencias al mundo físico.
        return [(s.sala_id, s.estado, s.nombre,
                 [(e.direccion, e.destino.sala_id,
                   e.destino.nombre if e.destino.estado == 2 else None,
                   e.costo, e.puerta.observada) for e in s.salidas])
                for s in self.salas if s.estado != 0]
