import pyautogui
import time

print("Mova o mouse para ver as coordenadas. Pressione Ctrl+C para sair.")

try:
    while True:
        # Obtém a posição atual do mouse
        x, y = pyautogui.position()
        # Imprime as coordenadas. O '\r' faz com que a linha seja sobrescrita.
        print(f"Coordenadas do mouse: X={x}, Y={y}       ", end='\r')
        time.sleep(0.1) # Pequena pausa para não sobrecarregar a CPU
except KeyboardInterrupt:
    print("\nPrograma encerrado.")
