from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QCalendarWidget, QDialog,
    QDialogButtonBox, QPushButton, QWidget, QApplication, QDesktopWidget, QMainWindow
)
from PyQt5.QtCore import QDate, QEventLoop, Qt, QEvent
from datetime import date, timedelta, datetime
import sys
import os
import random
import openpyxl
import pyperclip
import pyautogui
import time
import subprocess
import pandas as pd
import atexit
from playwright.sync_api import sync_playwright
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))  # Adjust path to include the parent directory

# Script to help build the executable with PyInstaller
try:
    # Para o executável PyInstaller
    sys.path.append(os.path.join(sys._MEIPASS, "repository"))
except Exception:
    # Para desenvolvimento
    sys.path.append(str(Path(__file__).resolve().parent.parent / "repository"))

class MyCalendar(QWidget):  # Changed to inherit from QWidget
    def __init__(self):
        super().__init__()  # Initialize the QWidget parent class
        # Create the initial dialog
        self.initial_dialog = self.InitialDialog(self)
        self.calendar_window = None
        self.date_list = []  # Store selected dates
        self.qt_days = 0  # Store the number of days

    def show(self):
        # Show the initial dialog
        self.initial_dialog.show()

    class InitialDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Atenção!")
            self.setGeometry(100, 100, 350, 200)

            # Centralize the window
            self.center()

            # Layout
            layout = QVBoxLayout()

            # Instruction text with increased font size
            instrucao = QLabel(
                "No calendário que irá aparecer selecione a data da última publicação!\n"
                "As publicações iniciarão a partir de amanhã, até a data escolhida!"
            )

            # Increase font size by 50%
            font = instrucao.font()
            current_size = font.pointSize()
            font.setPointSize(int(current_size * 1.5))
            instrucao.setFont(font)

            # Center the text
            instrucao.setAlignment(Qt.AlignCenter)
            layout.addWidget(instrucao)

            # OK button
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.ok_clicked)

            # Increase button font size
            button_font = ok_button.font()
            button_font.setPointSize(int(button_font.pointSize() * 1.5))
            ok_button.setFont(button_font)
            layout.addWidget(ok_button)

            # Set layout
            self.setLayout(layout)

        def ok_clicked(self):
            # Create and show the CalendarWindow, passing self.parent() as the parent
            self.calendar_window = MyCalendar.CalendarWindow(self.parent())
            self.calendar_window.show()

            # Wait for the CalendarWindow to close
            loop = QEventLoop()
            self.calendar_window.destroyed.connect(loop.quit)
            loop.exec_()

            # Close the initial dialog
            self.close()

        def center(self):
            # Center the window on the screen
            screen = QDesktopWidget().screenGeometry()
            size = self.geometry()
            self.move(
                (screen.width() - size.width()) // 2,
                (screen.height() - size.height()) // 2
            )

    class CalendarWindow(QMainWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Seleção de Data")
            self.setGeometry(100, 100, 400, 300)

            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            # Layout
            layout = QVBoxLayout(central_widget)

            # Label
            label = QLabel("Clique para informar até qual dia serão realizadas as postagens:")
            layout.addWidget(label)

            # Calendar widget
            self.calendar = QCalendarWidget()
            tomorrow = datetime.today() + timedelta(days=1)
            self.calendar.setMinimumDate(QDate(tomorrow.year, tomorrow.month, tomorrow.day))
            self.calendar.clicked.connect(self.date_selected)
            layout.addWidget(self.calendar)

            # Center the window
            self.center()

        def date_selected(self, date):
            selected_date = date.toString("dd/MM/yyyy")
            print(f"Data selecionada: {selected_date}")

            selected_date_obj = datetime.strptime(selected_date, "%d/%m/%Y").date()
            day_tomorrow = (datetime.today() + timedelta(days=1)).date()

            # Calculate the number of days between tomorrow and the selected date
            self.parent().qt_days = (selected_date_obj - day_tomorrow).days + 1  # Store qt_days in the parent
            print(f"Quantidade de dias: {self.parent().qt_days}")

            # Store the dates in the parent's date_list
            if self.parent():
                self.parent().date_list = [
                    (day_tomorrow + timedelta(days=i)).strftime("%d/%m/%Y")
                    for i in range(self.parent().qt_days)
                ]
                print(f"lista_datas = {self.parent().date_list}")
            else:
                print("Erro: Nenhum pai definido para CalendarWindow.")

            # Show the confirmation dialog
            confirmation_dialog = MyCalendar.ConfirmationDialog(selected_date, self)
            confirmation_dialog.exec_()

        def center(self):
            # Center the window on the screen
            screen = QDesktopWidget().screenGeometry()
            size = self.geometry()
            self.move(
                (screen.width() - size.width()) // 2,
                (screen.height() - size.height()) // 2
            )

    class ConfirmationDialog(QDialog):
        def __init__(self, selected_date, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Atenção!")
            self.setGeometry(100, 100, 350, 200)

            # Centralize the window
            self.center()

            # Layout
            layout = QVBoxLayout()

            # Confirmation text
            confirmation_text = QLabel(f"A data escolhida foi {selected_date}. Proceder?")
            confirmation_text.setAlignment(Qt.AlignCenter)
            layout.addWidget(confirmation_text)

            # Buttons
            button_box = QDialogButtonBox()

            # SIM button
            sim_button = button_box.addButton("SIM", QDialogButtonBox.AcceptRole)
            sim_button.clicked.connect(self.sim_clicked)

            # Escolher outra data button
            escolher_button = button_box.addButton("Escolher outra data", QDialogButtonBox.RejectRole)
            escolher_button.clicked.connect(self.escolher_clicked)

            # SAIR button
            sair_button = button_box.addButton("SAIR", QDialogButtonBox.DestructiveRole)
            sair_button.clicked.connect(self.sair_clicked)

            layout.addWidget(button_box)

            # Set layout
            self.setLayout(layout)

        def sim_clicked(self):
            # Close all windows and dialogs
            self.parent().close()  # Close the CalendarWindow
            self.close()  # Close the ConfirmationDialog
            QApplication.quit()  # Exit the program

        def escolher_clicked(self):
            # Close only the confirmation dialog
            self.close()

        def sair_clicked(self):
            # Close all windows and exit the program
            QApplication.quit()

        def center(self):
            # Center the window on the screen
            screen = QDesktopWidget().screenGeometry()
            size = self.geometry()
            self.move(
                (screen.width() - size.width()) // 2,
                (screen.height() - size.height()) // 2
            )

# Variáveis globais para manter referências
playwright_instance = None
browser_context = None

def cleanup_playwright():
    """Função para limpar recursos do Playwright ao sair"""
    global playwright_instance, browser_context
    try:
        if browser_context:
            browser_context.close()
        if playwright_instance:
            playwright_instance.stop()
    except:
        pass

# Registra função de limpeza para ser chamada ao sair
atexit.register(cleanup_playwright)

def open_chrome_with_profile():
    """
    Abre uma instância do Google Chrome com todos os dados do perfil,
    mantendo a sessão ativa indefinidamente.
    """
    global playwright_instance, browser_context
    
    # Instala Playwright se necessário
    print("Verificando instalação do Playwright...")
    subprocess.run(["playwright", "install"], shell=True, capture_output=True)
    subprocess.run(["playwright", "install", "chromium"], shell=True, capture_output=True)
    
    # Caminho do perfil do Chrome
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data\Default"
    
    # Verifica se o diretório do perfil existe
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Diretório do perfil não encontrado: {profile_path}")
    
    print("Aviso: Certifique-se de que o Chrome está completamente fechado")
    
    try:
        print("Iniciando Playwright...")
        # IMPORTANTE: NÃO usar 'with' aqui para manter a sessão ativa
        playwright_instance = sync_playwright().start()
        
        print("Lançando Chrome com perfil...")
        
        # Inicia Chrome com perfil específico
        browser_context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            args=[
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-sync',
                '--disable-web-security',
                '--disable-features=msRealtimeCommunication,TranslateUI',
                '--remote-debugging-port=0'
                
            ],
            timeout=30000
        )

        print("Browser lançado com sucesso!")
        
        # Abre nova aba
        page = browser_context.new_page()
        print("Nova aba aberta")
        
        # Navega para a página
        print("Navegando para Fanfever...")
        page.goto("https://m.fanfever.com/br/milfelectra", timeout=15000)

        print("Chrome aberto com sucesso com todos os dados do perfil!")
        print("Você pode agora interagir com cookies, histórico e dados do perfil salvos")
        
        return browser_context, page
        
    except Exception as e:
        print(f"Erro ao abrir Chrome: {e}")
        print("Dicas de solução:")
        print("1. Certifique-se de que o Chrome está completamente fechado (verifique no Gerenciador de Tarefas)")
        print("2. Execute este script como administrador")
        print("3. Tente usar um caminho de perfil diferente se necessário")
        
        # Limpa recursos em caso de erro
        cleanup_playwright()
        raise

def keep_browser_alive():
    """
    Mantém o browser ativo indefinidamente.
    Chame esta função após open_chrome_with_profile() se quiser manter o browser aberto.
    """
    try:
        print("Mantendo browser ativo... (Pressione Ctrl+C para encerrar)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando browser...")
        cleanup_playwright()

def open_chrome_native():
    """
    Alternativa: abre Chrome nativo sem Playwright.
    Usa o executável do Chrome diretamente com o perfil especificado.
    """
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data"
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    # Verifica se o Chrome está instalado
    if not os.path.exists(chrome_exe):
        raise FileNotFoundError(f"Chrome não encontrado em: {chrome_exe}")
    
    # Verifica se o diretório do perfil existe
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Diretório do perfil não encontrado: {profile_path}")
    
    # Comando para abrir Chrome com perfil
    cmd = [
        chrome_exe,
        f"--user-data-dir={profile_path}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--remote-debugging-port=0",
        "https://m.fanfever.com/br/milfelectra"  # URL para abrir
    ]
    
    try:
        print("Abrindo Chrome nativo...")
        print(f"Executável: {chrome_exe}")
        print(f"Perfil: {profile_path}")
        
        # Inicia o processo do Chrome
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        print(f"Chrome iniciado com PID: {process.pid}")
        print("Chrome aberto com sucesso!")
        
        # Aguarda Chrome inicializar
        time.sleep(3)
        
        # Verifica se o processo ainda está rodando
        if process.poll() is None:
            print("Chrome está rodando corretamente")
            return True
        else:
            print("Chrome foi fechado inesperadamente")
            return False
            
    except FileNotFoundError as e:
        print(f"Arquivo não encontrado: {e}")
        return False
    except Exception as e:
        print(f"Erro ao abrir Chrome nativo: {e}")
        return False

def click_plus_button(page):
    """
    Attempt to find and click the plus button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#wrapper > header > div > nav > a.fs-header__menu-item.is-uploader > svg",
            # JavaScript path
            "document.querySelector(\"#wrapper > header > div > nav > a.fs-header__menu-item.is-uploader > svg\")",
            # XPath
            "//*[@id=\"wrapper\"]/header/div/nav/a[2]/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying plus button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const svgElement = {selector};
                        if (svgElement) {{
                            svgElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            svgElement.closest('a').click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked plus button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            print(f"Successfully clicked plus button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            print(f"Successfully clicked plus button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with plus button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for plus button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding SVG elements related to the plus button
            const svgSelectors = [
                'svg.is-uploader.js-post-content',
                'svg[class="is-uploader js-post-content"]',
                'svg > use[class="default"]'
            ];
            
            for (const selector of svgSelectors) {
                const svgElements = document.querySelectorAll(selector);
                for (const svg of svgElements) {
                    if (svg) {
                        svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                        // Try clicking the SVG or its closest clickable parent
                        const clickableParent = svg.closest('a[clickable], a.fs-header__menu-item');
                        if (clickableParent) {
                            clickableParent.click();
                            return true;
                        }
                        svg.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked plus button using JavaScript fallback!")
            return True
        
        print("Could not find or click plus button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_plus_button: {str(e)}")
        return False

class AttentionWindow(QWidget):
    def __init__(self, page):
        super().__init__()
        self.page = page  # Store the Playwright page object
        self.initUI()

    def initUI(self):
        # Set window title
        self.setWindowTitle('Attention!')

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add a label with the text "Procedimento finalizado!"
        label = QLabel('Procedimento finalizado!', self)
        layout.addWidget(label)

        # Add a button to finish the program
        btn_finish = QPushButton('Finalizar', self)
        btn_finish.clicked.connect(self.close_application)
        layout.addWidget(btn_finish)

        # Set the layout to the window
        self.setLayout(layout)

    def showEvent(self, event: QEvent):
        """Override showEvent to center the window when it is displayed."""
        super().showEvent(event)
        self.center()

    def center(self):
        """Center the window on the screen."""
        # Get the geometry of the screen
        screen = QDesktopWidget().screenGeometry()
        # Get the geometry of the window
        size = self.geometry()
        # Calculate the center position
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        # Move the window to the center
        self.move(x, y)

    def go_to_scheduled_posts(self):
        # Use the Playwright page object to navigate to the URL
        self.page.goto('https://onlyfans.com/my/queue')
        print("Navigated to scheduled posts page.")

    def close_application(self):
        # Close the application
        self.close()

def click_add_new_story_button(page):
    """
    Attempt to find and click the "Add New Story" button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#wrapper > header > div > nav > a.fs-header__menu-item.is-uploader > div.fs-header__menu-item.js-post-content-wrapper.box-uploader-media.active > span.fs-header__menu-item.js-upload__stories--open",
            # JavaScript path
            "document.querySelector(\"#wrapper > header > div > nav > a.fs-header__menu-item.is-uploader > div.fs-header__menu-item.js-post-content-wrapper.box-uploader-media.active > span.fs-header__menu-item.js-upload__stories--open\")",
            # XPath
            "//*[@id=\"wrapper\"]/header/div/nav/a[2]/div[2]/span[2]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying 'Add New Story' button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const buttonElement = {selector};
                        if (buttonElement) {{
                            buttonElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            buttonElement.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked 'Add New Story' button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            print(f"Successfully clicked 'Add New Story' button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            print(f"Successfully clicked 'Add New Story' button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with 'Add New Story' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for 'Add New Story' button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements related to the "Add New Story" button
            const buttonSelectors = [
                'span.fs-header__menu-item.js-upload__stories--open',
                'span[class="fs-header__menu-item js-upload__stories--open"]',
                'svg.is-story > use.default'
            ];
            
            for (const selector of buttonSelectors) {
                const buttonElements = document.querySelectorAll(selector);
                for (const button of buttonElements) {
                    if (button) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        // Try clicking the button or its closest clickable parent
                        const clickableParent = button.closest('span[clickable], span.fs-header__menu-item');
                        if (clickableParent) {
                            clickableParent.click();
                            return true;
                        }
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked 'Add New Story' button using JavaScript fallback!")
            return True
        
        print("Could not find or click 'Add New Story' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_add_new_story_button: {str(e)}")
        return False

def selec_midias():
    folder_path = r'G:\Meu Drive\SFS'  # Caminho da pasta
    all_files = os.listdir(folder_path)
    files_only = [f for f in all_files if os.path.isfile(os.path.join(folder_path, f))]
    
    # Embaralha a lista de mídias
    random.shuffle(files_only)
    
    # Imprime a lista de mídias e a quantidade de itens
    # print(f"Quantidade de mídias selecionadas: {len(files_only)}")
    # print(f"Mídias aleatórias selecionadas: {files_only}")
    return files_only

def click_On_Schedule_btn(page):
    """
    Attempt to find and click the 'Schedule' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#modal_container > div > div > div.cp-modal-stories__preview > div.cp-stories-form__buttons.is-column > div.rq-wrapper-schedule > div > label:nth-child(4)",
            # Alternative CSS selectors
            "label.js-upload__stories--schedule-button.rq-wrapper-schedule__label",
            "label[for='rq-stories__scheduled--1']",
            "label[data-type='setSchedule']",
            # JavaScript path
            "document.querySelector(\"#modal_container > div > div > div.cp-modal-stories__preview > div.cp-stories-form__buttons.is-column > div.rq-wrapper-schedule > div > label:nth-child(4)\")",
            # XPath
            "//*[@id=\"modal_container\"]/div/div/div[2]/div[3]/div[3]/div/label[2]",
            # Alternative XPath
            "//label[@for='rq-stories__scheduled--1']",
            "//label[@data-type='setSchedule']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Schedule button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            button.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked Schedule button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            print(f"Successfully clicked Schedule button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            print(f"Successfully clicked Schedule button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Schedule button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Schedule button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding label elements with schedule-related attributes or classes
            const labelSelectors = [
                'label.js-upload__stories--schedule-button',
                'label.rq-wrapper-schedule__label',
                'label[data-type="setSchedule"]',
                'label[for*="scheduled"]',
                'label[data-category="generic"]'
            ];
            
            for (const selector of labelSelectors) {
                const labels = document.querySelectorAll(selector);
                for (const label of labels) {
                    if (label) {
                        label.scrollIntoView({behavior: 'smooth', block: 'center'});
                        label.click();
                        return true;
                    }
                }
            }
            
            // Try finding by SVG content or icon
            const svgLabels = document.querySelectorAll('label svg use[xlink\\:href="#icon-defaults-scheduled"]');
            if (svgLabels.length > 0) {
                const parentLabel = svgLabels[0].closest('label');
                if (parentLabel) {
                    parentLabel.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentLabel.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Schedule button using JavaScript fallback!")
            return True
        
        print("Could not find or click Schedule button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_On_Schedule_btn: {str(e)}")
        return False

def click_On_DateTime_input(page):
    """
    Attempt to find and click the DateTime input field using multiple approaches.
    Prioritizes the selector that worked: input.rq-wrapper-schedule__field.js-upload__stories--schedule-field
    """
    try:
        # List of selectors to try - PRIORIZANDO O QUE FUNCIONOU
        selectors = [
            # PRIMEIRO: O selector que obteve sucesso
            "input.rq-wrapper-schedule__field.js-upload__stories--schedule-field",
            
            # Depois os demais em ordem de probabilidade
            "#js-upload__stories--schedule-field",
            "input.js-upload__stories--schedule-field",
            "input.rq-wrapper-schedule__field",
            "input[type='datetime-local']",
            
            # JavaScript path
            "document.querySelector(\"input.rq-wrapper-schedule__field.js-upload__stories--schedule-field\")",
            "document.querySelector(\"#js-upload__stories--schedule-field\")",
            
            # XPath
            "//input[@class='rq-wrapper-schedule__field js-upload__stories--schedule-field']",
            "//*[@id=\"js-upload__stories--schedule-field\"]",
            "//input[@type='datetime-local']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying DateTime input selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    input_clicked = page.evaluate(f'''() => {{
                        const input = {selector};
                        if (input) {{
                            input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            input.focus();
                            input.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if input_clicked:
                        print(f"Successfully clicked DateTime input with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    selector, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.disabled = false;
                                }}
                            }}''', selector)
                            
                            # Scroll, focus and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.focus()
                            xpath_elements.first.click(force=True)
                            print(f"Successfully clicked DateTime input with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector - MÉTODO PRINCIPAL
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility and enable input
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.disabled = false;
                                    element.readOnly = false;
                                }}
                            }}''', selector)
                            
                            # Scroll, focus and click with timeout adjustment
                            css_elements.first.scroll_into_view_if_needed(timeout=10000)  # Reduz timeout
                            css_elements.first.focus(timeout=5000)
                            css_elements.first.click(force=True, timeout=5000)
                            print(f"Successfully clicked DateTime input with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with DateTime input selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach - FOCADO NO SELECTOR QUE FUNCIONOU
        print("Trying JavaScript fallback approach for DateTime input...")
        fallback_clicked = page.evaluate('''() => {
            // PRIMEIRO: Tentar o selector que funcionou
            const successfulSelector = 'input.rq-wrapper-schedule__field.js-upload__stories--schedule-field';
            const successfulInput = document.querySelector(successfulSelector);
            
            if (successfulInput) {
                successfulInput.style.opacity = '1';
                successfulInput.style.visibility = 'visible';
                successfulInput.style.display = 'block';
                successfulInput.disabled = false;
                successfulInput.readOnly = false;
                
                successfulInput.scrollIntoView({behavior: 'smooth', block: 'center'});
                successfulInput.focus();
                successfulInput.click();
                return true;
            }
            
            // Depois tentar outros selectors
            const inputSelectors = [
                '#js-upload__stories--schedule-field',
                'input.js-upload__stories--schedule-field',
                'input.rq-wrapper-schedule__field',
                'input[type="datetime-local"]',
                'input[id*="schedule"]',
                'input[class*="schedule"]'
            ];
            
            for (const selector of inputSelectors) {
                const inputs = document.querySelectorAll(selector);
                for (const input of inputs) {
                    if (input) {
                        input.style.opacity = '1';
                        input.style.visibility = 'visible';
                        input.style.display = 'block';
                        input.disabled = false;
                        input.readOnly = false;
                        
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked DateTime input using JavaScript fallback!")
            return True
        
        print("Could not find or click DateTime input using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_On_DateTime_input: {str(e)}")
        return False

def click_btn_send_story(page):
    """
    Attempt to find and click the send story button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#js-upload__stories--send > svg",
            # JavaScript path
            "document.querySelector(\"#js-upload__stories--send > svg\")",
            # XPath
            "//*[@id=\"js-upload__stories--send\"]/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying send story selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const svgElement = {selector};
                        if (svgElement) {{
                            svgElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            svgElement.closest('div').click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked send story button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            print(f"Successfully clicked send story button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            print(f"Successfully clicked send story button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with send story selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for send story button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding SVG elements related to sending stories
            const svgSelectors = [
                'svg.is-add > use.default[xlink\\:href="#icon-defaults-upload"]',
                'svg.is-add',
                'svg[class*="upload"]'
            ];
            
            for (const selector of svgSelectors) {
                const svgElements = document.querySelectorAll(selector);
                for (const svg of svgElements) {
                    if (svg) {
                        svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                        // Try clicking the SVG or its closest clickable parent
                        const clickableParent = svg.closest('button, div[clickable]');
                        if (clickableParent) {
                            clickableParent.click();
                            return true;
                        }
                        svg.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked send story button using JavaScript fallback!")
            return True
        
        print("Could not find or click send story button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_btn_send_story: {str(e)}")
        return False

def main():

    # Closes any Chrome Browser instances
    time.sleep(2)
    print("Closing browser instances...")
    os.system("taskkill /f /im chrome.exe")
    time.sleep(2)

    app = QApplication(sys.argv)

    # Create an instance of MyCalendar
    my_calendar = MyCalendar()

    # Show the initial dialog
    my_calendar.show()

    # Execute the application
    app.exec_()

    try:
        # Opens Chrome with the specified user profile
        browser_context, page = open_chrome_with_profile()
        
        #print("Successfully opened Chrome with user profile!")
        print("IMPORTANTE: Não feche este terminal para manter o Chrome ativo")
        
        # Se você quiser que o script continue rodando indefinidamente:
        # keep_browser_alive()
        
        # OU se você quiser que o script termine mas mantenha o Chrome:
        # (o Chrome continuará aberto mesmo após o script terminar)
        
    except Exception as e:
        print(f"Erro com Playwright: {e}")

    pyautogui.press('f11')

    for day_index, date_str in enumerate(my_calendar.date_list):
    # Convert string date to datetime object
        current_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        print(f"\nProcessing day {day_index + 1}: {date_str}")
        
        # Process 24 hours for this day (0-23)
        for hour in range(0, 24, 1):  # Explicit step of 1 to ensure single increments
            print(f"  Processing hour {hour:02d}:00")  # Shows as 00:00, 01:00, etc.
            
            # Get date components from current_date (the day we're actually processing)
            day_str = current_date.strftime("%d")
            month_str = current_date.strftime("%m")
            year_str = current_date.strftime("%Y")

            # Tries to click the "plus_button" with retries
            max_retries = 3
            clique_sucesso = False

            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click plus button...")
                
                if click_plus_button(page):
                    clique_sucesso = True
                    #print("Successfully clicked plus button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} failed to click plus button.")
                    if attempt < max_retries - 1:
                        print("Waiting 3 seconds before next attempt...")
                        page.wait_for_timeout(3000)

            if not clique_sucesso:
                print("Error: Failed to click plus button after all attempts.")
                sys.exit(1)

            page.wait_for_timeout(1000)

            # Try to click the "Add New Story" button with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click 'Add New Story' button...")
                if click_add_new_story_button(page):
                    #print("Successfully clicked 'Add New Story' button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        page.wait_for_timeout(5000)
            else:
                print("Failed to click 'Add New Story' button after all attempts.")

            page.wait_for_timeout(3000)

            # File Explorer operations
            pyautogui.hotkey('ctrl','l')
            page.wait_for_timeout(2000)
            pyautogui.typewrite(r'G:\Meu Drive\SFS')
            page.wait_for_timeout(1000)
            pyautogui.press('enter')
            page.wait_for_timeout(1000)

            # Comes back to the file name field
            pyautogui.hotkey('alt','n')
            page.wait_for_timeout(2000)

            # Copy and paste media file
            try:
                media_file = selec_midias()[day_index]
                pyperclip.copy(media_file)
                page.wait_for_timeout(2000)
                pyautogui.hotkey('ctrl', 'v')
                page.wait_for_timeout(2000)
                pyautogui.press('enter')
                page.wait_for_timeout(2000)
            except IndexError:
                print(f"Error: No media file found for index {day_index}")
                sys.exit(1)

            # Try to click the Schedule button with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click Schedule button...")
                if click_On_Schedule_btn(page):
                    #print("Successfully clicked Schedule button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        time.sleep(5)  # Wait 5 seconds before retrying
            else:
                print("Failed to click Schedule button after all attempts.")

            time.sleep(2)

            # Try to click the DateTime input with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click DateTime input...")
                if click_On_DateTime_input(page):
                    #print("Successfully clicked DateTime input!")
                    break
                else:
                    print(f"Attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        time.sleep(2)  # Wait 2 seconds before retrying
            else:
                print("Failed to click DateTime input after all attempts.")

            # Goes to the day field in the datefield
            for _ in range(4):
                pyautogui.hotkey('shift', 'tab')

            time.sleep(1)
            
            # Type date components (now using current_date instead of always tomorrow)
            pyautogui.typewrite(day_str)  # Day
            pyautogui.typewrite(month_str)  # Month
            pyautogui.typewrite(year_str)  # Year
            pyautogui.press('tab') # Move to hour field

            # FIXED HOUR TYPING - ENSURES SINGLE INCREMENT
            hour_str = f"{hour:02d}"  # Formats as 00, 01, 02...23
            pyautogui.typewrite(hour_str)  # Type the hour
            print(f"Typed hour: {hour_str}")  # Debug output
            
            pyautogui.typewrite('03')  # Minutes
            page.wait_for_timeout(1000)
    
            # Try to click the send story button with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to send story...")
                if click_btn_send_story(page):
                    #print("Successfully clicked send story button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        page.wait_for_timeout(5000)  # Wait 5 seconds before retrying
            else:
                print("Failed to send story after all attempts.")
        
            page.wait_for_timeout(5000)

            page.goto('https://m.fanfever.com/br/milfelectra')

            page.wait_for_timeout(3000)


    window = AttentionWindow(page)
    window.show()

    # Keep the application running
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()