import pytest

from adaptadores.cache_catalogo import CacheCatalogo
from adaptadores.servicio_cripta import ServicioCripta, ErrorCripta

DATOS = {"id": "cripta-x", "paginas": 2, "sala_inicial": 1, "sala_salida": 4}

PAGINAS = {
    1: {"salas": [
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {
            "S": {"sala": 1}, "N": {"sala": 3}, "E": {"sala": 4, "cerrada": True, "llave": "itm_llave"}}},
    ]},
    2: {"salas": [
        {"id": 3, "nombre": "Nicho", "salidas": {"S": {"sala": 2}}},
        {"id": 4, "nombre": "Salida", "salidas": {"O": {"sala": 2}}},
    ]},
}

CONTENIDOS = {
    1: {"sala": 1, "enemigos": [], "objetos": ["itm_antorcha"], "trampas": []},
    2: {"sala": 2,
        "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 12}, {"instancia": "e-2", "tipo": "ent_rata", "vida": 10}],
        "objetos": ["itm_daga"],
        "trampas": [{"instancia": "t-1", "tipo": "trp_dardos"}]},
    3: {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
    4: {"sala": 4, "enemigos": [], "objetos": ["itm_antorcha"], "trampas": []},
}

FICHAS = {
    "ent_rata": {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "suelta": ["itm_pocion"]},
    "itm_pocion": {"id": "itm_pocion", "clase": "pocion", "nombre": "Pocion"},
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga"},
    "itm_antorcha": {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha"},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos"},
}


class FuenteFalsa:
    def __init__(self, contenidos=CONTENIDOS):
        self.contenidos = contenidos
        self.pedidos_contenido = []
        self.pedidos_catalogo = []
 
    def datos_cripta(self, cripta_id):
        return DATOS
 
    def pagina_esqueleto(self, cripta_id, pagina):
        return PAGINAS[pagina]
 
    def contenido(self, cripta_id, salas):
        self.pedidos_contenido.append(list(salas))
        return {"contenido": [self.contenidos[s] for s in salas if s in self.contenidos]}
 
    def catalogo(self, ids):
        self.pedidos_catalogo.append(list(ids))
        return {"entidades": [FICHAS[i] for i in ids]}
 
    def version_catalogo(self):
        return {"version": "v1"}
 
 
def crear_servicio(tmp_path, fuente=None):
    fuente = fuente or FuenteFalsa()
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path))
    servicio = ServicioCripta(fuente, cache, precarga_adaptativa=False)
    servicio.cargar("cripta-x")
    return servicio, fuente
 
 
def test_cargar_devuelve_los_datos_y_lee_todas_las_paginas(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    assert servicio.esqueleto.cantidad == 4
    assert fuente.pedidos_contenido == []
 
 
def test_primera_sala_completa_el_lote_con_las_cuatro_salas(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.sala_resuelta(1)
    assert fuente.pedidos_contenido == [[1, 2, 3, 4]]
 
 
def test_entrar_a_otra_sala_precarga_sus_vecinas_sin_repetir(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.sala_resuelta(1)
    servicio.sala_resuelta(2)
    assert fuente.pedidos_contenido == [[1, 2, 3, 4]]
 
 
def test_repetir_una_sala_no_hace_nuevas_solicitudes(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.sala_resuelta(2)
    cantidad_contenido = len(fuente.pedidos_contenido)
    cantidad_catalogo = len(fuente.pedidos_catalogo)
    servicio.sala_resuelta(2)
    assert len(fuente.pedidos_contenido) == cantidad_contenido
    assert len(fuente.pedidos_catalogo) == cantidad_catalogo
 
 
def test_la_sala_sale_con_sus_fichas(tmp_path):
    servicio, _ = crear_servicio(tmp_path)
    sala = servicio.sala_resuelta(2)
    assert sala["nombre"] == "Pasillo"
    assert [e["instancia"] for e in sala["enemigos"]] == ["e-1", "e-2"]
    assert sala["enemigos"][0]["ficha"]["nombre"] == "Rata"
    assert sala["enemigos"][1]["vida"] == 10
    assert sala["objetos"][0]["ficha"]["nombre"] == "Daga"
    assert sala["trampas"][0]["ficha"]["nombre"] == "Dardos"
 
 
def test_cada_enemigo_trae_las_fichas_de_lo_que_suelta(tmp_path):
    servicio, _ = crear_servicio(tmp_path)
    sala = servicio.sala_resuelta(2)
    for enemigo in sala["enemigos"]:
        assert [ficha["id"] for ficha in enemigo["suelta"]] == ["itm_pocion"]
 
 
def test_un_tipo_repetido_se_pide_una_sola_vez_al_catalogo(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.sala_resuelta(2)
    todos_los_ids = []
    for pedido in fuente.pedidos_catalogo:
        todos_los_ids += pedido
    assert todos_los_ids.count("ent_rata") == 1
    assert todos_los_ids.count("itm_pocion") == 1
 
 
def test_sala_que_no_existe(tmp_path):
    servicio, _ = crear_servicio(tmp_path)
    with pytest.raises(ErrorCripta):
        servicio.sala_resuelta(99)
 
 
def test_contenido_que_no_llega_se_reporta(tmp_path):
    sin_la_sala_2 = {1: CONTENIDOS[1]}
    servicio, _ = crear_servicio(tmp_path, FuenteFalsa(sin_la_sala_2))
    with pytest.raises(ErrorCripta) as error:
        servicio.sala_resuelta(2)
    assert "sala 2" in str(error.value)


class FuenteDosCriptas(FuenteFalsa):
    def datos_cripta(self, cripta_id):
        if cripta_id == "cripta-x":
            return super().datos_cripta(cripta_id)
        return {"id": cripta_id, "version": "v2", "paginas": 1}

    def pagina_esqueleto(self, cripta_id, pagina):
        if cripta_id == "cripta-x":
            return super().pagina_esqueleto(cripta_id, pagina)
        return {"salas": [{"id": 1, "nombre": "Entrada Y", "salidas": {}}]}

    def contenido(self, cripta_id, salas):
        if cripta_id == "cripta-x":
            return super().contenido(cripta_id, salas)
        self.pedidos_contenido.append(list(salas))
        return {"contenido": [{"sala": 1, "enemigos": [], "objetos": ["itm_daga"], "trampas": []}]}


def test_cambiar_de_cripta_no_mezcla_salas_ni_contenido(tmp_path):
    servicio, fuente = crear_servicio(tmp_path, FuenteDosCriptas())
    servicio.sala_resuelta(1)
    servicio.cargar("cripta-y")
    sala = servicio.sala_resuelta(1)
    assert servicio.cripta_id == "cripta-y"
    assert servicio.esqueleto.cantidad == 1
    assert servicio.esqueleto.buscar(2) is None
    assert sala["nombre"] == "Entrada Y"
    assert sala["objetos"][0]["id"] == "itm_daga"
    assert fuente.pedidos_contenido == [[1, 2, 3, 4], [1]]


def test_lotes_hasta_diez_sin_repetir_ni_ampliar_cada_consulta(tmp_path):
    class FuenteGrande(FuenteFalsa):
        def __init__(self):
            super().__init__({i: {"sala": i, "enemigos": [], "objetos": [], "trampas": []}
                              for i in range(1, 26)})

        def datos_cripta(self, cripta_id):
            return {"id": cripta_id, "paginas": 1}

        def pagina_esqueleto(self, cripta_id, pagina):
            salas = []
            for i in range(1, 26):
                salidas = {}
                if i < 25:
                    salidas["N"] = {"sala": i + 1}
                if i > 1:
                    salidas["S"] = {"sala": i - 1}
                salas.append({"id": i, "nombre": str(i), "salidas": salidas})
            return {"salas": salas}

    fuente = FuenteGrande()
    servicio, _ = crear_servicio(tmp_path, fuente)
    servicio.sala_resuelta(1)
    servicio.sala_resuelta(2)
    servicio.sala_resuelta(9)
    assert fuente.pedidos_contenido == [list(range(1, 11))]
    servicio.sala_resuelta(10)
    servicio.sala_resuelta(20)
    assert fuente.pedidos_contenido == [list(range(1, 11)), list(range(11, 21)), list(range(21, 26))]
    for i in range(1, 26):
        servicio.sala_resuelta(i)
    assert len(fuente.pedidos_contenido) == 3


def test_precarga_resuelve_fichas_de_todo_el_lote_y_suelta_null(tmp_path):
    contenidos = dict(CONTENIDOS)
    contenidos[4] = {"sala": 4, "enemigos": [{"instancia": "e-4", "tipo": "ent_rata"}],
                     "objetos": ["itm_pocion"], "trampas": []}

    class FuenteSinBotin(FuenteFalsa):
        def catalogo(self, ids):
            respuesta = super().catalogo(ids)
            return {"entidades": [dict(ficha, suelta=None) if ficha["clase"] == "enemigo" else ficha
                                  for ficha in respuesta["entidades"]]}

    servicio, fuente = crear_servicio(tmp_path, FuenteSinBotin(contenidos))
    servicio.sala_resuelta(1)
    assert "itm_pocion" in [clave for pedido in fuente.pedidos_catalogo for clave in pedido]
    anteriores = len(fuente.pedidos_catalogo)
    sala = servicio.sala_resuelta(4)
    assert sala["enemigos"][0]["vida"] is None
    assert sala["enemigos"][0]["suelta"] == []
    assert len(fuente.pedidos_catalogo) == anteriores


def test_recargar_misma_cripta_invalida_contenido_anterior(tmp_path):
    fuente = FuenteFalsa(contenidos=dict(CONTENIDOS))
    servicio, _ = crear_servicio(tmp_path, fuente)
    servicio.sala_resuelta(1)
    fuente.contenidos[1] = {"sala": 1, "enemigos": [], "objetos": [], "trampas": []}
    servicio.cargar("cripta-x")
    assert servicio.sala_resuelta(1)["objetos"] == []


def test_carga_fallida_conserva_la_cripta_anterior(tmp_path, monkeypatch):
    servicio, fuente = crear_servicio(tmp_path)
    sala = servicio.sala_resuelta(1)
    esqueleto, contenido = servicio.esqueleto, servicio.contenido

    def pagina_fallida(cripta_id, pagina):
        if pagina == 2:
            raise ErrorCripta("fallo de pagina")
        return PAGINAS[1]

    monkeypatch.setattr(fuente, "pagina_esqueleto", pagina_fallida)
    with pytest.raises(ErrorCripta, match="fallo de pagina"):
        servicio.cargar("cripta-y")
    assert servicio.cripta_id == "cripta-x"
    assert servicio.esqueleto is esqueleto
    assert servicio.contenido is contenido
    assert servicio.sala_resuelta(1) == sala


def test_anticipa_fichas_y_objetos_sueltos_de_la_vecina(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.sala_resuelta(1)
    ids = [clave for pedido in fuente.pedidos_catalogo for clave in pedido]
    assert ids == ["itm_antorcha", "ent_rata", "itm_daga", "trp_dardos", "itm_pocion"]
    assert all(len(pedido) <= 10 for pedido in fuente.pedidos_catalogo)
    anteriores = len(fuente.pedidos_catalogo)
    sala = servicio.sala_resuelta(2)
    assert len(fuente.pedidos_catalogo) == anteriores
    assert sala["enemigos"][0]["suelta"][0]["id"] == "itm_pocion"


def test_precarga_con_cache_pequena_recupera_de_disco_sin_repedir(tmp_path):
    fuente = FuenteFalsa()
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path), tope=1)
    servicio = ServicioCripta(fuente, cache)
    servicio.cargar("cripta-x")
    servicio.sala_resuelta(1)
    anteriores = len(fuente.pedidos_catalogo)
    sala = servicio.sala_resuelta(2)
    assert fuente.pedidos_catalogo[anteriores:] == [["itm_pocion"]]
    anteriores = len(fuente.pedidos_catalogo)
    servicio.sala_resuelta(2)
    assert len(fuente.pedidos_catalogo) == anteriores
    assert cache.lecturas_disco > 0
    assert cache.lista.cantidad == cache.arbol.cantidad == 1
    assert sala["objetos"][0]["id"] == "itm_daga"


def test_precarga_respeta_la_proteccion_existente_de_fichas_en_uso(tmp_path):
    fuente = FuenteFalsa()
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path), tope=2,
                          esta_en_uso=lambda clave: clave == "itm_antorcha")
    ficha = cache.obtener("itm_antorcha")
    servicio = ServicioCripta(fuente, cache)
    servicio.cargar("cripta-x")
    servicio.sala_resuelta(2)
    assert cache.arbol.buscar("itm_antorcha").ficha is ficha
    assert cache.lista.cantidad == cache.arbol.cantidad == 2


def test_salas_vacias_no_consultan_el_catalogo(tmp_path):
    class FuenteVacia(FuenteFalsa):
        def version_catalogo(self):
            raise AssertionError("no hay fichas que resolver")

    contenidos = {numero: {"sala": numero, "enemigos": [], "objetos": [], "trampas": []}
                  for numero in range(1, 5)}
    fuente = FuenteVacia(contenidos)
    servicio, _ = crear_servicio(tmp_path, fuente)
    assert servicio.sala_resuelta(1)["enemigos"] == []
    assert fuente.pedidos_catalogo == []


def test_adaptativa_no_resuelve_fichas_lejanas_ni_botin_antes_de_necesitarlos(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.precarga_adaptativa = True
    servicio.sala_resuelta(1)
    descargados = [identificador for lote in fuente.pedidos_catalogo for identificador in lote]
    assert "ent_rata" in descargados  # Vecina abierta en el mismo GET necesario.
    assert "itm_pocion" not in descargados  # Botin aun no instanciado.
    assert len(fuente.pedidos_catalogo) == 1
    servicio.sala_resuelta(2)
    assert fuente.pedidos_catalogo[-1] == ["itm_pocion"]


def test_adaptativa_no_consulta_solo_por_precarga_si_actual_esta_resuelta(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.precarga_adaptativa = True
    servicio.cache.obtener("itm_antorcha")
    anteriores = len(fuente.pedidos_catalogo)
    servicio.sala_resuelta(1)
    assert len(fuente.pedidos_catalogo) == anteriores
    assert servicio.cache.arbol.buscar("ent_rata") is None


def test_vecindad_no_amplia_anticipacion_desde_una_sala_ya_cargada(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.precarga_adaptativa = True
    servicio.sala_resuelta(1)
    assert fuente.pedidos_contenido == [[1, 2]]
    servicio.sala_resuelta(2)
    assert fuente.pedidos_contenido == [[1, 2]]
    assert servicio.contenido.buscar(3) is None
    assert servicio.contenido.buscar(4) is None
    servicio.sala_resuelta(3)
    assert fuente.pedidos_contenido[-1] == [3]
    assert servicio.contenido.buscar(4) is None


def test_adaptativa_no_anticipa_salas_lejanas_con_presupuesto_holgado(tmp_path):
    contenidos = dict(CONTENIDOS)
    contenidos[4] = {"sala": 4, "enemigos": [], "objetos": ["itm_pocion"], "trampas": []}
    fuente = FuenteFalsa(contenidos)
    fuente.limite_normal = 100
    fuente.solicitudes_normales = 5
    servicio, _ = crear_servicio(tmp_path, fuente)
    servicio.precarga_adaptativa = True
    servicio.sala_resuelta(1)
    assert len(fuente.pedidos_catalogo) == 1
    assert "itm_pocion" not in fuente.pedidos_catalogo[0]
    assert servicio.contenido.buscar(4) is None
    assert all(len(lote) <= 10 for lote in fuente.pedidos_catalogo)


def test_excepcion_agrupa_contenido_y_fichas_cuando_vecindad_no_cabe(tmp_path):
    contenidos = dict(CONTENIDOS)
    contenidos[4] = {"sala": 4, "enemigos": [], "objetos": ["itm_pocion"], "trampas": []}
    fuente = FuenteFalsa(contenidos)
    fuente.limite_normal = 7
    fuente.solicitudes_normales = 5
    servicio, _ = crear_servicio(tmp_path, fuente)
    servicio.precarga_adaptativa = True
    servicio.sala_resuelta(1)
    assert servicio.agrupacion_amplia
    assert "se estiman" in servicio.motivo_agrupacion
    assert fuente.pedidos_contenido == [[1, 2, 3, 4]]
    assert "itm_pocion" in fuente.pedidos_catalogo[0]
    assert fuente.limite_normal == 7 and fuente.solicitudes_normales == 5
    servicio.cargar("cripta-x")
    assert not servicio.agrupacion_amplia
    assert servicio.motivo_agrupacion is None and servicio.lotes_contenido == 0


def test_estimacion_de_excepcion_no_realiza_solicitudes(tmp_path):
    servicio, fuente = crear_servicio(tmp_path)
    servicio.precarga_adaptativa = True
    fuente.limite_normal = 7
    fuente.solicitudes_normales = 2
    servicio._evaluar_agrupacion([1, 2])
    assert fuente.pedidos_contenido == [] and fuente.pedidos_catalogo == []


def test_respuesta_vacia_no_rompe_la_estimacion_al_reintentar(tmp_path):
    fuente = FuenteFalsa({})
    fuente.limite_normal = 100
    fuente.solicitudes_normales = 2
    servicio, _ = crear_servicio(tmp_path, fuente)
    servicio.precarga_adaptativa = True
    for _ in range(2):
        with pytest.raises(ErrorCripta, match="no vino en la respuesta"):
            servicio.asegurar_contenido(1)
    assert servicio.contenido.cantidad == 0 and servicio.lotes_contenido == 2


def test_estimacion_de_faltantes_reutiliza_disco_y_no_pide_fichas(tmp_path):
    fuente = FuenteFalsa()
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path), tope=1)
    cache.obtener("itm_antorcha")
    cache.obtener("itm_daga")
    anteriores = len(fuente.pedidos_catalogo)
    assert cache.faltantes(["itm_antorcha", "itm_antorcha", "nuevo"]) == ["nuevo"]
    assert cache.lecturas_disco > 0
    assert len(fuente.pedidos_catalogo) == anteriores
