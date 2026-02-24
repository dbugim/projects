import subprocess
import pyautogui
import time
import pytesseract
from PIL import Image
import io
import os
from datetime import datetime, timedelta
import pyperclip # Importa a biblioteca pyperclip

# Configure o caminho para o executável do Tesseract OCR
# Substitua pelo caminho onde você instalou o Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ler_texto_da_tela(x1, y1, x2, y2):
    """
    Captura uma região da tela e usa OCR para extrair o texto.

    Args:
        x1, y1: Coordenadas do canto superior esquerdo da região.
        x2, y2: Coordenadas do canto inferior direito da região.

    Returns:
        O texto extraído da região.
    """
    print(f"Capturando região da tela: ({x1},{y1}) a ({x2},{y2})...")
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))

    # Usa Tesseract para extrair texto da imagem
    texto_extraido = pytesseract.image_to_string(screenshot, lang='por', config='--psm 6')

    return texto_extraido.strip()

def automatizar_tarefas_windows():
    print("Abrindo o Telegram...")
    try:
        subprocess.Popen([r"C:\Users\danie\AppData\Roaming\Telegram Desktop\Telegram.exe"])
        time.sleep(5)
    except FileNotFoundError:
        print("Erro: O aplicativo 'Telegram.exe' não foi encontrado. Verifique o caminho.")
        return

    # region Acessando o campo de busca de inscritos
    x_coord_clique_inicial = 285
    y_coord_clique_inicial = 47
    print(f"Clicando na coordenada ({x_coord_clique_inicial}, {y_coord_clique_inicial}) 5 vezes...")
    pyautogui.click(x=x_coord_clique_inicial, y=y_coord_clique_inicial, clicks=5, interval=0.1)
    time.sleep(2)

    print("Pressionando Backspace 10 vezes para limpar o campo...")
    pyautogui.press('backspace', presses=10, interval=0.1)
    time.sleep(1)

    pyautogui.click(x_coord_clique_inicial, y_coord_clique_inicial)
    time.sleep(1)

    print("Digitando Electra VIP House'...")
    pyautogui.write('Electra VIP House')
    time.sleep(3)

    print("Clicando no canal Electra VIP House...")
    pyautogui.click(x=284, y=107)
    time.sleep(3)

    print("Clicando em mais opções do canal...")
    pyautogui.click(x=644, y=49)
    time.sleep(3)

    for _ in range(20):
        pyautogui.press('down')

    print("Clicando nos inscritos do canal...")
    pyautogui.click(x=662, y=561)
    time.sleep(3)

    print("Clicando no campo de busca inscritos do canal...")
    pyautogui.click(x=644, y=132)
    time.sleep(3)

    print("Digitando o nome do inscrito a cobrar'...")
    pyautogui.write('$')
    time.sleep(3)

    print("\nVerificando a tabela de inadimplentes...")

    regiao_x1 = 489
    regiao_y1 = 157
    regiao_x2 = 867
    regiao_y2 = 717

    time.sleep(3)

    texto_na_tela = ler_texto_da_tela(regiao_x1, regiao_y1, regiao_x2, regiao_y2)

    if texto_na_tela:
        print(f"\n--- Texto extraído da tela ---\n{texto_na_tela}\n-----------------------------")
    else:
        print("\nNenhum texto foi extraído da região especificada.")

#     if "$" in texto_na_tela:
#         print("Texto '$' encontrado na tela. Executando ações condicionais...")
#         pyautogui.click(x=642, y=698, clicks=5, interval=0.1)
#         time.sleep(1)

        mensagem = """𝕆𝕚

𝗤𝘂𝗲 𝘁𝗮𝗹 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗮𝗿 𝗰𝗼𝗻𝘁𝗿𝗶𝗯𝘂𝗶𝗻𝗱𝗼 𝗰𝗼𝗺 𝗮𝘀 𝗺𝗶𝗻𝗵𝗮𝘀 𝘁𝗿𝗮𝘃𝗲𝘀𝘀𝘂𝗿𝗮𝘀? 👅😈

𝗦ó R$14,99 𝗻𝗼 𝗣𝗜𝗫:
milfelectra@gmail.com 

𝗦ó 𝗺𝗲 𝗲𝗻𝘃𝗶𝗮𝗿 𝗼 𝗰𝗼𝗺𝗽𝗿𝗼𝘃𝗮𝗻𝘁𝗲 𝗾𝘂𝗲 𝗲𝘂 𝗷á 𝗹𝗶𝗯𝗲𝗿𝗼 𝗼 𝗮𝗰𝗲𝘀𝘀𝗼 𝗽𝗮𝗿𝗮 𝘁𝗶 ♥️

⭐️ OFERTAS ⭐️

- Plano trimestral: 31,99 no pix!
- Plano semestral: 55,99 no pix!

Mas se não puder por enquanto, continue me seguindo aqui, gratuitamente 👉🏻 https://t.me/milfelectrafree

Ou no Instagram: https://www.instagram.com/sraelectra

💋💋💋💋💋💋💋💋💋💋💋💋💋"""

        print("Copiando a mensagem para a área de transferência e colando...")
        pyperclip.copy(mensagem) # Copia a mensagem para a área de transferência
        time.sleep(0.5) # Pequena pausa para garantir que a cópia foi processada
        pyautogui.hotkey('ctrl', 'v') # Cola o conteúdo da área de transferência
        time.sleep(2) # Espera 2 segundos após colar

#         print("Pressionando ENTER...")
#         pyautogui.press('enter')
#         time.sleep(1)
    # else:
    #     print("Texto '987897897897' NÃO encontrado na tela. Seguindo para o final da automação.")

    print("Automação concluída.")

if __name__ == "__main__":
    automatizar_tarefas_windows()
