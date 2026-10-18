from adaptadores.cache_catalogo import ArbolAVL
from adaptadores.prefetch import _salas_por_id, seleccionar_lote, vecinas


class ErrorCripta(Exception):
    pass


class ServicioCripta:
    def __init__(self, fuente, cache, *, precarga_adaptativa=True):
        self.fuente = fuente
        self.cache = cache
        self.cripta_id = None
        self.esqueleto = ArbolAVL()
        self.contenido = ArbolAVL()
        self.precarga_adaptativa = precarga_adaptativa
        self.agrupacion_amplia = False
        self.motivo_agrupacion = None
        self.salas_al_ampliar = None
        self.lotes_contenido = 0

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
        self.agrupacion_amplia = False
        self.motivo_agrupacion = None
        self.salas_al_ampliar = None
        self.lotes_contenido = 0
        return datos

    def _evaluar_agrupacion(self, lote_local):
        limite = getattr(self.fuente, "limite_normal", None)
        if limite is None or self.agrupacion_amplia:
            return
        pendientes = self.esqueleto.cantidad - self.contenido.cantidad
        if self.lotes_contenido and self.contenido.cantidad:
            # Rendimiento observado: salas nuevas por consulta de contenido.
            contenido_estimado = (
                pendientes * self.lotes_contenido + self.contenido.cantidad - 1
            ) // self.contenido.cantidad
        else:
            rendimiento = max(1, len(lote_local))
            contenido_estimado = (pendientes + rendimiento - 1) // rendimiento
        conocidas = [entrada["sala"] for entrada in _salas_por_id(self.contenido.raiz)]
        tipos = self._tipos_en_salas(conocidas)
        if self.cache.version is not None:
            tipos = self.cache.faltantes(tipos)
        catalogo_estimado = (len(tipos) + 9) // 10
        version = int(self.cache.version is None and (bool(tipos) or pendientes > 0))
        # Al no conocer aun todas las fichas se contempla una consulta de tipos
        # nuevos y otra de botin. Es una estimacion, no una cota del servidor.
        desconocidas = 2 if pendientes else 0
        estimadas = contenido_estimado + catalogo_estimado + version + desconocidas
        disponibles = limite - self.fuente.solicitudes_normales
        if estimadas > disponibles:
            self.agrupacion_amplia = True
            self.salas_al_ampliar = self.contenido.cantidad
            self.motivo_agrupacion = (
                f"Se amplia la agrupacion: se estiman {estimadas} consultas "
                f"pendientes y quedan {disponibles} normales; la reserva se mantiene."
            )

    def asegurar_contenido(self, sala_id):
        # Vecindad por defecto; excepcion preventiva si la estimacion no cabe.
        sala = self.esqueleto.buscar(sala_id)
        if sala is None:
            raise ErrorCripta(f"la sala {sala_id} no existe en el esqueleto de {self.cripta_id}")

        # Si el destino ya se anticipo, no abrir otra consulta solo para ampliar
        # su vecindad. Se espera a necesitar una sala aun no disponible.
        if self.precarga_adaptativa and self.contenido.buscar(sala_id) is not None:
            return []

        faltantes = seleccionar_lote(self.esqueleto, self.contenido, sala_id)
        if self.precarga_adaptativa:
            self._evaluar_agrupacion(faltantes)
        faltantes = seleccionar_lote(
            self.esqueleto, self.contenido, sala_id,
            solo_vecindad=self.precarga_adaptativa and not self.agrupacion_amplia,
        )
        recibidas = []

        if len(faltantes) > 0:
            respuesta = self.fuente.contenido(self.cripta_id, faltantes)
            self.lotes_contenido += 1
            for entrada in respuesta["contenido"]:
                self.contenido.insertar(entrada["sala"], entrada)
                recibidas.append(entrada["sala"])

        if self.contenido.buscar(sala_id) is None:
            raise ErrorCripta(f"el contenido de la sala {sala_id} no vino en la respuesta")
        return recibidas

    def precargar_catalogo(self, sala_id):
        """Resuelve tambien las fichas de la vecindad ya usada por el prefetch.

        La cache conserva su AVL, su LRU y la persistencia existentes. Si una ficha
        anticipada sale de memoria, la siguiente entrada la recupera del disco.
        """
        anticipadas = self.asegurar_contenido(sala_id)
        if self.precarga_adaptativa:
            self._precargar_adaptativo(sala_id)
            return
        sala = self.esqueleto.buscar(sala_id)
        tipos = []
        salas = [sala_id] + vecinas(sala)
        for identificador in anticipadas:
            if identificador not in salas:
                salas.append(identificador)
        for id_vecina in salas:
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
                for objeto in ficha.get("suelta") or []:
                    if objeto not in soltados:
                        soltados.append(objeto)
        if soltados:
            self.cache.obtener_varias(soltados)

    def _tipos_en_salas(self, identificadores):
        tipos = []
        for identificador in identificadores:
            contenido = self.contenido.buscar(identificador)
            if contenido is None:
                continue
            for entrada in contenido["enemigos"] + contenido["trampas"]:
                if entrada["tipo"] not in tipos:
                    tipos.append(entrada["tipo"])
            for objeto in contenido["objetos"]:
                if objeto not in tipos:
                    tipos.append(objeto)
        return tipos

    def _resolver_adaptativo(self, necesarios, cercanos):
        faltantes = self.cache.faltantes(necesarios)
        if not faltantes:
            # No se abre una consulta solo para precarga opcional.
            return
        candidatos = self.cache.faltantes(cercanos)
        if self.agrupacion_amplia:
            conocidas = [entrada["sala"] for entrada in _salas_por_id(self.contenido.raiz)]
            for identificador in self.cache.faltantes(self._tipos_en_salas(conocidas)):
                if identificador not in candidatos:
                    candidatos.append(identificador)
        capacidad = ((len(faltantes) + 9) // 10) * 10
        lote = list(faltantes)
        for identificador in candidatos:
            if len(lote) == capacidad:
                break
            if identificador not in lote:
                lote.append(identificador)
        self.cache.obtener_varias(lote)

    def _precargar_adaptativo(self, sala_id):
        sala = self.esqueleto.buscar(sala_id)
        vecinas_abiertas = []
        for direccion in ("N", "S", "E", "O"):
            salida = sala.get("salidas", {}).get(direccion)
            if salida is not None and not salida.get("cerrada", False):
                vecinas_abiertas.append(salida["sala"])
        cercanos = self._tipos_en_salas(vecinas_abiertas)
        necesarios = self._tipos_en_salas([sala_id])
        self._resolver_adaptativo(necesarios, cercanos)
        fichas = self.cache.obtener_varias(necesarios) if necesarios else []
        botin = []
        for ficha in fichas:
            if ficha["clase"] == "enemigo":
                for identificador in ficha.get("suelta") or []:
                    if identificador not in botin:
                        botin.append(identificador)
        # Solo el botin de enemigos que se van a incorporar a esta sala.
        self._resolver_adaptativo(botin, cercanos)

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
            enemigos.append({"instancia": enemigo["instancia"], "vida": enemigo.get("vida"),"ficha": fichas[posicion]})
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
            soltados += enemigo["ficha"].get("suelta") or []
        fichas_soltadas = self.cache.obtener_varias(soltados) if soltados else []

        posicion = 0
        for enemigo in enemigos:
            enemigo["suelta"] = []
            for _ in enemigo["ficha"].get("suelta") or []:
                enemigo["suelta"].append(fichas_soltadas[posicion])
                posicion += 1

        return {"id": sala_id, "nombre": sala["nombre"], "salidas": sala["salidas"],
                "enemigos": enemigos, "objetos": objetos, "trampas": trampas}
