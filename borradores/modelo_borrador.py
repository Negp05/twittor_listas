# modelo_borrador.py

# Lista global para almacenar los borradores
borradores = []

class Borrador:
    """Representa un borrador de tweet."""
    def __init__(self, id, contenido, publicado=False):
        self.id = id
        self.contenido = contenido
        self.publicado = publicado

    def __str__(self):
        """Devuelve una representación legible del borrador."""
        estado = "Publicado ✅" if self.publicado else "Pendiente ✏️"
        return f"[{self.id}] {self.contenido} - {estado}"

