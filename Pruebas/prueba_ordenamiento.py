import random

from comun.ordenamiento import (
    ContadorOperaciones,
    insertion_sort,
    merge_sort,
    ordenar,
    vista_ordenada,
    UMBRAL_TAMANO_PEQUENO,
)


# --- Correctitud basica de cada algoritmo ---

def test_insertion_sort_lista_vacia_y_de_un_elemento():
    assert insertion_sort([]) == []
    assert insertion_sort([5]) == [5]


def test_merge_sort_lista_vacia_y_de_un_elemento():
    assert merge_sort([]) == []
    assert merge_sort([5]) == [5]


def test_insertion_sort_ordena_correctamente():
    datos = [5, 2, 8, 1, 9, 3]
    assert insertion_sort(datos) == [1, 2, 3, 5, 8, 9]


def test_merge_sort_ordena_correctamente():
    datos = [5, 2, 8, 1, 9, 3]
    assert merge_sort(datos) == [1, 2, 3, 5, 8, 9]


def test_ambos_algoritmos_coinciden_con_datos_aleatorios():
    random.seed(1234)
    for _ in range(20):
        datos = [random.randint(-50, 50) for _ in range(random.randint(0, 60))]
        esperado = list(sorted(datos))  # solo para comparar en la prueba, no en produccion
        assert insertion_sort(datos) == esperado
        assert merge_sort(datos) == esperado


def test_no_modifican_la_lista_original():
    original = [3, 1, 2]
    copia = list(original)
    insertion_sort(original)
    merge_sort(original)
    assert original == copia  # la entrada nunca se toca


# --- Uso de una funcion clave (como para peso/valor/nombre del inventario) ---

def test_ordenar_objetos_por_clave():
    class Objeto:
        def __init__(self, nombre, peso):
            self.nombre = nombre
            self.peso = peso

    daga = Objeto("daga", 2)
    escudo = Objeto("escudo", 8)
    pocion = Objeto("pocion", 1)

    resultado = insertion_sort([daga, escudo, pocion], clave=lambda o: o.peso)
    assert [o.nombre for o in resultado] == ["pocion", "daga", "escudo"]

    resultado = merge_sort([daga, escudo, pocion], clave=lambda o: o.peso)
    assert [o.nombre for o in resultado] == ["pocion", "daga", "escudo"]


# --- Estabilidad: elementos con la misma clave conservan su orden relativo ---

def test_insertion_sort_es_estable():
    datos = [("a", 1), ("b", 1), ("c", 0), ("d", 1)]
    resultado = insertion_sort(datos, clave=lambda x: x[1])
    assert resultado == [("c", 0), ("a", 1), ("b", 1), ("d", 1)]


def test_merge_sort_es_estable():
    datos = [("a", 1), ("b", 1), ("c", 0), ("d", 1)]
    resultado = merge_sort(datos, clave=lambda x: x[1])
    assert resultado == [("c", 0), ("a", 1), ("b", 1), ("d", 1)]


# --- El contador de operaciones sirve como evidencia empirica ---

def test_contador_registra_comparaciones_y_movimientos():
    contador = ContadorOperaciones()
    insertion_sort([3, 2, 1], contador=contador)
    assert contador.comparaciones > 0
    assert contador.movimientos > 0


def test_insertion_sort_hace_pocas_comparaciones_en_datos_ya_ordenados():
    # Caso adaptativo: con datos ya ordenados, cada elemento se compara una sola vez.
    datos = list(range(100))
    contador = ContadorOperaciones()
    insertion_sort(datos, contador=contador)
    assert contador.comparaciones == 99
    assert contador.movimientos == 0


def test_merge_sort_hace_aproximadamente_n_log_n_comparaciones_sin_importar_el_orden():
    contador_ordenado = ContadorOperaciones()
    merge_sort(list(range(200)), contador=contador_ordenado)

    contador_invertido = ContadorOperaciones()
    merge_sort(list(range(200, 0, -1)), contador=contador_invertido)

    # A diferencia de insertion sort, el costo de merge sort no depende fuertemente del
    # orden inicial: la diferencia entre mejor y peor caso es una fraccion pequena de n,
    # no una diferencia de orden de magnitud como ocurre con insertion sort.
    diferencia = abs(contador_ordenado.comparaciones - contador_invertido.comparaciones)
    assert diferencia < 0.5 * len(range(200))


def test_insertion_sort_es_mucho_mas_costoso_que_merge_sort_en_datos_invertidos_grandes():
    # Esta es la evidencia de "la alternativa descartada" que pide el §8 del enunciado.
    datos = list(range(300, 0, -1))

    contador_insertion = ContadorOperaciones()
    insertion_sort(datos, contador=contador_insertion)

    contador_merge = ContadorOperaciones()
    merge_sort(datos, contador=contador_merge)

    assert contador_insertion.comparaciones > contador_merge.comparaciones * 5


# --- Seleccion automatica (ordenar) ---

def test_ordenar_usa_insertion_sort_en_arreglos_pequenos():
    datos = list(range(UMBRAL_TAMANO_PEQUENO, 0, -1))  # pequeno pero muy desordenado
    resultado, algoritmo = ordenar(datos)
    assert algoritmo == "insertion_sort"
    assert resultado == list(range(1, UMBRAL_TAMANO_PEQUENO + 1))


def test_ordenar_usa_insertion_sort_en_arreglos_grandes_casi_ordenados():
    datos = list(range(500))
    # Un par de elementos fuera de lugar; el resto sigue casi ordenado.
    datos[10], datos[11] = datos[11], datos[10]
    resultado, algoritmo = ordenar(datos)
    assert algoritmo == "insertion_sort"
    assert resultado == list(range(500))


def test_ordenar_usa_merge_sort_en_arreglos_grandes_y_desordenados():
    random.seed(7)
    datos = list(range(500))
    random.shuffle(datos)
    resultado, algoritmo = ordenar(datos)
    assert algoritmo == "merge_sort"
    assert resultado == list(range(500))


def test_ordenar_con_comparacion_costosa_prefiere_merge_sort_aunque_sea_mediano():
    # Sin marcar como costosa, un arreglo de este tamano (> UMBRAL_TAMANO_PEQUENO)
    # y desordenado ya elegiria merge sort de todas formas; lo interesante aca es
    # que el umbral de "pequeno" se reduce cuando la comparacion es costosa.
    datos = list(range(20, 0, -1))  # tamano 20: pequeno en el caso normal
    _, algoritmo_normal = ordenar(datos)
    _, algoritmo_costoso = ordenar(datos, comparacion_costosa=True)
    assert algoritmo_normal == "insertion_sort"
    assert algoritmo_costoso == "merge_sort"


def test_vista_ordenada_devuelve_solo_la_lista():
    resultado = vista_ordenada([3, 1, 2])
    assert resultado == [1, 2, 3]
