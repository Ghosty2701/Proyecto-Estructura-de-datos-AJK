class ErrorBitacora(Exception):
    pass

class EncabezadoLog:
    def __init__(self, id_cripta, version_cripta, version_catalogo, semilla):
        self.id_cripta = id_cripta
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.semilla = semilla

class EscritorBitacora:
    def __init__(self, ruta, id_cripta, version_cripta, version_catalogo, semilla):
        try:
            self.archivo = open(ruta, "x")
        except FileExistsError as error:
            raise ErrorBitacora(f"la bitacora {ruta} ya existe") from error

        self.archivo.write("CRIPTA-LOG 1\n")
        self.archivo.write(f"cripta={id_cripta}\n")
        self.archivo.write(f"version_cripta={version_cripta}\n")
        self.archivo.write(f"version_catalogo={version_catalogo}\n")
        self.archivo.write(f"semilla={semilla}\n")
        self.archivo.write("---\n")
        self.archivo.flush()

    def registrar_accion(self, accion):
        if "\n" in accion:
            raise ErrorBitacora("una accion no puede contener saltos de linea")
        self.archivo.write(accion + "\n")
        self.archivo.flush()

    def cerrar(self):
        self.archivo.close()

# ------------------------------------------------------------------------------------------------------------

def _leer_valor(archivo, clave_esperada):
    linea = archivo.readline().rstrip("\n")
    clave, separador, valor = linea.partition("=")
    if separador == "" or clave != clave_esperada:
        raise ErrorBitacora(f"encabezado mal formado: se esperaba '{clave_esperada}=###'")
    return valor


def leer_bitacora(ruta):
    try:
        with open(ruta) as archivo:
            if archivo.readline().rstrip("\n") != "CRIPTA-LOG 1":
                raise ErrorBitacora(f"{ruta} no es una bitacora de Cripta")

            id_cripta = _leer_valor(archivo, "cripta")
            version_cripta = _leer_valor(archivo, "version_cripta")
            version_catalogo = _leer_valor(archivo, "version_catalogo")
            semilla_texto = _leer_valor(archivo, "semilla")

            if archivo.readline().rstrip("\n") != "---":
                raise ErrorBitacora("encabezado mal formado")

            acciones = []
            for linea in archivo:
                acciones.append(linea.rstrip("\n"))
    except FileNotFoundError as error:
        raise ErrorBitacora(f"no existe la bitacora {ruta}") from error

    try:
        semilla = int(semilla_texto)
    except ValueError as error:
        raise ErrorBitacora(f"la semilla '{semilla_texto}' no es un numero entero") from error

    return EncabezadoLog(id_cripta, version_cripta, version_catalogo, semilla), acciones


def verificar_compatibilidad(encabezado, id_cripta_actual, version_cripta_actual, version_catalogo_actual):
    if encabezado.id_cripta != id_cripta_actual:
        raise ErrorBitacora(
            f"el log es de la cripta '{encabezado.id_cripta}' y se esta usando '{id_cripta_actual}': "
            "no se puede garantizar una reproduccion fiel")

    if encabezado.version_cripta != version_cripta_actual:
        raise ErrorBitacora(
            f"el log uso la version '{encabezado.version_cripta}' de la cripta pero la actual es "
            f"'{version_cripta_actual}': no se puede garantizar una reproduccion fiel")

    if encabezado.version_catalogo != version_catalogo_actual:
        raise ErrorBitacora(
            f"el log uso la version '{encabezado.version_catalogo}' del catalogo pero la actual es "
            f"'{version_catalogo_actual}': no se puede garantizar una reproduccion fiel")