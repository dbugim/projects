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

# --- NOVA FUNÇÃO PARA CLICAR EM IMAGENS ---
def click_on_image(image_path, confidence=0.9, grayscale=False, description="elemento"):
    """
    Tenta localizar e clicar em uma imagem na tela.

    Args:
        image_path (str): Caminho completo para o arquivo da imagem.
        confidence (float): Nível de confiança para a correspondência da imagem (0.0 a 1.0).
        grayscale (bool): Se True, a imagem será convertida para escala de cinza antes da comparação.
        description (str): Descrição do elemento para mensagens de log.

    Returns:
        bool: True se o elemento foi encontrado e clicado, False caso contrário.
    """
    print(f"Clicando em {description} ('{image_path}')...")
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence, grayscale=grayscale)
        if location:
            pyautogui.click(location)
            print(f"  ✅ {description.capitalize()} encontrado e clicado em: {location}")
            return True
        else:
            # Se locateCenterOnScreen retornar None, significa que não encontrou com a confiança dada
            print(f"  ❌ {description.capitalize()} '{image_path}' NÃO encontrado na tela (locateCenterOnScreen retornou None).")
            return False
    except pyautogui.ImageNotFoundException:
        # Esta exceção é levantada se locateOnScreen não encontrar a imagem
        print(f"  ❌ {description.capitalize()} '{image_path}' NÃO encontrado (exceção ImageNotFoundException).")
        return False
    except Exception as e:
        print(f"  ⚠️ Erro inesperado ao tentar clicar em {description}: {e}")
        return False
# --- FIM DA NOVA FUNÇÃO ---


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

def abre_telegram_e_confere():

    telegram_path = r"C:\Users\danie\AppData\Roaming\Telegram Desktop\Telegram.exe"
    print("Abrindo o Telegram...")
    try:
        subprocess.Popen(f'start "" /max "{telegram_path}"', shell=True)
        time.sleep(5)

        elementos_para_verificar = [
        r"C:\Users\danie\Desktop\projects\telegram\menu_hamburguer_telegram.png",
        r"C:\Users\danie\Desktop\projects\telegram\opcoes_da_janela_telegram.png",     
    ]

        max_tentativas = 10
        intervalo_tentativas = 3 # segundos
        telegram_aberto_e_maximizado = False

        for tentativa in range(max_tentativas):
            print(f"Verificando elementos visuais do Telegram (Tentativa {tentativa + 1}/{max_tentativas})...")
            todos_elementos_encontrados = True

            for elemento_img in elementos_para_verificar:
                try:
                    localizacao = pyautogui.locateOnScreen(elemento_img, confidence=0.8)
                    if localizacao:
                        print(f"  ✅ Elemento '{elemento_img}' encontrado em: {localizacao}")
                    else:
                        print(f"  ❌ Elemento '{elemento_img}' NÃO encontrado.")
                        todos_elementos_encontrados = False
                        break # Se um elemento não for encontrado, não precisamos verificar os outros
                except pyautogui.ImageNotFoundException:
                    print(f"  ❌ Elemento '{elemento_img}' NÃO encontrado (exceção).")
                    todos_elementos_encontrados = False
                    break
                except Exception as e:
                    print(f"  ⚠️ Erro ao procurar '{elemento_img}': {e}")
                    todos_elementos_encontrados = False
                    break

            if todos_elementos_encontrados:
                telegram_aberto_e_maximizado = True
                break # Todos os elementos foram encontrados, podemos sair do loop de tentativas
            else:
                print(f"Aguardando {intervalo_tentativas} segundos antes de tentar novamente...")
                time.sleep(intervalo_tentativas)

        if telegram_aberto_e_maximizado:
            print("\n🎉 Telegram aparentemente aberto de forma maximizada aguardando instruções!")
        else:
            print("\n😔 Não foi possível confirmar que o Telegram está aberto e maximizado após várias tentativas.")

    except FileNotFoundError:
        print(f"Erro: O aplicativo '{telegram_path}' não foi encontrado. Verifique o caminho.")
    except Exception as e:
        print(f"Ocorreu um erro ao tentar abrir o Telegram ou verificar sua presença: {e}")

def mostra_tabela_de_inadimplentes():

    print("\nVerificando a tabela de inadimplentes...")

    regiao_x1 = 489
    regiao_y1 = 157
    regiao_x2 = 867
    regiao_y2 = 717

    time.sleep(3)

    linhas_com_coordenadas = ler_texto_e_coordenadas_da_tela(regiao_x1, regiao_y1, regiao_x2, regiao_y2)

    ocorrencias_encontradas = []
    if linhas_com_coordenadas:
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

    return ocorrencias_encontradas

def main():

    abre_telegram_e_confere()

    time.sleep(2)

    # region Acessando o campo de busca de contatos, grupos e canais
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

    print("Digitando o nome do inscrito a cobrar'...")
    pyautogui.write('$ 01/03/2026') # Altere conforme a data de corte desejada
    time.sleep(3)

    ocorrencias_encontradas = mostra_tabela_de_inadimplentes()

    # Loop para processar cada ocorrência visível na tela
    for i, item_ocorrencia in enumerate(ocorrencias_encontradas):
        print(f"Processando Ocorrência {i+1}: {item_ocorrencia['text']}")

        # Clica na ocorrência atual
        x1_item, y1_item, x2_item, y2_item = item_ocorrencia['bbox']
        pyautogui.click(x=(x1_item + x2_item) / 2, y=(y1_item + y2_item) / 2)
        time.sleep(3)

        # --- Chamadas usando a nova função click_on_image ---

        # Clica no botão de mensagem
        message_button_path = r"C:\Users\danie\Desktop\projects\telegram\message_button_telegram.png"
        if click_on_image(message_button_path, confidence=0.8, grayscale=True, description="botão de mensagem"):
            time.sleep(3) # Aguarda após o clique

            # Clica no campo de digitação de mensagem
            # ATENÇÃO: Certifique-se de que 'write_a_message_telegram.png' é a imagem correta para o campo de digitação!
            message_field_path = r"C:\Users\danie\Desktop\projects\telegram\write_a_message_telegram.png"
            if click_on_image(message_field_path, confidence=0.8, grayscale=True, description="campo de digitação de mensagem"):
                time.sleep(3) # Aguarda após o clique

                # Insere mensagem de cobrança
                mensagem_cobranca = """𝕆𝕚

    𝗤𝘂𝗲 𝘁𝗮𝗹 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗮𝗿 𝗰𝗼𝗻𝘁𝗿𝗶𝗯𝘂𝗶𝗻𝗱𝗼 𝗰𝗼𝗺 𝗮𝘀 𝗺𝗶𝗻𝗵𝗮𝘀 𝘁𝗿𝗮𝘃𝗲𝘀𝘀𝘂𝗿𝗮𝘀? 👅😈

    𝗦ó R$14,99 𝗻𝗼 𝗣𝗜𝗫:
    milfelectra@gmail.com 

    𝗦ó 𝗺𝗲 𝗲𝗻𝘃𝗶𝗮𝗿 𝗼 𝗰𝗼𝗺𝗽𝗿𝗼𝘃𝗮𝗻𝘁𝗲 𝗾𝘂𝗲 𝗲𝘂 𝗷á 𝗹𝗶𝗯𝗲𝗿𝗼 𝗼 𝗮𝗰𝗲𝘀𝘀𝗼 𝗽𝗮𝗿𝗮 𝘁𝗶 ♥️

    ⭐️ OFERTAS ⭐️

    - Plano trimestral: 31,99 no pix!
    - Plano semestral: 55,99 no pix!

    Mas se não puder por enquanto, continue me seguindo aqui, gratuitamente 👉🏻 https://t.me/milfelectrafree

    Ou no Instagram: https://www.instagram.com/sraelectra

    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
    CASO JÁ TENHA PAGADO, ME ENVIE O COMPROVANTE PARA NÃO PERDER O ACESSO!
    ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

    💋💋💋💋💋💋💋💋💋💋💋💋💋"""

                print("Inserindo mensagem de cobrança")
                pyperclip.copy(mensagem_cobranca)
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(2)
                # pyautogui.press('enter') # Comentado, pois você o tinha comentado
                # time.sleep(2)

                # Clica na seta para voltar
                click_back_path = r"C:\Users\danie\Desktop\projects\telegram\seta_para_voltar_telegram.png"
                if click_on_image(click_back_path, confidence=0.8, grayscale=True, description="seta para voltar"):
                    time.sleep(3) # Aguarda após o clique
                else:
                    print("  ⚠️ Não foi possível clicar na seta para voltar. Verifique a imagem ou o estado da tela.")
            else:
                print("  ⚠️ Não foi possível clicar no campo de digitação de mensagem. Verifique a imagem ou o estado da tela.")
        else:
            print("  ⚠️ Não foi possível clicar no botão de mensagem. Verifique a imagem ou o estado da tela.")

    print("Automação concluída.")

if __name__ == "__main__":
    main()
