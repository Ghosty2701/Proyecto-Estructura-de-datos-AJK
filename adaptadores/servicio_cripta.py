from adaptadores.cache_catalogo import ArbolAVL
from adaptadores.prefetch import vecinas


class ErrorCripta(Exception):
    pass


class ServicioCripta:
    def __init__(self, fuente, cache):
        self.fuente = fuente
        self.cache = cache
        self.cripta_id = None
        self.esqueleto = ArbolAVL()
        self.contenido = ArbolAVL()

    def cargar(self, cripta_id):
        datos = self.fuente.datos_cripta(cripta_id)
        # Publicar la nueva cripta solo cuando todas sus paginas esten completas.
        # Se mantiene la estructura AVL; los datos de otra carga no se reutilizan.
        esqueleto = ArbolAVL()
        for pagina in range(1, datos["paginas"] + 1):
            respuesta = self.fuente.pagina_esqueleto(cripta_id, pagina)
            for sala in respuesta["salas"]:
                esqueleto.insertar(sala["id"], sala)
        self.cripta_id = cripta_id
        self.esqueleto = esqueleto
        self.contenido = ArbolAVL()
        return datos

    def asegurar_contenido(self, sala_id):
        # Pide en un solo lote el contenido de la sala y de sus vecinas que aun no esta cargado
        sala = self.esqueleto.buscar(sala_id)
        if sala is None:
            raise ErrorCripta(f"la sala {sala_id} no existe en el esqueleto de {self.cripta_id}")

        faltantes = []
        for id_sala in [sala_id] + vecinas(sala):
            if self.contenido.buscar(id_sala) is None and id_sala not in faltantes:
                faltantes.append(id_sala)

        if len(faltantes) > 0:
            respuesta = self.fuente.contenido(self.cripta_id, faltantes)
            for entrada in respuesta["contenido"]:
                self.contenido.insertar(entrada["sala"], entrada)

        if self.contenido.buscar(sala_id) is None:
            raise ErrorCripta(f"el contenido de la sala {sala_id} no vino en la respuesta")

    def precargar_catalogo(self, sala_id):
        """Resuelve tambien las fichas de la vecindad ya usada por el prefetch.

        La cache conserva su AVL, su LRU y la persistencia existentes. Si una ficha
        anticipada sale de memoria, la siguiente entrada la recupera del disco.
        """
        self.asegurar_contenido(sala_id)
        sala = self.esqueleto.buscar(sala_id)
        tipos = []
        for id_vecina in [sala_id] + vecinas(sala):
            contenido = self.contenido.buscar(id_vecina)
            if contenido is None:
                continue
            for enemigo in contenido["enemigos"]:
                if enemigo["tipo"] not in tipos:
                    tipos.append(enemigo["tipo"])
            for objeto in contenido["objetos"]:
                if objeto not in tipos:
                    tipos.append(objeto)
            for trampa in contenido["trampas"]:
                if trampa["tipo"] not in tipos:
                    tipos.append(trampa["tipo"])

        if not tipos:
            return
        fichas = self.cache.obtener_varias(tipos)
        soltados = []
        for ficha in fichas:
            if ficha["clase"] == "enemigo":
                for objeto in ficha.get("suelta", []):
                    if objeto not in soltados:
                        soltados.append(objeto)
        if soltados:
            self.cache.obtener_varias(soltados)

    def sala_resuelta(self, sala_id):
        self.precargar_catalogo(sala_id)
        sala = self.esqueleto.buscar(sala_id)
        contenido = self.contenido.buscar(sala_id)

        tipos = []
        for enemigo in contenido["enemigos"]:
            tipos.append(enemigo["tipo"])
        for objeto in contenido["objetos"]:
            tipos.append(objeto)
        for trampa in contenido["trampas"]:
            tipos.append(trampa["tipo"])
        fichas = self.cache.obtener_varias(tipos) if tipos else []

        posicion = 0
        enemigos = []
        for enemigo in contenido["enemigos"]:
            enemigos.append({"instancia": enemigo["instancia"], "vida": enemigo["vida"],"ficha": fichas[posicion]})
            posicion += 1
        objetos = []
        for objeto in contenido["objetos"]:
            objetos.append({"id": objeto, "ficha": fichas[posicion]})
            posicion += 1
        trampas = []
        for trampa in contenido["trampas"]:
            trampas.append({"instancia": trampa["instancia"], "ficha": fichas[posicion]})
            posicion += 1

        soltados = []
        for enemigo in enemigos:
            soltados += enemigo["ficha"].get("suelta", [])
        fichas_soltadas = self.cache.obtener_varias(soltados) if soltados else []

        posicion = 0
        for enemigo in enemigos:
            enemigo["suelta"] = []
            for _ in enemigo["ficha"].get("suelta", []):
                enemigo["suelta"].append(fichas_soltadas[posicion])
                posicion += 1

        return {"id": sala_id, "nombre": sala["nombre"], "salidas": sala["salidas"],
                "enemigos": enemigos, "objetos": objetos, "trampas": trampas}
