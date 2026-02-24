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

def mostra_tabela_de_inadimplentes():
    """
    Captura a região da tela onde a tabela de inadimplentes é esperada
    e extrai as ocorrências de texto que contêm '$'.
    """
    # Coordenadas da região onde a tabela de inadimplentes aparece
    # Ajuste essas coordenadas conforme a sua tela e a posição do Telegram
    x1_regiao, y1_regiao, x2_regiao, y2_regiao = 489, 169, 867, 464

    ocorrencias = ler_texto_e_coordenadas_da_tela(x1_regiao, y1_regiao, x2_regiao, y2_regiao)

    ocorrencias_filtradas = [
        item for item in ocorrencias if '$' in item['text']
    ]

    if ocorrencias_filtradas:
        print("\n--- Texto extraído da tela com coordenadas ---")
        for i, item in enumerate(ocorrencias_filtradas):
            x1_item, y1_item, x2_item, y2_item = item['bbox']
            print(f"Ocorrência {i+1}: {item['text']} (Região: x1={x1_item}, y1={y1_item}, x2={x2_item}, y2={y2_item})")
        print("---------------------------------------------")
    else:
        print("Nenhuma ocorrência com '$' encontrada na região especificada.")

    return ocorrencias_filtradas

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
                        break # Sai do loop interno se um elemento não for encontrado
                except pyautogui.ImageNotFoundException:
                    print(f"  ❌ Elemento '{elemento_img}' NÃO encontrado (exceção).")
                    todos_elementos_encontrados = False
                    break # Sai do loop interno se um elemento não for encontrado
                except Exception as e:
                    print(f"  ⚠️ Erro inesperado ao verificar elemento '{elemento_img}': {e}")
                    todos_elementos_encontrados = False
                    break # Sai do loop interno em caso de erro inesperado

            if todos_elementos_encontrados:
                telegram_aberto_e_maximizado = True
                print("🎉 Telegram aparentemente aberto de forma maximizada aguardando instruções!")
                break
            else:
                if tentativa < max_tentativas - 1:
                    print(f"Aguardando {intervalo_tentativas} segundos para a próxima tentativa...")
                    time.sleep(intervalo_tentativas)
                else:
                    print("❌ Não foi possível confirmar que o Telegram está aberto e maximizado após várias tentativas.")
                    # Aqui você pode adicionar uma lógica para encerrar o script ou tentar outra abordagem
                    exit() # Encerra o script se o Telegram não abrir corretamente

    except FileNotFoundError:
        print(f"❌ Erro: O executável do Telegram não foi encontrado no caminho: {telegram_path}")
        exit()
    except Exception as e:
        print(f"❌ Ocorreu um erro ao tentar abrir o Telegram: {e}")
        exit()

def main():

    abre_telegram_e_confere()

    time.sleep(2)

    # --- Acessando o campo de busca de contatos, grupos e canais ---
    busca_canal_path = r"C:\Users\danie\Desktop\projects\telegram\busca_canal_telegram.png"
    print(f"Clicando no campo de busca de canais ('{busca_canal_path}')...")
    try:
        busca_canal_location = pyautogui.locateCenterOnScreen(busca_canal_path, confidence=0.9, grayscale=True)
        if busca_canal_location:
            pyautogui.click(busca_canal_location)
            print(f"  ✅ Campo de busca de canais encontrado e clicado em: {busca_canal_location}")
            time.sleep(2)
        else:
            print(f"  ❌ Campo de busca de canais '{busca_canal_path}' NÃO encontrado na tela. Encerrando automação.")
            return # Sai da função main
    except pyautogui.ImageNotFoundException:
        print(f"  ❌ Campo de busca de canais '{busca_canal_path}' NÃO encontrado (exceção). Encerrando automação.")
        return
    except Exception as e:
        print(f"  ⚠️ Erro inesperado ao tentar clicar no campo de busca de canais: {e}. Encerrando automação.")
        return

    # --- Digitando o nome do canal "Electra VIP House" ---
    nome_canal = "Electra VIP House"
    print(f"Digitando o nome do canal: '{nome_canal}'...")
    pyautogui.write(nome_canal)
    time.sleep(3)

    # --- Clicando no canal "Electra VIP House" ---
    canal_electra_path = r"C:\Users\danie\Desktop\projects\telegram\canal_electra_vip_house.png"
    print(f"Clicando no canal '{nome_canal}' ('{canal_electra_path}')...")
    try:
        canal_electra_location = pyautogui.locateCenterOnScreen(canal_electra_path, confidence=0.9, grayscale=True)
        if canal_electra_location:
            pyautogui.click(canal_electra_location)
            print(f"  ✅ Canal '{nome_canal}' encontrado e clicado em: {canal_electra_location}")
            time.sleep(3)
        else:
            print(f"  ❌ Canal '{nome_canal}' '{canal_electra_path}' NÃO encontrado na tela. Encerrando automação.")
            return # Sai da função main
    except pyautogui.ImageNotFoundException:
        print(f"  ❌ Canal '{nome_canal}' '{canal_electra_path}' NÃO encontrado (exceção). Encerrando automação.")
        return
    except Exception as e:
        print(f"  ⚠️ Erro inesperado ao tentar clicar no canal '{nome_canal}': {e}. Encerrando automação.")
        return

    # --- LOOP PRINCIPAL PARA PROCESSAR CADA INADIMPLENTE ---
    while True:
        print("\n--- Iniciando nova iteração para encontrar e processar inadimplentes ---")

        # Clica em mais opções do canal (isso abre o painel lateral com a opção "Inscritos")
        print("Clicando em mais opções do canal...")
        pyautogui.click(x=644, y=49) # Coordenada fixa para "mais opções"
        time.sleep(3)

        # --- NOVO: Clica em uma área do painel lateral para garantir o foco antes de rolar ---
        # ATENÇÃO: Você precisará ajustar essas coordenadas (x_painel_lateral, y_painel_lateral)
        # para um ponto *dentro* do painel lateral que aparece.
        # Por exemplo, pode ser o topo do painel ou uma área vazia.
        # Use pyautogui.displayMousePosition() para encontrar uma coordenada segura.
        x_painel_lateral = 750 # Exemplo: ajuste para uma coordenada X dentro do painel
        y_painel_lateral = 100 # Exemplo: ajuste para uma coordenada Y dentro do painel
        print(f"Clicando no painel lateral em ({x_painel_lateral}, {y_painel_lateral}) para garantir o foco...")
        pyautogui.click(x=x_painel_lateral, y=y_painel_lateral)
        time.sleep(1) # Pequena pausa para o foco ser estabelecido
        # --- FIM DO NOVO CLIQUE PARA FOCO ---

        # --- ROLAGEM DA TELA PARA EXIBIR OS INSCRITOS ---
        print("Rolando a tela para baixo para exibir a opção 'Inscritos'...")
        for _ in range(20):
            pyautogui.press('down')
        time.sleep(2) # Pequena pausa após a rolagem
        # --- FIM DA ROLAGEM ---

        print("Clicando nos inscritos do canal...")
        pyautogui.click(x=662, y=561) # Coordenada fixa para "Inscritos"
        time.sleep(3)

        print("Clicando no campo de busca inscritos do canal...")
        pyautogui.click(x=644, y=132) # Coordenada fixa para o campo de busca de inscritos
        time.sleep(3)

        print("Digitando o nome do inscrito a cobrar'...")
        pyautogui.write('$ 01/03/2026') # Altere conforme a data de corte desejada
        time.sleep(3)

        ocorrencias_encontradas = mostra_tabela_de_inadimplentes()

        if not ocorrencias_encontradas:
            print("\nNenhuma ocorrência com '$' foi encontrada na região especificada. Automação de cobrança concluída.")
            break # Sai do loop while True se não houver mais ocorrências

        # Loop para processar cada ocorrência visível na tela
        for i, item_ocorrencia in enumerate(ocorrencias_encontradas):
            print(f"Processando Ocorrência {i+1}: {item_ocorrencia['text']}")

            # Clica na ocorrência atual
            x1_item, y1_item, x2_item, y2_item = item_ocorrencia['bbox']
            pyautogui.click(x=(x1_item + x2_item) / 2, y=(y1_item + y2_item) / 2)
            time.sleep(3)

            # --- Clicando no botão de mensagem ---
            message_button_path = r"C:\Users\danie\Desktop\projects\telegram\message_button_telegram.png"
            print(f"Clicando no botão de mensagem ('{message_button_path}')...")
            try:
                message_button_location = pyautogui.locateCenterOnScreen(message_button_path, confidence=0.8, grayscale=True)
                if message_button_location:
                    pyautogui.click(message_button_location)
                    print(f"  ✅ Botão de mensagem encontrado e clicado em: {message_button_location}")
                    time.sleep(3)
                else:
                    print(f"  ❌ Botão de mensagem '{message_button_path}' NÃO encontrado na tela. Pulando para o próximo inadimplente.")
                    continue # Pula para a próxima ocorrência no loop 'for'
            except pyautogui.ImageNotFoundException:
                print(f"  ❌ Botão de mensagem '{message_button_path}' NÃO encontrado (exceção). Pulando para o próximo inadimplente.")
                continue
            except Exception as e:
                print(f"  ⚠️ Erro inesperado ao tentar clicar no botão de mensagem: {e}. Pulando para o próximo inadimplente.")
                continue

            # --- Clicando no campo de digitação de mensagem ---
            message_field_path = r"C:\Users\danie\Desktop\projects\telegram\write_a_message_telegram.png" # Verifique se esta imagem é para o campo de digitação
            print(f"Clicando no campo de digitação de mensagem ('{message_field_path}')...")
            try:
                message_field_location = pyautogui.locateCenterOnScreen(message_field_path, confidence=0.8, grayscale=True)
                if message_field_location:
                    pyautogui.click(message_field_location)
                    print(f"  ✅ Campo de digitação de mensagem encontrado e clicado em: {message_field_location}")
                    time.sleep(3)
                else:
                    print(f"  ❌ Campo de digitação de mensagem '{message_field_path}' NÃO encontrado na tela. Pulando para o próximo inadimplente.")
                    continue
            except pyautogui.ImageNotFoundException:
                print(f"  ❌ Campo de digitação de mensagem '{message_field_path}' NÃO encontrado (exceção). Pulando para o próximo inadimplente.")
                continue
            except Exception as e:
                print(f"  ⚠️ Erro inesperado ao tentar clicar no campo de digitação de mensagem: {e}. Pulando para o próximo inadimplente.")
                continue

            # --- Insere mensagem de cobrança ---
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
            # pyautogui.press('enter') # Mantido comentado conforme sua instrução
            # time.sleep(2)

            # --- Clica na seta para voltar ---
            click_back_path = r"C:\Users\danie\Desktop\projects\telegram\seta_para_voltar_telegram.png"
            print(f"Clicando na seta para voltar e sair da mensagem ('{click_back_path}')...")
            try:
                click_back_location = pyautogui.locateCenterOnScreen(click_back_path, confidence=0.8, grayscale=True)
                if click_back_location:
                    pyautogui.click(click_back_location)
                    print(f"  ✅ Seta para voltar encontrada e clicada em: {click_back_location}")
                    time.sleep(3)
                else:
                    print(f"  ❌ Seta para voltar '{click_back_path}' NÃO encontrada na tela. A automação pode estar em um estado inesperado.")
                    return # Sai da função main, encerrando a automação.
            except pyautogui.ImageNotFoundException:
                print(f"  ❌ Seta para voltar '{click_back_path}' NÃO encontrada (exceção). A automação pode estar em um estado inesperado.")
                return
            except Exception as e:
                print(f"  ⚠️ Erro inesperado ao tentar clicar na seta para voltar: {e}. A automação pode estar em um estado inesperado.")
                return

            # --- Lógica para retornar ao título do canal e re-iniciar a busca ---
            # Após processar UM inadimplente e voltar, precisamos re-acessar a lista.
            # Clica no título do canal para voltar à tela principal do canal (onde a lista de inscritos está)
            chanel_title_path = r"C:\Users\danie\Desktop\projects\telegram\chanel_title_telegram.png"
            print(f"Clicando no título do canal para retornar à lista ('{chanel_title_path}')...")
            try:
                chanel_title_location = pyautogui.locateCenterOnScreen(chanel_title_path, confidence=0.9, grayscale=True)
                if chanel_title_location:
                    pyautogui.click(chanel_title_location)
                    print(f"  ✅ Título do canal encontrado e clicado em: {chanel_title_location}")
                    time.sleep(3)
                    # O `break` aqui é crucial para sair do loop `for` interno e permitir que o `while True`
                    # comece uma nova iteração, re-escaneando a lista de inadimplentes.
                    break 
                else:
                    print(f"  ❌ Título do canal '{chanel_title_path}' NÃO encontrado na tela. A automação pode estar em um estado inesperado.")
                    return # Sai da função main, encerrando a automação.
            except pyautogui.ImageNotFoundException:
                print(f"  ❌ Título do canal '{chanel_title_path}' NÃO encontrado (exceção). A automação pode estar em um estado inesperado.")
                return
            except Exception as e:
                print(f"  ⚠️ Erro inesperado ao tentar clicar no título do canal: {e}. A automação pode estar em um estado inesperado.")
                return

    # --- FIM DO LOOP PRINCIPAL ---

    print("Automação concluída.")

if __name__ == "__main__":
    main()
