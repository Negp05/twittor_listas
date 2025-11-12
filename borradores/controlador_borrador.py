# controlador_borrador.py

import sys
import os

# Asegura que Python reconozca la carpeta actual como parte del path del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .modelo_borrador import Borrador, borradores


def guardar_borrador(contenido):
    """Guarda un nuevo borrador en la lista."""
    nuevo_id = len(borradores) + 1
    nuevo = Borrador(nuevo_id, contenido)
    borradores.append(nuevo)
    print(f"✅ Borrador guardado: {contenido}")


def listar_borradores():
    """Devuelve todos los borradores existentes."""
    return borradores


def publicar_borrador(id_borrador):
    """Marca un borrador como publicado según su ID."""
    for b in borradores:
        if b.id == id_borrador:
            b.publicado = True
            print(f"🚀 Borrador publicado: {b.contenido}")
            return
    print("⚠️ No se encontró el borrador con ese ID.")
