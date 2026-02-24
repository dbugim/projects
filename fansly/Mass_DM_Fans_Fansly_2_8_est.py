import sys
import os
import atexit
import pyautogui
import time
import subprocess
import csv
from pathlib import Path    
from playwright.sync_api import sync_playwright, Page, TimeoutError, Error

def close_all_chrome_instances():
    """Safely close all existing Chrome instances before starting automation"""
    print("Closing all existing Chrome instances...")
    # /f = force close, /im = image name (process), >nul 2>&1 = suppress output and errors
    os.system("taskkill /f /im chrome.exe >nul 2>&1")
    time.sleep(3)  # Give Windows time to fully terminate all Chrome child processes
    print("All Chrome instances have been closed.")

# region Script to help build the executable with PyInstaller
try:
    # Para o executável PyInstaller
    sys.path.append(os.path.join(sys._MEIPASS, "repository"))
except Exception:
    # Para desenvolvimento
    sys.path.append(str(Path(__file__).resolve().parent.parent / "repository"))

# Variáveis globais para manter referências
playwright_instance = None
browser_context = None
# endregion

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
    #print("Verificando instalação do Playwright...")
    subprocess.run(["playwright", "install"], shell=True, capture_output=True)
    subprocess.run(["playwright", "install", "chromium"], shell=True, capture_output=True)
    
    # Caminho do perfil do Chrome
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data\Default"
    
    # Verifica se o diretório do perfil existe
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Diretório do perfil não encontrado: {profile_path}")
    
    print("Aviso: Certifique-se de que o Chrome está completamente fechado")
    
    try:
        #print("Iniciando Playwright...")
        # IMPORTANTE: NÃO usar 'with' aqui para manter a sessão ativa
        playwright_instance = sync_playwright().start()
        
        #print("Lançando Chrome com perfil...")
        
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
        
        #print("Browser lançado com sucesso!")
        
        # Abre nova aba
        page = browser_context.new_page()
        #print("Nova aba aberta")
        
        # Navega para a página
        #print("Navegando para página de mensagens do Fansly...")
        page.goto("https://fansly.com/messages", timeout=15000)
        
        #print("Chrome aberto com sucesso com todos os dados do perfil!")
        #print("Você pode agora interagir com cookies, histórico e dados do perfil salvos")
        
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

def click_on_maybe_later_btn(page):
    """
    Attempt to find and click the 'Maybe Later' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-web-push-enable-modal > div > div.modal-content > div.btn.margin-top-2",
            # JavaScript path
            "document.querySelector('body > app-root > div > div.modal-wrapper > app-web-push-enable-modal > div > div.modal-content > div.btn.margin-top-2')",
            # XPath
            "/html/body/app-root/div/div[3]/app-web-push-enable-modal/div/div[2]/div[4]",
            # Text-based selector
            "text=Maybe Later"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Maybe Later button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        ##print(f"Successfully clicked Maybe Later button with JS selector")
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
                            ##print(f"Successfully clicked Maybe Later button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS or text selector
                    elements = page.locator(selector)
                    if elements.count() > 0:
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
                            elements.first.scroll_into_view_if_needed()
                            elements.first.click(force=True)
                            ##print(f"Successfully clicked Maybe Later button with selector")
                            return True
                        except Exception as e:
                            print(f"Selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Maybe Later button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ####print("Trying JavaScript fallback approach for Maybe Later button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with "Maybe Later" text
            const textSelectors = [
                'div.btn:has-text("Maybe Later")',
                'div:has(> div:has-text("Maybe Later"))',
                'div[class*="btn"]:has-text("Maybe Later")'
            ];
            
            for (const selector of textSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            ##print("Successfully clicked Maybe Later button using JavaScript fallback!")
            return True
        
        print("Could not find or click Maybe Later button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_maybe_later_btn: {str(e)}")
        return False

def click_on_DM_btn(page):
    """
    Attempt to find and click the password field using multiple approaches.
    """
    try:
        # List of selectors to try (ordered by most reliable first)
        selectors = [
            # CSS selectors
            "i.fa-fw.far.fa-envelope.bottom-menu-icon-size",
            "app-nav-bar-mobile i.fa-envelope",
            # XPath selectors
            "//i[contains(@class, 'fa-envelope')]",
            "/html/body/app-root/div/div[1]/app-nav-bar-mobile/div[3]/i[1]",
            # JavaScript path
            "document.querySelector('i.fa-fw.far.fa-envelope.bottom-menu-icon-size')"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying password field selector: {selector}")
                
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    element_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if element_clicked:
                        ##print("Successfully clicked password field with JS selector")
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
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            ##print("Successfully clicked password field with XPath")
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
                            ##print("Successfully clicked password field with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with password field selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ####print("Trying JavaScript fallback approach for password field...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding envelope icon elements
            const iconSelectors = [
                'i.fa-envelope',
                'i[class*="envelope"]',
                'i[class*="mail"]'
            ];
            
            for (const selector of iconSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked DM button using JavaScript fallback!")
            return True
        
        print("Could not find or click DM button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_DM_btn: {str(e)}")
        return False

def click_on_new_msg_btn(page):
    """
    Attempt to find and click the new message button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "div.stacked-icons.new-message-btn",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.site-wrapper.nav-bar-visible > div > app-messages-route > div.page-content > div > div.messages-list-wrapper.border-color > div.messages-top-header.border-color.sm-mobile-hidden > div.stacked-icons.new-message-btn\")",
            # XPath
            "/html/body/app-root/div/div[1]/div/app-messages-route/div[2]/div/div[1]/div[1]/div[2]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying new message button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const btnElement = {selector};
                        if (btnElement) {{
                            btnElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            btnElement.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked new message button with JS selector")
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
                            #print(f"Successfully clicked new message button with XPath")
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
                            ##print(f"Successfully clicked new message button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with new message button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for new message button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with envelope and plus icons
            const iconSelectors = [
                'i.fa-envelope.hover-effect',
                'i.fa-circle-plus',
                'div.stacked-icons i.fa-fw'
            ];
            
            for (const selector of iconSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        const clickableParent = element.closest('div.stacked-icons.new-message-btn');
                        if (clickableParent) {
                            clickableParent.scrollIntoView({behavior: 'smooth', block: 'center'});
                            clickableParent.click();
                            return true;
                        }
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked new message button using JavaScript fallback!")
            return True
        
        print("Could not find or click new message button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_new_msg_btn: {str(e)}")
        return False

def click_On_Close_Sch_Msg_btn(page):
    """
    Click on the close schedule message button with retry logic
    Returns True if successful, False if failed
    """
    try:
        # Multiple selector options for robustness
        selectors = [
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-header.flex-row > div.actions > i",
            "i.fa-xmark.pointer.blue-1-hover-only",
            "i.fa-xmark",
            ".modal-header .actions i"
        ]
        
        # Try each selector until we find the element
        for selector in selectors:
            close_btn = page.query_selector(selector)
            if close_btn:
                #print("Found close button - clicking it")
                close_btn.click()
                
                # Wait for the modal to close (verify it's gone)
                page.wait_for_timeout(1000)
                
                # Verify the modal is no longer visible
                modal_selector = "app-message-schedule-modal"
                modal = page.query_selector(modal_selector)
                if not modal or not modal.is_visible():
                    #print("Successfully closed the schedule message modal")
                    return True
                else:
                    print("Modal still visible after clicking close button")
                    return False
        
        print("Close button not found with any selector")
        return False
            
    except Exception as e:
        print(f"Error clicking close schedule message button: {str(e)}")
        return False

def click_On_Close_New_Message_Window(page):
    """
    Click on the close new message window button with retry logic
    Returns True if successful, False if failed
    """
    try:
        # Multiple selector options for robustness
        selectors = [
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-header > div.actions > div > i",
            "i.fa-xmark.pointer.blue-1-hover-only",
            "i.fa-xmark",
            ".modal-header .actions i",
            "app-new-message-modal .fa-xmark"
        ]
        
        # Try each selector until we find the element
        for selector in selectors:
            close_btn = page.query_selector(selector)
            if close_btn:
                #print("Found new message window close button - clicking it")
                close_btn.click()
                
                # Wait for the modal to close (verify it's gone)
                page.wait_for_timeout(1000)
                
                # Verify the modal is no longer visible
                modal_selector = "app-new-message-modal"
                modal = page.query_selector(modal_selector)
                if not modal or not modal.is_visible():
                    #print("Successfully closed the new message modal")
                    return True
                else:
                    print("New message modal still visible after clicking close button")
                    return False
        
        print("New message window close button not found with any selector")
        return False
            
    except Exception as e:
        print(f"Error clicking close new message window button: {str(e)}")
        return False

def click_on_new_mass_msg_btn(page):
    """
    Attempt to find and click the "New Mass Message" button using multiple approaches.
    """
    try:
        # List of selectors to try (updated based on the actual HTML structure)
        selectors = [
            # Text-based selector (most reliable)
            "text=New Mass Message",
            # Direct tab item with text
            "div.tab-nav-item:has-text('New Mass Message')",
            # Specific element with text
            "xd-localization-string:has-text('New Mass Message')",
            # Second tab item (position-based)
            ".tab-nav-items > div.tab-nav-item:nth-child(2)",
            # Within the modal structure
            "app-new-message-modal .tab-nav-item:nth-child(2)",
            # XPath with text content
            "//div[contains(@class, 'tab-nav-item') and .//xd-localization-string[contains(text(), 'New Mass Message')]]",
            # XPath for the specific text element
            "//xd-localization-string[contains(text(), 'New Mass Message')]",
            # Full structure XPath
            "//app-new-message-modal//div[@class='tab-nav-items']/div[2]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying New Mass Message button selector: {selector}")
                
                if selector.startswith("text=") or selector.startswith(":has-text"):
                    # Playwright text-based selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        # Wait for element to be stable
                        element.first.wait_for(state="visible")
                        element.first.scroll_into_view_if_needed()
                        element.first.click(force=True)
                        
                        # Verify click was successful by checking if the tab becomes selected
                        page.wait_for_timeout(1000)
                        selected_tab = page.locator("div.tab-nav-item.selected:has-text('New Mass Message')")
                        if selected_tab.count() > 0:
                            #print(f"Successfully clicked and verified New Mass Message button with text selector: {selector}")
                            return True
                        else:
                            print("Click performed but tab selection not verified")
                            return True  # Still return True as click was attempted
                
                elif selector.startswith('/') or selector.startswith('//'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                    if element.count() > 0:
                        element.first.wait_for(state="visible")
                        element.first.scroll_into_view_if_needed()
                        element.first.click(force=True)
                        
                        # Verify selection
                        page.wait_for_timeout(1000)
                        selected_tab = page.locator("div.tab-nav-item.selected:has-text('New Mass Message')")
                        if selected_tab.count() > 0:
                            print(f"Successfully clicked and verified New Mass Message button with XPath: {selector}")
                            return True
                        else:
                            print("Click performed but tab selection not verified")
                            return True
                
                else:
                    # CSS selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        element.first.wait_for(state="visible")
                        element.first.scroll_into_view_if_needed()
                        element.first.click(force=True)
                        
                        # Verify selection
                        page.wait_for_timeout(1000)
                        selected_tab = page.locator("div.tab-nav-item.selected:has-text('New Mass Message')")
                        if selected_tab.count() > 0:
                            print(f"Successfully clicked and verified New Mass Message button with CSS selector: {selector}")
                            return True
                        else:
                            print("Click performed but tab selection not verified")
                            return True
                        
            except Exception as e:
                print(f"Failed with selector '{selector}': {str(e)}")
                continue
        
        # Enhanced JavaScript fallback approach
        print("Trying enhanced JavaScript fallback approach for New Mass Message button...")
        fallback_clicked = page.evaluate('''() => {
            // Method 1: Find by exact text content in tab items
            const tabItems = document.querySelectorAll('div.tab-nav-item');
            for (const item of tabItems) {
                const textElement = item.querySelector('xd-localization-string');
                if (textElement && textElement.textContent.includes('New Mass Message')) {
                    item.scrollIntoView({behavior: 'smooth', block: 'center'});
                    item.click();
                    return true;
                }
            }
            
            // Method 2: Find by position (second tab item)
            const secondTab = document.querySelector('.tab-nav-items div.tab-nav-item:nth-child(2)');
            if (secondTab) {
                secondTab.scrollIntoView({behavior: 'smooth', block: 'center'});
                secondTab.click();
                return true;
            }
            
            // Method 3: Direct text search
            const elements = document.querySelectorAll('xd-localization-string');
            for (const element of elements) {
                if (element.textContent && element.textContent.includes('New Mass Message')) {
                    // Find the parent tab item and click it
                    let parent = element.closest('div.tab-nav-item');
                    if (parent) {
                        parent.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parent.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked New Mass Message button using JavaScript fallback!")
            # Verify the click was successful
            page.wait_for_timeout(1000)
            return True
        
        # Final attempt: Wait for element and retry with different strategies
        print("Final attempt: waiting for element and retrying...")
        try:
            # Wait for the modal to be fully loaded
            page.wait_for_selector("app-new-message-modal", timeout=5000)
            
            # Try multiple approaches with waiting
            selectors_to_try = [
                ".tab-nav-item:has-text('New Mass Message')",
                "text=New Mass Message",
                ".tab-nav-items > div:nth-child(2)"
            ]
            
            for final_selector in selectors_to_try:
                try:
                    element = page.locator(final_selector)
                    element.wait_for(state="visible", timeout=3000)
                    element.click(force=True)
                    print(f"Successfully clicked using final attempt with: {final_selector}")
                    return True
                except:
                    continue
                    
        except Exception as e:
            print(f"Final attempt failed: {str(e)}")
        
        print("Could not find or click New Mass Message button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_new_mass_msg_btn: {str(e)}")
        return False

def click_to_uncheck_exclude_creators_list(page):
    """
    Attempt to find and uncheck the "Exclude Creators" option using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Text-based selector (most reliable for this case)
            "xd-localization-string:has-text('Exclude Creators')",
            # CSS selector
            "div.mass-message-settings > div:nth-child(4) > xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.mass-message-settings > div:nth-child(4) > xd-localization-string\")",
            # XPath
            "//xd-localization-string[contains(text(), 'Exclude Creators')]",
            # Alternative XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/div[4]/xd-localization-string"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Exclude Creators selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    uncheck_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            // Find the associated checkbox input
                            const checkbox = element.closest('div').querySelector('input[type="checkbox"]');
                            if (checkbox) {{
                                if (checkbox.checked) {{
                                    checkbox.click();
                                    return true;
                                }}
                                return false; // Already unchecked
                            }}
                            // If no checkbox found, click the element itself
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if uncheck_clicked:
                        #print(f"Successfully unchecked Exclude Creators with JS selector")
                        return True
                
                elif selector.startswith('/') or selector.startswith('//'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Find the checkbox associated with this element
                            checkbox = page.locator(f"xpath={selector}/ancestor::div[1]//input[@type='checkbox']")
                            if checkbox.count() > 0:
                                if checkbox.is_checked():
                                    checkbox.uncheck()
                                    #print(f"Successfully unchecked Exclude Creators checkbox with XPath")
                                    return True
                                else:
                                    print("Exclude Creators checkbox already unchecked")
                                    return True
                            
                            # If no checkbox found, click the element itself
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked Exclude Creators with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS/text selector
                    elements = page.locator(selector)
                    if elements.count() > 0:
                        try:
                            # Find the checkbox first
                            checkbox = page.locator(f"{selector} >> xpath=./ancestor::div[1]//input[@type='checkbox']")
                            if checkbox.count() > 0:
                                if checkbox.is_checked():
                                    checkbox.uncheck()
                                    #print(f"Successfully unchecked Exclude Creators checkbox with CSS/text selector")
                                    return True
                                else:
                                    print("Exclude Creators checkbox already unchecked")
                                    return True
                            
                            # If no checkbox found, click the element
                            elements.first.scroll_into_view_if_needed()
                            elements.first.click(force=True)
                            #print(f"Successfully clicked Exclude Creators with CSS/text selector")
                            return True
                        except Exception as e:
                            print(f"CSS/text selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Exclude Creators selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Exclude Creators...")
        fallback_unchecked = page.evaluate('''() => {
            // Try finding elements with the exact text
            const elements = document.querySelectorAll('xd-localization-string');
            for (const element of elements) {
                if (element.textContent.includes('Exclude Creators')) {
                    // First try to find and uncheck the checkbox
                    const checkbox = element.closest('div').querySelector('input[type="checkbox"]');
                    if (checkbox) {
                        if (checkbox.checked) {
                            checkbox.click();
                            return true;
                        }
                        return false; // Already unchecked
                    }
                    
                    // If no checkbox, click the element
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_unchecked:
            #print("Successfully unchecked Exclude Creators using JavaScript fallback!")
            return True
        elif fallback_unchecked == False:
            print("Exclude Creators was already unchecked")
            return True
        
        print("Could not find or uncheck Exclude Creators using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_uncheck_exclude_creators_list: {str(e)}")
        return False

def click_to_include_list(page):
    """
    Attempt to find and click the include list button (plus icon) using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # CSS selector by class
            "i.fa-circle-plus.pointer.hover-effect.blue-1-hover-only",
            # More specific CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(3) > i",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(3) > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[3]/i",
            # More flexible XPath
            "//i[contains(@class, 'fa-circle-plus') and contains(@class, 'pointer')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying include list button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked include list button with JS selector")
                        return True
                
                elif selector.startswith('/') or selector.startswith('//'):
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
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked include list button with XPath")
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
                            #print(f"Successfully clicked include list button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with include list button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for include list button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding plus icon elements
            const iconSelectors = [
                'i.fa-circle-plus',
                'i[class*="fa-circle-plus"]',
                'i[class*="pointer"][class*="hover-effect"]'
            ];
            
            for (const selector of iconSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        // Check if it's in the right context
                        const parentDiv = element.closest('div.modal-content > div');
                        if (parentDiv) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try any plus icon as last resort
            const plusIcons = document.querySelectorAll('i.fa-circle-plus');
            for (const icon of plusIcons) {
                if (icon) {
                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    icon.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked include list button using JavaScript fallback!")
            return True
        
        print("Could not find or click include list button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_include_list: {str(e)}")
        return False

def click_Fans_That_Have_Money_btn(page):
    """
    Attempt to find and click the 'Fans That Have Money' button using multiple approaches.
    """
    try:
        # List of selectors to try for the money button
        selectors = [
            # CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(2) > app-list > div > div > div.bold",
            # Alternative CSS selectors
            "div.bold",
            "div[class='bold']",
            "div[ng-content='ng-c2231467073']",
            "div[_ngcontent-ng-c2231467073]",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(2) > app-list > div > div > div.bold\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-list-select-modal/div/div[2]/div[2]/app-list/div/div/div[1]",
            # Alternative XPaths
            "//div[@class='bold']",
            "//div[contains(text(), '$')]",
            "//div[text()=' $ ']",
            "//div[@_ngcontent-ng-c2231467073]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Fans That Have Money button selector: {selector}")
                
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
                        #print(f"Successfully clicked Fans That Have Money button with JS selector")
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
                                    element.style.zIndex = '9999';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked Fans That Have Money button with XPath")
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
                                    element.style.zIndex = '9999';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked Fans That Have Money button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Fans That Have Money button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Fans That Have Money button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding div elements with money-related content
            const moneySelectors = [
                'div.bold',
                'div[class*="money"]',
                'div[class*="dollar"]',
                'div[class*="cash"]',
                'div[class*="currency"]',
                'div:has(> svg[aria-label*="money"])',
                'div:has(> svg[aria-label*="dollar"])'
            ];
            
            // First try exact text match
            const moneyDivs = document.querySelectorAll('div');
            for (const div of moneyDivs) {
                if (div.textContent && div.textContent.trim() === '$') {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            // Try selectors with dollar sign content
            for (const selector of moneySelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && (element.textContent.includes('$') || 
                        element.getAttribute('aria-label')?.includes('money') ||
                        element.getAttribute('aria-label')?.includes('dollar'))) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by specific attributes
            const ngElements = document.querySelectorAll('div[_ngcontent]');
            for (const element of ngElements) {
                if (element.textContent && element.textContent.includes('$')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Fans That Have Money button using JavaScript fallback!")
            return True
        
        print("Could not find or click Fans That Have Money button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_Fans_That_Have_Money_btn: {str(e)}")
        return False

def click_NonCreator_btn(page):
    """
    Attempt to find and click the 'Non-creators ♥️' button using multiple approaches.
    """
    try:
        # List of selectors to try for the Non-creators button
        selectors = [
            # CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(3) > app-list > div > div > div.bold",
            # Alternative CSS selectors
            "div.bold",
            "div[class='bold']",
            "div[ng-content='ng-c2231467073']",
            "div[_ngcontent-ng-c2231467073]",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(3) > app-list > div > div > div.bold\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-list-select-modal/div/div[2]/div[3]/app-list/div/div/div[1]",
            # Alternative XPaths
            "//div[@class='bold']",
            "//div[contains(text(), 'Non-creators')]",
            "//div[contains(text(), '♥️')]",
            "//div[text()=' Non-creators ♥️ ']",
            "//div[@_ngcontent-ng-c2231467073]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Non-creators button selector: {selector}")
                
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
                        #print(f"Successfully clicked Non-creators button with JS selector")
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
                                    element.style.zIndex = '9999';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked Non-creators button with XPath")
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
                                    element.style.zIndex = '9999';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked Non-creators button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Non-creators button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Non-creators button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding div elements with Non-creators related content
            const nonCreatorSelectors = [
                'div.bold',
                'div[class*="non"]',
                'div[class*="creator"]',
                'div[class*="fan"]',
                'div[aria-label*="non-creator"]',
                'div[aria-label*="fan"]'
            ];
            
            // First try exact text match
            const nonCreatorDivs = document.querySelectorAll('div');
            for (const div of nonCreatorDivs) {
                if (div.textContent && div.textContent.trim() === 'Non-creators ♥️') {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            // Try partial text match
            for (const div of nonCreatorDivs) {
                if (div.textContent && (div.textContent.includes('Non-creators') || 
                    div.textContent.includes('♥️'))) {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            // Try selectors with Non-creators content
            for (const selector of nonCreatorSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && (element.textContent.includes('Non-creators') || 
                        element.textContent.includes('♥️') ||
                        element.getAttribute('aria-label')?.includes('non-creator') ||
                        element.getAttribute('aria-label')?.includes('fan'))) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by specific attributes
            const ngElements = document.querySelectorAll('div[_ngcontent]');
            for (const element of ngElements) {
                if (element.textContent && (element.textContent.includes('Non-creators') || 
                    element.textContent.includes('♥️'))) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Non-creators button using JavaScript fallback!")
            return True
        
        print("Could not find or click Non-creators button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_NonCreator_btn: {str(e)}")
        return False

def click_on_Next_btn(page):
    """
    Attempt to find and click the 'Next' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.message-content-footer > div > div.btn.outline-blue > xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.message-content-footer > div > div.btn.outline-blue > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[14]/div/div[3]/xd-localization-string",
            # Parent button selector
            "div.btn.outline-blue"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying 'Next' button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const btnElement = {selector};
                        if (btnElement) {{
                            btnElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            // Click the parent button element if this is the text element
                            const parentBtn = btnElement.closest('div.btn');
                            if (parentBtn) {{
                                parentBtn.click();
                                return true;
                            }}
                            btnElement.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked 'Next' button with JS selector")
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
                                    // Also ensure parent is visible
                                    const parent = element.closest('div.btn');
                                    if (parent) {{
                                        parent.style.opacity = '1';
                                        parent.style.visibility = 'visible';
                                        parent.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click - try clicking parent button if available
                            xpath_elements.first.scroll_into_view_if_needed()
                            parent_button = xpath_elements.first.locator("xpath=./ancestor::div[contains(@class, 'btn')]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                            else:
                                xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked 'Next' button with XPath")
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
                                    // Also ensure parent is visible
                                    const parent = element.closest('div.btn');
                                    if (parent) {{
                                        parent.style.opacity = '1';
                                        parent.style.visibility = 'visible';
                                        parent.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click - try clicking parent button if available
                            css_elements.first.scroll_into_view_if_needed()
                            if "xd-localization-string" in selector:
                                parent_button = css_elements.first.locator("xpath=./ancestor::div[contains(@class, 'btn')]")
                                if parent_button.count() > 0:
                                    parent_button.first.click(force=True)
                                else:
                                    css_elements.first.click(force=True)
                            else:
                                css_elements.first.click(force=True)
                            #print(f"Successfully clicked 'Next' button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with 'Next' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for 'Next' button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding buttons with Next text
            const buttonSelectors = [
                'div.btn',
                'button',
                'div[role="button"]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    const buttonText = button.textContent?.toLowerCase()?.trim();
                    if (buttonText && buttonText.includes('next')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked 'Next' button using JavaScript fallback!")
            return True
        
        print("Could not find or click 'Next' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Next_btn: {str(e)}")
        return False

def insert_caption_in_text_area(page, caption_to_paste):
    """
    Finds the text area and uses fill() to insert the caption.
    """
    try:
        # List of CSS and XPath selectors
        selectors = [
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.material-input > textarea",
            "xpath=/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/app-group-message-input/div[2]/textarea",
            "textarea.material-input",
            "textarea"
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    element.scroll_into_view_if_needed()
                    # Use fill() as requested
                    element.fill(caption_to_paste)
                    return True
            except Exception:
                continue
        
        return False
    
    except Exception as e:
        print(f"Error in insert_caption_in_text_area: {str(e)}")
        return False

def click_on_Send_btn(page):
    """
    Attempt to find and click the Send button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > app-button > div > span > xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > app-button > div > span > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/app-group-message-input/div[3]/app-button/div/span/xd-localization-string",
            # Parent button selector
            "div.input-footer > app-button > div"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Send button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const btnElement = {selector};
                        if (btnElement) {{
                            btnElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            // Click the parent button element if this is the text element
                            const parentBtn = btnElement.closest('div');
                            if (parentBtn) {{
                                parentBtn.click();
                                return true;
                            }}
                            btnElement.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked Send button with JS selector")
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
                                    // Also ensure parent is visible
                                    const parent = element.closest('div');
                                    if (parent) {{
                                        parent.style.opacity = '1';
                                        parent.style.visibility = 'visible';
                                        parent.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click - try clicking parent button if available
                            xpath_elements.first.scroll_into_view_if_needed()
                            parent_button = xpath_elements.first.locator("xpath=./ancestor::div[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                            else:
                                xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked Send button with XPath")
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
                                    // Also ensure parent is visible
                                    const parent = element.closest('div');
                                    if (parent) {{
                                        parent.style.opacity = '1';
                                        parent.style.visibility = 'visible';
                                        parent.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click - try clicking parent button if available
                            css_elements.first.scroll_into_view_if_needed()
                            if "xd-localization-string" in selector:
                                parent_button = css_elements.first.locator("xpath=./ancestor::div[1]")
                                if parent_button.count() > 0:
                                    parent_button.first.click(force=True)
                                else:
                                    css_elements.first.click(force=True)
                            else:
                                css_elements.first.click(force=True)
                            #print(f"Successfully clicked Send button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Send button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Send button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding buttons with Send text
            const buttonSelectors = [
                'div.btn',
                'button',
                'div[role="button"]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    const buttonText = button.textContent?.toLowerCase()?.trim();
                    if (buttonText && buttonText.includes('send')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Send button using JavaScript fallback!")
            return True
        
        print("Could not find or click Send button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Send_btn: {str(e)}")
        return False

def click_to_Close_Mass_DM_Sent_Confirmation_Window(page):
    """
    Attempt to find and click the close button (X icon) of the Mass DM confirmation window.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-header > div.actions > div > i",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-header > div.actions > div > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[1]/div[2]/div/i",
            # Class-based selector
            "i.fa-xmark.pointer.blue-1-hover-only"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying close button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const closeIcon = {selector};
                        if (closeIcon) {{
                            closeIcon.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            closeIcon.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked close button with JS selector")
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
                            #print(f"Successfully clicked close button with XPath")
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
                            #print(f"Successfully clicked close button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with close button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for close button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding close (X) icons
            const closeSelectors = [
                'i.fa-xmark',
                'i.fa-times',
                'i[class*="close"]',
                'i[class*="xmark"]'
            ];
            
            for (const selector of closeSelectors) {
                const closeIcons = document.querySelectorAll(selector);
                for (const icon of closeIcons) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked close button using JavaScript fallback!")
            return True
        
        print("Could not find or click close button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_Close_Mass_DM_Sent_Confirmation_Window: {str(e)}")
        return False

CSV_FILE = "G:\\Meu Drive\\Fansly\\bundles_caption.csv"      # Name of your CSV file containing the captions
INDEX_FILE = "G:\\Meu Drive\\Fansly\\caption_index.txt"      # File that stores the current index between script runs

def get_next_caption():
    """
    Returns the next caption in sequence.
    Saves the current index for the next script execution.
    Cycles back to the first caption when it reaches the end.
    """
    # 1. Load all captions from the CSV (only once, or if the file changes)
    if not hasattr(get_next_caption, "captions"):
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f"File not found: {CSV_FILE}")
        
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Extract the text, remove surrounding quotes and whitespace
            get_next_caption.captions = [row[0].strip().strip('"') for row in reader if row]
        
        #print(f"Loaded {len(get_next_caption.captions)} captions from the file.")

    captions = get_next_caption.captions
    total = len(captions)

    # 2. Read the current index (starts at 0 if the index file doesn't exist)
    current_index = 0
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            try:
                current_index = int(f.read().strip())
                # Safety check: reset if the CSV now has fewer lines
                if current_index >= total:
                    current_index = 0
            except:
                current_index = 0

    # 3. Get the current caption
    caption = captions[current_index]

    # 4. Advance the index (wraps around to 0 at the end)
    next_index = (current_index + 1) % total

    # 5. Save the next index for the next script run
    with open(INDEX_FILE, 'w') as f:
        f.write(str(next_index))

    #print(f"Using caption #{current_index + 1}/{total}: {caption[:50]}...")
    return caption

def Insert_New_Media_btn(page):
    """
    Attempt to find and click the 'Insert New Media' button using multiple approaches.
    """
    try:
        # List of selectors to try based on the provided parameters
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > div.input-addon.transparent-dropdown.margin-right-text > div.dropdown-title.blue-1-hover-only > i",
            # Alternative CSS selectors
            "i.fa-fw.fal.fa-image.hover-effect",
            "i.fa-image.hover-effect",
            "div.dropdown-title.blue-1-hover-only > i",
            "i[class*='fa-image']",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > div.input-addon.transparent-dropdown.margin-right-text > div.dropdown-title.blue-1-hover-only > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/app-group-message-input/div[3]/div[1]/div[1]/i",
            # Alternative XPaths
            "//i[@class='fa-fw fal fa-image hover-effect']",
            "//i[contains(@class, 'fa-image')]",
            "//div[contains(@class, 'dropdown-title')]/i"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Insert New Media button selector: {selector}")
                
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
                        #print(f"Successfully clicked Insert New Media button with JS selector")
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
                            #print(f"Successfully clicked Insert New Media button with XPath")
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
                            #print(f"Successfully clicked Insert New Media button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Insert New Media button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Insert New Media button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with image icon classes
            const iconSelectors = [
                'i.fa-image',
                'i.fal.fa-image',
                'i.fa-fw.fa-image',
                'i[class*="image"]',
                'i.hover-effect'
            ];
            
            for (const selector of iconSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        // Check if it's in the expected context (modal, dropdown, etc.)
                        const parentText = element.closest('div')?.textContent || '';
                        if (parentText.includes('media') || parentText.includes('image') || 
                            element.closest('.input-footer') || element.closest('.dropdown-title')) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by parent elements
            const parentSelectors = [
                'div.dropdown-title.blue-1-hover-only',
                'div.input-addon.transparent-dropdown',
                'div.input-footer',
                'div[class*="media"]',
                'div[class*="image"]'
            ];
            
            for (const selector of parentSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element) {
                        const icon = element.querySelector('i.fa-image, i[class*="image"]');
                        if (icon) {
                            icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            icon.click();
                            return true;
                        } else {
                            // Click the parent if no icon found
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Insert New Media button using JavaScript fallback!")
            return True
        
        print("Could not find or click Insert New Media button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in Insert_New_Media_btn: {str(e)}")
        return False

def click_on_from_vault_btn(page):
    
    try:
        # A nova lista de seletores prioriza o JavaScript, seguido por CSS e depois XPath.
        selectors = [
            # 1. JavaScript path (PRIORIDADE)
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(3)")',
            
            # 2. CSS Selector Direto
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(3)",
            
            # 3. CSS Seletor por classe e texto
            "div.dropdown-item:has(xd-localization-string:has-text('From Vault'))",
            
            # 4. CSS Seletor pelo ícone
            "div.dropdown-item:has(i.fa-upload)",
            
            # 5. XPath (Por texto)
            "//div[contains(@class, 'dropdown-item') and contains(., 'From Vault')]",
            
            # 6. XPath (Altamente específico)
            '/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[1]/app-account-media-template/div[1]/div[3]/div/div/div/div[3]/div[3]'
        ]

        # Tenta cada seletor na nova ordem
        for selector in selectors:
            try:
                #print(f"Trying 'From Vault' button selector: {selector}")
                
                # Trata o seletor JavaScript (prioridade 1)
                if selector.startswith("document.querySelector"):
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
                        #print(f"Successfully clicked 'From Vault' button with JS selector (Priority 1)")
                        return True
                
                # Trata seletores Playwright (CSS e XPath)
                else:
                    locator_elements = page.locator(f"xpath={selector}") if selector.startswith('/') else page.locator(selector)
                    locator_type = "XPath" if selector.startswith('/') else "CSS"

                    if locator_elements.count() > 0:
                        try:
                            # Scroll e click forçado
                            locator_elements.first.scroll_into_view_if_needed()
                            locator_elements.first.click(force=True, timeout=5000) 
                            #print(f"Successfully clicked 'From Vault' button with {locator_type} selector")
                            return True
                        except TimeoutError as e:
                            print(f"{locator_type} click timed out: {str(e)}")
                        except Exception as e:
                            print(f"{locator_type} click failed: {str(e)}")
                
            except Exception as e:
                # print(f"Failed with 'From Vault' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach (finding by visible text content)
        print("Trying JavaScript fallback approach for 'From Vault' button...")
        fallback_clicked = page.evaluate('''() => {
            // Find the element containing the exact text 'From Vault'
            const textContent = 'From Vault';
            const elements = Array.from(document.querySelectorAll('div.dropdown-item, xd-localization-string'))
                .filter(el => el.textContent.includes(textContent));

            // Click the first matching element, or its closest ancestor with the dropdown-item class
            if (elements.length > 0) {
                const button = elements[0].closest('.dropdown-item') || elements[0];
                if (button) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked 'From Vault' button using JavaScript fallback!")
            return True
        
        print("Could not find or click 'From Vault' button using any method.")
        return False
        
    except Exception as e:
        print(f"Error in click_on_from_vault_btn: {str(e)}")
        return False

def click_on_Search_Albums_input(page):
    """
    Attempt to find and click the 'Search Albums' input field using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # CSS selector from provided
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.album-search-container.flex-row.flex-0.material-input.icon-left.icon-right.margin-top-1 > input",
            # Alternative CSS selectors based on classes and attributes
            "input[type='text'][required].ng-dirty.ng-valid.ng-touched",
            "input.album-search-container__input",
            "input.material-input",
            "input[type='text'][required]",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.album-search-container.flex-row.flex-0.material-input.icon-left.icon-right.margin-top-1 > input\")",
            # XPath from provided
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div/div[2]/input",
            # Alternative XPaths
            "//input[@type='text' and @required]",
            "//input[contains(@class, 'material-input')]",
            "//input[contains(@class, 'ng-dirty') and contains(@class, 'ng-valid')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Search Albums input selector: {selector}")
                
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
                        #print(f"Successfully clicked Search Albums input with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility and enable input
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
                                    element.removeAttribute('disabled');
                                    element.removeAttribute('readonly');
                                }}
                            }}''', selector)
                            
                            # Scroll, focus and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.focus()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked Search Albums input with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
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
                                    element.removeAttribute('disabled');
                                    element.removeAttribute('readonly');
                                }}
                            }}''', selector)
                            
                            # Scroll, focus and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.focus()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked Search Albums input with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Search Albums input selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Search Albums input...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding input elements with search-related attributes or classes
            const inputSelectors = [
                'input[type="text"][required]',
                'input.material-input',
                'input.ng-dirty.ng-valid.ng-touched',
                'input[placeholder*="search" i]',
                'input[placeholder*="album" i]',
                'input.search-input',
                'input.album-search'
            ];
            
            for (const selector of inputSelectors) {
                const inputs = document.querySelectorAll(selector);
                for (const input of inputs) {
                    if (input && input.offsetParent !== null) { // Check if visible
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.click();
                        return true;
                    }
                }
            }
            
            // Try finding by container class
            const searchContainers = document.querySelectorAll('[class*="search" i], [class*="album" i]');
            for (const container of searchContainers) {
                const input = container.querySelector('input[type="text"]');
                if (input && input.offsetParent !== null) {
                    input.scrollIntoView({behavior: 'smooth', block: 'center'});
                    input.focus();
                    input.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Search Albums input using JavaScript fallback!")
            return True
        
        print("Could not find or click Search Albums input using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Search_Albums_input: {str(e)}")
        return False

def insert_album_search_term(page, bundle_name):
    """
    Finds the 'Search Albums' input and uses fill() to enter the bundle name.
    """
    try:
        # Simplified list of selectors from original code
        selectors = [
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.album-search-container.flex-row.flex-0.material-input.icon-left.icon-right.margin-top-1 > input",
            "xpath=/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div/div[2]/input",
            "input.album-search-container__input",
            "input.material-input",
            "input[type='text'][required]"
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    element.scroll_into_view_if_needed()
                    # Use fill() to insert the text directly
                    element.fill(bundle_name)
                    return True
            except Exception:
                continue
        
        return False
    
    except Exception as e:
        print(f"Error in insert_album_search_term: {str(e)}")
        return False

def get_current_bundle_name():
    """
    Reads the current caption index from the index file and returns it formatted as 'BundleX'.
    Example: if caption_index.txt contains '6' → returns 'Bundle6'
    """
    INDEX_FILE = r"G:\\Meu Drive\\Fansly\\caption_index.txt"
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_str = f.read().strip()
            # The index file contains the *next* index, so we subtract 1 to get the current one
            # (because get_next_caption() saves the next index after using the current one)
            current_index = int(index_str) - 1
            
            # Safety: if for some reason it's 0 or negative after subtraction
            if current_index < 0:
                # This means we just used the last caption and wrapped around
                # We need to know how many captions there are
                CSV_FILE = "bundles_caption.csv"
                with open(CSV_FILE, 'r', encoding='utf-8') as csv_file:
                    import csv
                    reader = csv.reader(csv_file)
                    total_captions = sum(1 for row in reader if row)
                current_index = total_captions - 1  # last one
    except Exception as e:
        print(f"Error reading index file: {e}")
        return "Bundle1"  # fallback
    
    bundle_name = f"Bundle{current_index + 1}"  # +1 because bundle numbers start from 1
    #print(f"Current bundle name: {bundle_name}")
    return bundle_name

def click_on_bundle_label(page, bundle_name):
    """
    Attempt to find and click the bundle label using multiple approaches.
    bundle_name: The specific bundle name to look for (e.g., "#bundle1", "#bundle2", etc.)
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector from provided
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.vault-albums.margin-top-1 > div:nth-child(1) > div.vault-album-footer.margin-top-text.margin-bottom-text.xd-drag-ignore > div.semi-bold",
            # Alternative CSS selectors based on classes and content
            f"div.semi-bold:contains('{bundle_name}')",
            "div.vault-album-footer div.semi-bold",
            "div.semi-bold",
            # JavaScript path from provided
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.vault-albums.margin-top-1 > div:nth-child(1) > div.vault-album-footer.margin-top-text.margin-bottom-text.xd-drag-ignore > div.semi-bold\")",
            # XPath from provided
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div/div[3]/div[1]/div[2]/div[1]",
            # Alternative XPaths that target the specific bundle text
            f"//div[contains(@class, 'semi-bold') and contains(text(), '{bundle_name}')]",
            "//div[@class='semi-bold']",
            "//div[contains(@class, 'vault-album-footer')]//div[contains(@class, 'semi-bold')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying bundle label selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    label_clicked = page.evaluate(f'''() => {{
                        const label = {selector};
                        if (label && label.textContent.includes('{bundle_name}')) {{
                            label.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            label.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if label_clicked:
                        #print(f"Successfully clicked bundle label with JS selector")
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
                            #print(f"Successfully clicked bundle label with XPath")
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
                            #print(f"Successfully clicked bundle label with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with bundle label selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for bundle label...")
        fallback_clicked = page.evaluate(f'''() => {{
            // Try finding div elements with the specific bundle text
            const divSelectors = [
                'div.semi-bold',
                'div.vault-album-footer div',
                '[class*="bundle"]',
                '[class*="album"] div'
            ];
            
            for (const selector of divSelectors) {{
                const divs = document.querySelectorAll(selector);
                for (const div of divs) {{
                    if (div && div.textContent.includes('{bundle_name}')) {{
                        div.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        div.click();
                        return true;
                    }}
                }}
            }}
            
            // Try finding by text content
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {{
                if (element.textContent && element.textContent.trim() === '{bundle_name}') {{
                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    element.click();
                    return true;
                }}
            }}
            
            return false;
        }}''')
        
        if fallback_clicked:
            #print("Successfully clicked bundle label using JavaScript fallback!")
            return True
        
        print("Could not find or click bundle label using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_bundle_label: {str(e)}")
        return False

#def click_On_Bundle_Preview_Media(page):
    """
    Attempt to find and click the Bundle Preview Media icon using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div:nth-child(2) > div.render-container > div.image-controls.image > div > i",
            # Alternative CSS selectors (simpler versions)
            "div.image-controls.image > div > i",
            "i.fa-fw.fal.fa-circle",
            "i[class*='fa-circle']",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div:nth-child(2) > div.render-container > div.image-controls.image > div > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[4]/div/div[2]/div[2]/div[3]/div/i",
            # Alternative XPath
            "//i[@class='fa-fw fal fa-circle']",
            "//i[contains(@class, 'fa-circle')]",
            "//div[contains(@class, 'image-controls')]//i"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Bundle Preview Media selector: {selector}")
                
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
                        #print(f"Successfully clicked Bundle Preview Media with JS selector")
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
                            #print(f"Successfully clicked Bundle Preview Media with XPath")
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
                            #print(f"Successfully clicked Bundle Preview Media with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Bundle Preview Media selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Bundle Preview Media...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding icon elements with specific classes
            const iconSelectors = [
                'i.fa-fw.fal.fa-circle',
                'i[class*="fa-circle"]',
                'div.image-controls i',
                'div.render-container i'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            // Try finding by parent container structure
            const imageControls = document.querySelectorAll('div.image-controls.image');
            for (const control of imageControls) {
                const icons = control.querySelectorAll('i');
                for (const icon of icons) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Bundle Preview Media using JavaScript fallback!")
            return True
        
        print("Could not find or click Bundle Preview Media using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_On_Bundle_Preview_Media: {str(e)}")
        return False

def click_on_bundle_label_cover(page, bundle_name):
    """
    Tries to find and click the bundle label and its associated circle icon.
    """
    try:
        # Construct the specific cover name for the bundle
        bundle_cover_name = f"{bundle_name}_cover"
        
        # 1. Try to find the div by text and click it
        label_selector = f"div.image-filename:has-text('{bundle_cover_name}')"
        if page.is_visible(label_selector):
            page.click(label_selector)
            return True

        # 2. JavaScript Fallback: Search all elements for the bundle name
        fallback_clicked = page.evaluate(f'''() => {{
            const allElements = document.querySelectorAll('div.image-filename');
            for (const element of allElements) {{
                if (element.textContent && element.textContent.trim() === '{bundle_cover_name}') {{
                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    element.click();
                    return True;
                }}
            }}
            return false;
        }}''')
        
        return fallback_clicked
    
    except Exception as e:
        print(f"Error in click_on_bundle_label: {str(e)}")
        return False

def click_on_actions_btn(page):
    """
    Attempt to find and click the 'Actions' button using multiple approaches.
    """
    try:
        # List of selectors to try based on the provided parameters
        selectors = [
            # CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.flex-row.vault-header > div.vault-actions.margin-top-1 > div > div.bubble",
            # Alternative CSS selectors (simpler versions)
            "div.bubble",
            "div.vault-actions div.bubble",
            "div[class*='bubble']",
            "xd-localization-string:has-text('Actions')",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.flex-row.vault-header > div.vault-actions.margin-top-1 > div > div.bubble\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[1]/div[5]/div/div[1]",
            # Alternative XPath
            "//div[contains(@class, 'bubble')]",
            "//xd-localization-string[contains(text(), 'Actions')]",
            "//div[@class='bubble']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Actions button selector: {selector}")
                
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
                        #print(f"Successfully clicked Actions button with JS selector")
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
                            #print(f"Successfully clicked Actions button with XPath")
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
                            #print(f"Successfully clicked Actions button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Actions button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Actions button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with Actions text
            const actionSelectors = [
                'div.bubble',
                'xd-localization-string:contains("Actions")',
                '[class*="bubble"]',
                '[class*="action"]',
                'div:has(> xd-localization-string:contains("Actions"))'
            ];
            
            for (const selector of actionSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    const text = element.textContent || element.innerText;
                    if (text && text.includes('Actions')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by exact text content
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                const text = element.textContent || element.innerText;
                if (text && text.trim() === 'Actions') {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Actions button using JavaScript fallback!")
            return True
        
        print("Could not find or click Actions button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_actions_btn: {str(e)}")
        return False

def click_on_select_all_btn(page):
    """
    Attempt to find and click the 'Select All' button using multiple approaches.
    """
    try:
        # List of selectors to try based on the provided parameters
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.flex-row.vault-header > div.vault-actions.margin-top-1 > div > div.dropdown-list.font-size-sm > div:nth-child(2)",
            # Alternative CSS selectors
            "div.dropdown-item",
            "div.dropdown-list div.dropdown-item",
            "div[class*='dropdown-item']",
            "xd-localization-string:has-text('Select All')",
            "div:has(> xd-localization-string:contains('Select All'))",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.flex-row.vault-header > div.vault-actions.margin-top-1 > div > div.dropdown-list.font-size-sm > div:nth-child(2)\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[1]/div[5]/div/div[2]/div[2]",
            # Alternative XPath
            "//div[contains(@class, 'dropdown-item')]",
            "//xd-localization-string[contains(text(), 'Select All')]",
            "//div[@class='dropdown-item']",
            "//div[contains(text(), 'Select All')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Select All button selector: {selector}")
                
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
                        #print(f"Successfully clicked Select All button with JS selector")
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
                            #print(f"Successfully clicked Select All button with XPath")
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
                            #print(f"Successfully clicked Select All button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Select All button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Select All button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with Select All text
            const selectAllSelectors = [
                'div.dropdown-item',
                'xd-localization-string:contains("Select All")',
                '[class*="dropdown-item"]',
                'div:has(> xd-localization-string:contains("Select All"))'
            ];
            
            for (const selector of selectAllSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    const text = element.textContent || element.innerText;
                    if (text && text.includes('Select All')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by exact text content
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                const text = element.textContent || element.innerText;
                if (text && text.trim().includes('Select All')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            // Try finding by icon class
            const iconElements = document.querySelectorAll('i.fa-object-ungroup');
            if (iconElements.length > 0) {
                const parentDiv = iconElements[0].closest('div.dropdown-item');
                if (parentDiv) {
                    parentDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentDiv.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Select All button using JavaScript fallback!")
            return True
        
        print("Could not find or click Select All button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_select_all_btn: {str(e)}")
        return False

def uncheck_cover_btn(page):
    """
    Finds the first .vault-row associated with a file containing "cover",
    and clicks the blue circle icon inside it using multiple fail-safe approaches.
    """
    try:
        # List of strategy-based selectors
        # We use Playwright's ability to chain and filter locators
        selectors = [
            # Strategy 1: The row containing 'cover' text + the specific icon class
            ".vault-row:has-text('cover') i.fa-circle.blue-1",
            
            # Strategy 2: Targeting by the specific Angular attribute and hierarchy
            "div.vault-row:has(.image-filename:has-text('cover')) i.blue-1",
            
            # Strategy 3: Specific filename element sibling to the controls
            ".render-container:has(.image-filename:has-text('cover')) .image-controls i",
            
            # Strategy 4: XPath for "A row that contains 'cover' anywhere in its text"
            "//div[contains(@class, 'vault-row')][descendant::*[contains(text(), 'cover')]]//i[contains(@class, 'fa-circle')]",
            
            # Strategy 5: JavaScript path (The specific one from your HTML snippet)
            "document.querySelector('.vault-row').querySelector('.image-controls i.blue-1')"
        ]

        for selector in selectors:
            try:
                if selector.startswith("document.querySelector"):
                    # JavaScript injection approach
                    clicked = page.evaluate(f'''() => {{
                        const row = Array.from(document.querySelectorAll('.vault-row'))
                                     .find(r => r.innerText.toLowerCase().includes('cover'));
                        if (row) {{
                            const icon = row.querySelector('i.fa-circle.blue-1');
                            if (icon) {{
                                icon.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                icon.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    if clicked: return True

                elif selector.startswith("//"):
                    # XPath approach
                    element = page.locator(f"xpath={selector}").first
                    if element.count() > 0:
                        element.scroll_into_view_if_needed()
                        element.click(force=True)
                        return True
                
                else:
                    # Standard Playwright CSS/Text engine
                    element = page.locator(selector).first
                    if element.count() > 0:
                        # Ensure visibility before clicking
                        page.evaluate(f'''(sel) => {{
                            const el = document.querySelector(sel);
                            if(el) {{ el.style.visibility = 'visible'; el.style.opacity = '1'; }}
                        }}''', selector)
                        element.click(force=True)
                        return True

            except Exception:
                continue

        # Final Fallback: Iterate through all rows manually via JS
        fallback = page.evaluate('''() => {
            const rows = document.querySelectorAll('.vault-row');
            for (const row of rows) {
                if (row.textContent.toLowerCase().includes('cover')) {
                    const icon = row.querySelector('.blue-1');
                    if (icon) {
                        icon.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        return fallback

    except Exception as e:
        print(f"Error in uncheck_cover_btn: {str(e)}")
        return False

def click_to_uncheck_media_cover(page, current_bundle):
    """
    Finds the media item matching current_bundle and clicks its blue check icon.
    """
    try:
        # Use JavaScript to find the specific container holding the bundle name
        # and click the blue icon within that same container.
        success = page.evaluate(f'''(bundleName) => {{
            // 1. Find the filename div that contains the bundle text
            const filenameDivs = Array.from(document.querySelectorAll('.image-filename'));
            const targetDiv = filenameDivs.find(el => el.textContent.includes(bundleName));
            
            if (targetDiv) {{
                // 2. Find the parent container (render-container)
                const container = targetDiv.closest('.render-container');
                if (container) {{
                    // 3. Find the blue check icon inside this specific container
                    const checkIcon = container.querySelector('i.blue-1, i.fa-circle');
                    if (checkIcon) {{
                        checkIcon.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        checkIcon.click();
                        return true;
                    }}
                }}
            }}
            return false;
        }}''', current_bundle)
        
        return success
    except Exception as e:
        print(f"Error unchecking bundle {{current_bundle}}: {{str(e)}}")
        return False

def click_on_add_images_btn(page):
    """
    Attempt to find and click the 'Add Images' button using multiple approaches.
    The button text can vary (Add 10 images, Add 9 images, etc).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-footer.flex-col > div.btn.large.solid-blue",
            # Alternative CSS selectors based on classes
            "div.btn.large.solid-blue",
            "div.solid-blue",
            "div.btn.large",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-footer.flex-col > div.btn.large.solid-blue\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[3]/div[2]",
            # Alternative XPaths
            "//div[contains(@class, 'btn') and contains(@class, 'large') and contains(@class, 'solid-blue')]",
            "//div[contains(@class, 'solid-blue')]",
            "//div[contains(text(), 'Add') and contains(text(), 'Images')]",
            "//div[contains(text(), 'Add')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Add Images button selector: {selector}")
                
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
                        #print(f"Successfully clicked Add Images button with JS selector")
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
                            #print(f"Successfully clicked Add Images button with XPath")
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
                            #print(f"Successfully clicked Add Images button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Add Images button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Add Images button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with specific classes and text content
            const buttonSelectors = [
                'div.btn.large.solid-blue',
                'div.solid-blue',
                'div.btn.large',
                'div[class*="btn"]',
                'div[class*="solid"]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button) {
                        // Check if it's in the expected container structure (modal footer)
                        const parentContainer = button.closest('div.modal-footer');
                        if (parentContainer) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                        
                        // Also check for buttons containing "Add" text
                        const buttonText = button.textContent || '';
                        if (buttonText.includes('Add') && buttonText.includes('Images')) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by text content (case insensitive)
            const allDivs = document.querySelectorAll('div');
            for (const div of allDivs) {
                const text = div.textContent || '';
                if (text.includes('Add') && text.includes('Images')) {
                    // Check if it looks like a button (has button-like classes or styling)
                    const classes = div.className || '';
                    if (classes.includes('btn') || classes.includes('solid') || 
                        classes.includes('large') || div.closest('div.modal-footer')) {
                        div.scrollIntoView({behavior: 'smooth', block: 'center'});
                        div.click();
                        return true;
                    }
                }
            }
            
            // Try finding any element with "Add" text in modal footer
            const modalFooters = document.querySelectorAll('div.modal-footer');
            for (const footer of modalFooters) {
                const addElements = footer.querySelectorAll('*');
                for (const element of addElements) {
                    const text = element.textContent || '';
                    if (text.includes('Add') && (text.includes('Images') || text.includes('Image'))) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Add Images button using JavaScript fallback!")
            return True
        
        print("Could not find or click Add Images button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_add_images_btn: {str(e)}")
        return False

def click_on_add_free_preview_btn(page):
    """
    Attempt to find and click the 'Add Free Preview' button/icon (the locked-icon)
    using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.locked-icon",
            # Shorter, less specific CSS selector using classes and attributes
            "div.media-container.selected div.locked-icon",
            "div.locked-icon > i.fa-plus", # Targeting the inner icon which might be more stable
            
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.locked-icon")',
            
            # XPath
            '/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[1]/app-account-media-template/div[1]/div[3]/div/div/div/div[2]',
            # Alternative XPath (using class)
            "//div[contains(@class, 'locked-icon') and ./i[contains(@class, 'fa-plus')]]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Ad Free Preview button selector: {selector}")
                
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
                        #print(f"Successfully clicked Ad Free Preview button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Use force=True to click potentially covered elements, matching your original logic
                            xpath_elements.first.click(force=True, timeout=5000) 
                            #print(f"Successfully clicked Ad Free Preview button with XPath")
                            return True
                        except TimeoutError as e:
                            print(f"XPath click timed out: {str(e)}")
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            # Use force=True
                            css_elements.first.click(force=True, timeout=5000)
                            #print(f"Successfully clicked Ad Free Preview button with CSS selector")
                            return True
                        except TimeoutError as e:
                            print(f"CSS selector click timed out: {str(e)}")
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                # print(f"Failed with Ad Free Preview button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        #print("Trying JavaScript fallback approach for Ad Free Preview button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the icon element by its specific class
            const iconElement = document.querySelector('div.locked-icon');
            if (iconElement) {
                iconElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                iconElement.click();
                return true;
            }
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Ad Free Preview button using JavaScript fallback!")
            return True
        
        # print("Could not find or click Ad Free Preview button using any method.")
        return False
        
    except Exception as e:
        print(f"Error in click_on_ad_free_preview_btn: {str(e)}")
        return False

def click_to_check_the_media(page):
    """
    Attempt to find and click the media check element using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div:nth-child(2) > div.render-container > div.image-controls.image > div > i",
            # Alternative CSS selectors based on classes
            "i.fa-fw.fal.fa-circle",
            "i.fal.fa-circle",
            "i.fa-circle",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div:nth-child(2) > div.render-container > div.image-controls.image > div > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[4]/div/div[2]/div[2]/div[3]/div/i",
            # Alternative XPaths
            "//i[@class='fa-fw fal fa-circle']",
            "//i[contains(@class, 'fa-circle')]",
            "//i[contains(@class, 'fal')]",
            "//div[contains(@class, 'image-controls')]//i[contains(@class, 'fa-circle')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying media check selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    element_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if element_clicked:
                        #print(f"Successfully clicked media check with JS selector")
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
                            #print(f"Successfully clicked media check with XPath")
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
                            #print(f"Successfully clicked media check with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with media check selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for media check...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding circle icon elements
            const circleIconSelectors = [
                'i.fa-fw.fal.fa-circle',
                'i.fal.fa-circle',
                'i.fa-circle',
                '[class*="fa-circle"]',
                'i[class*="circle"]'
            ];
            
            for (const selector of circleIconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        // Check if it's in the expected container structure (image controls)
                        const parentImageControls = icon.closest('div.image-controls.image');
                        if (parentImageControls) {
                            icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            icon.click();
                            return true;
                        }
                        
                        // Also check if it's in render container
                        const parentRenderContainer = icon.closest('div.render-container');
                        if (parentRenderContainer) {
                            icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            icon.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding elements in the specific media vault structure
            const mediaVaults = document.querySelectorAll('app-media-vault');
            for (const vault of mediaVaults) {
                const circleIcons = vault.querySelectorAll('i.fa-circle');
                for (const icon of circleIcons) {
                    // Check if it's in image controls div
                    const imageControls = icon.closest('div.image-controls');
                    if (imageControls) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            // Try finding all circle icons and check their context
            const allCircleIcons = document.querySelectorAll('i');
            for (const icon of allCircleIcons) {
                const classes = icon.className || '';
                if (classes.includes('fa-circle')) {
                    // Check if it's in a media-related container
                    const parent = icon.closest('div');
                    const parentClasses = parent.className || '';
                    if (parentClasses.includes('image-controls') || 
                        parentClasses.includes('render-container') ||
                        parent.closest('app-media-vault')) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            // Try finding by specific structure path
            const imageControls = document.querySelectorAll('div.image-controls.image');
            for (const control of imageControls) {
                const icons = control.querySelectorAll('i');
                for (const icon of icons) {
                    if (icon.classList.contains('fa-circle') || 
                        icon.classList.contains('fal') || 
                        icon.classList.contains('fa-fw')) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked media check using JavaScript fallback!")
            return True
        
        print("Could not find or click media check using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_check_the_media: {str(e)}")
        return False

def check_media_cover(page):
    """
    Finds the first .vault-row associated with a file containing "cover",
    and clicks the icon to CHECK it (targeting the empty/non-blue state).
    """
    try:
        # We target the icon that is NOT currently the 'blue-1' active state
        # or simply the icon within the 'cover' row that is available to be clicked.
        selectors = [
            # Strategy 1: Find row with 'cover' and look for the light/regular circle
            ".vault-row:has-text('cover') i.fa-circle:not(.blue-1)",
            
            # Strategy 2: Targeting any circle icon in the 'cover' row (generic)
            ".vault-row:has(.image-filename:has-text('cover')) .image-controls i",
            
            # Strategy 3: XPath - find row with 'cover' text and get the clickable icon
            "//div[contains(@class, 'vault-row')][descendant::*[contains(text(), 'cover')]]//i[contains(@class, 'fa-circle')]",
            
            # Strategy 4: JS Path for the first available icon in a cover row
            "document.querySelector('.vault-row').querySelector('.image-controls i')"
        ]

        for selector in selectors:
            try:
                if selector.startswith("document.querySelector"):
                    clicked = page.evaluate(f'''() => {{
                        const row = Array.from(document.querySelectorAll('.vault-row'))
                                     .find(r => r.innerText.toLowerCase().includes('cover'));
                        if (row) {{
                            // Try to find an icon that isn't already blue, or just the first icon
                            const icon = row.querySelector('i.fa-circle:not(.blue-1)') || row.querySelector('i');
                            if (icon) {{
                                icon.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                icon.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    if clicked: return True

                elif selector.startswith("//"):
                    element = page.locator(f"xpath={selector}").first
                    if element.count() > 0:
                        element.scroll_into_view_if_needed()
                        element.click(force=True)
                        return True
                
                else:
                    element = page.locator(selector).first
                    if element.count() > 0:
                        # Ensure it's not hidden by Angular styles
                        page.evaluate(f'''(sel) => {{
                            const el = document.querySelector(sel);
                            if(el) {{ el.style.visibility = 'visible'; el.style.opacity = '1'; }}
                        }}''', selector)
                        element.click(force=True)
                        return True

            except Exception:
                continue

        # Final Fallback: Manual row iteration
        fallback = page.evaluate('''() => {
            const rows = document.querySelectorAll('.vault-row');
            for (const row of rows) {
                if (row.textContent.toLowerCase().includes('cover')) {
                    // Look for the circle icon. If it's already blue-1, it's already checked.
                    const icon = row.querySelector('i.fa-circle');
                    if (icon && !icon.classList.contains('blue-1')) {
                        icon.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        return fallback

    except Exception as e:
        print(f"Error in check_media_cover: {str(e)}")
        return False

def click_on_save_changes_btn(page):
    """
    Attempt to find and click the 'Save Changes' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-editor > div > div.modal-footer > div > div.btn.large.solid-blue > xd-localization-string",
            # Alternative CSS selectors based on classes and text
            "div.btn.large.solid-blue xd-localization-string",
            "xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-editor > div > div.modal-footer > div > div.btn.large.solid-blue > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-editor/div/div[3]/div/div[3]/xd-localization-string",
            # Alternative XPaths
            "//xd-localization-string[contains(text(), 'Save Changes')]",
            "//div[contains(@class, 'btn') and contains(@class, 'solid-blue')]//xd-localization-string",
            "//div[contains(@class, 'modal-footer')]//xd-localization-string"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Save Changes button selector: {selector}")
                
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
                        #print(f"Successfully clicked Save Changes button with JS selector")
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
                            #print(f"Successfully clicked Save Changes button with XPath")
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
                            #print(f"Successfully clicked Save Changes button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Save Changes button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Save Changes button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with "Save Changes" text
            const textSelectors = [
                'xd-localization-string',
                'button',
                'div',
                'span'
            ];
            
            for (const selector of textSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    const text = element.textContent || element.innerText || '';
                    if (text.trim() === 'Save Changes') {
                        // Check if it's in the expected container structure
                        const parentModalFooter = element.closest('div.modal-footer');
                        if (parentModalFooter) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                        
                        // Also try clicking if it's in a button-like container
                        const parentButton = element.closest('div.btn.large.solid-blue');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding button elements with specific classes
            const buttonSelectors = [
                'div.btn.large.solid-blue',
                'div.solid-blue',
                'div.btn.large',
                'div[class*="btn"]',
                'div[class*="solid"]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button) {
                        // Check if it's in modal footer and contains "Save Changes" text
                        const parentModalFooter = button.closest('div.modal-footer');
                        const buttonText = button.textContent || button.innerText || '';
                        if (parentModalFooter && buttonText.includes('Save Changes')) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding within app-media-editor specifically
            const mediaEditors = document.querySelectorAll('app-media-editor');
            for (const editor of mediaEditors) {
                // Look for xd-localization-string elements
                const localizationStrings = editor.querySelectorAll('xd-localization-string');
                for (const element of localizationStrings) {
                    const text = element.textContent || element.innerText || '';
                    if (text.trim() === 'Save Changes') {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
                
                // Look for buttons in modal footer
                const modalFooters = editor.querySelectorAll('div.modal-footer');
                for (const footer of modalFooters) {
                    const saveButtons = footer.querySelectorAll('div');
                    for (const button of saveButtons) {
                        const text = button.textContent || button.innerText || '';
                        if (text.includes('Save Changes')) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by text content (case insensitive)
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                const text = element.textContent || element.innerText || '';
                if (text.trim().toLowerCase() === 'save changes') {
                    // Check if it's in a clickable context
                    const style = window.getComputedStyle(element);
                    if (style.cursor === 'pointer' || 
                        element.closest('div.modal-footer') ||
                        element.tagName.toLowerCase() === 'button' ||
                        element.closest('button')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Save Changes button using JavaScript fallback!")
            return True
        
        print("Could not find or click Save Changes button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_save_changes_btn: {str(e)}")
        return False

#def click_from_vault_inside_upload_media_btn(page):
    """
    Attempt to find and click the 'From Vault' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(2)",
            # Alternative CSS selectors
            "div.dropdown-item",
            "div[class*='dropdown-item']",
            "div:has(i.fa-upload)",
            "div:has(xd-localization-string:has-text('From Vault'))",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(2)\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[1]/app-account-media-template/div[1]/div[3]/div/div/div/div[3]/div[2]",
            # Alternative XPaths
            "//div[contains(@class, 'dropdown-item')]",
            "//div[i[contains(@class, 'fa-upload')]]",
            "//xd-localization-string[contains(text(), 'From Vault')]/parent::div"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying From Vault button selector: {selector}")
                
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
                        #print(f"Successfully clicked From Vault button with JS selector")
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
                            print(f"Successfully clicked From Vault button with XPath")
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
                            #print(f"Successfully clicked From Vault button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with From Vault button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        #print("Trying JavaScript fallback approach for From Vault button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding dropdown items with upload icon or From Vault text
            const dropdownSelectors = [
                'div.dropdown-item',
                'div[class*="dropdown-item"]',
                'div.dropdown-list > div'
            ];
            
            for (const selector of dropdownSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    // Check if element contains upload icon or From Vault text
                    const hasUploadIcon = element.querySelector('i.fa-upload, i.fal-upload');
                    const hasFromVaultText = element.textContent.includes('From Vault');
                    
                    if (hasUploadIcon || hasFromVaultText) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by text content
            const allDivs = document.querySelectorAll('div');
            for (const div of allDivs) {
                if (div.textContent.includes('From Vault')) {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked From Vault button using JavaScript fallback!")
            return True
        
        print("Could not find or click From Vault button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_from_vault_inside_upload_media_btn: {str(e)}")
        return False

#def click_on_vault_button_inside_upload_media_modal(page):
    """
    Attempt to find and click the 'From Vault' button inside the Upload Media modal.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(3) > xd-localization-string",
            # Alternative CSS selectors
            "xd-localization-string:contains('From Vault')",
            "div.dropdown-list.center > div:nth-child(3) > xd-localization-string",
            ".dropdown-list.center > div:nth-child(3)",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[1]/app-account-media-template/div[1]/div[3]/div/div/div/div[3]/div[3]/xd-localization-string",
            # Alternative XPath approaches
            "//xd-localization-string[contains(text(), 'From Vault')]",
            "//div[@class='dropdown-list center']//div[contains(., 'From Vault')]",
            "//div[@class='dropdown-item']//xd-localization-string[contains(text(), 'From Vault')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying From Vault button selector: {selector}")

                # Handle different selector types
                if selector.startswith('/'):
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
                            print(f"Successfully clicked From Vault button with XPath")
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
                            print(f"Successfully clicked From Vault button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with From Vault button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for From Vault button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding by text content "From Vault"
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                if (element.textContent && element.textContent.includes('From Vault')) {
                    // Check if it's a clickable element or parent
                    let clickableElement = element;

                    // If it's a localization string, get the parent div
                    if (element.tagName === 'XD-LOCALIZATION-STRING') {
                        clickableElement = element.closest('div.dropdown-item') || element.parentElement;
                    }

                    if (clickableElement) {
                        clickableElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                        clickableElement.click();
                        return true;
                    }
                }
            }

            // Try finding dropdown-list and click the third item
            const dropdownList = document.querySelector('div.dropdown-list.center');
            if (dropdownList) {
                const items = dropdownList.querySelectorAll('div.dropdown-item');
                if (items.length >= 3) {
                    items[2].scrollIntoView({behavior: 'smooth', block: 'center'});
                    items[2].click();
                    return true;
                }
            }

            return false;
        }''')

        if fallback_clicked:
            print("Successfully clicked From Vault button using JavaScript fallback!")
            return True

        print("Could not find or click From Vault button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_vault_button_inside_upload_media_modal: {str(e)}")
        return False

def click_on_vault_button_inside_upload_media_modal(page):
    """
    Attempt to find and click the 'From Vault' button inside the Upload Media modal.
    Starts with XPath for faster execution.
    """
    try:
        # List of selectors to try - XPath FIRST for speed
        selectors = [
            # XPath (FIRST - fastest)
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[1]/app-account-media-template/div[1]/div[3]/div/div/div/div[3]/div[3]/xd-localization-string",
            # Alternative XPath approaches
            "//xd-localization-string[contains(text(), 'From Vault')]",
            "//div[@class='dropdown-list center']//div[contains(., 'From Vault')]",
            "//div[@class='dropdown-item']//xd-localization-string[contains(text(), 'From Vault')]",
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div:nth-child(1) > app-account-media-template > div.media-container.selected > div.preview-image > div > div > div > div.dropdown-list.center > div:nth-child(3) > xd-localization-string",
            # Alternative CSS selectors
            "xd-localization-string:contains('From Vault')",
            "div.dropdown-list.center > div:nth-child(3) > xd-localization-string",
            ".dropdown-list.center > div:nth-child(3)",
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying From Vault button selector: {selector}")

                # Handle XPath selectors (PRIORITY)
                if selector.startswith('/'):
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
                            print(f"Successfully clicked From Vault button with XPath")
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
                            print(f"Successfully clicked From Vault button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with From Vault button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for From Vault button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding by text content "From Vault"
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                if (element.textContent && element.textContent.includes('From Vault')) {
                    // Check if it's a clickable element or parent
                    let clickableElement = element;

                    // If it's a localization string, get the parent div
                    if (element.tagName === 'XD-LOCALIZATION-STRING') {
                        clickableElement = element.closest('div.dropdown-item') || element.parentElement;
                    }

                    if (clickableElement) {
                        clickableElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                        clickableElement.click();
                        return true;
                    }
                }
            }

            // Try finding dropdown-list and click the third item
            const dropdownList = document.querySelector('div.dropdown-list.center');
            if (dropdownList) {
                const items = dropdownList.querySelectorAll('div.dropdown-item');
                if (items.length >= 3) {
                    items[2].scrollIntoView({behavior: 'smooth', block: 'center'});
                    items[2].click();
                    return true;
                }
            }

            return false;
        }''')

        if fallback_clicked:
            print("Successfully clicked From Vault button using JavaScript fallback!")
            return True

        print("Could not find or click From Vault button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_vault_button_inside_upload_media_modal: {str(e)}")
        return False

def click_on_save_changes_btn_inside_modal(page):
    """
    Attempt to find and click the 'Save Changes' button inside modal using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-editor > div > div.modal-footer > div > div.btn.large.solid-blue > xd-localization-string",
            # Alternative CSS selectors
            "div.btn.large.solid-blue",
            "div.modal-footer div.btn.solid-blue",
            "xd-localization-string:has-text('Save Changes')",
            "div.btn:has-text('Save Changes')",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-media-editor > div > div.modal-footer > div > div.btn.large.solid-blue > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-media-editor/div/div[3]/div/div[3]/xd-localization-string",
            # Alternative XPaths
            "//xd-localization-string[contains(text(), 'Save Changes')]",
            "//div[contains(@class, 'btn') and contains(@class, 'solid-blue')]",
            "//div[contains(text(), 'Save Changes')]",
            "//div[@class='modal-footer']//div[contains(@class, 'btn') and contains(text(), 'Save Changes')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Save Changes button selector: {selector}")
                
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
                        #print(f"Successfully clicked Save Changes button with JS selector")
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
                            #print(f"Successfully clicked Save Changes button with XPath")
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
                            #print(f"Successfully clicked Save Changes button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Save Changes button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        #print("Trying JavaScript fallback approach for Save Changes button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with Save Changes text
            const textSelectors = [
                'xd-localization-string',
                'div.btn',
                'div.modal-footer div',
                'div[class*="btn"]'
            ];
            
            for (const selector of textSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element.textContent.includes('Save Changes')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by button classes and modal context
            const modal = document.querySelector('app-media-editor');
            if (modal) {
                const saveButtons = modal.querySelectorAll('.btn.solid-blue, .modal-footer .btn');
                for (const button of saveButtons) {
                    if (button.textContent.includes('Save Changes')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding the solid blue button specifically
            const solidBlueButtons = document.querySelectorAll('.btn.solid-blue');
            for (const button of solidBlueButtons) {
                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                button.click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Save Changes button using JavaScript fallback!")
            return True
        
        print("Could not find or click Save Changes button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_save_changes_btn_inside_modal: {str(e)}")
        return False

def click_On_Load_Preset_btn(page):
    """
    Attempt to find and click the 'Load Preset' button using multiple approaches.
    """
    try:
        # List of selectors to try (updated based on the actual HTML structure)
        selectors = [
            # Text-based selector (most reliable)
            "text=Load Preset",
            # Direct dropdown button
            "div.transparent-dropdown .btn.large:has-text('Load Preset')",
            # Specific dropdown structure
            "app-account-media-permission-flags-editor .transparent-dropdown .btn.large",
            # Button with large class in the permission editor
            "app-account-media-permission-flags-editor .btn.large",
            # Direct CSS selector from the structure
            "div.transparent-dropdown.margin-right-2 > div.btn.large",
            # Alternative text selector
            "div:has-text('Load Preset')",
            # JavaScript path
            "document.querySelector(\"app-account-media-permission-flags-editor .transparent-dropdown .btn.large\")",
            # XPath from the structure
            "//app-account-media-permission-flags-editor//div[@class='transparent-dropdown']/div[contains(@class, 'btn large')]",
            # Alternative XPath
            "//div[contains(@class, 'btn large') and contains(text(), 'Load Preset')]",
            # Full structure XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[1]/div[1]/div[1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Load Preset button selector: {selector}")
                
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
                        #print(f"Successfully clicked Load Preset button with JS selector")
                        return True
                
                elif selector.startswith('/') or selector.startswith('//'):
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
                            #print(f"Successfully clicked Load Preset button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector or text selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                let element;
                                if (selector.includes('has-text') || selector.startsWith('text=')) {{
                                    // Handle text-based selector
                                    const elements = Array.from(document.querySelectorAll('div.btn.large'));
                                    element = elements.find(el => el.textContent.includes('Load Preset'));
                                }} else {{
                                    element = document.querySelector(selector);
                                }}
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked Load Preset button with CSS/text selector")
                            return True
                        except Exception as e:
                            print(f"CSS/text selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Load Preset button selector {selector}: {str(e)}")
                continue
        
        # Enhanced JavaScript fallback approach
        ###print("Trying enhanced JavaScript fallback approach for Load Preset button...")
        fallback_clicked = page.evaluate('''() => {
            // Method 1: Find in the specific permission flags editor section
            const permissionEditor = document.querySelector('app-account-media-permission-flags-editor');
            if (permissionEditor) {
                const dropdownButtons = permissionEditor.querySelectorAll('div.transparent-dropdown div.btn.large');
                for (const button of dropdownButtons) {
                    if (button.textContent.includes('Load Preset')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Method 2: Find all buttons with large class and Load Preset text
            const largeButtons = document.querySelectorAll('div.btn.large');
            for (const button of largeButtons) {
                if (button.textContent.includes('Load Preset')) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Method 3: Find in the media settings section
            const mediaSettings = document.querySelector('.media-settings');
            if (mediaSettings) {
                const buttons = mediaSettings.querySelectorAll('div.btn');
                for (const button of buttons) {
                    if (button.textContent.includes('Load Preset')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Method 4: Find by exact text content
            const allDivs = document.querySelectorAll('div');
            for (const div of allDivs) {
                if (div.textContent.trim() === 'Load Preset') {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Load Preset button using JavaScript fallback!")
            return True
        
        # Final attempt: Wait for the specific element and retry
        ###print("Final attempt: waiting for Load Preset button and retrying...")
        try:
            # Wait for the permission flags editor to be visible
            page.wait_for_selector("app-account-media-permission-flags-editor", timeout=5000)
            
            # Try specific selectors with waiting
            final_selectors = [
                "div.transparent-dropdown .btn.large:has-text('Load Preset')",
                "text=Load Preset",
                "app-account-media-permission-flags-editor .btn.large"
            ]
            
            for final_selector in final_selectors:
                try:
                    element = page.locator(final_selector)
                    element.wait_for(state="visible", timeout=3000)
                    element.click(force=True)
                    #print(f"Successfully clicked using final attempt with: {final_selector}")
                    return True
                except:
                    continue
                    
        except Exception as e:
            print(f"Final attempt failed: {str(e)}")
        
        print("Could not find or click Load Preset button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_On_Load_Preset_btn: {str(e)}")
        return False

def click_On_Mixed_Bundles_Preset_btn(page: Page) -> bool:
    """
    Attempt to find and click the 'mixed_bundles' preset button using multiple approaches.
    """
    # New selector information from your context
    new_css_selector = "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.flex-row.margin-bottom-3 > div.transparent-dropdown.margin-right-2.dropdown-open > div.dropdown-list.bottom.left > div:nth-child(2) > div.flex-1"
    new_xpath_selector = "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[1]/div[1]/div[2]/div[2]/div[1]"

    # List of selectors to try, ordered from most robust to more specific/brittle
    selectors = [
        # 1. Playwright's text-based locator (often most reliable)
        "text=Mixed bundles",
        "div:has-text('Mixed bundles')",

        # 2. Your newly provided specific CSS selector
        new_css_selector,

        # 3. Your newly provided specific XPath selector
        f"xpath={new_xpath_selector}",

        # 4. More general CSS selectors, combined with text if possible
        "div.flex-1:has-text('Mixed bundles')",
        "div[class*='flex-1']:has-text('Mixed bundles')",
        "div.dropdown-list > div:nth-child(2) > div.flex-1", # Using nth-child(2) as per new info
        "div.dropdown-list.bottom.left > div:nth-child(2) > div.flex-1",

        # 5. More general XPaths, combined with text if possible
        "xpath=//div[contains(@class, 'flex-1') and text()='Mixed bundles']",
        "xpath=//div[text()='Mixed bundles']",
        "xpath=//div[contains(text(), 'Mixed bundles')]",
        "xpath=//div[@class='dropdown-list']/div[2]/div[contains(@class, 'flex-1')]" # Using div[2] as per new info
    ]

    for i, selector in enumerate(selectors):
        try:
            print(f"Attempting to click with selector {i+1}/{len(selectors)}: {selector}")

            # Playwright's locator handles CSS and XPath directly
            locator = page.locator(selector)

            # Wait for the element to be visible and enabled
            locator.wait_for(state="visible", timeout=10000) # Wait up to 10 seconds

            # Scroll into view and click. Use force=True as a fallback for stubborn elements.
            # Playwright's click generally handles scrolling, but explicit scroll_into_view_if_needed
            # can sometimes help for very tricky layouts.
            locator.scroll_into_view_if_needed()
            locator.click(timeout=10000, force=True) # Click with a timeout, force if needed

            print(f"Successfully clicked 'Mixed bundles' preset button with selector: {selector}")
            return True

        except TimeoutError:
            print(f"Timeout: Element not found or clickable with selector: {selector}")
        except Error as e:
            print(f"Playwright error with selector {selector}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with selector {selector}: {e}")

    print("Could not find or click 'Mixed bundles' preset button using any method.")
    return False

def click_On_Upload_btn_inside_Upload_Media_Modal(page):
    """
    Attempt to find and click the 'Upload' button inside the Upload Media modal using multiple approaches.
    """
    try:
        # List of selectors to try for the upload button
        selectors = [
            # Direct CSS selector from hierarchy
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-footer.flex-col > div:nth-child(3) > div.btn.solid-blue.large > xd-localization-string",
            # Alternative CSS selectors
            "div.btn.solid-blue.large > xd-localization-string",
            "div.modal-footer xd-localization-string:has-text('Upload')",
            "xd-localization-string:has-text('Upload')",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-footer.flex-col > div:nth-child(3) > div.btn.solid-blue.large > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[3]/div[2]/div[3]/xd-localization-string",
            # Alternative XPaths
            "//xd-localization-string[text()='Upload']",
            "//div[contains(@class, 'btn solid-blue large')]//xd-localization-string",
            "//xd-localization-string[contains(text(), 'Upload')]",
            "//div[@class='modal-footer']//xd-localization-string[text()='Upload']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle JavaScript selector type
                if selector.startswith("document.querySelector"):
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            button.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    if button_clicked: return True
                
                # Handle XPath selector type
                elif selector.startswith('/'):
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        page.evaluate(f'''(xpath) => {{
                            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (element) {{
                                element.style.opacity = '1';
                                element.style.visibility = 'visible';
                                element.style.display = 'block';
                            }}
                        }}''', selector)
                        xpath_elements.first.scroll_into_view_if_needed()
                        xpath_elements.first.click(force=True)
                        return True
                
                # Handle standard CSS selector type
                else:
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        page.evaluate(f'''(sel) => {{
                            const element = document.querySelector(sel);
                            if (element) {{
                                element.style.opacity = '1';
                                element.style.visibility = 'visible';
                                element.style.display = 'block';
                            }}
                        }}''', selector)
                        css_elements.first.scroll_into_view_if_needed()
                        css_elements.first.click(force=True)
                        return True

            except Exception:
                continue
        
        # Fallback JavaScript approach
        fallback_clicked = page.evaluate('''() => {
            const elementSelectors = [
                'xd-localization-string',
                'div.btn.solid-blue.large > xd-localization-string',
                'div.modal-footer xd-localization-string',
                'div.btn.large xd-localization-string'
            ];
            
            for (const selector of elementSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element.textContent.includes('Upload')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        return fallback_clicked

    except Exception as e:
        print(f"Error in click_On_Upload_btn_inside_Upload_Media_Modal: {str(e)}")
        return False

def click_To_Set_Free_Media(page):
    """
    Attempt to find and click the 'FREE' media option using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.flex-row.margin-bottom-3 > div.transparent-dropdown.margin-right-2.dropdown-open > div.dropdown-list.bottom.left > div:nth-child(2) > div.flex-1",
            # Alternative CSS selectors
            "div.dropdown-list.bottom.left > div:nth-child(2) > div.flex-1",
            "div.flex-1:has-text('FREE')",
            "div[class='flex-1']:contains('FREE')",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.flex-row.margin-bottom-3 > div.transparent-dropdown.margin-right-2.dropdown-open > div.dropdown-list.bottom.left > div:nth-child(2) > div.flex-1\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[1]/div[1]/div[2]/div[2]/div[1]",
            # Alternative XPath
            "//div[@class='flex-1' and contains(text(), 'FREE')]",
            "//div[text()='FREE']",
            "//div[contains(@class, 'dropdown-list')]//div[text()='FREE']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying FREE media option selector: {selector}")
                
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
                        #print(f"Successfully clicked FREE media option with JS selector")
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
                            #print(f"Successfully clicked FREE media option with XPath")
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
                            #print(f"Successfully clicked FREE media option with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with FREE media option selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for FREE media option...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding div elements with FREE text
            const freeSelectors = [
                'div.flex-1',
                'div.dropdown-list div',
                'div[class*="dropdown"] div'
            ];
            
            for (const selector of freeSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent.trim() === 'FREE') {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by text content
            const allDivs = document.querySelectorAll('div');
            for (const div of allDivs) {
                if (div.textContent && div.textContent.trim() === 'FREE') {
                    // Check if it's in a dropdown context
                    const parentDropdown = div.closest('div.dropdown-list, div[class*="dropdown"]');
                    if (parentDropdown) {
                        div.scrollIntoView({behavior: 'smooth', block: 'center'});
                        div.click();
                        return true;
                    }
                }
            }
            
            // Try finding dropdown options
            const dropdownOptions = document.querySelectorAll('div.dropdown-list > div, div[class*="dropdown"] > div');
            for (const option of dropdownOptions) {
                const freeText = option.querySelector('div.flex-1, div:first-child');
                if (freeText && freeText.textContent && freeText.textContent.trim() === 'FREE') {
                    option.scrollIntoView({behavior: 'smooth', block: 'center'});
                    option.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked FREE media option using JavaScript fallback!")
            return True
        
        print("Could not find or click FREE media option using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_To_Set_Free_Media: {str(e)}")
        return False

def click_To_Add_Media_Second_Spot(page):
    """
    Attempt to find and click the 'Add Media' plus icon in the second spot using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div.media-container-wrapper.xd-drag-ignore > div > div.dropdown-title > i",
            # Alternative CSS selectors
            "div.dropdown-title > i",
            "i.fa-fw.fal.fa-plus",
            "i[class*='fa-plus']",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div.media-container-wrapper.xd-drag-ignore > div > div.dropdown-title > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[2]/div/div[1]/i",
            # Alternative XPath
            "//i[@class='fa-fw fal fa-plus']",
            "//i[contains(@class, 'fa-plus')]",
            "//div[contains(@class, 'dropdown-title')]//i"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Add Media plus icon selector: {selector}")
                
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
                        #print(f"Successfully clicked Add Media plus icon with JS selector")
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
                            #print(f"Successfully clicked Add Media plus icon with XPath")
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
                            #print(f"Successfully clicked Add Media plus icon with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Add Media plus icon selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Add Media plus icon...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding plus icon elements with specific classes
            const iconSelectors = [
                'i.fa-fw.fal.fa-plus',
                'i[class*="fa-plus"]',
                'div.dropdown-title i',
                'div.media-container-wrapper i'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            // Try finding by parent container structure (second spot specifically)
            const mediaContainers = document.querySelectorAll('div.media-container-wrapper');
            if (mediaContainers.length >= 2) {
                // Target the second container (index 1)
                const secondContainer = mediaContainers[1];
                const plusIcon = secondContainer.querySelector('i.fa-plus, i[class*="plus"]');
                if (plusIcon) {
                    plusIcon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    plusIcon.click();
                    return true;
                }
            }
            
            // Try finding all plus icons and click the appropriate one
            const allPlusIcons = document.querySelectorAll('i.fa-plus, i[class*="plus"]');
            if (allPlusIcons.length > 0) {
                // Try to find one in a media container context
                for (const icon of allPlusIcons) {
                    const inMediaContainer = icon.closest('div.media-container-wrapper, div[class*="media"]');
                    if (inMediaContainer) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
                // If none found in specific context, click the first one
                allPlusIcons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                allPlusIcons[0].click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Add Media plus icon using JavaScript fallback!")
            return True
        
        print("Could not find or click Add Media plus icon using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_To_Add_Media_Second_Spot: {str(e)}")
        return False

def click_To_Add_From_Vault_Second_Spot(page):
    """
    Attempt to find and click the 'From Vault' option in the second spot using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div.media-container-wrapper.xd-drag-ignore > div > div.dropdown-list.center > div:nth-child(2)",
            # Alternative CSS selectors
            "div.dropdown-list.center > div:nth-child(2)",
            "div.dropdown-item:has-text('From Vault')",
            "div[class='dropdown-item']:has(i.fa-photo-film)",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-wrapper-container > div > div.media-container-wrapper.xd-drag-ignore > div > div.dropdown-list.center > div:nth-child(2)\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[1]/div/div[2]/div/div[2]/div[2]",
            # Alternative XPath
            "//div[@class='dropdown-item' and contains(., 'From Vault')]",
            "//div[contains(@class, 'dropdown-list')]//div[contains(text(), 'From Vault')]",
            "//div[i[@class='fal fa-photo-film']]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying From Vault option selector: {selector}")
                
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
                        #print(f"Successfully clicked From Vault option with JS selector")
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
                            #print(f"Successfully clicked From Vault option with XPath")
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
                            #print(f"Successfully clicked From Vault option with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with From Vault option selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for From Vault option...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding dropdown items with "From Vault" text
            const vaultSelectors = [
                'div.dropdown-item',
                'div.dropdown-list div',
                'div[class*="dropdown"] div'
            ];
            
            for (const selector of vaultSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent && element.textContent.includes('From Vault')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by icon class (fa-photo-film)
            const photoFilmIcons = document.querySelectorAll('i.fa-photo-film, i[class*="photo-film"]');
            for (const icon of photoFilmIcons) {
                const parentItem = icon.closest('div.dropdown-item, div[class*="dropdown"]');
                if (parentItem) {
                    parentItem.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentItem.click();
                    return true;
                }
            }
            
            // Try finding the second dropdown item specifically in the second media container
            const mediaContainers = document.querySelectorAll('div.media-container-wrapper');
            if (mediaContainers.length >= 2) {
                const secondContainer = mediaContainers[1];
                const dropdownItems = secondContainer.querySelectorAll('div.dropdown-item, div[class*="dropdown"] > div');
                
                // Try to find the second item (index 1) which should be "From Vault"
                if (dropdownItems.length > 1) {
                    dropdownItems[1].scrollIntoView({behavior: 'smooth', block: 'center'});
                    dropdownItems[1].click();
                    return true;
                }
                
                // If specific index doesn't work, look for "From Vault" text in any item
                for (const item of dropdownItems) {
                    if (item.textContent && item.textContent.includes('From Vault')) {
                        item.scrollIntoView({behavior: 'smooth', block: 'center'});
                        item.click();
                        return true;
                    }
                }
            }
            
            // Fallback: click any dropdown item that contains "Vault"
            const allDropdownItems = document.querySelectorAll('div.dropdown-item, div[role="menu"] div, div[class*="dropdown"] div');
            for (const item of allDropdownItems) {
                if (item.textContent && item.textContent.includes('Vault')) {
                    item.scrollIntoView({behavior: 'smooth', block: 'center'});
                    item.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked From Vault option using JavaScript fallback!")
            return True
        
        print("Could not find or click From Vault option using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_To_Add_From_Vault_Second_Spot: {str(e)}")
        return False

def click_To_Set_Amount_Input(page):
    """
    Attempt to find and click the amount input field using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.permission-settings-container > div:nth-child(3) > app-balance-input > div > input",
            # Alternative CSS selectors
            "app-balance-input input",
            "input[type='text'][step='0.01']",
            "input.conversionHidden",
            "input[required][type='text']",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.permission-settings-container > div:nth-child(3) > app-balance-input > div > input\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[2]/div[3]/app-balance-input/div/input",
            # Alternative XPath
            "//input[@type='text' and @step='0.01']",
            "//input[contains(@class, 'conversionHidden')]",
            "//app-balance-input//input",
            "//div[contains(@class, 'permission-settings-container')]//input"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying amount input selector: {selector}")
                
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
                        #print(f"Successfully clicked amount input with JS selector")
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
                            
                            # Scroll, focus and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.focus()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked amount input with XPath")
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
                            
                            # Scroll, focus and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.focus()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked amount input with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with amount input selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for amount input...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding input elements with specific attributes
            const inputSelectors = [
                'input[type="text"][step="0.01"]',
                'input.conversionHidden',
                'input[required][type="text"]',
                'app-balance-input input',
                'div.permission-settings-container input'
            ];
            
            for (const selector of inputSelectors) {
                const inputs = document.querySelectorAll(selector);
                for (const input of inputs) {
                    if (input) {
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.click();
                        return true;
                    }
                }
            }
            
            // Try finding balance/amount inputs by context
            const balanceContainers = document.querySelectorAll('app-balance-input, div[class*="balance"], div[class*="amount"]');
            for (const container of balanceContainers) {
                const inputs = container.querySelectorAll('input');
                for (const input of inputs) {
                    if (input) {
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.click();
                        return true;
                    }
                }
            }
            
            // Try finding inputs in permission settings context
            const permissionContainers = document.querySelectorAll('div.permission-settings-container, div[class*="permission"]');
            for (const container of permissionContainers) {
                const inputs = container.querySelectorAll('input[type="text"]');
                for (const input of inputs) {
                    if (input) {
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.click();
                        return true;
                    }
                }
            }
            
            // Fallback: find any numeric input with step attribute
            const numericInputs = document.querySelectorAll('input[step]');
            for (const input of numericInputs) {
                if (input) {
                    input.scrollIntoView({behavior: 'smooth', block: 'center'});
                    input.focus();
                    input.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked amount input using JavaScript fallback!")
            return True
        
        print("Could not find or click amount input using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_To_Set_Amount_Input: {str(e)}")
        return False

def click_On_Send_Btn(page):
    """
    Attempt to find and click the 'Send' button using multiple approaches.
    First checks if the button is disabled, and only proceeds if it's not disabled.
    """
    try:
        # First, check if the button is disabled
        disabled_selectors = [
            "app-button.disabled",
            "app-button[disabled]",
            "button.disabled",
            "button[disabled]",
            ".btn.disabled",
            ".btn.outline-blue.disabled",
            "//app-button[contains(@class, 'disabled')]",
            "//button[contains(@class, 'disabled')]"
        ]
        
        for disabled_selector in disabled_selectors:
            try:
                if disabled_selector.startswith('/'):
                    # XPath selector
                    disabled_elements = page.locator(f"xpath={disabled_selector}")
                    if disabled_elements.count() > 0:
                        # Check if any disabled button contains "Send" text
                        for i in range(disabled_elements.count()):
                            element = disabled_elements.nth(i)
                            if "Send" in (element.text_content() or ""):
                                print("Send button is disabled, cannot click.")
                                return False
                else:
                    # CSS selector
                    disabled_elements = page.locator(disabled_selector)
                    if disabled_elements.count() > 0:
                        # Check if any disabled button contains "Send" text
                        for i in range(disabled_elements.count()):
                            element = disabled_elements.nth(i)
                            if "Send" in (element.text_content() or ""):
                                print("Send button is disabled, cannot click.")
                                return False
            except Exception as e:
                continue
        
        # If we get here, the button is not disabled - proceed with clicking
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > app-button > div > span > xd-localization-string",
            # Alternative CSS selectors
            "div.input-footer app-button xd-localization-string",
            "xd-localization-string:has-text('Send')",
            "app-button xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.input-footer > app-button > div > span > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/app-group-message-input/div[3]/app-button/div/span/xd-localization-string",
            # Alternative XPath
            "//xd-localization-string[contains(text(), 'Send')]",
            "//app-button//xd-localization-string[text()='Send']",
            "//div[contains(@class, 'input-footer')]//xd-localization-string"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Send button selector: {selector}")
                
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
                        #print(f"Successfully clicked Send button with JS selector")
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
                            #print(f"Successfully clicked Send button with XPath")
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
                            #print(f"Successfully clicked Send button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Send button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for Send button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with "Send" text that are not disabled
            const sendSelectors = [
                'xd-localization-string',
                'span',
                'div',
                'button',
                'app-button'
            ];
            
            for (const selector of sendSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent && element.textContent.trim() === 'Send') {
                        // Check if element or its parent is disabled
                        let isDisabled = element.closest('.disabled') || 
                                        element.closest('[disabled]') ||
                                        element.closest('app-button.disabled') ||
                                        element.hasAttribute('disabled');
                        
                        if (!isDisabled) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by parent button structure that is not disabled
            const buttons = document.querySelectorAll('app-button:not(.disabled), button:not([disabled]), div[role="button"]:not([disabled])');
            for (const button of buttons) {
                const sendText = button.querySelector('xd-localization-string, span, div');
                if (sendText && sendText.textContent && sendText.textContent.trim() === 'Send') {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding in input footer context that is not disabled
            const inputFooters = document.querySelectorAll('div.input-footer, div[class*="footer"]');
            for (const footer of inputFooters) {
                const sendElements = footer.querySelectorAll('*');
                for (const element of sendElements) {
                    if (element.textContent && element.textContent.trim() === 'Send') {
                        // Check if disabled
                        let isDisabled = element.closest('.disabled') || 
                                        element.closest('[disabled]');
                        
                        if (!isDisabled) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by component context that is not disabled
            const messageInputs = document.querySelectorAll('app-group-message-input, app-message-input');
            for (const input of messageInputs) {
                const sendButtons = input.querySelectorAll('app-button:not(.disabled), button:not([disabled])');
                for (const button of sendButtons) {
                    if (button.textContent && button.textContent.includes('Send')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked Send button using JavaScript fallback!")
            return True
        
        print("Could not find or click Send button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_On_Send_Btn: {str(e)}")
        return False

def click_To_Close_DM_Sent_Message(page):
    """
    Attempt to find and click the close (X) button for DM sent message using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-header > div.actions > div > i",
            # Alternative CSS selectors
            "div.modal-header div.actions i",
            "i.fa-xmark.pointer",
            "i.fa-xmark",
            "i[class*='xmark']",
            "i.blue-1-hover-only",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-header > div.actions > div > i\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[1]/div[2]/div/i",
            # Alternative XPath
            "//i[@class='fa-fw fa fa-xmark pointer blue-1-hover-only hover-effect']",
            "//i[contains(@class, 'fa-xmark')]",
            "//div[contains(@class, 'modal-header')]//i[contains(@class, 'xmark')]",
            "//div[contains(@class, 'actions')]//i"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying close button selector: {selector}")
                
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
                        #print(f"Successfully clicked close button with JS selector")
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
                            #print(f"Successfully clicked close button with XPath")
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
                            #print(f"Successfully clicked close button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with close button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        ###print("Trying JavaScript fallback approach for close button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding close/X icons with specific classes
            const closeIconSelectors = [
                'i.fa-xmark',
                'i.fa-times',
                'i.fa-close',
                'i[class*="xmark"]',
                'i[class*="times"]',
                'i[class*="close"]'
            ];
            
            for (const selector of closeIconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        icon.click();
                        return true;
                    }
                }
            }
            
            // Try finding in modal header actions context
            const modalHeaders = document.querySelectorAll('div.modal-header');
            for (const header of modalHeaders) {
                const actionDivs = header.querySelectorAll('div.actions, div[class*="action"]');
                for (const actions of actionDivs) {
                    const closeIcons = actions.querySelectorAll('i');
                    for (const icon of closeIcons) {
                        if (icon) {
                            icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            icon.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding pointer/hover icons specifically
            const pointerIcons = document.querySelectorAll('i.pointer, i[class*="hover"], i[class*="pointer"]');
            for (const icon of pointerIcons) {
                // Check if it's in a modal or header context
                const inModal = icon.closest('div.modal, div[class*="modal"], app-new-message-modal');
                if (inModal) {
                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    icon.click();
                    return true;
                }
            }
            
            // Try finding by blue hover effect
            const blueHoverIcons = document.querySelectorAll('i.blue-1-hover-only, i[class*="blue"]');
            for (const icon of blueHoverIcons) {
                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                icon.click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked close button using JavaScript fallback!")
            return True
        
        print("Could not find or click close button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_To_Close_DM_Sent_Message: {str(e)}")
        return False

def main():
    # region Handles with Chrome Browser
    # 1. Close all existing Chrome instances to avoid profile conflicts
    close_all_chrome_instances()

    # 2. Launch browser with the desired profile using Playwright
    browser_context, page = open_chrome_with_profile()

    print("Browser started successfully!")
    print("IMPORTANT: Do not close this terminal window to keep Chrome running")

    # Maximize browser window
    pyautogui.press("f11")
    time.sleep(2)
    # endregion

    # region: Click the new message button with retries
    max_retries = 3
    for attempt in range(max_retries):
        if click_on_new_msg_btn(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to click new message button.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)
    else:
        print("Failed to click new message button after all attempts.")
    time.sleep(3)
    # endregion

    # region: Click the New Mass Message button with retries
    max_retries = 3
    success = False
    try:
        page.wait_for_selector("app-new-message-modal", timeout=10000)
    except:
        print("New Message modal not found within timeout")

    for attempt in range(max_retries):
        time.sleep(1)
        if click_on_new_mass_msg_btn(page):
            success = True
            try:
                page.wait_for_timeout(2000)
                selected_indicator = page.locator("div.tab-nav-item.selected:has-text('New Mass Message')")
                if selected_indicator.count() > 0:
                    pass  # Tab correctly selected
                else:
                    print("Note: Unable to verify tab selection, but click was performed")
            except Exception as e:
                print(f"Verification check failed: {e}")
            break
        else:
            print(f"Attempt {attempt + 1} failed to click New Mass Message button.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)

    if not success:
        print("Failed to click New Mass Message button after all attempts.")
    time.sleep(2)
    # endregion

    # region: Uncheck "Exclude Creators" with retries
    max_retries = 3
    for attempt in range(max_retries):
        if click_to_uncheck_exclude_creators_list(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to uncheck Exclude Creators.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to uncheck Exclude Creators after all attempts.")
    time.sleep(3)
    # endregion

    # region: Click include list button (first time)
    max_retries = 3
    for attempt in range(max_retries):
        if click_to_include_list(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to click include list button.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to click include list button after all attempts.")
    time.sleep(3)
    # endregion

    # region: Click "Fans That Have Money" button
    max_retries = 3
    for attempt in range(max_retries):
        if click_Fans_That_Have_Money_btn(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to click Fans That Have Money button.")
            if attempt < max_retries - 1:
                time.sleep(3)
    else:
        print("Failed to click Fans That Have Money button after all attempts.")
    time.sleep(2)
    # endregion

    # region: Click include list button (second time)
    max_retries = 3
    for attempt in range(max_retries):
        if click_to_include_list(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to click include list button.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to click include list button after all attempts.")
    time.sleep(3)
    # endregion

    # region: Click Non-creators button
    max_retries = 3
    for attempt in range(max_retries):
        if click_NonCreator_btn(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed to click Non-creators button.")
            if attempt < max_retries - 1:
                time.sleep(3)
    else:
        print("Failed to click Non-creators button after all attempts.")
    time.sleep(2)
    # endregion

    # region Try to click the 'Next' button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click 'Next' button...")
        if click_on_Next_btn(page):
            #print("Successfully clicked 'Next' button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click 'Next' button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to insert caption in the text area with retries
    max_retries = 3
    caption_to_paste = get_next_caption()

    for attempt in range(max_retries):
        if insert_caption_in_text_area(page, caption_to_paste):
            #print("Caption inserted successfully!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to insert caption after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Insert New Media button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Insert New Media button...")
        if Insert_New_Media_btn(page):
            #print("Successfully clicked Insert New Media button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(3)  # Wait 3 seconds before retrying
    else:
        print("Failed to click Insert New Media button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the From Vault button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click From Vault button...")
        if click_on_from_vault_btn(page):
            #print("Successfully clicked From Vault button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click From Vault button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the Search Albums input with retries
    max_retries = 3
    current_bundle = get_current_bundle_name()

    for attempt in range(max_retries):
        if insert_album_search_term(page, current_bundle):
            #print("Search term inserted successfully!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to interact with Search Albums input after all attempts.")

    time.sleep(3)
    
    # endregion

    # region Try to click the bundle label with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click bundle label for {current_bundle}...")
        if click_on_bundle_label(page, current_bundle):
            #print(f"Successfully clicked bundle label for {current_bundle}!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(3)  # Wait 3 seconds before retrying
    else:
        print(f"Failed to click bundle label for {current_bundle} after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Actions button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Actions button...")
        if click_on_actions_btn(page):
            #print("Successfully clicked Actions button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Actions button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Select All button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Select All button...")
        if click_on_select_all_btn(page):
            #print("Successfully clicked Select All button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Select All button after all attempts.")

    time.sleep(5)
    # endregion

    # region: Click "Uncheck Cover" button
    max_retries = 3
    for attempt in range(max_retries):
        if uncheck_cover_btn(page):
            #print(f"Successfully unchecked cover on attempt {attempt + 1}")
            break
        else:
            print(f"Attempt {attempt + 1} failed to find cover file.")
            if attempt < max_retries - 1:
                time.sleep(3)
    else:
        print("Failed to uncheck cover after all attempts.")
    
    time.sleep(3)
    # endregion

    # region Try to click the Add Images button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Add Images button...")
        if click_on_add_images_btn(page):
            #print("Successfully clicked Add Images button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Add Images button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Add Free Preview button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Add Free Preview button...")
        if click_on_add_free_preview_btn(page):
            #print("Successfully clicked Add Free Preview button!")
            break
        else:
            #print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                #print("Waiting before next attempt...")
                time.sleep(1) # Wait 1 second before retrying
    else:
        print("Failed to click Add Free Preview button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the From Vault button inside Upload Media modal with retries
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1} to click From Vault button...")
        if click_on_vault_button_inside_upload_media_modal(page):
            #print("Successfully clicked From Vault button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(1)  # Wait 1 second before retrying
    else:
        print("Failed to click From Vault button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Search Albums input with retries
    max_retries = 3
    current_bundle = get_current_bundle_name()

    for attempt in range(max_retries):
        if insert_album_search_term(page, current_bundle):
            #print("Search term inserted successfully!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to interact with Search Albums input after all attempts.")

    time.sleep(3)
    
    # endregion

    # region Try to click the bundle label with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click bundle label for {current_bundle}...")
        if click_on_bundle_label(page, current_bundle):
            #print(f"Successfully clicked bundle label for {current_bundle}!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(3)  # Wait 3 seconds before retrying
    else:
        print(f"Failed to click bundle label for {current_bundle} after all attempts.")

    time.sleep(4)
    # endregion

    # region: Click "Check Media Cover" button
    max_retries = 3
    for attempt in range(max_retries):
        if check_media_cover(page):
            #print(f"Successfully checked cover on attempt {attempt + 1}")
            break
        else:
            print(f"Attempt {attempt + 1} failed to find cover file or it was already checked.")
            if attempt < max_retries - 1:
                time.sleep(3)
    else:
        print("Failed to check cover after all attempts.")

    time.sleep(4)
    # endregion

    # region Try to click the Add Images button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Add Images button...")
        if click_on_add_images_btn(page):
            #print("Successfully clicked Add Images button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Add Images button after all attempts.")

    time.sleep(4)
    # endregion

    # region Try to click the Load Preset button with retries
    max_retries = 3
    success = False

    # First, ensure the upload modal and permission section are visible
    try:
        page.wait_for_selector("app-account-media-upload", timeout=10000)
        #print("Upload media modal is visible")
        
        # Wait for the permission flags editor specifically
        page.wait_for_selector("app-account-media-permission-flags-editor", timeout=5000)
        #print("Permission flags editor is visible")
    except Exception as e:
        print(f"Required elements not found: {e}")
        # Continue anyway as the button might still be accessible

    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Load Preset button...")
        
        # Add a small delay before each attempt
        time.sleep(1)
        
        if click_On_Load_Preset_btn(page):
            #print("Successfully clicked Load Preset button!")
            success = True
            
            # Wait for the dropdown to open
            try:
                page.wait_for_selector("div.dropdown-open", timeout=3000)
                #print("Load Preset dropdown opened successfully")
            except:
                print("Note: Unable to verify dropdown opened, but click was performed")
                
            break
        else:
            print(f"Attempt {attempt + 1} failed to click Load Preset button.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait before retrying

    if not success:
        print("Failed to click Load Preset button after all attempts.")
        # Consider taking screenshot for debugging
        # page.screenshot(path="debug_load_preset_failure.png")

    # Wait for interface to stabilize after click
    time.sleep(2)
    # endregion

    # region Try to click the Mixed Bundles preset button with retries
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1} to click Mixed Bundles preset button...")
        if click_On_Mixed_Bundles_Preset_btn(page):
            print("Successfully clicked Mixed Bundles preset button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Mixed Bundles preset button after all attempts.")

    time.sleep(7)
    # endregion

    # region: Click "Upload" button inside Upload Media Modal
    max_retries = 3
    for attempt in range(max_retries):
        if click_On_Upload_btn_inside_Upload_Media_Modal(page):
            #print(f"Successfully clicked Upload button on attempt {attempt + 1}")
            break
        else:
            print(f"Attempt {attempt + 1} failed to click Upload button.")
            if attempt < max_retries - 1:
                time.sleep(3)
    else:
        print("Failed to click Upload button after all attempts.")

    time.sleep(4)
    # endregion

    # region Try to click the Send button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Send button...")
        
        # Check if button is disabled first
        if click_On_Send_Btn(page):
            #print("Successfully clicked Send button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed - button may be disabled or not found.")
            if attempt < max_retries - 1:
                #print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Send button after all attempts. Button may be disabled or unavailable.")

    time.sleep(2)
    # endregion

    print("\nAutomation sequence completed!")
    print("Browser will remain open until you close the popup.")

    # Clean closure of the Playwright browser context
    try:
        browser_context.close()
        print("Browser closed successfully.")
    except Exception as e:
        print(f"Error closing browser: {e}")

    print("Script terminated. Goodbye!")

    # Completely exit the application
    sys.exit(0)

if __name__ == "__main__":
    main()