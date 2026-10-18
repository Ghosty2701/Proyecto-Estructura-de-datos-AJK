import tempfile
import pytest

from adaptadores.cache_catalogo import NodoLRU, ListaLRU, ArbolAVL, CacheCatalogo, ErrorCatalogo


def test_desalojo_vacia_referencia_compartida_y_recupera_desde_disco(tmp_path):
    from types import SimpleNamespace

    fuente = SimpleNamespace(
        version_catalogo=lambda: {"version": "v1"},
        catalogo=lambda ids: {"entidades": [{"id": identificador, "nombre": identificador} for identificador in ids]},
    )
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path), tope=1)
    cache.obtener("a")
    referencia = cache.referencia("a")
    assert cache.referencia("a") is referencia
    cache.obtener("b")
    assert referencia.datos is None and cache.arbol.buscar("a") is None
    fuente.catalogo = lambda ids: (_ for _ in ()).throw(AssertionError("No debe consultar la red"))
    cache.obtener("a")
    assert cache.referencia("a") is referencia
    assert referencia["nombre"] == "a" and cache.lecturas_disco == 1


def test_precarga_con_todas_protegidas_queda_en_disco(tmp_path):
    from types import SimpleNamespace

    lotes = []
    def catalogo(ids):
        lotes.append(list(ids))
        return {"entidades": [{"id": i} for i in ids]}
    fuente = SimpleNamespace(version_catalogo=lambda: {"version": "v1"}, catalogo=catalogo)
    protegida = ["a"]
    cache = CacheCatalogo(fuente, carpeta=str(tmp_path), tope=1,
                          esta_en_uso=lambda i: i in protegida)
    cache.obtener("a")
    referencia = cache.referencia("a")
    assert cache.obtener("b")["id"] == "b"
    assert cache.lista.cantidad == cache.arbol.cantidad == 1 and referencia.datos is not None
    assert cache.arbol.buscar("b") is None
    protegida.clear()
    cache.obtener("b")
    assert lotes == [["a"], ["b"]] and cache.lecturas_disco == 1
    assert referencia.datos is None


def comprobar(descripcion, condicion):
    print(("OK    " if condicion else "FALLO ") + descripcion)
    assert condicion, descripcion

def ids_hacia_el_final(lista):
    resultado = []
    nodo = lista.frente
    while nodo is not None:
        resultado.append(nodo.id_ficha)
        nodo = nodo.siguiente
    return resultado


def ids_hacia_el_frente(lista):
    resultado = []
    nodo = lista.final
    while nodo is not None:
        resultado.append(nodo.id_ficha)
        nodo = nodo.anterior
    return resultado

def test_lista_avl_y_cache_persistente():
    lista = ListaLRU()
    comprobar("lista vacia: sin frente ni final", lista.frente is None and lista.final is None)

    a, b, c = NodoLRU("a", {}), NodoLRU("b", {}), NodoLRU("c", {})
    lista.agregar_al_frente(a)
    comprobar("un solo nodo es frente y final", lista.frente is a and lista.final is a)

    lista.agregar_al_frente(b)
    lista.agregar_al_frente(c)
    comprobar("orden frente->final es c,b,a", ids_hacia_el_final(lista) == ["c", "b", "a"])
    comprobar("orden final->frente es a,b,c", ids_hacia_el_frente(lista) == ["a", "b", "c"])
    comprobar("cantidad es 3", lista.cantidad == 3)

    lista.mover_al_frente(a)
    comprobar("mover el ultimo al frente: a,c,b", ids_hacia_el_final(lista) == ["a", "c", "b"])
    comprobar("enlaces de vuelta coherentes", ids_hacia_el_frente(lista) == ["b", "c", "a"])

    lista.mover_al_frente(a)
    comprobar("mover el que ya esta al frente no cambia nada", ids_hacia_el_final(lista) == ["a", "c", "b"])

    lista.quitar(c)
    comprobar("quitar un nodo del medio: a,b", ids_hacia_el_final(lista) == ["a", "b"])
    comprobar("cantidad baja a 2", lista.cantidad == 2)

    lista.quitar(a)
    comprobar("quitar el frente deja a b como frente y final", lista.frente is b and lista.final is b)

    lista.quitar(b)
    comprobar("quitar el ultimo deja la lista vacia", lista.frente is None and lista.final is None and lista.cantidad == 0)


    # ---------------------------------------------------------------------------
    # ArbolAVL
    # ---------------------------------------------------------------------------

    def revisar(nodo):
        # Devuelve (altura, cantidad) y verifica orden, alturas guardadas y balance de cada nodo.
        if nodo is None:
            return 0, 0, True
        alt_i, cant_i, ok_i = revisar(nodo.izquierdo)
        alt_d, cant_d, ok_d = revisar(nodo.derecho)
        ok = ok_i and ok_d
        ok = ok and abs(alt_i - alt_d) <= 1
        ok = ok and nodo.altura == 1 + max(alt_i, alt_d)
        if nodo.izquierdo is not None:
            ok = ok and nodo.izquierdo.clave < nodo.clave
        if nodo.derecho is not None:
            ok = ok and nodo.derecho.clave > nodo.clave
        return 1 + max(alt_i, alt_d), 1 + cant_i + cant_d, ok


    def clave(numero):
        return "id_" + str(numero).zfill(3)


    arbol = ArbolAVL()
    comprobar("arbol vacio: buscar devuelve None", arbol.buscar("x") is None)

    # Claves en orden creciente: el peor caso para un arbol sin balanceo.
    for n in range(100):
        arbol.insertar(clave(n), n)
    altura, cantidad, ok = revisar(arbol.raiz)
    comprobar("100 claves ordenadas: arbol equilibrado y ordenado", ok)
    comprobar("100 claves ordenadas: altura <= 8 (un arbol simple tendria 100)", altura <= 8)
    comprobar("cantidad guardada coincide con la real", arbol.cantidad == 100 and cantidad == 100)
    comprobar("buscar encuentra todas las claves", all(arbol.buscar(clave(n)) == n for n in range(100)))
    comprobar("buscar una clave ausente devuelve None", arbol.buscar("zzz") is None)

    arbol.insertar(clave(5), "nuevo")
    comprobar("insertar una clave repetida cambia el valor sin duplicar",
              arbol.buscar(clave(5)) == "nuevo" and arbol.cantidad == 100)

    for n in range(0, 100, 2):
        arbol.quitar(clave(n))
    altura, cantidad, ok = revisar(arbol.raiz)
    comprobar("quitar las 50 pares: sigue equilibrado y ordenado", ok)
    comprobar("quitar: cantidad 50", arbol.cantidad == 50 and cantidad == 50)
    comprobar("quitar: las pares ya no estan y las impares si", all(arbol.buscar(clave(n)) is None for n in range(0, 100, 2))
              and all(arbol.buscar(clave(n)) is not None for n in range(1, 100, 2)))

    arbol.quitar("zzz")
    comprobar("quitar una clave ausente no cambia nada", arbol.cantidad == 50)

    for n in range(1, 100, 2):
        arbol.quitar(clave(n))
    comprobar("quitar todo deja el arbol vacio", arbol.raiz is None and arbol.cantidad == 0)

    # Orden decreciente y orden mezclado (rotaciones dobles).
    arbol = ArbolAVL()
    for n in range(99, -1, -1):
        arbol.insertar(clave(n), n)
    comprobar("100 claves decrecientes: equilibrado", revisar(arbol.raiz)[2])

    arbol = ArbolAVL()
    for n in [50, 20, 80, 10, 30, 25, 27, 26, 90, 95, 92]:
        arbol.insertar(clave(n), n)
    comprobar("orden mezclado (rotaciones dobles): equilibrado", revisar(arbol.raiz)[2])

    class FuenteFalsa:
        def __init__(self, version="cat-1", ausentes=()):
            self.version = version
            self.ausentes = ausentes
            self.lotes = []   # un elemento por cada solicitud de catalogo
            self.consultas_version = 0

        def catalogo(self, ids):
            self.lotes.append(list(ids))
            return {"entidades": [{"id": i, "clase": "arma", "nombre": "Ficha " + i}
                                  for i in ids if i not in self.ausentes]}

        def version_catalogo(self):
            self.consultas_version += 1
            return {"version": self.version}


    def nombres(n):
        return ["itm_" + str(numero).zfill(2) for numero in range(n)]


    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        cache = CacheCatalogo(fuente, carpeta, tope=25)

        fichas = cache.obtener_varias(["itm_a", "itm_b", "itm_c"])
        comprobar("primera vez: una sola solicitud para 3 ids", len(fuente.lotes) == 1)
        comprobar("devuelve las fichas en el orden pedido", [f["id"] for f in fichas] == ["itm_a", "itm_b", "itm_c"])
        comprobar("la version del catalogo se consulta una sola vez", fuente.consultas_version == 1)
        comprobar("primera vez: 3 fallos y 0 aciertos", cache.fallos == 3 and cache.aciertos == 0)

        cache.obtener_varias(["itm_a", "itm_b"])
        comprobar("segunda vez: sin nuevas solicitudes", len(fuente.lotes) == 1)
        comprobar("segunda vez: 2 aciertos", cache.aciertos == 2)
        comprobar("la version no se vuelve a consultar", fuente.consultas_version == 1)

        cache.obtener_varias(["itm_x", "itm_x", "itm_a", "itm_x"])
        comprobar("un id repetido se pide una sola vez", fuente.lotes[1] == ["itm_x"])
        comprobar("el id repetido devuelve la misma ficha las 3 veces",
                  cache.obtener("itm_x")["id"] == "itm_x")

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        cache = CacheCatalogo(fuente, carpeta, tope=50)
        cache.obtener_varias(nombres(12))
        comprobar("12 ids faltantes: dos lotes de 10 y 2",
                  [len(lote) for lote in fuente.lotes] == [10, 2])

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        cache = CacheCatalogo(fuente, carpeta, tope=3)
        cache.obtener_varias(nombres(5))
        comprobar("con tope 3 nunca hay mas de 3 fichas en memoria",
                  cache.lista.cantidad == 3 and cache.arbol.cantidad == 3)

        solicitudes = len(fuente.lotes)
        ficha = cache.obtener("itm_00")   # fue liberada de memoria
        comprobar("ficha liberada: se recupera del disco sin solicitud",
                  ficha["id"] == "itm_00" and len(fuente.lotes) == solicitudes and cache.lecturas_disco == 1)
        comprobar("la ficha recuperada vuelve a memoria", cache.arbol.buscar("itm_00") is not None)
        comprobar("y sigue habiendo 3 en memoria", cache.lista.cantidad == 3)

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        cache = CacheCatalogo(fuente, carpeta)
        cache.obtener_varias(["itm_a", "itm_b"])

        # Simula cerrar y volver a abrir el programa: cache nueva, misma carpeta.
        cache_nueva = CacheCatalogo(fuente, carpeta)
        cache_nueva.obtener_varias(["itm_a", "itm_b"])
        comprobar("sobrevive al cierre: sin solicitudes de catalogo nuevas", len(fuente.lotes) == 1)
        comprobar("sobrevive al cierre: se leyo del disco", cache_nueva.lecturas_disco == 2)

        fuente.version = "cat-2"
        cache_otra_version = CacheCatalogo(fuente, carpeta)
        cache_otra_version.obtener("itm_a")
        comprobar("version de catalogo distinta: se vuelve a pedir a la red", len(fuente.lotes) == 2)

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        en_uso = ["todas"]
        cache = CacheCatalogo(fuente, carpeta, tope=2, esta_en_uso=lambda id_ficha: bool(en_uso))
        with pytest.raises(ErrorCatalogo, match="Capacidad insuficiente"):
            cache.obtener_varias(nombres(4))
        comprobar("todas en uso: el tope sigue siendo 2", cache.lista.cantidad == 2 and cache.arbol.cantidad == 2)
        comprobar("el lote completo quedo en disco", all(cache._leer_de_disco(i) is not None for i in nombres(4)))

        en_uso.clear()
        cache.obtener("itm_nueva")
        comprobar("al dejar de estar en uso, la cache vuelve al tope", cache.lista.cantidad <= 2)

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa()
        en_uso = ["itm_00"]
        cache = CacheCatalogo(fuente, carpeta, tope=2, esta_en_uso=lambda id_ficha: id_ficha in en_uso)
        cache.obtener_varias(["itm_00", "itm_01", "itm_02", "itm_03"])
        comprobar("una ficha en uso nunca se libera", cache.arbol.buscar("itm_00") is not None)
        comprobar("las demas si se liberan segun LRU", cache.arbol.buscar("itm_01") is None)

    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteFalsa(ausentes=["itm_fantasma"])
        cache = CacheCatalogo(fuente, carpeta)
        try:
            cache.obtener("itm_fantasma")
            comprobar("id ausente en la respuesta lanza ErrorCatalogo", False)
        except ErrorCatalogo:
            comprobar("id ausente en la respuesta lanza ErrorCatalogo", True)
