import time
import random

SEMILLA_BENCH = 2042

class NodoSimple:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None


class ArbolSimple:
    def __init__(self):
        self.raiz = None
        self.altura = 0

    def insertar(self, clave, valor):
        nuevo = NodoSimple(clave, valor)
        if self.raiz is None:
            self.raiz = nuevo
            self.altura = 1
            return

        actual = self.raiz
        nivel = 1
        while True:
            if clave == actual.clave:
                actual.valor = valor
                return
            nivel += 1
            if clave < actual.clave:
                if actual.izquierdo is None:
                    actual.izquierdo = nuevo
                    break
                actual = actual.izquierdo
            else:
                if actual.derecho is None:
                    actual.derecho = nuevo
                    break
                actual = actual.derecho

        if nivel > self.altura:
            self.altura = nivel

    def buscar(self, clave):
        nodo = self.raiz
        while nodo is not None:
            if clave == nodo.clave:
                return nodo.valor
            if clave < nodo.clave:
                nodo = nodo.izquierdo
            else:
                nodo = nodo.derecho
        return None

def medir(funcion, repeticiones, rondas=5):
    mejor = None
    for ronda in range(rondas):
        inicio = time.perf_counter()
        for i in range(repeticiones):
            funcion()
        promedio = (time.perf_counter() - inicio) / repeticiones
        if mejor is None or promedio < mejor:
            mejor = promedio
    return mejor * 1_000_000


def mostrar(nombre, microsegundos):
    print(f"  {nombre:<40} {microsegundos:10.3f} us")

def generar_ids(cantidad, mezclados):
    ids = [f"ficha_{numero:06d}" for numero in range(cantidad)]
    if mezclados:
        random.Random(SEMILLA_BENCH).shuffle(ids)
    return ids


def construir(clase_arbol, ids):
    arbol = clase_arbol()
    for posicion in range(len(ids)):
        arbol.insertar(ids[posicion], posicion)
    return arbol


def microsegundos_por_busqueda(arbol, ids, repeticiones):
    def buscar_todos():
        for id_ficha in ids:
            arbol.buscar(id_ficha)
    return medir(buscar_todos, repeticiones) / len(ids)


def microsegundos_por_insercion(clase_arbol, ids, repeticiones):
    return medir(lambda: construir(clase_arbol, ids), repeticiones) / len(ids)

def bench_busqueda_cache():
    print("Busqueda en la cache: AVL vs arbol simple")
    print(f"  {'n':<6}{'orden':<11}{'altura AVL/simple':<20}{'buscar AVL/simple':<22}{'insertar AVL/simple'}")

    for cantidad in (25, 100, 1000):
        for mezclados in (False, True):
            ids = generar_ids(cantidad, mezclados)
            repeticiones = max(2, 5000 // cantidad)

            avl = construir(ArbolAVL, ids)
            simple = construir(ArbolSimple, ids)

            buscar_avl = microsegundos_por_busqueda(avl, ids, repeticiones)
            buscar_simple = microsegundos_por_busqueda(simple, ids, repeticiones)
            insertar_avl = microsegundos_por_insercion(ArbolAVL, ids, repeticiones)
            insertar_simple = microsegundos_por_insercion(ArbolSimple, ids, repeticiones)

            orden = "mezclados" if mezclados else "ordenados"
            alturas = f"{avl.raiz.altura} / {simple.altura}"
            buscar = f"{buscar_avl:.3f} / {buscar_simple:.3f}"
            insertar = f"{insertar_avl:.3f} / {insertar_simple:.3f}"
            print(f"  {cantidad:<6}{orden:<11}{alturas:<20}{buscar:<22}{insertar}")


def ejecutar_bench():
    bench_busqueda_cache()


if __name__ == "__main__":
    ejecutar_bench()