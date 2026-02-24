import sys
import os
import random
import atexit
import pyperclip
import pyautogui
import time
import subprocess
import pandas as pd
from pathlib import Path    
from playwright.sync_api import sync_playwright

# region Script to help build the executable with PyInstaller
try:
    # Para o executável PyInstaller
    sys.path.append(os.path.join(sys._MEIPASS, "repository"))
except Exception:
    # Para desenvolvimento
    sys.path.append(str(Path(__file__).resolve().parent.parent / "repository"))

# endregion

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
    
    #print("Aviso: Certifique-se de que o Chrome está completamente fechado")
    
    try:
        print("Iniciando Playwright...")
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
        print("Nova aba aberta")
        
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
        #print("Mantendo browser ativo... (Pressione Ctrl+C para encerrar)")
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
                        #print(f"Successfully clicked Maybe Later button with JS selector")
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
                            #print(f"Successfully clicked Maybe Later button with XPath")
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
                            #print(f"Successfully clicked Maybe Later button with selector")
                            return True
                        except Exception as e:
                            print(f"Selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Maybe Later button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Maybe Later button...")
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
            print("Successfully clicked Maybe Later button using JavaScript fallback!")
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
                        print("Successfully clicked password field with JS selector")
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
                            print("Successfully clicked password field with XPath")
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
                            print("Successfully clicked password field with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with password field selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for password field...")
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
            print("Successfully clicked DM button using JavaScript fallback!")
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
                            #print(f"Successfully clicked new message button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with new message button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for new message button...")
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
            print("Successfully clicked new message button using JavaScript fallback!")
            return True
        
        print("Could not find or click new message button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_new_msg_btn: {str(e)}")
        return False

def click_on_new_mass_msg_btn(page):
    """
    Attempt to find and click the "New Mass Message" button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "xd-localization-string:has-text('New Mass Message')",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.tab-nav-wrapper.font-size-sm > div > div:nth-child(2) > xd-localization-string\")",
            # XPath
            "//xd-localization-string[contains(text(), 'New Mass Message')]",
            # Alternative XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[1]/div/div[2]/xd-localization-string"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying New Mass Message button selector: {selector}")
                
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
                        #print(f"Successfully clicked New Mass Message button with JS selector")
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
                            #print(f"Successfully clicked New Mass Message button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector (or Playwright's text selector)
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                let element;
                                if (selector.includes('has-text')) {{
                                    // Handle text-based selector
                                    const elements = Array.from(document.querySelectorAll('xd-localization-string'));
                                    element = elements.find(el => el.textContent.includes('New Mass Message'));
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
                            #print(f"Successfully clicked New Mass Message button with CSS/text selector")
                            return True
                        except Exception as e:
                            print(f"CSS/text selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with New Mass Message button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for New Mass Message button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with the exact text
            const elements = document.querySelectorAll('xd-localization-string');
            for (const element of elements) {
                if (element.textContent.includes('New Mass Message')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            // Try finding parent elements that might contain the text
            const divElements = document.querySelectorAll('div.tab-nav-wrapper div');
            for (const div of divElements) {
                if (div.textContent.includes('New Mass Message')) {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked New Mass Message button using JavaScript fallback!")
            return True
        
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
        print("Trying JavaScript fallback approach for Exclude Creators...")
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
            print("Successfully unchecked Exclude Creators using JavaScript fallback!")
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
        print("Trying JavaScript fallback approach for include list button...")
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
            print("Successfully clicked include list button using JavaScript fallback!")
            return True
        
        print("Could not find or click include list button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_include_list: {str(e)}")
        return False

def click_on_creators_all_list(page):
    """
    Attempt to find and click the "Creators ⭐" list header using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Text-based selector (most reliable)
            "div.bold:has-text('Creators ⭐')",
            # CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(1) > app-list > div > div > div.bold",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(1) > app-list > div > div > div.bold\")",
            # XPath with text
            "//div[contains(@class, 'bold') and contains(text(), 'Creators ⭐')]",
            # Alternative XPath
            "/html/body/app-root/div/div[3]/app-list-select-modal/div/div[2]/div[1]/app-list/div/div/div[1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Creators list selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if clicked:
                        #print(f"Successfully clicked Creators list with JS selector")
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
                            #print(f"Successfully clicked Creators list with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS/text selector
                    elements = page.locator(selector)
                    if elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                let element;
                                if (selector.includes('has-text')) {{
                                    // Handle text-based selector
                                    const divs = Array.from(document.querySelectorAll('div.bold'));
                                    element = divs.find(el => el.textContent.includes('Creators ⭐'));
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
                            elements.first.scroll_into_view_if_needed()
                            elements.first.click(force=True)
                            #print(f"Successfully clicked Creators list with CSS/text selector")
                            return True
                        except Exception as e:
                            print(f"CSS/text selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Creators list selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Creators list...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with the exact text
            const elements = document.querySelectorAll('div.bold');
            for (const element of elements) {
                if (element.textContent.includes('Creators ⭐')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            // Try any bold div in the modal content
            const modalContent = document.querySelector('div.modal-content');
            if (modalContent) {
                const boldDivs = modalContent.querySelectorAll('div.bold');
                for (const div of boldDivs) {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Creators list using JavaScript fallback!")
            return True
        
        print("Could not find or click Creators list using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_creators_all_list: {str(e)}")
        return False

def click_on_creators_that_have_money_list(page):
    """
    Attempt to find and click the "Creator $" list header using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Text-based selector (most reliable)
            "div.bold:has-text('Creator $')",
            # CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(7) > app-list > div > div > div.bold",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-list-select-modal > div > div.modal-content.margin-top-3 > div:nth-child(7) > app-list > div > div > div.bold\")",
            # XPath with text
            "//div[contains(@class, 'bold') and contains(text(), 'Creator $')]",
            # Alternative XPath
            "/html/body/app-root/div/div[3]/app-list-select-modal/div/div[2]/div[7]/app-list/div/div/div[1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Creator $ list selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if clicked:
                        #print(f"Successfully clicked Creator $ list with JS selector")
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
                            #print(f"Successfully clicked Creator $ list with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS/text selector
                    elements = page.locator(selector)
                    if elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                let element;
                                if (selector.includes('has-text')) {{
                                    // Handle text-based selector
                                    const divs = Array.from(document.querySelectorAll('div.bold'));
                                    element = divs.find(el => el.textContent.includes('Creator $'));
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
                            elements.first.scroll_into_view_if_needed()
                            elements.first.click(force=True)
                            #print(f"Successfully clicked Creator $ list with CSS/text selector")
                            return True
                        except Exception as e:
                            print(f"CSS/text selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Creator $ list selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Creator $ list...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with the exact text
            const elements = document.querySelectorAll('div.bold');
            for (const element of elements) {
                if (element.textContent.includes('Creator $')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }
            
            // Try any bold div in the 7th position of modal content
            const modalContent = document.querySelector('div.modal-content');
            if (modalContent) {
                const seventhDiv = modalContent.children[6]; // 0-based index
                if (seventhDiv) {
                    const boldDiv = seventhDiv.querySelector('div.bold');
                    if (boldDiv) {
                        boldDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
                        boldDiv.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Creator $ list using JavaScript fallback!")
            return True
        
        print("Could not find or click Creator $ list using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_creators_that_have_money_list: {str(e)}")
        return False

def click_on_Schedule_Mass_DM_btn(page):
    """
    Attempt to find and click the Schedule Mass DM button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.bold.margin-top-3.option-header > div.dark-blue-1.flex-row.margin-right-1.pointer.blue-1-hover-only > div > i.fa-fw.fal.fa-calendar",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div.bold.margin-top-3.option-header > div.dark-blue-1.flex-row.margin-right-1.pointer.blue-1-hover-only > div > i.fa-fw.fal.fa-calendar\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[12]/div[2]/div/i[1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying Schedule Mass DM button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.closest('div').click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        #print(f"Successfully clicked Schedule Mass DM button with JS selector")
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
                            #print(f"Successfully clicked Schedule Mass DM button with XPath")
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
                            #print(f"Successfully clicked Schedule Mass DM button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Schedule Mass DM button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Schedule Mass DM button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding calendar icon elements
            const iconSelectors = [
                'i.fa-calendar',
                'i.fal.fa-calendar',
                'i.fa-fw.fal.fa-calendar'
            ];
            
            for (const selector of iconSelectors) {
                const iconElements = document.querySelectorAll(selector);
                for (const icon of iconElements) {
                    if (icon) {
                        icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                        // Try clicking the icon or its closest clickable parent
                        const clickableParent = icon.closest('div[clickable], div.pointer');
                        if (clickableParent) {
                            clickableParent.click();
                            return true;
                        }
                        icon.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Schedule Mass DM button using JavaScript fallback!")
            return True
        
        print("Could not find or click Schedule Mass DM button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Schedule_Mass_DM_btn: {str(e)}")
        return False

def click_on_One_More_Day_btn(page):
    """
    Attempt to find and click the '+1d' (One More Day) button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(5)",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(5)\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/app-xd-date-picker/div[6]/div[5]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying '+1d' button selector: {selector}")
                
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
                        #print(f"Successfully clicked '+1d' button with JS selector")
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
                            #print(f"Successfully clicked '+1d' button with XPath")
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
                            #print(f"Successfully clicked '+1d' button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with '+1d' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for '+1d' button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with '+1d' text
            const buttonSelectors = [
                'div.btn.margin-right-1',
                'div[class*="btn"][class*="margin-right-1"]',
                'div:contains("+1d")'
            ];
            
            for (const selector of buttonSelectors) {
                const buttonElements = document.querySelectorAll(selector);
                for (const button of buttonElements) {
                    if (button && (button.textContent.includes('+1d') || button.innerText.includes('+1d'))) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked '+1d' button using JavaScript fallback!")
            return True
        
        print("Could not find or click '+1d' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_One_More_Day_btn: {str(e)}")
        return False

def click_on_24_hours_btn(page):
    """
    Attempt to find and click the '+24h' button using multiple approaches.
    """
    try:
        # List of selectors to try - focused on identifying the specific +24h button
        selectors = [
            # Direct CSS selector for the specific +24h button
            "div.flex-row.flex-wrap.flex-align-center.margin-top-text > div.btn.margin-right-1:last-child",
            "div.btn.margin-right-1:contains('+24h')",
            # Text-based selectors
            "text=+24h",
            # Specific position in the container (last child)
            "div.flex-row.flex-wrap.flex-align-center.margin-top-text > div:nth-child(6)",
            # Full provided selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(6)",
            # Class-based selector with text content
            "div.btn.margin-right-1",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(6)\")",
            # XPath from provided
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/app-xd-date-picker/div[6]/div[6]",
            # Smart XPath that finds the specific +24h button
            "//div[contains(@class, 'flex-row') and contains(@class, 'flex-wrap')]/div[contains(@class, 'btn') and contains(@class, 'margin-right-1') and contains(text(), '+24h')]",
            "//div[contains(@class, 'btn') and contains(@class, 'margin-right-1') and text()=' +24h ']",
            "//div[contains(@class, 'flex-row')]/div[position()=6]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                ##print(f"Trying +24h button selector: {selector}")
                
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
                        ##print(f"Successfully clicked +24h button with JS selector")
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
                            ##print(f"Successfully clicked +24h button with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                elif selector.startswith('text='):
                    # Text selector
                    text_elements = page.locator(selector)
                    if text_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const text = selector.replace('text=', '');
                                const elements = document.querySelectorAll('div');
                                for (const element of elements) {{
                                    if (element.textContent && element.textContent.includes(text)) {{
                                        element.style.opacity = '1';
                                        element.style.visibility = 'visible';
                                        element.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            text_elements.first.scroll_into_view_if_needed()
                            text_elements.first.click(force=True)
                            ##print(f"Successfully clicked +24h button with text selector")
                            return True
                        except Exception as e:
                            print(f"Text selector click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # For CSS selectors, we need to ensure we're clicking the right button
                            if 'contains' in selector or css_elements.count() == 1:
                                # This is likely our specific button or a text-based selector
                                css_elements.first.scroll_into_view_if_needed()
                                css_elements.first.click(force=True)
                                ##print(f"Successfully clicked +24h button with CSS selector")
                                return True
                            else:
                                # Multiple buttons found, need to find the one with +24h text
                                for i in range(css_elements.count()):
                                    element = css_elements.nth(i)
                                    text_content = element.text_content()
                                    if text_content and '+24h' in text_content:
                                        element.scroll_into_view_if_needed()
                                        element.click(force=True)
                                        ##print(f"Successfully clicked +24h button with filtered CSS selector")
                                        return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with +24h button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach - specifically for the button group
        #print("Trying JavaScript fallback approach for +24h button...")
        fallback_clicked = page.evaluate('''() => {
            // Method 1: Find the container and get the last button (+24h)
            const container = document.querySelector('div.flex-row.flex-wrap.flex-align-center.margin-top-text');
            if (container) {
                const buttons = container.querySelectorAll('div.btn.margin-right-1');
                if (buttons.length >= 6) {
                    // +24h is the last button (6th)
                    const plus24hBtn = buttons[5];
                    plus24hBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                    plus24hBtn.click();
                    return true;
                }
            }
            
            // Method 2: Find by exact text content
            const allDivs = document.querySelectorAll('div.btn.margin-right-1');
            for (const div of allDivs) {
                if (div.textContent && div.textContent.trim() === '+24h') {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            // Method 3: Find by partial text
            for (const div of allDivs) {
                if (div.textContent && div.textContent.includes('+24h')) {
                    div.scrollIntoView({behavior: 'smooth', block: 'center'});
                    div.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            #print("Successfully clicked +24h button using JavaScript fallback!")
            return True
        
        print("Could not find or click +24h button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_24_hours_btn: {str(e)}")
        return False

def click_for_tomorrow_button(page):
    """
    Attempt to find and click the '+24h' (Tomorrow) button using multiple approaches.
    """
    try:
        # List of selectors to try based on provided parameters
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(6)",
            # Alternative CSS using classes
            "div.btn.margin-right-1",
            # JavaScript path (provided)
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(6)\")",
            # XPath (provided)
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/app-xd-date-picker/div[6]/div[6]",
            # Text-based Playwright locator
            "text='+24h'"
        ]

        for selector in selectors:
            try:
                if selector.startswith("document.querySelector"):
                    # JavaScript selector approach
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
                        return True
                
                elif selector.startswith('/') or selector.startswith('xpath='):
                    # XPath approach
                    clean_xpath = selector.replace("xpath=", "")
                    xpath_elements = page.locator(f"xpath={clean_xpath}")
                    if xpath_elements.count() > 0:
                        xpath_elements.first.scroll_into_view_if_needed()
                        xpath_elements.first.click(force=True)
                        return True
                
                else:
                    # CSS or Text selector approach
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        css_elements.first.scroll_into_view_if_needed()
                        css_elements.first.click(force=True)
                        return True
                        
            except Exception:
                continue
        
        # Fallback JavaScript approach specifically for the +24h text
        fallback_clicked = page.evaluate('''() => {
            const divs = Array.from(document.querySelectorAll('div.btn'));
            const tomorrowBtn = divs.find(el => el.textContent.includes('+24h'));
            if (tomorrowBtn) {
                tomorrowBtn.scrollIntoView({behavior: 'smooth', block: 'center'});
                tomorrowBtn.click();
                return true;
            }
            return false;
        }''')
        
        return fallback_clicked

    except Exception as e:
        print(f"Error in click_for_tomorrow_button: {str(e)}")
        return False

def click_on_Hour_Listbox(page):
    """
    Attempt to find and select a random hour (00-23) from the hour listbox using multiple approaches.
    Args:
        page: Playwright page object
    """
    try:
        # Generate random hour between 00 and 23 with leading zero
        hour_to_select = f"{random.randint(0, 23):02d}"
        #print(f"\nAttempting to select random hour: {hour_to_select}")

        # List of selectors to try for the hour dropdown
        selectors = [
            # Direct CSS selector for the select element
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(4) > div:nth-child(1) > select",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(4) > div:nth-child(1) > select\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/app-xd-date-picker/div[3]/div[1]/select"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying hour listbox selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    selection_successful = page.evaluate(f'''(hour_value) => {{
                        const selectElement = {selector};
                        if (selectElement) {{
                            selectElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            selectElement.value = hour_value;
                            selectElement.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }}''', hour_to_select)
                    
                    if selection_successful:
                        #print(f"Successfully selected hour {hour_to_select} with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility and select the hour
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.select_option(value=hour_to_select)
                            #print(f"Successfully selected hour {hour_to_select} with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath selection failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility and select the hour
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.select_option(value=hour_to_select)
                            #print(f"Successfully selected hour {hour_to_select} with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector selection failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with hour listbox selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for hour listbox...")
        fallback_successful = page.evaluate('''(hour_value) => {
            // Try finding select elements that might be the hour dropdown
            const selectSelectors = [
                'select.form-select.text-center.pointer',
                'div.material-input select',
                'select[class*="form-select"]'
            ];
            
            for (const selector of selectSelectors) {
                const selectElements = document.querySelectorAll(selector);
                for (const select of selectElements) {
                    // Check if this is likely the hour dropdown by looking for HH label
                    const parentDiv = select.closest('div.material-input');
                    if (parentDiv) {
                        const labels = parentDiv.querySelectorAll('div.label');
                        for (const label of labels) {
                            if (label.textContent.includes('HH')) {
                                select.value = hour_value;
                                select.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }
                        }
                    }
                    
                    // Fallback check for options length
                    if (select.options.length >= 24) {
                        select.value = hour_value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                }
            }
            return false;
        }''', hour_to_select)
        
        if fallback_successful:
            #print(f"Successfully selected hour {hour_to_select} using JavaScript fallback!")
            return True
        
        print("Could not find or interact with hour listbox using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Hour_Listbox: {str(e)}")
        return False

def click_on_Check_Remember_Time_Option(page):
    """
    Attempt to find and click the 'Remember Time' checkbox using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > div.flex-row.margin-top-1 > app-xd-checkbox > div",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > div.flex-row.margin-top-1 > app-xd-checkbox > div\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/div[2]/app-xd-checkbox/div"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying 'Remember Time' checkbox selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    checkbox_clicked = page.evaluate(f'''() => {{
                        const checkboxElement = {selector};
                        if (checkboxElement) {{
                            checkboxElement.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            checkboxElement.click();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if checkbox_clicked:
                        #print(f"Successfully clicked 'Remember Time' checkbox with JS selector")
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
                            #print(f"Successfully clicked 'Remember Time' checkbox with XPath")
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
                            #print(f"Successfully clicked 'Remember Time' checkbox with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with 'Remember Time' checkbox selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for 'Remember Time' checkbox...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding checkbox elements
            const checkboxSelectors = [
                'div.checkbox',
                'div[class*="checkbox"]',
                'div[role="checkbox"]'
            ];
            
            for (const selector of checkboxSelectors) {
                const checkboxes = document.querySelectorAll(selector);
                for (const checkbox of checkboxes) {
                    // Check if it's in the right context
                    const parentText = checkbox.parentElement?.textContent?.toLowerCase() || '';
                    if (parentText.includes('remember') || parentText.includes('time')) {
                        checkbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                        checkbox.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked 'Remember Time' checkbox using JavaScript fallback!")
            return True
        
        print("Could not find or click 'Remember Time' checkbox using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Check_Remember_Time_Option: {str(e)}")
        return False

def uncheck_remember_time(page):
    """
    Finds the 'Remember Time' checkbox and clicks it ONLY if it is currently selected.
    """
    try:
        # Use the selectors you provided
        selectors = [
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > div.flex-row.margin-top-1 > app-xd-checkbox > div",
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/div[2]/app-xd-checkbox/div"
        ]

        for selector in selectors:
            # Check if this specific element exists and has the 'selected' class
            locator = page.locator(selector)
            
            if locator.count() > 0:
                # Get the class attribute to see if it contains 'selected'
                classes = locator.first.get_attribute("class") or ""
                
                if "selected" in classes:
                    # It is checked, so click to uncheck
                    locator.first.scroll_into_view_if_needed()
                    locator.first.click(force=True)
                    return True
                else:
                    # It's already unchecked
                    return "ALREADY_UNCHECKED"

        # Fallback JavaScript to handle complex "selected" state logic
        return page.evaluate('''() => {
            const xpath = "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/div[2]/app-xd-checkbox/div";
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue 
                            || document.querySelector("app-xd-checkbox > div");

            if (element) {
                if (element.classList.contains('selected')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
                return "ALREADY_UNCHECKED";
            }
            return false;
        }''')

    except Exception as e:
        print(f"Error in uncheck_remember_time: {str(e)}")
        return False

def click_on_Confirm_Date_btn(page):
    """
    Attempt to find and click the 'Confirm Date' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-footer > div.btn.outline-blue.large.confirm-btn > xd-localization-string",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-footer > div.btn.outline-blue.large.confirm-btn > xd-localization-string\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[3]/div[3]/xd-localization-string",
            # Alternative selector for the parent button
            "div.btn.outline-blue.large.confirm-btn"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying 'Confirm Date' button selector: {selector}")
                
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
                        #print(f"Successfully clicked 'Confirm Date' button with JS selector")
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
                            #print(f"Successfully clicked 'Confirm Date' button with XPath")
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
                            #print(f"Successfully clicked 'Confirm Date' button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with 'Confirm Date' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for 'Confirm Date' button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding buttons with confirm text
            const buttonSelectors = [
                'div.btn',
                'button',
                'div[role="button"]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    const buttonText = button.textContent?.toLowerCase()?.trim();
                    if (buttonText && (buttonText.includes('confirm') || buttonText.includes('date'))) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked 'Confirm Date' button using JavaScript fallback!")
            return True
        
        print("Could not find or click 'Confirm Date' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Confirm_Date_btn: {str(e)}")
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
        print("Trying JavaScript fallback approach for 'Next' button...")
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
            print("Successfully clicked 'Next' button using JavaScript fallback!")
            return True
        
        print("Could not find or click 'Next' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Next_btn: {str(e)}")
        return False

def click_on_Text_Area(page):
    """
    Attempt to find and focus/click the text area using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.material-input > textarea",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-new-message-modal > div > div.modal-content > div:nth-child(2) > app-group-message-input > div.material-input > textarea\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-new-message-modal/div/div[2]/div[2]/app-group-message-input/div[2]/textarea",
            # More general selector
            "textarea.material-input"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying text area selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    textarea_focused = page.evaluate(f'''() => {{
                        const textarea = {selector};
                        if (textarea) {{
                            textarea.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            textarea.focus();
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    if textarea_focused:
                        #print(f"Successfully focused text area with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility and focus
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
                                    element.focus();
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully interacted with text area using XPath")
                            return True
                        except Exception as e:
                            print(f"XPath interaction failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility and focus
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.focus();
                                }}
                            }}''', selector)
                            
                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            #print(f"Successfully interacted with text area using CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector interaction failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with text area selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for text area...")
        fallback_focused = page.evaluate('''() => {
            // Try finding textarea elements
            const textareaSelectors = [
                'textarea',
                'textarea[rows]',
                'textarea.material-input'
            ];
            
            for (const selector of textareaSelectors) {
                const textareas = document.querySelectorAll(selector);
                for (const textarea of textareas) {
                    if (textarea) {
                        textarea.scrollIntoView({behavior: 'smooth', block: 'center'});
                        textarea.focus();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_focused:
            print("Successfully focused text area using JavaScript fallback!")
            return True
        
        print("Could not find or interact with text area using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Text_Area: {str(e)}")
        return False

def insert_random_msg_in_text_area(page, message_text):
    """
    Finds the text area using multiple selectors and uses fill() 
    to enter the message text directly.
    """
    try:
        # Combined selectors based on your click_on_Text_Area logic
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
                    # Use fill() to insert text directly (Approach from source 1 & 3)
                    element.fill(message_text)
                    return True
            except Exception:
                continue
        
        return False
    
    except Exception as e:
        print(f"Error in insert_random_msg_in_text_area: {str(e)}")
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
        print("Trying JavaScript fallback approach for Send button...")
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
            print("Successfully clicked Send button using JavaScript fallback!")
            return True
        
        print("Could not find or click Send button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_Send_btn: {str(e)}")
        return False

def click_on_One_More_Hour_btn(page):
    """
    Attempt to find and click the '+1h' (One More Hour) button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(4)",
            # JavaScript path
            "document.querySelector(\"body > app-root > div > div.modal-wrapper > app-message-schedule-modal > div > div.modal-content > app-xd-date-picker > div:nth-child(7) > div:nth-child(4)\")",
            # XPath
            "/html/body/app-root/div/div[3]/app-message-schedule-modal/div/div[2]/app-xd-date-picker/div[6]/div[4]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying '+1h' button selector: {selector}")
                
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
                        #print(f"Successfully clicked '+1h' button with JS selector")
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
                            #print(f"Successfully clicked '+1h' button with XPath")
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
                            #print(f"Successfully clicked '+1h' button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with '+1h' button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for '+1h' button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with '+1h' text
            const buttonSelectors = [
                'div.btn.margin-right-1',
                'div[class*="btn"][class*="margin-right-1"]',
                'div:contains("+1h")'
            ];
            
            for (const selector of buttonSelectors) {
                const buttonElements = document.querySelectorAll(selector);
                for (const button of buttonElements) {
                    if (button && (button.textContent.includes('+1h') || button.innerText.includes('+1h'))) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked '+1h' button using JavaScript fallback!")
            return True
        
        print("Could not find or click '+1h' button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_One_More_Hour_btn: {str(e)}")
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
        print("Trying JavaScript fallback approach for close button...")
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
            print("Successfully clicked close button using JavaScript fallback!")
            return True
        
        print("Could not find or click close button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_Close_Mass_DM_Sent_Confirmation_Window: {str(e)}")
        return False

def main():

    # region Closes any Chrome Browser instances
    time.sleep(2)
    print("Closing browser instances...")
    os.system("taskkill /f /im chrome.exe")
    time.sleep(2)
    # endregion

    # region start browser with profile
    browser_context, page = open_chrome_with_profile()
    
    # Manter browser ativo - IMPORTANTE!
    print("Browser iniciado com sucesso!")
    print("IMPORTANTE: Não feche este terminal para manter o Chrome ativo")
    
    # Maximize browser window 
    pyautogui.press("f11")

    time.sleep(2)
    # endregion

    # region Try to click the new message button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click new message button...")
        if click_on_new_msg_btn(page):
            #print("Successfully clicked new message button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click new message button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the New Mass Message button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click New Mass Message button...")
        if click_on_new_mass_msg_btn(page):
            #print("Successfully clicked New Mass Message button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click New Mass Message button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to uncheck Exclude Creators with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to uncheck Exclude Creators...")
        if click_to_uncheck_exclude_creators_list(page):
            print("Successfully unchecked Exclude Creators!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait 2 seconds before retrying
    else:
        print("Failed to uncheck Exclude Creators after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the include list button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click include list button...")
        if click_to_include_list(page):
            #print("Successfully clicked include list button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait 2 seconds before retrying
    else:
        print("Failed to click include list button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the Creators list header with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Creators list...")
        if click_on_creators_all_list(page):
            #print("Successfully clicked Creators list!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait 2 seconds before retrying
    else:
        print("Failed to click Creators list after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the include list button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click include list button...")
        if click_to_include_list(page):
            #print("Successfully clicked include list button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait 2 seconds before retrying
    else:
        print("Failed to click include list button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the Creator $ list header with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Creator $ list...")
        if click_on_creators_that_have_money_list(page):
            #print("Successfully clicked Creator $ list!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Wait 2 seconds before retrying
    else:
        print("Failed to click Creator $ list after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the Schedule Mass DM button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Schedule Mass DM button...")
        if click_on_Schedule_Mass_DM_btn(page):
            #print("Successfully clicked Schedule Mass DM button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Schedule Mass DM button after all attempts.")

    time.sleep(2)
    # endregion

    # region Uncheck Remember Time
    max_retries = 3
    for attempt in range(max_retries):
        result = uncheck_remember_time(page)
        
        if result == True:
            print("Successfully unchecked 'Remember Time'.")
            break
        elif result == "ALREADY_UNCHECKED":
            print("'Remember Time' was already unchecked - skipping.")
            break
        else:
            print(f"Attempt {attempt + 1} to uncheck failed (Element not found).")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to uncheck 'Remember Time' after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the Tomorrow (+24h) button
    max_retries = 3
    for attempt in range(max_retries):
        if click_for_tomorrow_button(page):
            # print("Successfully clicked Tomorrow (+24h) button!")
            break
        else:
            print(f"Attempt {attempt + 1} to click Tomorrow button failed.")
            if attempt < max_retries - 1:
                time.sleep(1) 
    else:
        print("Failed to click Tomorrow button after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to select random hour from listbox with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to select random hour...")
        if click_on_Hour_Listbox(page):
            print("Successfully selected random hour!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Shorter wait time for dropdown interaction
    else:
        print("Failed to select hour after all attempts.")

    time.sleep(2)
    # endregion

    # region Try to click the 'Confirm Date' button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click 'Confirm Date' button...")
        if click_on_Confirm_Date_btn(page):
            #print("Successfully clicked 'Confirm Date' button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click 'Confirm Date' button after all attempts.")

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

    time.sleep(2)
    # endregion

    # region Try to insert random message in the text area with retries
    max_retries = 3

    # Random message selection
    text_to_insert = random.choice([
        '''6$ 👉 Mass DM to all my followers or fans "(subscribers, buyers and potential buyers)".

        Tip on the TIPOMETER (Creators Support) 🪙 here: https://fansly.com/post/732275677243383808

        ‼️Don't tip this message, tip the post above 👆🏻

        Send me your best post link 🔥

        Include a non-censored naughty picture (suggested) 😈

        Tell me if you want to send it to the Creators too ⭐

        And wait for answer with Mass DM proof send 🤩

        Offer ends today 11:59 PM ⏱️''',
        
        '''💓💣💓💣💓💣ᒪIKᗴ ᗷOᗰᗷ💓💣💓💣💓💣💓

        𝗧𝗜𝗣 2$ (𝗧𝗪𝗢 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to receive about 100 likes
        
        𝗧𝗜𝗣 3$ (𝗧𝗛𝗥𝗘𝗘 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to receive about 200 likes

        𝗧𝗜𝗣 4$ (𝗙𝗢𝗨𝗥 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to receive about 300 likes

        If you are interested, please TIP on the TIPOMETER gauge here: https://fansly.com/post/732275677243383808''',

        '''🔝📌 TOP PINNED POST 📌🔝

        𝗧𝗜𝗣 2$ (𝗧𝗪𝗢 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to be pinned on the tops of my feed for 3 days!

        𝗧𝗜𝗣 4$ (𝗙𝗢𝗨𝗥 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to be pinned on the tops of my feed for 7 days!

        𝗧𝗜𝗣 8$ (𝗘𝗜𝗚𝗛𝗧 𝗗𝗢𝗟𝗟𝗔𝗥𝗦) to be pinned on the tops of my feed for 15 days!

        If you are interested, please TIP on the TIPOMETER gauge here: https://fansly.com/post/732275677243383808

        And send me your best post link!! 🔥🔥🔥''',


        '''⚒️⚡ 𝗘𝗟𝗘𝗖𝗧𝗥𝗔'𝗦 𝗧𝗛𝗨𝗡𝗗𝗘𝗥 𝗣𝗥𝗢𝗠𝗢 ⚡⚒️

        📧 (scheduled) + 7 days pinned 📌 post + 1 Story Shout-out 📢 for only 10$

        🔥 NOW you gonna be seen and heard 🔥

        ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

        - Mass DM will be scheduled to avoid flood my subscriber's DM box

        - Must send at least non-censored picture (full nude), if you want to send videoclips, must be through Telegr@m: @milf_electra

        ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

        ❓ Doubts? Feel free to ask me ❓

        Just tip the TIPOMETER GAUGE here: https://fansly.com/post/732275677243383808

        And send me your best post link, caption and/or free trial link and naughty non-censored medias by DM 🔥🔥🔥'''
    ])

    # Retry logic based on Source 5 & 6
    for attempt in range(max_retries):
        if insert_random_msg_in_text_area(page, text_to_insert):
            print("Random message inserted successfully!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                time.sleep(2)
    else:
        print("Failed to insert random message after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to click the Send button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Send button...")
        if click_on_Send_btn(page):
            #print("Successfully clicked Send button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(5)  # Wait 5 seconds before retrying
    else:
        print("Failed to click Send button after all attempts.")

    time.sleep(2)
    # endregion

    # Try to click the close button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to close Mass DM confirmation window...")
        if click_to_Close_Mass_DM_Sent_Confirmation_Window(page):
            print("Successfully closed Mass DM confirmation window!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)  # Shorter wait time for closing windows
    else:
        print("Failed to close Mass DM confirmation window after all attempts.")

    time.sleep(2)

    # region Clean closure of the Playwright browser context
    try:
        browser_context.close()
        print("Browser closed successfully.")
    except Exception as e:
        print(f"Error closing browser: {e}")

    print("Script terminated. Goodbye!")
    # endregion

    # Completely exit the application
    sys.exit(0)

if __name__ == "__main__":
    main()