# Ordenamiento (§4.9). Dos algoritmos con caracteristicas distintas, mas una funcion
# que elige cual usar segun propiedades medibles de los datos: tamano, nivel de
# desorden y si el llamador marca la comparacion como costosa.
#
# Ninguna funcion de este modulo usa list.sort() ni sorted() (prohibido por §7 para
# los ordenamientos evaluados). Todas devuelven una lista NUEVA: la entrada nunca
# se modifica, para poder usarlas en vistas (ej. inventario) sin alterar el orden real.

UMBRAL_TAMANO_PEQUENO = 32
# Con comparacion costosa, el margen para "arreglo pequeno" se reduce: el riesgo de
# caer en el peor caso de insertion sort (muchas comparaciones caras) pesa mas que
# el ahorro de usarlo en arreglos un poco mas grandes.
UMBRAL_TAMANO_PEQUENO_COSTOSO = 8
# Proporcion maxima de "descensos" para considerar los datos casi ordenados.
UMBRAL_PROPORCION_DESORDEN = 0.05


def _clave_identidad(x):
    return x


class ContadorOperaciones:
    # Cuenta comparaciones y movimientos hechos durante un ordenamiento.
    # Es la evidencia empirica que pide el Documento de Decisiones (§8) y el modo --bench:
    # permite comparar las dos alternativas con numeros propios, no solo con la notacion O().
    def __init__(self):
        self.comparaciones = 0
        self.movimientos = 0

    def comparar(self):
        self.comparaciones += 1

    def mover(self):
        self.movimientos += 1

    def __repr__(self):
        return f"ContadorOperaciones(comparaciones={self.comparaciones}, movimientos={self.movimientos})"


def insertion_sort(datos, clave=_clave_identidad, contador=None, *, _limite=None):
    # Estable. Adaptativo: O(n) si los datos ya vienen casi ordenados, O(n^2) en el
    # peor caso (orden inverso). Barato de arrancar: sin recursion ni arreglos auxiliares.
    resultado = list(datos)
    n = len(resultado)
    movimientos = 0

    for i in range(1, n):
        actual = resultado[i]
        clave_actual = clave(actual)
        j = i - 1

        while j >= 0:
            if contador is not None:
                contador.comparar()
            if clave(resultado[j]) > clave_actual:
                if _limite is not None and movimientos >= _limite:
                    return None
                resultado[j + 1] = resultado[j]
                movimientos += 1
                if contador is not None:
                    contador.mover()
                j -= 1
            else:
                break

        resultado[j + 1] = actual

    return resultado


def merge_sort(datos, clave=_clave_identidad, contador=None):
    # Estable. Garantiza O(n log n) comparaciones sin importar el orden inicial de
    # entrada, a costa de arreglos auxiliares en cada nivel de la recursion.
    lista = list(datos)
    if len(lista) <= 1:
        return lista
    return _mezclar_recursivo(lista, clave, contador)


def _mezclar_recursivo(lista, clave, contador):
    if len(lista) <= 1:
        return lista

    medio = len(lista) // 2
    izquierda = _mezclar_recursivo(lista[:medio], clave, contador)
    derecha = _mezclar_recursivo(lista[medio:], clave, contador)
    return _mezclar(izquierda, derecha, clave, contador)


def _mezclar(izquierda, derecha, clave, contador):
    resultado = []
    i = j = 0

    while i < len(izquierda) and j < len(derecha):
        if contador is not None:
            contador.comparar()
        # "<=" preserva estabilidad: en un empate siempre gana el elemento de la izquierda,
        # que es el que estaba primero en la lista original.
        if clave(izquierda[i]) <= clave(derecha[j]):
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1
        if contador is not None:
            contador.mover()

    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])
    return resultado


def _contar_descensos(datos, clave):
    # Una sola pasada O(n): cuenta los puntos donde el orden se rompe.
    # No es el numero exacto de inversiones (calcularlo costaria O(n log n) con
    # merge sort o mas), pero alcanza como señal barata de "que tan desordenado esta".
    descensos = 0
    for i in range(1, len(datos)):
        if clave(datos[i - 1]) > clave(datos[i]):
            descensos += 1
    return descensos


def ordenar(datos, clave=_clave_identidad, comparacion_costosa=False, contador=None):
    # Selecciona automaticamente el algoritmo segun tamano, nivel de desorden y si
    # el llamador marca la comparacion como costosa. Devuelve (resultado, nombre_usado)
    # para que quien mida con --bench sepa cual algoritmo corrio realmente.
    n = len(datos)
    umbral_pequeno = UMBRAL_TAMANO_PEQUENO_COSTOSO if comparacion_costosa else UMBRAL_TAMANO_PEQUENO

    if n <= umbral_pequeno:
        return insertion_sort(datos, clave, contador), "insertion_sort"

    if not comparacion_costosa:
        descensos = _contar_descensos(datos, clave)
        if descensos <= n * UMBRAL_PROPORCION_DESORDEN:
            # Pocos descensos pueden esconder muchas inversiones (dos bloques
            # ordenados en posicion inversa). Limitar el intento evita O(n^2).
            resultado = insertion_sort(datos, clave, contador, _limite=n * n.bit_length())
            if resultado is not None:
                return resultado, "insertion_sort"

    return merge_sort(datos, clave, contador), "merge_sort"


def vista_ordenada(datos, clave=_clave_identidad):
    # Atajo para el caso de uso mas comun (ej. vistas del inventario): solo interesa
    # la lista resultante, no cual algoritmo se uso.
    resultado, _ = ordenar(datos, clave)
    return resultado
