
import json
import os

class ErrorCatalogo(Exception):
    # Una ficha pedida no llego en la respuesta del catalogo.
    pass


class ReferenciaFicha:
    """Identidad compartida; los datos solo existen mientras la ficha esta residente."""

    def __init__(self, id_ficha, datos=None):
        self.id_ficha = id_ficha
        self.datos = datos

    def _datos(self):
        if self.datos is None:
            raise ErrorCatalogo(f"La ficha {self.id_ficha} no esta en memoria; debe recuperarse desde el adaptador")
        return self.datos

    def __getitem__(self, clave):
        return self.id_ficha if clave == "id" else self._datos()[clave]

    def get(self, clave, defecto=None):
        return self.id_ficha if clave == "id" else self._datos().get(clave, defecto)

    def __contains__(self, clave):
        return clave == "id" or clave in self._datos()

class NodoLRU:
    # Un nodo guarda una ficha y sus dos vecinos en la lista.
    def __init__(self, id_ficha, ficha):
        self.id_ficha = id_ficha
        self.ficha = ficha
        self.anterior = None    # vecino mas reciente (hacia el frente)
        self.siguiente = None   # vecino mas antiguo (hacia el final)


class ListaLRU:
    # El frente es la ficha usada mas recientemente; el final, la menos reciente.
    def __init__(self):
        self.frente = None
        self.final = None
        self.cantidad = 0

    def agregar_al_frente(self, nodo):
        nodo.anterior = None
        nodo.siguiente = self.frente
        if self.frente is not None:
            self.frente.anterior = nodo
        else:
            # La lista estaba vacia: el nodo es a la vez frente y final.
            self.final = nodo
        self.frente = nodo
        self.cantidad += 1

    def quitar(self, nodo):
        # Los vecinos se enlazan entre si para "saltarse" al nodo.
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.frente = nodo.siguiente

        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.final = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = None
        self.cantidad -= 1

    def mover_al_frente(self, nodo):
        # Se llama en cada acierto: la ficha pasa a ser la mas reciente.
        if nodo is self.frente:
            return
        self.quitar(nodo)
        self.agregar_al_frente(nodo)

class NodoArbol:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1


def _altura(nodo):
    if nodo is None:
        return 0
    return nodo.altura


def _actualizar_altura(nodo):
    nodo.altura = 1 + max(_altura(nodo.izquierdo), _altura(nodo.derecho))


def _balance(nodo):
    # Positivo: pesa mas el lado izquierdo. Negativo: pesa mas el derecho.
    return _altura(nodo.izquierdo) - _altura(nodo.derecho)


def _rotar_derecha(nodo):
    # El hijo izquierdo sube y el nodo actual baja a su derecha.
    hijo = nodo.izquierdo
    nodo.izquierdo = hijo.derecho
    hijo.derecho = nodo
    _actualizar_altura(nodo)
    _actualizar_altura(hijo)
    return hijo


def _rotar_izquierda(nodo):
    # El hijo derecho sube y el nodo actual baja a su izquierda.
    hijo = nodo.derecho
    nodo.derecho = hijo.izquierdo
    hijo.izquierdo = nodo
    _actualizar_altura(nodo)
    _actualizar_altura(hijo)
    return hijo


def _equilibrar(nodo):
    # Devuelve la raiz del subarbol ya equilibrado.
    _actualizar_altura(nodo)
    balance = _balance(nodo)

    if balance > 1:
        if _balance(nodo.izquierdo) < 0:
            nodo.izquierdo = _rotar_izquierda(nodo.izquierdo)
        return _rotar_derecha(nodo)

    if balance < -1:
        if _balance(nodo.derecho) > 0:
            nodo.derecho = _rotar_derecha(nodo.derecho)
        return _rotar_izquierda(nodo)

    return nodo


class ArbolAVL:
    def __init__(self):
        self.raiz = None
        self.cantidad = 0

    def buscar(self, clave):
        # Devuelve el valor de la clave, o None si no esta.
        nodo = self.raiz
        while nodo is not None:
            if clave == nodo.clave:
                return nodo.valor
            if clave < nodo.clave:
                nodo = nodo.izquierdo
            else:
                nodo = nodo.derecho
        return None

    def insertar(self, clave, valor):
        self.raiz = self._insertar(self.raiz, clave, valor)

    def _insertar(self, nodo, clave, valor):
        if nodo is None:
            self.cantidad += 1
            return NodoArbol(clave, valor)

        if clave < nodo.clave:
            nodo.izquierdo = self._insertar(nodo.izquierdo, clave, valor)
        elif clave > nodo.clave:
            nodo.derecho = self._insertar(nodo.derecho, clave, valor)
        else:
            # La clave ya existia: solo se cambia su valor.
            nodo.valor = valor
            return nodo

        return _equilibrar(nodo)

    def quitar(self, clave):
        self.raiz = self._quitar(self.raiz, clave)

    def _quitar(self, nodo, clave):
        if nodo is None:
            return None

        if clave < nodo.clave:
            nodo.izquierdo = self._quitar(nodo.izquierdo, clave)
        elif clave > nodo.clave:
            nodo.derecho = self._quitar(nodo.derecho, clave)
        else:
            # Este es el nodo a quitar. Con 0 o 1 hijo, el hijo (si hay) ocupa su lugar.
            if nodo.izquierdo is None:
                self.cantidad -= 1
                return nodo.derecho
            if nodo.derecho is None:
                self.cantidad -= 1
                return nodo.izquierdo

            # Con 2 hijos: se copia el sucesor (el menor del lado derecho) y se quita el sucesor.
            sucesor = nodo.derecho
            while sucesor.izquierdo is not None:
                sucesor = sucesor.izquierdo
            nodo.clave = sucesor.clave
            nodo.valor = sucesor.valor
            nodo.derecho = self._quitar(nodo.derecho, sucesor.clave)

        return _equilibrar(nodo)


class CacheCatalogo:
    def __init__(self, fuente, carpeta="cache_catalogo", tope=25, esta_en_uso=None):
        self.fuente = fuente
        self.carpeta = carpeta
        self.tope = tope
        self.esta_en_uso = esta_en_uso
        self.arbol = ArbolAVL()     # id -> NodoLRU
        self.referencias = ArbolAVL()  # id -> referencia ligera, incluso sin datos residentes
        self.lista = ListaLRU()
        self.version = None         # version del catalogo; se lee la primera vez que hace falta
        self.aciertos = 0           # la ficha estaba en memoria
        self.fallos = 0             # la ficha no estaba en memoria (salio de disco o de red)
        self.lecturas_disco = 0     # fallos resueltos leyendo el disco

    # --- Consulta ---

    def referencia(self, id_ficha):
        referencia = self.referencias.buscar(id_ficha)
        if referencia is None:
            referencia = ReferenciaFicha(id_ficha)
            self.referencias.insertar(id_ficha, referencia)
        nodo = self.arbol.buscar(id_ficha)
        referencia.datos = nodo.ficha if nodo is not None else None
        return referencia

    def faltantes(self, ids):
        """IDs sin ficha valida en memoria ni disco; no descarga fichas.

        La primera consulta valida la version del catalogo con el contrato
        existente. Las recuperaciones de disco se incorporan a la misma LRU.
        """
        if not ids:
            return []
        self._asegurar_version()
        resultado = []
        for id_ficha in ids:
            if self.arbol.buscar(id_ficha) is not None:
                continue
            ficha = self._leer_de_disco(id_ficha)
            if ficha is not None:
                self._insertar_en_memoria(id_ficha, ficha)
            elif id_ficha not in resultado:
                resultado.append(id_ficha)
        return resultado

    def obtener(self, id_ficha):
        return self.obtener_varias([id_ficha])[0]

    def obtener_varias(self, ids):
        # Devuelve las fichas en el mismo orden de ids. Lo que falta se pide por lotes de 10.
        self._asegurar_version()

        fichas = []      # resultado; None marca las fichas que faltan pedir a la red
        faltantes = []   # ids que no estan ni en memoria ni en disco, sin repetir

        for id_ficha in ids:
            if id_ficha in faltantes:
                fichas.append(None)
                continue

            ficha = self._buscar_en_memoria(id_ficha)
            if ficha is None:
                ficha = self._leer_de_disco(id_ficha)
                if ficha is not None:
                    self._insertar_en_memoria(id_ficha, ficha)
            if ficha is None:
                faltantes.append(id_ficha)
            fichas.append(ficha)

        recibidas = self._pedir_a_la_red(faltantes)

        # Se completan los huecos con lo recibido. Se usa "recibidas" y no la cache porque
        # al insertar una ficha nueva otra pudo haberse liberado.
        for posicion in range(len(ids)):
            if fichas[posicion] is None:
                fichas[posicion] = self._buscar_en_recibidas(recibidas, ids[posicion])
        return fichas

    # --- Memoria ---

    def _buscar_en_memoria(self, id_ficha):
        nodo = self.arbol.buscar(id_ficha)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self.lista.mover_al_frente(nodo)
        return nodo.ficha

    def _insertar_en_memoria(self, id_ficha, ficha):
        existente = self.arbol.buscar(id_ficha)
        if existente is not None:
            existente.ficha = ficha
            self.lista.mover_al_frente(existente)
            referencia = self.referencias.buscar(id_ficha)
            if referencia is not None:
                referencia.datos = ficha
            return
        # Se libera hasta que quede espacio. Si todas las fichas estan en uso no hay a quien
        # liberar y se supera el tope temporalmente: el enunciado prohibe liberar fichas en uso.
        while self.lista.cantidad >= self.tope:
            candidato = self._buscar_candidato()
            if candidato is None:
                break
            self.arbol.quitar(candidato.id_ficha)
            self.lista.quitar(candidato)
            referencia = self.referencias.buscar(candidato.id_ficha)
            if referencia is not None:
                referencia.datos = None
            candidato.ficha = None

        nodo = NodoLRU(id_ficha, ficha)
        self.arbol.insertar(id_ficha, nodo)
        self.lista.agregar_al_frente(nodo)
        referencia = self.referencias.buscar(id_ficha)
        if referencia is not None:
            referencia.datos = ficha

    def _buscar_candidato(self):
        # Recorre desde la ficha menos reciente hacia la mas reciente y devuelve el
        # primer nodo que el modelo no esta usando. Si todas estan en uso, devuelve None.
        nodo = self.lista.final
        while nodo is not None:
            if not self._en_uso(nodo.id_ficha):
                return nodo
            nodo = nodo.anterior
        return None

    def _en_uso(self, id_ficha):
        if self.esta_en_uso is None:
            return False
        return self.esta_en_uso(id_ficha)

    # --- Disco ---
    # Cada ficha vive en <carpeta>/<version del catalogo>/<id>.json. Si la version del
    # catalogo cambia, se usa otra subcarpeta y las fichas viejas simplemente no se leen.

    def _asegurar_version(self):
        # Cuesta una solicitud (o cero en modo offline), y solo la primera vez.
        if self.version is None:
            self.version = self.fuente.version_catalogo()["version"]

    def _ruta_ficha(self, id_ficha):
        if "/" in id_ficha or "\\" in id_ficha:
            raise ErrorCatalogo(f"id de ficha invalido para guardar en disco: {id_ficha}")
        return os.path.join(self.carpeta, self.version, id_ficha + ".json")

    def _leer_de_disco(self, id_ficha):
        try:
            with open(self._ruta_ficha(id_ficha), encoding="utf-8") as archivo:
                ficha = json.load(archivo)
        except (FileNotFoundError, ValueError):
            # No existe o esta danado: se trata como si nunca se hubiera guardado.
            return None
        self.lecturas_disco += 1
        return ficha

    def _guardar_en_disco(self, ficha):
        ruta = self._ruta_ficha(ficha["id"])
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(ficha, archivo, ensure_ascii=False)

    def _pedir_a_la_red(self, faltantes):
        # Pide de 10 en 10 (maximo por solicitud). Cada ficha recibida se guarda en disco
        # y en memoria. Devuelve las fichas recibidas.
        recibidas = []
        for inicio in range(0, len(faltantes), 10):
            lote = faltantes[inicio:inicio + 10]
            respuesta = self.fuente.catalogo(lote)
            for ficha in respuesta["entidades"]:
                self._guardar_en_disco(ficha)
                self._insertar_en_memoria(ficha["id"], ficha)
                recibidas.append(ficha)
        return recibidas

    def _buscar_en_recibidas(self, recibidas, id_ficha):
        for ficha in recibidas:
            if ficha["id"] == id_ficha:
                return ficha
        raise ErrorCatalogo(f"la ficha {id_ficha} no vino en la respuesta del catalogo")
