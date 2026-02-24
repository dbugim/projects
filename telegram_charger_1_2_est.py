import subprocess
import pyautogui
import time
import pytesseract
from PIL import Image
import io
import os
from datetime import datetime, timedelta
import pyperclip
import pandas as pd # Importa pandas para facilitar a manipulação dos dados do Tesseract

# Configure o caminho para o executável do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ler_texto_e_coordenadas_da_tela(x1, y1, x2, y2):
    """
    Captura uma região da tela e usa OCR para extrair texto e suas coordenadas.

    Args:
        x1, y1: Coordenadas do canto superior esquerdo da região.
        x2, y2: Coordenadas do canto inferior direito da região.

    Returns:
        Uma lista de dicionários, onde cada dicionário contém 'text' e 'bbox' (bounding box).
    """
    print(f"Capturando região da tela para OCR detalhado: ({x1},{y1}) a ({x2},{y2})...")
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))

    # Usa Tesseract para extrair dados detalhados, incluindo bounding boxes
    # output_type=pytesseract.Output.DATAFRAME converte o resultado em um DataFrame do pandas
    data = pytesseract.image_to_data(screenshot, lang='por', output_type=pytesseract.Output.DATAFRAME, config='--psm 6')

    # Remove linhas vazias e converte as coordenadas para o sistema de coordenadas da tela
    # Adiciona as coordenadas x1, y1 da região capturada para obter as coordenadas absolutas na tela
    data = data.dropna(subset=['text'])

    # Resetar o índice após dropar linhas para garantir que 'index' seja sequencial
    data = data.reset_index(drop=True) 

    data['left'] = data['left'] + x1
    data['top'] = data['top'] + y1
    data['right'] = data['left'] + data['width']
    data['bottom'] = data['top'] + data['height']

    # Agrupa as palavras em linhas para obter as bounding boxes das linhas
    lines = []
    current_line_text = []
    current_line_bbox = {'left': float('inf'), 'top': float('inf'), 'right': float('-inf'), 'bottom': float('-inf')}

    for index, row in data.iterrows():
        if row['text'] and str(row['text']).strip(): # Garante que o texto não é vazio
            # Verifica se é uma nova linha (baseado na coordenada 'top' e 'line_num')
            # Adicionei a condição 'index > 0' para evitar o KeyError na primeira iteração
            is_new_line = True
            if index > 0:
                prev_row = data.loc[index-1]
                if (row['block_num'] == prev_row['block_num'] and
                    row['par_num'] == prev_row['par_num'] and
                    row['line_num'] == prev_row['line_num']):
                    is_new_line = False

            if is_new_line:
                if current_line_text: # Salva a linha anterior se houver
                    lines.append({
                        'text': ' '.join(current_line_text),
                        'bbox': (current_line_bbox['left'], current_line_bbox['top'],
                                 current_line_bbox['right'], current_line_bbox['bottom'])
                    })
                current_line_text = [str(row['text'])]
                current_line_bbox = {'left': row['left'], 'top': row['top'],
                                     'right': row['right'], 'bottom': row['bottom']}
            else:
                current_line_text.append(str(row['text']))
                current_line_bbox['left'] = min(current_line_bbox['left'], row['left'])
                current_line_bbox['top'] = min(current_line_bbox['top'], row['top'])
                current_line_bbox['right'] = max(current_line_bbox['right'], row['right'])
                current_line_bbox['bottom'] = max(current_line_bbox['bottom'], row['bottom'])

    if current_line_text: # Adiciona a última linha
        lines.append({
            'text': ' '.join(current_line_text),
            'bbox': (current_line_bbox['left'], current_line_bbox['top'],
                     current_line_bbox['right'], current_line_bbox['bottom'])
        })

    return lines

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
    pyautogui.write('$ 01/03/2026') # Alterado para o exemplo que você deu
    time.sleep(3)

    print("\nVerificando a tabela de inadimplentes...")

    regiao_x1 = 489
    regiao_y1 = 157
    regiao_x2 = 867
    regiao_y2 = 717

    time.sleep(3)

    linhas_com_coordenadas = ler_texto_e_coordenadas_da_tela(regiao_x1, regiao_y1, regiao_x2, regiao_y2)

    if linhas_com_coordenadas:
        ocorrencias_encontradas = []
        for item in linhas_com_coordenadas:
            if '$' in item['text']: # Mantém a verificação para '$' no texto
                ocorrencias_encontradas.append(item)

        if ocorrencias_encontradas:
            print(f"{len(ocorrencias_encontradas)} ocorrências encontradas")
            print("\n--- Texto extraído da tela com coordenadas ---")
            for i, item in enumerate(ocorrencias_encontradas):
                x1_item, y1_item, x2_item, y2_item = item['bbox']
                print(f"Ocorrência {i+1}: {item['text']} (Região: x1={x1_item}, y1={y1_item}, x2={x2_item}, y2={y2_item})")
            print("---------------------------------------------")

            # Lógica para clicar na primeira ocorrência e enviar mensagem
            print("Clicando na ocorrência 1...")
            primeira_ocorrencia_bbox = ocorrencias_encontradas[0]['bbox']
            # Clica no centro da primeira ocorrência
            pyautogui.click(x=(primeira_ocorrencia_bbox[0] + primeira_ocorrencia_bbox[2]) / 2,
                            y=(primeira_ocorrencia_bbox[1] + primeira_ocorrencia_bbox[3]) / 2)
            time.sleep(3)

            print("Clicando no botão message...")
            pyautogui.click(x=545, y=240)
            time.sleep(3)

            print("Clicando no campo de texto para enviar mensagem a este inscrito...")
            pyautogui.click(x=612, y=694)
            time.sleep(3)

            print("Inserindo mensagem de cobrança")
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
            pyautogui.press('enter') # Adiciona um ENTER para enviar a mensagem
            time.sleep(1) # Espera após enviar

            print("Clicando para retornar...")
            pyautogui.click(x=557, y=51)
            time.sleep(3)

        else:
            print("\nNenhuma ocorrência com '$ 01/03' foi encontrada na região especificada.")
    else:
        print("\nNenhum texto foi extraído da região especificada.")

    print("Automação concluída.")

if __name__ == "__main__":
    automatizar_tarefas_windows()
