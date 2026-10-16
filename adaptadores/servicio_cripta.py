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
        self.cripta_id = cripta_id
        datos = self.fuente.datos_cripta(cripta_id)
        for pagina in range(1, datos["paginas"] + 1):
            respuesta = self.fuente.pagina_esqueleto(cripta_id, pagina)
            for sala in respuesta["salas"]:
                self.esqueleto.insertar(sala["id"], sala)
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

    def sala_resuelta(self, sala_id):
        self.asegurar_contenido(sala_id)
        sala = self.esqueleto.buscar(sala_id)
        contenido = self.contenido.buscar(sala_id)

        tipos = []
        for enemigo in contenido["enemigos"]:
            tipos.append(enemigo["tipo"])
        for objeto in contenido["objetos"]:
            tipos.append(objeto)
        for trampa in contenido["trampas"]:
            tipos.append(trampa["tipo"])
        fichas = self.cache.obtener_varias(tipos)

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
        fichas_soltadas = self.cache.obtener_varias(soltados)

        posicion = 0
        for enemigo in enemigos:
            enemigo["suelta"] = []
            for _ in enemigo["ficha"].get("suelta", []):
                enemigo["suelta"].append(fichas_soltadas[posicion])
                posicion += 1

        return {"id": sala_id, "nombre": sala["nombre"], "salidas": sala["salidas"],
                "enemigos": enemigos, "objetos": objetos, "trampas": trampas}