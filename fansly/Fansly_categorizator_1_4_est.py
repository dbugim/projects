import sys
import os
import atexit
import pyautogui
import time
import subprocess
import csv
import pandas as pd
from pathlib import Path    
from playwright.sync_api import sync_playwright

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
        #print("Navegando para página de notificações do Fansly...")
        page.goto("https://fansly.com/notifications", timeout=60000, wait_until="domcontentloaded")
        
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

def click_on_select_filters_button(page):
    """
    Attempt to find and click the 'Select Filters' button using multiple approaches.
    """
    try:
        # List of selectors based on provided parameters
        selectors = [
            # Direct CSS selector provided
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-notifications-route > div > div.current-page-wrapper > div > div > div.dropdown-title.flex-center",
            
            # Shorter CSS alternatives
            "div.dropdown-title.flex-center",
            "xd-localization-string:has-text('Select Filters')",
            
            # JavaScript path provided
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-notifications-route > div > div.current-page-wrapper > div > div > div.dropdown-title.flex-center")',
            
            # XPath provided
            "/html/body/app-root/div/div[1]/div/app-notifications-route/div/div[1]/div/div/div[1]",
            
            # Flexible XPath
            "//div[contains(@class, 'dropdown-title')][contains(., 'Select Filters')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle JavaScript path type
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
                        return True
                
                # Handle XPath type
                elif selector.startswith('/') or selector.startswith('//'):
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        page.evaluate(f'''(sel) => {{
                            const element = document.evaluate(sel, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (element) {{
                                element.style.opacity = '1';
                                element.style.visibility = 'visible';
                                element.style.display = 'block';
                            }}
                        }}''', selector)
                        xpath_elements.first.scroll_into_view_if_needed()
                        xpath_elements.first.click(force=True)
                        return True
                
                # Handle Standard CSS type
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
        
        # Fallback JavaScript approach focusing on the specific text content
        fallback_clicked = page.evaluate('''() => {
            const divs = Array.from(document.querySelectorAll('div.dropdown-title, xd-localization-string'));
            const target = divs.find(el => el.textContent.includes('Select Filters'));
            
            if (target) {
                target.scrollIntoView({behavior: 'smooth', block: 'center'});
                target.click();
                return true;
            }
            return false;
        }''')
        
        return fallback_clicked
    
    except Exception as e:
        print(f"Error in click_on_select_filters_button: {str(e)}")
        return False

def click_to_filter_followers(page):
    """
    Find and click the 'Followers' filter only if it is not already selected.
    """
    try:
        # Define the selectors for the dropdown item
        selectors = [
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-notifications-route > div > div.current-page-wrapper > div > div > div.dropdown-list > div:nth-child(5)",
            "div.dropdown-list > div:nth-child(5)",
            "div.dropdown-item:has-text('Followers')"
        ]

        # JavaScript to check if already selected and click if not
        # We check if the .checkbox div contains an <i> tag or has an 'active' class
        js_logic = '''(selector) => {
            const item = document.querySelector(selector);
            if (!item) return "not_found";
            
            // Check if it's already checked (usually by looking for the icon <i> inside the checkbox div)
            const checkbox = item.querySelector('.checkbox');
            const isChecked = checkbox && (checkbox.querySelector('i') !== null || checkbox.classList.contains('active'));
            
            if (isChecked) {
                return "already_checked";
            } else {
                item.scrollIntoView({behavior: 'smooth', block: 'center'});
                item.click();
                return "clicked";
            }
        }'''

        for selector in selectors:
            try:
                result = page.evaluate(js_logic, selector)
                if result == "already_checked":
                    # print("Followers filter is already selected. Skipping.")
                    return True
                if result == "clicked":
                    # print("Followers filter clicked successfully.")
                    return True
            except Exception:
                continue

        # Fallback: Text-based search
        fallback_result = page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll('.dropdown-item'));
            const followerItem = items.find(el => el.textContent.includes('Followers'));
            if (followerItem) {
                const checkbox = followerItem.querySelector('.checkbox');
                if (checkbox && (checkbox.querySelector('i') !== null)) return "already_checked";
                followerItem.click();
                return "clicked";
            }
            return "not_found";
        }''')

        return fallback_result in ["clicked", "already_checked"]

    except Exception as e:
        print(f"Error in click_to_filter_followers: {str(e)}")
        return False

def open_top_20_followers(page):
    try:
        print("Scrolling to ensure notifications are loaded...")
        # Initial scroll to trigger the first batch of loading
        page.mouse.wheel(0, 500)
        
        # Explicitly wait for at least one notification to appear
        try:
            page.wait_for_selector("app-follow-notification", timeout=8000)
        except Exception:
            print("No follow notifications detected on page.")
            return False

        opened_count = 0
        # Hard limit for the loop to avoid infinite processing
        for i in range(30): 
            if opened_count >= 20:
                break
                
            try:
                # Re-locate elements to prevent "stale element" errors
                profile_names = page.locator("app-follow-notification .display-name")
                
                # If we've reached the end of the current visible list, scroll for more
                if i >= profile_names.count():
                    print("Scrolling for more notifications...")
                    page.mouse.wheel(0, 1500)
                    time.sleep(2)
                    profile_names = page.locator("app-follow-notification .display-name")
                    
                    # If still no more, then we are truly at the end
                    if i >= profile_names.count():
                        print("No more visible notifications to process.")
                        break

                current_elem = profile_names.nth(i)
                
                # Make sure the element is actually in view to be clicked
                current_elem.scroll_into_view_if_needed()
                
                name = current_elem.inner_text(timeout=2000).strip()
                name_lower = name.lower()
                
                # FIXED SKIP LOGIC: 
                # Added 'in name_lower' to the "$" check so it doesn't return True every time.
                if name == "Unknown User" or "abordada" in name_lower or "abordado" in name_lower or "$" in name_lower:
                    continue
                
                print(f"[{opened_count + 1}/20] Opening {name}...")
                
                # Control + Click to open in a background tab
                current_elem.click(modifiers=["Control"])
                opened_count += 1
                
                # Small pause to allow the browser to register the new tab opening
                time.sleep(1.0) 
                
            except Exception:
                # If one element fails, skip to the next index
                continue

        print(f"Finished. Successfully opened {opened_count} tabs.")
        return True

    except Exception as e:
        print(f"Error in open_top_20_followers: {str(e)}")
        return False

def check_opened_tabs(browser_context):
    """
    Checks the current browser context and returns the number of open tabs.
    """
    # .pages is a list of all active tabs in the context
    return len(browser_context.pages)

def click_to_edit_followers_name(page):
    """
    Attempt to find and click the 'Notes/Edit Name' icon using multiple approaches.
    """
    try:
        # List of selectors provided for the notes icon
        selectors = [
            # Direct CSS selector provided
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details-2 > div > app-account-username > a > span > i",
            
            # Shorter version of the CSS selector
            "app-account-username i.notes-icon",
            "i.fa-note-sticky.pointer",
            
            # JSPath provided
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details-2 > div > app-account-username > a > span > i")',
            
            # XPath provided
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[3]/div/app-account-username/a/span/i"
        ]

        for selector in selectors:
            try:
                # Handle JavaScript Path
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
                
                # Handle XPath
                elif selector.startswith('/'):
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        xpath_elements.first.scroll_into_view_if_needed()
                        xpath_elements.first.click(force=True)
                        return True
                
                # Handle Standard CSS
                else:
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        css_elements.first.scroll_into_view_if_needed()
                        css_elements.first.click(force=True)
                        return True
                        
            except Exception:
                continue
        
        # Fallback JavaScript search by class name
        fallback_clicked = page.evaluate('''() => {
            const icon = document.querySelector('i.notes-icon') || document.querySelector('i.fa-note-sticky');
            if (icon) {
                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                icon.click();
                return true;
            }
            return false;
        }''')
        
        return fallback_clicked
    
    except Exception as e:
        print(f"Error in click_to_edit_followers_name: {str(e)}")
        return False

def change_followers_custom_name(page):
    try:
        # We scope the seal check to the profile header to avoid strict mode errors
        creators_seal_selector = ".profile-header i.fa-check.fa-stack-1x.fa-inverse"
        custom_name_input = "div.modal-content input[type='text']"
        close_modal_button = "div.modal-header i.fa-xmark"

        # Check visibility on the FIRST match found in the header
        is_creator = page.locator(creators_seal_selector).first.is_visible(timeout=3000)

        text_to_type = "Abordada" if is_creator else "Abordado"
        
        input_field = page.locator(custom_name_input).first
        if input_field.count() > 0:
            input_field.fill("") 
            input_field.type(text_to_type, delay=100)
            print(f"Typed: {text_to_type}")
        
        time.sleep(2)

        close_btn = page.locator(close_modal_button).first
        if close_btn.count() > 0:
            close_btn.click()
            return is_creator  # Return this so we can use it for the list later
        return False
    except Exception as e:
        print(f"Error in change_followers_custom_name: {str(e)}")
        return False

def put_follower_in_a_list(page, is_creator):
    """
    Adds user to a list and mutes if they are a Creator.
    Skips the entire process if the 'fa-square-check' icon is already present.
    """
    try:
        # Step 0: Fix for the 5000ms timeout error found in your logs
        # Ensure the profile header is actually loaded before looking for the menu
        page.wait_for_selector(".profile-header i.fa-ellipsis", timeout=10000)

        # 1. Click the Three Dots (Ellipsis)
        ellipsis_btn = page.locator(".profile-header i.fa-ellipsis").first
        ellipsis_btn.click(timeout=5000) 
        time.sleep(1.5)

        # 2. Click "Add To List"
        add_to_list_btn = page.locator(".profile-dropdown-item").filter(has_text="Add To List").first
        if add_to_list_btn.is_visible(timeout=5000):
            add_to_list_btn.click(force=True)
        else:
            page.locator("i.fa-list").first.click(force=True)
            
        # Wait for the List Selection Modal to appear
        page.wait_for_selector("div.modal-content", timeout=7000)
        time.sleep(1.5)

        # 3. Determine which list to check
        target_list = "Creators ⭐" if is_creator else "Non-creators ♥️"
        
        # JAVASCRIPT CHECK: Look for the specific 'fa-square-check' icon
        is_already_checked = page.evaluate('''(targetName) => {
            // Get all rows in the list modal
            const rows = Array.from(document.querySelectorAll('.modal-content .flex-row, .list-item-container'));
            const targetRow = rows.find(row => row.textContent.includes(targetName));
            
            if (targetRow) {
                // If this element exists, the list is already selected
                const checkIcon = targetRow.querySelector('i.fa-square-check');
                return checkIcon !== null;
            }
            return false;
        }''', target_list)

        if is_already_checked:
            print(f"Already inserted in {target_list}. ")
            page.keyboard.press("Escape") # Close modal
            return True # Exit method successfully without doing anything

        # 4. Click the list option if NOT checked
        list_option = page.locator("div.bold").filter(has_text=target_list).first
        if list_option.is_visible(timeout=5000):
            list_option.click(force=True)
            print(f"Selected list: {target_list}")
        else:
            print(f"Could not find list: {target_list}. Closing.")
            page.keyboard.press("Escape")
            return False
        
        time.sleep(1)

        # 5. Click Save
        save_btn = page.locator("div.btn.outline-blue").filter(has_text="Save").first
        save_btn.click(timeout=5000)
        print(f"Saved in {target_list}.")
        
        # 6. Mute Logic (Only for Creators)
        if is_creator:
            time.sleep(2)
            page.locator(".profile-header i.fa-ellipsis").first.click()
            time.sleep(1)
            page.locator(".profile-dropdown-item").filter(has_text="Mute user").first.click()
            print("User muted.")

        return True

    except Exception as e:
        print(f"Error in put_follower_in_a_list: {str(e)}")
        page.keyboard.press("Escape") # Safety close
        return False

def main():
    # 1. Close all existing Chrome instances to avoid profile conflicts
    close_all_chrome_instances()

    # 2. Launch browser with the desired profile using Playwright
    browser_context, page = open_chrome_with_profile()

    print("Browser started successfully!")
    print("IMPORTANT: Do not close this terminal window to keep Chrome running")

    # Maximize browser window
    pyautogui.press("f11")
    time.sleep(5)

    # region Try to click the Select Filters button with retries
    max_retries = 3
    for attempt in range(max_retries):
        if click_on_select_filters_button(page):
            break
        else:
            print(f"Attempt {attempt + 1} to click Select Filters failed.")
            if attempt < max_retries - 1:
                time.sleep(1) 
    else:
        print("Failed to click Select Filters button after all attempts.")

    time.sleep(3)
    # endregion

    # region Try to filter by Followers
    max_retries = 3
    for attempt in range(max_retries):
        if click_to_filter_followers(page):
            break
        else:
            print(f"Attempt {attempt + 1} to filter followers failed.")
            if attempt < max_retries - 1:
                time.sleep(1)
    else:
        print("Failed to handle Followers filter after all attempts.")

    time.sleep(1)
    # endregion
    
    # region Open top 20 notifications
    if click_to_filter_followers(page):
        print("Filter applied. Preparing to open profiles...")
        time.sleep(2) 
        open_top_20_followers(page)
    else:
        print("Could not apply Followers filter; skipping tab opening.")
    
    time.sleep(5)
    # endregion

    total_tabs = len(browser_context.pages)
    print(f"Action complete. Total tabs now open: {total_tabs}")

    # Get a list of all currently opened tabs
    all_tabs = browser_context.pages
    print(f"Starting processing for {len(all_tabs) - 2} new followers...")

    # Iterate through tabs, skipping index 0 (dashboard)
    for i in range(2, len(all_tabs)):
        current_tab = all_tabs[i]
        
        print(f"\n--- Processing Tab {i}/{len(all_tabs)-1} ---")
        
        try:
            current_tab.bring_to_front()
            time.sleep(2) # Allow profile to load fully

            # region Step 1: Click the Edit/Notes button
            edit_success = False
            for attempt in range(3):
                if click_to_edit_followers_name(current_tab):
                    edit_success = True
                    break
                else:
                    print(f"Tab {i} Attempt {attempt + 1}: Click Edit icon failed.")
                    time.sleep(1) 
            
            if not edit_success:
                print(f"Skipping Tab {i} - could not click edit button.")
                continue
            # endregion

            time.sleep(1.5)

            # region Step 2: Change Custom Name & Get Creator Status
            # We capture the is_creator status from the function return
            is_creator = change_followers_custom_name(current_tab)
            print(f"Tab {i}: Custom name updated. Creator Status: {is_creator}")
            # endregion

            time.sleep(7) # CRITICAL: Wait for the name-change modal to be COMPLETELY gone

            # 2. Put in List
            print(f"Tab {i}: Categorizing user...")
            # Add a global timeout for the whole list operation so it can't hang the script
            list_success = put_follower_in_a_list(current_tab, is_creator)
            
            if not list_success:
                print(f"Tab {i}: List categorization failed or timed out.")

            # 3. Close tab and move on
            print(f"Tab {i}: Closing...")
            current_tab.close()
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing Tab {i}: {e}")

    time.sleep(2)

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