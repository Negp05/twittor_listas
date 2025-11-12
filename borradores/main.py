# main.py
from borradores.controlador_borrador import guardar_borrador, listar_borradores, publicar_borrador

guardar_borrador("Mi primer tweet 🐦")
guardar_borrador("Otro tweet sin publicar ✏️")

print("\n--- BORRADORES ---")
for b in listar_borradores():
    print(b)

publicar_borrador(1)

print("\n--- DESPUÉS DE PUBLICAR ---")
for b in listar_borradores():
    print(b)
