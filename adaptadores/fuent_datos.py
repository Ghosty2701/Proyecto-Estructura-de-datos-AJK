class FuenteDatos:
    def listar_criptas(self):
        raise NotImplementedError

    def datos_cripta(self, cripta_id):
        raise NotImplementedError

    def pagina_esqueleto(self, cripta_id, pagina):
        raise NotImplementedError

    def contenido(self, cripta_id, salas):
        raise NotImplementedError

    def catalogo(self, ids):
        raise NotImplementedError

    def version_cripta(self, cripta_id):
        raise NotImplementedError

    def version_catalogo(self):
        raise NotImplementedError