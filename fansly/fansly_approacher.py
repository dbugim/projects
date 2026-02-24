import sys
import os
import random
import atexit
import pyautogui
import time
import csv
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
    Opens a Google Chrome instance with all profile data,
    keeping the session active indefinitely.
    """
    global playwright_instance, browser_context
    # Install Playwright if necessary
    print("Checking Playwright installation...")
    subprocess.run(["playwright", "install"], shell=True, capture_output=True)
    subprocess.run(["playwright", "install", "chromium"], shell=True, capture_output=True)
    # Chrome profile path
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data\Default"
    # Check if the profile directory exists
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile directory not found: {profile_path}")
    #print("Warning: Ensure that Chrome is completely closed")
    try:
        print("Starting Playwright...")
        # IMPORTANT: DO NOT use 'with' here to keep the session active
        playwright_instance = sync_playwright().start()
        #print("Launching Chrome with profile...")
        # Launch Chrome with specific profile
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
        #print("Browser launched successfully!")
        # Open new tab
        page = browser_context.new_page()
        print("New tab opened")
        # Navigate to the page
        #print("Navigating to Fansly hashtags explorer...")
        page.goto("https://fansly.com/explore/discover", timeout=15000)
        #print("Chrome opened successfully with all profile data!")
        #print("You can now interact with cookies, history, and saved profile data")
        return browser_context, page
    except Exception as e:
        print(f"Error opening Chrome: {e}")
        print("Troubleshooting tips:")
        print("1. Ensure that Chrome is completely closed (check in Task Manager)")
        print("2. Run this script as administrator")
        print("3. Try using a different profile path if necessary")
        # Clean up resources in case of error
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

# Global variable
current_hashtag = ""

def hashtag_picker_and_control():
    global current_hashtag

    hashtags_file = r"G:\Meu Drive\Fansly\hashtags_list.csv"
    index_file = r"G:\Meu Drive\Fansly\hashtags_use_index.csv"

    # Read the list of hashtags
    hashtags = []
    with open(hashtags_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # Assuming single column
                hashtags.append(row[0])

    if not hashtags:
        raise ValueError("Hashtags list is empty.")

    # Read the current index
    current_index = 0
    if os.path.exists(index_file):
        with open(index_file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    current_index = int(row[0])
                    break

    # Get the current hashtag
    current_hashtag = hashtags[current_index]

    # Increment the index, reset if at the end
    next_index = (current_index + 1) % len(hashtags)

    # Write the next index back to the file
    with open(index_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([next_index])

    return current_hashtag

def insert_hashtag_and_find(page, current_hashtag):
    """
    Attempt to find the search input field, insert the current_hashtag value, and simulate pressing Enter.
    Uses multiple selectors and fallbacks for reliability.
    """
    try:
        # List of selectors to try for the input field
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-explore-route > div > app-account-explore-route > div.material-input.icon-left.icon-right.margin-bottom-2 > input",
            # Alternative CSS (targeting the input directly)
            "div.material-input.icon-left.icon-right.margin-bottom-2 > input[type='text']",
            # JavaScript path
            """document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-explore-route > div > app-account-explore-route > div.material-input.icon-left.icon-right.margin-bottom-2 > input")""",
            # XPath
            "/html/body/app-root/div/div[1]/div/app-explore-route/div/app-account-explore-route/div[2]/input",
            # Alternative XPath (targeting input)
            "//div[contains(@class, 'material-input') and contains(@class, 'icon-left') and contains(@class, 'icon-right')]/input[@type='text']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying input selector: {selector}")

                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    success = page.evaluate(f'''(hashtag) => {{
                        const input = {selector};
                        if (input) {{
                            input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            input.focus();
                            input.value = hashtag;
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }}''', current_hashtag)

                    if success:
                        #print(f"Successfully inserted '{current_hashtag}' and pressed Enter with JS selector")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    input_locator = page.locator(f"xpath={selector}")
                    if input_locator.count() > 0:
                        try:
                            # Force visibility and focus
                            page.evaluate(f'''(sel, hashtag) => {{
                                const input = document.evaluate(
                                    sel, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (input) {{
                                    input.style.opacity = '1';
                                    input.style.visibility = 'visible';
                                    input.style.display = 'block';
                                    input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                    input.focus();
                                    input.value = hashtag;
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            }}''', [selector, current_hashtag])

                            # Simulate Enter key press
                            input_locator.first.press('Enter')
                            #print(f"Successfully inserted '{current_hashtag}' and pressed Enter with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath insertion failed: {str(e)}")
                else:
                    # CSS selector
                    input_locator = page.locator(selector)
                    if input_locator.count() > 0:
                        try:
                            # Force visibility and focus
                            page.evaluate(f'''(sel, hashtag) => {{
                                const input = document.querySelector(sel);
                                if (input) {{
                                    input.style.opacity = '1';
                                    input.style.visibility = 'visible';
                                    input.style.display = 'block';
                                    input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                    input.focus();
                                    input.value = hashtag;
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                }}
                            }}''', [selector, current_hashtag])

                            # Simulate Enter key press
                            input_locator.first.press('Enter')
                            #print(f"Successfully inserted '{current_hashtag}' and pressed Enter with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector insertion failed: {str(e)}")

            except Exception as e:
                print(f"Failed with selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach (inspired by dynamic input handling in sources)
        #print("Trying JavaScript fallback for input insertion...")
        fallback_success = page.evaluate(f'''(hashtag) => {{
            // Try finding input by class patterns
            const inputSelectors = [
                'input[type="text"][required]',
                '.material-input input.ng-untouched',
                'input[autocomplete="off"]'  // If applicable from similar examples
            ];
            for (const sel of inputSelectors) {{
                const input = document.querySelector(sel);
                if (input) {{
                    input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    input.focus();
                    input.value = hashtag;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                    input.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', bubbles: true }}));
                    return true;
                }}
            }}
            return false;
        }}''', current_hashtag)

        if fallback_success:
            #print(f"Successfully inserted '{current_hashtag}' and pressed Enter using JavaScript fallback!")
            return True

        print("Could not find or insert into input using any method.")
        return False

    except Exception as e:
        print(f"Error in insert_hashtag_and_find: {str(e)}")
        return False

def click_on_follower_card(page):
    """
    Attempt to find and click the follower card <div> with class 'flex-row follower'.
    Uses multiple selectors for reliability, forces visibility, scrolls into view, and clicks.
    Targets the specific card containing 'Abordada' or '@milf_' for accuracy.
    """
    try:
        # List of selectors to try for the follower card div
        selectors = [
            # Direct CSS selector for the outer div
            "div.flex-row.follower",
            # CSS with child elements for specificity (containing the username)
            "div.flex-row.follower:has(> div.flex-1 > div.flex-row > div.flex-1 > app-account-username > a[href='/milf_'])",
            # CSS targeting the link inside
            "div.flex-row.follower a.username-wrapper[href='/milf_']",
            # JavaScript path for the outer div
            """document.querySelector("div[_ngcontent-ng-c3635178294].flex-row.follower")""",
            # XPath for the outer div with class
            "//div[contains(@class, 'flex-row') and contains(@class, 'follower')]",
            # XPath with specific child (username link)
            "//div[contains(@class, 'flex-row') and contains(@class, 'follower') and .//a[@href='/milf_' and contains(@class, 'username-wrapper')]]",
            # XPath targeting the display name span
            "//div[contains(@class, 'flex-row') and contains(@class, 'follower') and .//span[contains(@class, 'display-name') and text()='Abordada']]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying follower card selector: {selector}")

                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector for click
                    success = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            element.style.opacity = '1';
                            element.style.visibility = 'visible';
                            element.style.display = 'block';
                            element.click();
                            return true;
                        }}
                        return false;
                    }}''')

                    if success:
                        #print("Successfully clicked follower card with JS selector")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    locator = page.locator(f"xpath={selector}")
                    if locator.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(sel) => {{
                                const element = document.evaluate(
                                    sel, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                }}
                            }}''', selector)

                            # Click the element
                            locator.first.click(force=True)
                            #print("Successfully clicked follower card with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                else:
                    # CSS selector
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate(f'''(sel) => {{
                                const element = document.querySelector(sel);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                }}
                            }}''', selector)

                            # Click the element
                            locator.first.click(force=True)
                            #print("Successfully clicked follower card with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach (search for similar elements on Fansly-like structure)
        #print("Trying JavaScript fallback for clicking follower card...")
        fallback_success = page.evaluate('''() => {
            const elementSelectors = [
                'div.flex-row.follower:has(a[href="/milf_"])',
                'div.flex-row.follower span.display-name:has-text("Abordada")',
                'div.flex-row.follower a.username-wrapper'
            ];
            for (const sel of elementSelectors) {
                const element = document.querySelector(sel);
                if (element) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.style.opacity = '1';
                    element.style.visibility = 'visible';
                    element.style.display = 'block';
                    element.click();
                    return true;
                }
            }
            // Broader fallback: first follower card
            const broadElement = document.querySelector('div.flex-row.follower');
            if (broadElement) {
                broadElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                broadElement.click();
                return true;
            }
            return false;
        }''')

        if fallback_success:
            #print("Successfully clicked follower card using JavaScript fallback!")
            return True

        print("Could not find or click the follower card using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_follower_card: {str(e)}")
        return False

def click_on_follow_button(page):
    """
    Attempt to find and click the 'Follow' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.follow-profile > div > span > xd-localization-string",
            # Simplified CSS selectors
            "div.follow-profile > div > span > xd-localization-string",
            "div.profile-details div.follow-profile xd-localization-string",
            "xd-localization-string",
            # Button containing the localization string
            "div.follow-profile button",
            "div.follow-profile div > span",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.follow-profile > div > span > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[6]/div/span/xd-localization-string",
            # Alternative XPaths
            "//div[@class='follow-profile']//xd-localization-string",
            "//xd-localization-string[contains(text(), 'Follow')]",
            "//div[@class='profile-details']//div[@class='follow-profile']//span"
        ]

        # Try each selector
        for selector in selectors:
            try:
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
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Follow button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        fallback_clicked = page.evaluate('''() => {
            // Try finding the Follow button by various methods
            const followSelectors = [
                'div.follow-profile xd-localization-string',
                'div.follow-profile button',
                'div.follow-profile div > span',
                'xd-localization-string'
            ];

            for (const selector of followSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent.trim().includes('Follow')) {
                        // Try to click the element or its parent button
                        const clickTarget = element.closest('button') || element.parentElement || element;
                        clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                        clickTarget.click();
                        return true;
                    }
                }
            }

            // Try by text content directly
            const allElements = document.querySelectorAll('*');
            for (const element of allElements) {
                if (element.textContent.trim() === 'Follow' && 
                    element.classList.contains('follow-profile') || 
                    element.closest('.follow-profile')) {
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.click();
                    return true;
                }
            }

            return false;
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click Follow button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_follow_button: {str(e)}")
        return False

def click_to_close_to_pay_to_follow_window(page):
    """
    Attempt to find and click the 'Close' button in the pay-to-follow modal using multiple approaches.
    Returns True if closed successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-follow-error-modal > div > div.modal-footer > div.btn.large.margin-left-2 > xd-localization-string",
            # Simplified CSS selectors
            "app-follow-error-modal div.modal-footer div.btn.large.margin-left-2 xd-localization-string",
            "div.modal-footer div.btn.large.margin-left-2 xd-localization-string",
            "div.modal-wrapper app-follow-error-modal xd-localization-string",
            "app-follow-error-modal xd-localization-string",
            # Button/div selectors
            "div.modal-footer div.btn.large.margin-left-2",
            "app-follow-error-modal div.btn.large",
            "div.modal-wrapper div.btn.large",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-follow-error-modal > div > div.modal-footer > div.btn.large.margin-left-2 > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[3]/app-follow-error-modal/div/div[3]/div[3]/xd-localization-string",
            # Alternative XPaths
            "//app-follow-error-modal//div[@class='modal-footer']//div[contains(@class, 'btn')]//xd-localization-string",
            "//div[@class='modal-wrapper']//xd-localization-string[contains(text(), 'Close')]",
            "//app-follow-error-modal//xd-localization-string[contains(text(), 'Close')]",
            "//div[@class='modal-footer']//div[contains(@class, 'btn')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
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
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Close button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach - click outside modal to close
        fallback_clicked = page.evaluate('''() => {
            // Try finding the Close button by various methods
            const closeSelectors = [
                'app-follow-error-modal xd-localization-string',
                'div.modal-footer div.btn xd-localization-string',
                'app-follow-error-modal div.btn.large',
                'div.modal-wrapper xd-localization-string'
            ];

            for (const selector of closeSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent.trim().includes('Close')) {
                        // Try to click the element or its parent button/div
                        const clickTarget = element.closest('div.btn') || element.parentElement || element;
                        clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                        clickTarget.click();
                        return true;
                    }
                }
            }

            // Alternative: Click on modal backdrop to close
            const modalWrapper = document.querySelector('div.modal-wrapper');
            if (modalWrapper) {
                modalWrapper.click();
                return true;
            }

            // Try clicking on any Close text within modal-footer
            const modalFooter = document.querySelector('div.modal-footer');
            if (modalFooter) {
                const allElements = modalFooter.querySelectorAll('*');
                for (const element of allElements) {
                    if (element.textContent.trim() === 'Close') {
                        const clickTarget = element.closest('div.btn') || element;
                        clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                        clickTarget.click();
                        return true;
                    }
                }
            }

            return false;
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click Close button in pay-to-follow modal - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_close_to_pay_to_follow_window: {str(e)} - continuing anyway.")
        return False

def click_on_creators_interactions_options(page):
    """
    Attempt to find and click the creator's interactions options (ellipsis icon) using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style > div.dropdown-title.blue-1-hover-only > i",
            # Simplified CSS selectors
            "div.transparent-dropdown.profile-more.new-style div.dropdown-title.blue-1-hover-only i",
            "div.profile-details div.transparent-dropdown i.fa-ellipsis",
            "div.dropdown-title.blue-1-hover-only i.fa-ellipsis",
            "i.fa-ellipsis",
            "i.fas.fa-ellipsis",
            # Parent element selectors
            "div.transparent-dropdown.profile-more.new-style div.dropdown-title",
            "div.dropdown-title.blue-1-hover-only",
            "div.profile-more.new-style",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style > div.dropdown-title.blue-1-hover-only > i")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[5]/div[1]/i",
            # Alternative XPaths
            "//div[@class='profile-details']//div[contains(@class, 'transparent-dropdown')]//i[@class='fas fa-ellipsis']",
            "//div[contains(@class, 'dropdown-title')]//i[@class='fas fa-ellipsis']",
            "//i[@class='fas fa-ellipsis']",
            "//div[contains(@class, 'profile-more')]//div[contains(@class, 'dropdown-title')]",
            "//app-profile-route//div[@class='profile-header']//i[@class='fas fa-ellipsis']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with additional waiting
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            // Wait for any animations
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.display = 'inline';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'inline';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with ellipsis icon selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with more aggressive clicking
        fallback_clicked = page.evaluate('''() => {
            // Wait for any animations to complete
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Try finding the ellipsis icon by various methods
                    const ellipsisSelectors = [
                        'i.fa-ellipsis',
                        'i.fas.fa-ellipsis',
                        'div.dropdown-title i',
                        'div.profile-more i',
                        'div.transparent-dropdown i'
                    ];

                    for (const selector of ellipsisSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.classList.contains('fa-ellipsis')) {
                                // Try to click the element or its parent
                                const clickTarget = element.closest('div.dropdown-title') || 
                                                  element.parentElement || 
                                                  element;
                                clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});

                                // Force click even if obscured
                                setTimeout(() => {
                                    clickTarget.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Try by class pattern matching
                    const allIcons = document.querySelectorAll('i[class*="ellipsis"]');
                    if (allIcons.length > 0) {
                        const icon = allIcons[0];
                        const clickTarget = icon.closest('div.dropdown-title') || icon;
                        clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            clickTarget.click();
                            resolve(true);
                        }, 200);
                        return;
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click creator's interactions options (ellipsis) - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_creators_interactions_options: {str(e)} - continuing anyway.")
        return False

def click_to_add_to_list(page):
    """
    Attempt to find and click the 'Add To List' option in the dropdown menu using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style.dropdown-open > div.dropdown-list > div:nth-child(1) > xd-localization-string",
            # Simplified CSS selectors
            "div.transparent-dropdown.profile-more.new-style.dropdown-open div.dropdown-list div:nth-child(1) xd-localization-string",
            "div.dropdown-list div:nth-child(1) xd-localization-string",
            "div.dropdown-open div.dropdown-list div:first-child xd-localization-string",
            "div.profile-details div.dropdown-list xd-localization-string",
            # Parent element selectors
            "div.dropdown-list div:nth-child(1)",
            "div.dropdown-list div:first-child",
            "div.transparent-dropdown.dropdown-open div.dropdown-list > div:first-child",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style.dropdown-open > div.dropdown-list > div:nth-child(1) > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[5]/div[2]/div[1]/xd-localization-string",
            # Alternative XPaths
            "//div[@class='dropdown-list']//div[1]//xd-localization-string",
            "//div[contains(@class, 'dropdown-open')]//div[@class='dropdown-list']//xd-localization-string[contains(text(), 'Add To List')]",
            "//xd-localization-string[contains(text(), 'Add To List')]",
            "//div[@class='dropdown-list']/div[1]",
            "//div[contains(@class, 'profile-more')]//div[@class='dropdown-list']//div[1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with additional waiting
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            // Wait for dropdown to be fully visible
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Add To List selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting dropdown items
        fallback_clicked = page.evaluate('''() => {
            // Wait for dropdown animations to complete
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Try finding the Add To List option by various methods
                    const addToListSelectors = [
                        'div.dropdown-list xd-localization-string',
                        'div.dropdown-list div:first-child xd-localization-string',
                        'div.dropdown-open xd-localization-string',
                        'div.profile-more xd-localization-string'
                    ];

                    for (const selector of addToListSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.trim().includes('Add To List')) {
                                // Try to click the element or its parent div
                                const clickTarget = element.closest('div.dropdown-list > div') || 
                                                  element.parentElement || 
                                                  element;
                                clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});

                                // Force click even if obscured
                                setTimeout(() => {
                                    clickTarget.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Try by nth-child pattern in dropdown-list
                    const dropdownItems = document.querySelectorAll('div.dropdown-list > div');
                    if (dropdownItems.length > 0) {
                        const firstItem = dropdownItems[0];
                        if (firstItem && firstItem.textContent.includes('Add To List')) {
                            firstItem.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                firstItem.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click 'Add To List' option in dropdown - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_add_to_list: {str(e)} - continuing anyway.")
        return False

def click_to_add_on_the_creators_list(page):
    """
    Attempt to find and click the 'Creators ⭐' list to add a creator.
    Checks if already selected and skips if so.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # First, check if the checkbox is already checked (fa-check-square instead of fa-square)
        checked_selectors = [
            "div.modal-content div.list i.fa-check-square",
            "app-list-add-account-modal i.fa-check-square",
            "div.checkbox i.fa-check-square",
            "//div[@class='checkbox']//i[contains(@class, 'fa-check-square')]"
        ]

        for selector in checked_selectors:
            try:
                if selector.startswith('/'):
                    # XPath
                    checked_elements = page.locator(f"xpath={selector}")
                else:
                    # CSS
                    checked_elements = page.locator(selector)

                if checked_elements.count() > 0:
                    # Check if it's the "Creators ⭐" list specifically
                    parent_text = page.evaluate('''() => {
                        const checkboxes = document.querySelectorAll('div.checkbox i.fa-check-square');
                        for (const checkbox of checkboxes) {
                            const listContainer = checkbox.closest('div.list');
                            if (listContainer && listContainer.textContent.includes('Creators')) {
                                return true;
                            }
                        }
                        return false;
                    }''')

                    if parent_text:
                        print("✅ This follower is already on the Creators ⭐ list! Skipping this step!")
                        return True
            except Exception as e:
                continue

        # If not already checked, proceed to click
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-add-account-modal > div > div.modal-content.margin-top-1 > div:nth-child(2)",
            # Simplified CSS selectors
            "app-list-add-account-modal div.modal-content div:nth-child(2)",
            "div.modal-content.margin-top-1 div:nth-child(2)",
            "div.modal-wrapper app-list div.list",
            "app-list div.list",
            # Target the checkbox or list container
            "div.modal-content div.list div.checkbox",
            "app-list-add-account-modal div.list",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-list-add-account-modal > div > div.modal-content.margin-top-1 > div:nth-child(2)")',
            # XPath
            "/html/body/app-root/div/div[3]/app-list-add-account-modal/div/div[2]/div[2]",
            # Alternative XPaths
            "//app-list-add-account-modal//div[@class='modal-content']//div[contains(@class, 'list')]",
            "//div[@class='modal-content']//div[contains(text(), 'Creators')]",
            "//app-list//div[@class='list']",
            "//div[@class='checkbox']//i[@class='fa-fw fal fa-square blue-1']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with text validation
                    button_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element && element.textContent.includes('Creators')) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    element.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("✅ Successfully added to Creators ⭐ list!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Creators"
                            element_text = xpath_elements.first.inner_text()
                            if "Creators" not in element_text:
                                continue

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
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("✅ Successfully added to Creators ⭐ list!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Creators"
                            element_text = css_elements.first.inner_text()
                            if "Creators" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("✅ Successfully added to Creators ⭐ list!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Creators list selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting the "Creators ⭐" list specifically
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Find all list items
                    const lists = document.querySelectorAll('div.list');

                    for (const list of lists) {
                        if (list.textContent.includes('Creators') && list.textContent.includes('⭐')) {
                            // Check if already selected
                            const checkbox = list.querySelector('i.fa-check-square');
                            if (checkbox) {
                                console.log('Already on Creators list');
                                resolve(true);
                                return;
                            }

                            // Click to add
                            list.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                list.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Alternative: look for "Creators" text in bold divs
                    const boldDivs = document.querySelectorAll('div.bold');
                    for (const div of boldDivs) {
                        if (div.textContent.trim().includes('Creators')) {
                            const listContainer = div.closest('div.list');
                            if (listContainer) {
                                listContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    listContainer.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click 'Creators ⭐' list - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_add_on_the_creators_list: {str(e)} - continuing anyway.")
        return False

def click_on_save_button_to_list_addition(page):
    """
    Attempt to find and click the 'Save' button in the list addition modal using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-list-add-account-modal > div > div.modal-footer.margin-top-2 > div > xd-localization-string",
            # Simplified CSS selectors
            "app-list-add-account-modal div.modal-footer.margin-top-2 div xd-localization-string",
            "div.modal-footer.margin-top-2 div xd-localization-string",
            "app-list-add-account-modal div.modal-footer xd-localization-string",
            "div.modal-wrapper div.modal-footer xd-localization-string",
            # Button/div selectors
            "div.modal-footer.margin-top-2 div",
            "app-list-add-account-modal div.modal-footer div",
            "div.modal-footer button",
            "div.modal-footer a",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-list-add-account-modal > div > div.modal-footer.margin-top-2 > div > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[3]/app-list-add-account-modal/div/div[3]/div/xd-localization-string",
            # Alternative XPaths
            "//app-list-add-account-modal//div[@class='modal-footer margin-top-2']//xd-localization-string",
            "//div[@class='modal-footer margin-top-2']//xd-localization-string[contains(text(), 'Save')]",
            "//xd-localization-string[contains(text(), 'Save')]",
            "//div[@class='modal-footer']//div//xd-localization-string",
            "//app-list-add-account-modal//div[contains(@class, 'modal-footer')]//div"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button && button.textContent.trim() === 'Save') {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("✅ Successfully clicked Save button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Save"
                            element_text = xpath_elements.first.inner_text()
                            if "Save" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("✅ Successfully clicked Save button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Save"
                            element_text = css_elements.first.inner_text()
                            if "Save" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("✅ Successfully clicked Save button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Save button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting Save button in modal footer
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Try finding the Save button by various methods
                    const saveSelectors = [
                        'div.modal-footer xd-localization-string',
                        'app-list-add-account-modal xd-localization-string',
                        'div.modal-footer div',
                        'div.modal-footer button'
                    ];

                    for (const selector of saveSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.trim() === 'Save') {
                                // Try to click the element or its parent
                                const clickTarget = element.closest('div.modal-footer > div') || 
                                                  element.closest('button') ||
                                                  element.parentElement || 
                                                  element;
                                clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});

                                setTimeout(() => {
                                    clickTarget.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Alternative: Find modal footer and click the button/div inside
                    const modalFooter = document.querySelector('div.modal-footer.margin-top-2');
                    if (modalFooter) {
                        const saveButton = modalFooter.querySelector('div, button, a');
                        if (saveButton && saveButton.textContent.includes('Save')) {
                            saveButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                saveButton.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully clicked Save button via fallback!")
            return True

        print("Could not find or click 'Save' button in list modal - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_save_button_to_list_addition: {str(e)} - continuing anyway.")
        return False

def click_on_mute_user_button(page):
    """
    Attempt to find and click the 'Mute user' button in the dropdown menu.
    Checks if user is already muted (shows 'Unmute user') and skips if so.
    Returns True if clicked successfully or already muted, False otherwise (but doesn't crash the program).
    """
    try:
        # First, check if the user is already muted (shows "Unmute user" instead of "Mute user")
        unmute_selectors = [
            "div.dropdown-list xd-localization-string",
            "div.transparent-dropdown.dropdown-open xd-localization-string",
            "div.profile-more xd-localization-string",
            "//div[@class='dropdown-list']//xd-localization-string[contains(text(), 'Unmute')]",
            "//xd-localization-string[contains(text(), 'Unmute user')]"
        ]

        for selector in unmute_selectors:
            try:
                if selector.startswith('/'):
                    # XPath
                    unmute_elements = page.locator(f"xpath={selector}")
                else:
                    # CSS
                    unmute_elements = page.locator(selector)

                if unmute_elements.count() > 0:
                    for i in range(unmute_elements.count()):
                        element_text = unmute_elements.nth(i).inner_text()
                        if "Unmute user" in element_text:
                            print("🔇 This creator is already muted, skipping this step!")
                            return True
            except Exception as e:
                continue

        # If not already muted, proceed to click "Mute user"
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style.dropdown-open > div.dropdown-list > div:nth-child(6) > xd-localization-string",
            # Simplified CSS selectors
            "div.transparent-dropdown.profile-more.new-style.dropdown-open div.dropdown-list div:nth-child(6) xd-localization-string",
            "div.dropdown-list div:nth-child(6) xd-localization-string",
            "div.dropdown-open div.dropdown-list div:nth-child(6) xd-localization-string",
            "div.profile-details div.dropdown-list xd-localization-string",
            # Parent element selectors
            "div.dropdown-list div:nth-child(6)",
            "div.transparent-dropdown.dropdown-open div.dropdown-list > div:nth-child(6)",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.transparent-dropdown.profile-more.new-style.dropdown-open > div.dropdown-list > div:nth-child(6) > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[5]/div[2]/div[6]/xd-localization-string",
            # Alternative XPaths
            "//div[@class='dropdown-list']//div[6]//xd-localization-string",
            "//div[contains(@class, 'dropdown-open')]//div[@class='dropdown-list']//xd-localization-string[contains(text(), 'Mute user')]",
            "//xd-localization-string[contains(text(), 'Mute user')]",
            "//div[@class='dropdown-list']/div[6]",
            "//div[contains(@class, 'profile-more')]//div[@class='dropdown-list']//div[6]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button && button.textContent.trim().includes('Mute user')) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("🔇 Successfully muted user!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Mute user"
                            element_text = xpath_elements.first.inner_text()
                            if "Mute user" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("🔇 Successfully muted user!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Mute user"
                            element_text = css_elements.first.inner_text()
                            if "Mute user" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("🔇 Successfully muted user!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Mute user selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "Mute user" in dropdown
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // First check if already muted
                    const allElements = document.querySelectorAll('div.dropdown-list xd-localization-string');
                    for (const element of allElements) {
                        if (element.textContent.trim().includes('Unmute user')) {
                            console.log('User already muted');
                            resolve(true);
                            return;
                        }
                    }

                    // Try finding the Mute user option
                    const muteSelectors = [
                        'div.dropdown-list xd-localization-string',
                        'div.dropdown-list div:nth-child(6) xd-localization-string',
                        'div.dropdown-open xd-localization-string',
                        'div.profile-more xd-localization-string'
                    ];

                    for (const selector of muteSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.trim().includes('Mute user')) {
                                // Try to click the element or its parent div
                                const clickTarget = element.closest('div.dropdown-list > div') || 
                                                  element.parentElement || 
                                                  element;
                                clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});

                                setTimeout(() => {
                                    clickTarget.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Try by nth-child(6) in dropdown-list
                    const dropdownItems = document.querySelectorAll('div.dropdown-list > div');
                    if (dropdownItems.length >= 6) {
                        const sixthItem = dropdownItems[5]; // 0-indexed
                        if (sixthItem && sixthItem.textContent.includes('Mute user')) {
                            sixthItem.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                sixthItem.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click 'Mute user' option in dropdown - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_mute_user_button: {str(e)} - continuing anyway.")
        return False

def click_on_send_DM_button(page):
    """
    Attempt to find and click the 'Send DM' button using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.dm-profile.dm-allowed.new-style > div.sm-mobile-visible.dm-button",
            # Simplified CSS selectors
            "div.dm-profile.dm-allowed.new-style div.sm-mobile-visible.dm-button",
            "div.profile-details div.dm-button",
            "div.dm-profile div.dm-button",
            "div.sm-mobile-visible.dm-button",
            "div.dm-button",
            # Icon-based selectors
            "div.dm-button i.fa-envelope",
            "i.fa-envelope",
            "i.fal.fa-envelope",
            # Parent element selectors
            "div.dm-profile.dm-allowed.new-style",
            "div.dm-profile.new-style",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details > div.dm-profile.dm-allowed.new-style > div.sm-mobile-visible.dm-button")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[3]/div[2]",
            # Alternative XPaths
            "//div[@class='profile-details']//div[contains(@class, 'dm-button')]",
            "//div[contains(@class, 'dm-profile')]//div[contains(@class, 'dm-button')]",
            "//div[contains(@class, 'dm-button')]",
            "//i[@class='fa-fw fal fa-envelope']",
            "//div[contains(@class, 'dm-profile')]//i[@class='fa-fw fal fa-envelope']",
            "//app-profile-route//div[@class='profile-header']//div[contains(@class, 'dm-button')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("📧 Successfully clicked DM button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("📧 Successfully clicked DM button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("📧 Successfully clicked DM button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with DM button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting DM button with multiple strategies
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by class combination
                    const dmButtonSelectors = [
                        'div.dm-button',
                        'div.sm-mobile-visible.dm-button',
                        'div.dm-profile div.dm-button',
                        'div[class*="dm-button"]'
                    ];

                    for (const selector of dmButtonSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            const button = elements[0];
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                button.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 2: Find by envelope icon and get parent
                    const envelopeIcons = document.querySelectorAll('i.fa-envelope');
                    if (envelopeIcons.length > 0) {
                        const dmButton = envelopeIcons[0].closest('div.dm-button') || 
                                       envelopeIcons[0].parentElement;
                        if (dmButton) {
                            dmButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                dmButton.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find dm-profile and click on the button inside
                    const dmProfile = document.querySelector('div.dm-profile');
                    if (dmProfile) {
                        const button = dmProfile.querySelector('div[class*="dm-button"]');
                        if (button) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                button.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 4: Look for elements with _ngcontent attributes containing dm-button class
                    const allDivs = document.querySelectorAll('div[class*="dm-button"]');
                    if (allDivs.length > 0) {
                        const button = allDivs[0];
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            button.click();
                            resolve(true);
                        }, 200);
                        return;
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📧 Successfully clicked DM button via fallback!")
            return True

        print("Could not find or click DM button - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_send_DM_button: {str(e)} - continuing anyway.")
        return False

def click_to_allow_send_me_DM(page):
    """
    Attempt to find and click the 'here' button to allow sending DMs using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.dark-blue-1.messaging-alert-container.flex-row.font-size-sm > div:nth-child(1) > app-button-new > div > div:nth-child(1)",
            # Simplified CSS selectors
            "app-group-message-input div.messaging-alert-container app-button-new div div:nth-child(1)",
            "div.messaging-alert-container.flex-row app-button-new div div:first-child",
            "div.messaging-alert-container app-button-new div[slot='button_content']",
            "app-messages-conversation-route app-button-new div[slot='button_content']",
            # Text-based selectors
            "div[slot='button_content'] span.pointer.blue-1",
            "span.margin-left-text.margin-right-text.pointer.blue-1.semi-bold",
            "app-button-new span.pointer.blue-1",
            # Parent element selectors
            "app-button-new div div:first-child",
            "div.messaging-alert-container app-button-new",
            "app-group-message-input app-button-new",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.dark-blue-1.messaging-alert-container.flex-row.font-size-sm > div:nth-child(1) > app-button-new > div > div:nth-child(1)")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[1]/div[1]/app-button-new/div/div[1]",
            # Alternative XPaths
            "//app-group-message-input//div[@class='dark-blue-1 messaging-alert-container flex-row font-size-sm']//app-button-new//div[@slot='button_content']",
            "//app-button-new//div[@slot='button_content']",
            "//span[@class='margin-left-text margin-right-text pointer blue-1 semi-bold' and text()='here']",
            "//div[@slot='button_content']//span[text()='here']",
            "//app-group-message-input//app-button-new//div//div[1]",
            "//app-messages-conversation-route//app-button-new",
            "//div[contains(@class, 'messaging-alert-container')]//app-button-new"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("✅ Successfully clicked 'Allow DM' button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("✅ Successfully clicked 'Allow DM' button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("✅ Successfully clicked 'Allow DM' button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Allow DM selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "here" text and slot attribute
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by slot attribute
                    const slotElements = document.querySelectorAll('div[slot="button_content"]');
                    for (const element of slotElements) {
                        if (element.textContent.includes('here')) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                element.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 2: Find by span with "here" text
                    const hereSpans = document.querySelectorAll('span.pointer.blue-1');
                    for (const span of hereSpans) {
                        if (span.textContent.trim() === 'here') {
                            const clickTarget = span.closest('div[slot="button_content"]') ||
                                              span.closest('app-button-new') ||
                                              span.parentElement ||
                                              span;
                            clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                clickTarget.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find app-button-new in messaging alert
                    const messagingAlert = document.querySelector('div.messaging-alert-container');
                    if (messagingAlert) {
                        const button = messagingAlert.querySelector('app-button-new');
                        if (button) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                button.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 4: Find all elements with _ngcontent containing slot attribute
                    const allDivs = document.querySelectorAll('div[slot*="button"]');
                    if (allDivs.length > 0) {
                        const button = allDivs[0];
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            button.click();
                            resolve(true);
                        }, 200);
                        return;
                    }

                    // Strategy 5: Text-based search for "here"
                    const allElements = document.querySelectorAll('*');
                    for (const element of allElements) {
                        if (element.textContent.trim() === 'here' && 
                            element.classList.contains('pointer') &&
                            element.classList.contains('blue-1')) {
                            const clickTarget = element.closest('app-button-new') || element;
                            clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                clickTarget.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully clicked 'Allow DM' button via fallback!")
            return True

        print("Could not find or click 'Allow DM' button - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_allow_send_me_DM: {str(e)} - continuing anyway.")
        return False

def click_yes_to_accept_receiving_DM_from_this_creator(page):
    """
    Attempt to find and click the 'Yes' button in the DM confirmation modal using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-button-new-confirmation-modal > div > div.modal-footer.margin-top-1 > div.btn.solid-blue.large",
            # Simplified CSS selectors
            "app-button-new-confirmation-modal div.modal-footer.margin-top-1 div.btn.solid-blue.large",
            "div.modal-footer.margin-top-1 div.btn.solid-blue.large",
            "app-button-new-confirmation-modal div.btn.solid-blue.large",
            "div.modal-wrapper div.btn.solid-blue.large",
            # Generic modal selectors
            "div.modal-footer div.btn.solid-blue",
            "div.btn.solid-blue.large",
            "app-button-new-confirmation-modal div.btn.solid-blue",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-button-new-confirmation-modal > div > div.modal-footer.margin-top-1 > div.btn.solid-blue.large")',
            # XPath
            "/html/body/app-root/div/div[3]/app-button-new-confirmation-modal/div/div[3]/div[2]",
            # Alternative XPaths
            "//app-button-new-confirmation-modal//div[@class='modal-footer margin-top-1']//div[@class='btn solid-blue large']",
            "//div[@class='modal-footer margin-top-1']//div[@class='btn solid-blue large']",
            "//div[@class='btn solid-blue large' and text()='Yes']",
            "//app-button-new-confirmation-modal//div[contains(@class, 'btn') and contains(@class, 'solid-blue')]",
            "//div[@class='modal-wrapper']//div[@class='btn solid-blue large']",
            "//div[contains(@class, 'modal-footer')]//div[contains(text(), 'Yes')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button && button.textContent.trim() === 'Yes') {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("✅ Successfully clicked 'Yes' to accept DM!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Yes"
                            element_text = xpath_elements.first.inner_text()
                            if "Yes" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("✅ Successfully clicked 'Yes' to accept DM!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Yes"
                            element_text = css_elements.first.inner_text()
                            if "Yes" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("✅ Successfully clicked 'Yes' to accept DM!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Yes button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "Yes" button in modal
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by class combination in modal footer
                    const yesButtonSelectors = [
                        'div.btn.solid-blue.large',
                        'app-button-new-confirmation-modal div.btn.solid-blue',
                        'div.modal-footer div.btn.solid-blue',
                        'div[class*="solid-blue"]'
                    ];

                    for (const selector of yesButtonSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.trim() === 'Yes') {
                                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    element.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find modal footer and look for Yes button
                    const modalFooter = document.querySelector('div.modal-footer.margin-top-1');
                    if (modalFooter) {
                        const yesButton = modalFooter.querySelector('div.btn.solid-blue');
                        if (yesButton && yesButton.textContent.trim() === 'Yes') {
                            yesButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                yesButton.click();
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find in confirmation modal specifically
                    const confirmationModal = document.querySelector('app-button-new-confirmation-modal');
                    if (confirmationModal) {
                        const allButtons = confirmationModal.querySelectorAll('div.btn');
                        for (const button of allButtons) {
                            if (button.textContent.trim() === 'Yes') {
                                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    button.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 4: Look for all divs with "Yes" text in modal wrapper
                    const modalWrapper = document.querySelector('div.modal-wrapper');
                    if (modalWrapper) {
                        const allDivs = modalWrapper.querySelectorAll('div');
                        for (const div of allDivs) {
                            if (div.textContent.trim() === 'Yes' && div.classList.contains('btn')) {
                                div.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    div.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully clicked 'Yes' to accept DM via fallback!")
            return True

        print("Could not find or click 'Yes' button in DM confirmation modal - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_yes_to_accept_receiving_DM_from_this_creator: {str(e)} - continuing anyway.")
        return False

def insert_text_to_be_sent(page, contact_message):
    """
    Attempt to find the message input textarea and insert the contact message using multiple approaches.
    Returns True if text inserted successfully, False otherwise (but doesn't crash the program).

    Args:
        page: Playwright page object
        contact_message: The message text to insert
    """
    try:
        # List of selectors to try for the textarea
        selectors = [
            # Direct CSS selector for textarea
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.message-input-container > textarea",
            # Simplified CSS selectors
            "div.message-input-container textarea.message-input",
            "app-group-message-input textarea.message-input",
            "app-group-message-input div.message-input-container textarea",
            "textarea.message-input.ng-untouched.ng-pristine",
            "textarea.message-input",
            "app-messages-conversation-route textarea",
            # Container selector
            "div.message-input-container",
            # JavaScript path for textarea
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.message-input-container > textarea")',
            # XPath for textarea
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/div[2]/textarea",
            # Alternative XPaths
            "//app-group-message-input//div[@class='message-input-container']//textarea",
            "//textarea[@class='message-input ng-untouched ng-pristine ng-invalid']",
            "//div[@class='message-input-container']//textarea",
            "//app-group-message-input//textarea[@class='message-input']",
            "//app-messages-conversation-route//textarea"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with text insertion
                    text_inserted = page.evaluate(f'''(message) => {{
                        const textarea = {selector};
                        if (textarea) {{
                            textarea.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            textarea.focus();
                            textarea.value = message;

                            // Trigger input events for Angular
                            textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));

                            return true;
                        }}
                        return false;
                    }}''', contact_message)

                    if text_inserted:
                        print(f"✅ Successfully inserted message text!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's a textarea
                            tag_name = xpath_elements.first.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name != "textarea":
                                continue

                            # Scroll into view and focus
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click()
                            page.wait_for_timeout(200)

                            # Fill the textarea
                            xpath_elements.first.fill(contact_message)

                            # Trigger Angular change detection
                            page.evaluate(f'''(selector) => {{
                                const textarea = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (textarea) {{
                                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print(f"✅ Successfully inserted message text!")
                            return True
                        except Exception as e:
                            print(f"XPath text insertion failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's a textarea or if we need to find textarea inside
                            tag_name = css_elements.first.evaluate("el => el.tagName.toLowerCase()")

                            if tag_name == "textarea":
                                target_element = css_elements.first
                            else:
                                # Try to find textarea inside the container
                                textarea_inside = css_elements.first.locator("textarea")
                                if textarea_inside.count() > 0:
                                    target_element = textarea_inside.first
                                else:
                                    continue

                            # Scroll into view and focus
                            target_element.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            target_element.click()
                            page.wait_for_timeout(200)

                            # Fill the textarea
                            target_element.fill(contact_message)

                            # Trigger Angular change detection
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                const textarea = element.tagName === 'TEXTAREA' ? element : element.querySelector('textarea');
                                if (textarea) {{
                                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print(f"✅ Successfully inserted message text!")
                            return True
                        except Exception as e:
                            print(f"CSS selector text insertion failed: {str(e)}")

            except Exception as e:
                print(f"Failed with message input selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with multiple strategies
        fallback_inserted = page.evaluate('''(message) => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find textarea by class
                    const textareaSelectors = [
                        'textarea.message-input',
                        'div.message-input-container textarea',
                        'app-group-message-input textarea',
                        'textarea[required]'
                    ];

                    for (const selector of textareaSelectors) {
                        const textareas = document.querySelectorAll(selector);
                        if (textareas.length > 0) {
                            const textarea = textareas[0];
                            textarea.scrollIntoView({behavior: 'smooth', block: 'center'});
                            textarea.focus();
                            textarea.value = message;

                            // Trigger events
                            textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            textarea.dispatchEvent(new Event('change', { bubbles: true }));
                            textarea.dispatchEvent(new Event('blur', { bubbles: true }));

                            resolve(true);
                            return;
                        }
                    }

                    // Strategy 2: Find by message-input-container
                    const container = document.querySelector('div.message-input-container');
                    if (container) {
                        const textarea = container.querySelector('textarea');
                        if (textarea) {
                            textarea.scrollIntoView({behavior: 'smooth', block: 'center'});
                            textarea.focus();
                            textarea.value = message;

                            textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            textarea.dispatchEvent(new Event('change', { bubbles: true }));

                            resolve(true);
                            return;
                        }
                    }

                    // Strategy 3: Find any textarea in app-group-message-input
                    const messageInput = document.querySelector('app-group-message-input');
                    if (messageInput) {
                        const textarea = messageInput.querySelector('textarea');
                        if (textarea) {
                            textarea.scrollIntoView({behavior: 'smooth', block: 'center'});
                            textarea.focus();
                            textarea.value = message;

                            textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            textarea.dispatchEvent(new Event('change', { bubbles: true }));

                            resolve(true);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''', contact_message)

        if fallback_inserted:
            print("✅ Successfully inserted message text via fallback!")
            return True

        print("❌ Can't send message to this creator, skipping this step!")
        return False

    except Exception as e:
        print(f"❌ Can't send message to this creator, skipping this step! Error: {str(e)}")
        return False

def click_to_add_media_button(page):
    """
    Attempt to find and click the 'Add Media' button (image icon) using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.collapsable-actions > div > div.input-addon.transparent-dropdown.margin-right-2 > div.dropdown-title.blue-1-hover-only",
            # Simplified CSS selectors
            "app-group-message-input div.input-addon.transparent-dropdown.margin-right-2 div.dropdown-title.blue-1-hover-only",
            "div.collapsable-actions div.input-addon.transparent-dropdown div.dropdown-title.blue-1-hover-only",
            "div.input-addon.transparent-dropdown.margin-right-2 div.dropdown-title",
            "app-group-message-input div.dropdown-title.blue-1-hover-only",
            "div.collapsable-actions div.dropdown-title.blue-1-hover-only",
            # Icon-based selectors
            "i.fal.fa-image.hover-effect",
            "i.fa-image.hover-effect",
            "i.fa-image",
            "div.dropdown-title i.fa-image",
            # Parent element selectors
            "div.input-addon.transparent-dropdown.margin-right-2",
            "div.input-addon.transparent-dropdown",
            "div.collapsable-actions div.input-addon",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.collapsable-actions > div > div.input-addon.transparent-dropdown.margin-right-2 > div.dropdown-title.blue-1-hover-only")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/div[1]/div/div[1]/div[1]",
            # Alternative XPaths
            "//app-group-message-input//div[@class='collapsable-actions']//div[@class='input-addon transparent-dropdown margin-right-2']//div[@class='dropdown-title blue-1-hover-only']",
            "//div[@class='dropdown-title blue-1-hover-only']//i[@class='fal fa-image hover-effect']",
            "//i[@class='fal fa-image hover-effect']",
            "//div[@class='collapsable-actions']//div[@class='dropdown-title blue-1-hover-only']",
            "//app-group-message-input//i[@class='fal fa-image hover-effect']",
            "//div[@class='input-addon transparent-dropdown margin-right-2']//div[@class='dropdown-title blue-1-hover-only']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with click event
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    // Dispatch click event for Angular
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("📷 Successfully clicked Add Media button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📷 Successfully clicked Add Media button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📷 Successfully clicked Add Media button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Add Media button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting image icon and dropdown
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by fa-image icon
                    const imageIcons = document.querySelectorAll('i.fa-image');
                    if (imageIcons.length > 0) {
                        for (const icon of imageIcons) {
                            // Get parent dropdown-title
                            const dropdownTitle = icon.closest('div.dropdown-title');
                            if (dropdownTitle) {
                                dropdownTitle.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    dropdownTitle.click();
                                    dropdownTitle.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find by dropdown-title in collapsable-actions
                    const collapsableActions = document.querySelector('div.collapsable-actions');
                    if (collapsableActions) {
                        const dropdownTitle = collapsableActions.querySelector('div.dropdown-title.blue-1-hover-only');
                        if (dropdownTitle) {
                            dropdownTitle.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                dropdownTitle.click();
                                dropdownTitle.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find by input-addon transparent-dropdown
                    const inputAddons = document.querySelectorAll('div.input-addon.transparent-dropdown');
                    for (const addon of inputAddons) {
                        const imageIcon = addon.querySelector('i.fa-image');
                        if (imageIcon) {
                            const dropdownTitle = addon.querySelector('div.dropdown-title');
                            if (dropdownTitle) {
                                dropdownTitle.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    dropdownTitle.click();
                                    dropdownTitle.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 4: Find all elements with _ngcontent containing fa-image
                    const allIcons = document.querySelectorAll('i[class*="fa-image"]');
                    if (allIcons.length > 0) {
                        const parentDiv = allIcons[0].closest('div.dropdown-title') || allIcons[0].parentElement;
                        if (parentDiv) {
                            parentDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                parentDiv.click();
                                parentDiv.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📷 Successfully clicked Add Media button via fallback!")
            return True

        print("Could not find or click Add Media button - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_add_media_button: {str(e)} - continuing anyway.")
        return False

def click_to_add_from_vault(page):
    """
    Attempt to find and click the 'From Vault' option in the dropdown menu using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.collapsable-actions > div > div.input-addon.transparent-dropdown.margin-right-2.dropdown-open > div.dropdown-list.top.left > div:nth-child(2) > xd-localization-string",
            # Simplified CSS selectors
            "div.input-addon.transparent-dropdown.margin-right-2.dropdown-open div.dropdown-list.top.left div:nth-child(2) xd-localization-string",
            "div.dropdown-list.top.left div:nth-child(2) xd-localization-string",
            "div.dropdown-open div.dropdown-list div:nth-child(2) xd-localization-string",
            "app-group-message-input div.dropdown-list xd-localization-string",
            "div.collapsable-actions div.dropdown-list xd-localization-string",
            # Parent element selectors
            "div.dropdown-list.top.left div:nth-child(2)",
            "div.dropdown-list div:nth-child(2)",
            "div.input-addon.dropdown-open div.dropdown-list > div:nth-child(2)",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > div.collapsable-actions > div > div.input-addon.transparent-dropdown.margin-right-2.dropdown-open > div.dropdown-list.top.left > div:nth-child(2) > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/div[1]/div/div[1]/div[2]/div[2]/xd-localization-string",
            # Alternative XPaths
            "//div[@class='dropdown-list top left']//div[2]//xd-localization-string",
            "//div[contains(@class, 'dropdown-open')]//div[@class='dropdown-list top left']//xd-localization-string[contains(text(), 'From Vault')]",
            "//xd-localization-string[contains(text(), 'From Vault')]",
            "//div[@class='dropdown-list top left']/div[2]",
            "//app-group-message-input//div[@class='dropdown-list']//div[2]",
            "//div[contains(@class, 'input-addon')]//div[@class='dropdown-list']//div[2]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button && button.textContent.trim().includes('From Vault')) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("🗄️ Successfully clicked 'From Vault' option!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "From Vault"
                            element_text = xpath_elements.first.inner_text()
                            if "From Vault" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)
                            print("🗄️ Successfully clicked 'From Vault' option!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for dropdown to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "From Vault"
                            element_text = css_elements.first.inner_text()
                            if "From Vault" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)
                            print("🗄️ Successfully clicked 'From Vault' option!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with From Vault selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "From Vault" in dropdown
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by text content in dropdown list
                    const fromVaultSelectors = [
                        'div.dropdown-list xd-localization-string',
                        'div.dropdown-list div:nth-child(2) xd-localization-string',
                        'div.dropdown-open xd-localization-string',
                        'div.input-addon xd-localization-string'
                    ];

                    for (const selector of fromVaultSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.trim().includes('From Vault')) {
                                // Try to click the element or its parent div
                                const clickTarget = element.closest('div.dropdown-list > div') || 
                                                  element.parentElement || 
                                                  element;
                                clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});

                                setTimeout(() => {
                                    clickTarget.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find second child in dropdown-list
                    const dropdownLists = document.querySelectorAll('div.dropdown-list');
                    for (const list of dropdownLists) {
                        const items = list.querySelectorAll(':scope > div');
                        if (items.length >= 2) {
                            const secondItem = items[1]; // 0-indexed, so [1] is 2nd child
                            if (secondItem && secondItem.textContent.includes('From Vault')) {
                                secondItem.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    secondItem.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 3: Find in open dropdown specifically
                    const openDropdown = document.querySelector('div.dropdown-open div.dropdown-list');
                    if (openDropdown) {
                        const allItems = openDropdown.querySelectorAll('div');
                        for (const item of allItems) {
                            if (item.textContent.trim().includes('From Vault')) {
                                item.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    item.click();
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("🗄️ Successfully clicked 'From Vault' option via fallback!")
            return True

        print("Could not find or click 'From Vault' option in dropdown - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_add_from_vault: {str(e)} - continuing anyway.")
        return False

def insert_text_to_find_specific_album(page, search_text):
    """
    Attempt to find the album search input and insert search text using multiple approaches.
    Triggers proper Angular events to ensure the search executes.
    Returns True if text inserted successfully, False otherwise (but doesn't crash the program).

    Args:
        page: Playwright page object
        search_text: The text to search for (e.g., "SFS")
    """
    try:
        # List of selectors to try for the input
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.album-search-container.flex-row.flex-0.material-input.icon-left.icon-right.margin-top-1 > input",
            # Simplified CSS selectors
            "app-media-vault-picker-modal div.album-search-container input",
            "div.album-search-container.flex-row input",
            "app-media-vault div.album-search-container input",
            "div.album-search-container input[type='text']",
            "app-media-vault input[type='text']",
            "div.modal-content app-media-vault input",
            # Class-based selectors
            "input.ng-untouched.ng-dirty.ng-invalid",
            "div.material-input input",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.album-search-container.flex-row.flex-0.material-input.icon-left.icon-right.margin-top-1 > input")',
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div/div[2]/input",
            # Alternative XPaths
            "//app-media-vault-picker-modal//div[@class='album-search-container flex-row flex-0 material-input icon-left icon-right margin-top-1']//input",
            "//app-media-vault//div[contains(@class, 'album-search-container')]//input",
            "//div[contains(@class, 'album-search-container')]//input[@type='text']",
            "//app-media-vault//input[@type='text']",
            "//app-media-vault-picker-modal//input[@type='text']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with text insertion and event triggering
                    text_inserted = page.evaluate(f'''(searchText) => {{
                        const input = {selector};
                        if (input) {{
                            input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            input.focus();

                            // Clear any existing value
                            input.value = '';

                            // Set the new value
                            input.value = searchText;

                            // Trigger all necessary events for Angular
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('blur', {{ bubbles: true }}));

                            return true;
                        }}
                        return false;
                    }}''', search_text)

                    if text_inserted:
                        print(f"🔍 Successfully inserted search text: '{search_text}'")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's an input element
                            tag_name = xpath_elements.first.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name != "input":
                                continue

                            # Scroll into view and focus
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click()
                            page.wait_for_timeout(200)

                            # Clear and fill the input
                            xpath_elements.first.fill("")
                            page.wait_for_timeout(100)
                            xpath_elements.first.fill(search_text)

                            # Trigger Angular events
                            page.evaluate(f'''(selector) => {{
                                const input = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (input) {{
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            # Press Enter to trigger search
                            xpath_elements.first.press("Enter")

                            print(f"🔍 Successfully inserted search text: '{search_text}'")
                            return True
                        except Exception as e:
                            print(f"XPath text insertion failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's an input element
                            tag_name = css_elements.first.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name != "input":
                                continue

                            # Scroll into view and focus
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click()
                            page.wait_for_timeout(200)

                            # Clear and fill the input
                            css_elements.first.fill("")
                            page.wait_for_timeout(100)
                            css_elements.first.fill(search_text)

                            # Trigger Angular events
                            page.evaluate(f'''(selector) => {{
                                const input = document.querySelector(selector);
                                if (input) {{
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            # Press Enter to trigger search
                            css_elements.first.press("Enter")

                            print(f"🔍 Successfully inserted search text: '{search_text}'")
                            return True
                        except Exception as e:
                            print(f"CSS selector text insertion failed: {str(e)}")

            except Exception as e:
                print(f"Failed with album search input selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with character-by-character typing
        fallback_inserted = page.evaluate('''(searchText) => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by album-search-container
                    const searchContainer = document.querySelector('div.album-search-container');
                    if (searchContainer) {
                        const input = searchContainer.querySelector('input');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = '';

                            // Type character by character to trigger events
                            let index = 0;
                            const typeChar = () => {
                                if (index < searchText.length) {
                                    input.value += searchText[index];
                                    input.dispatchEvent(new Event('input', { bubbles: true }));
                                    index++;
                                    setTimeout(typeChar, 50);
                                } else {
                                    input.dispatchEvent(new Event('change', { bubbles: true }));
                                    input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                                    resolve(true);
                                }
                            };
                            typeChar();
                            return;
                        }
                    }

                    // Strategy 2: Find by app-media-vault
                    const mediaVault = document.querySelector('app-media-vault');
                    if (mediaVault) {
                        const input = mediaVault.querySelector('input[type="text"]');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = searchText;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }));
                            resolve(true);
                            return;
                        }
                    }

                    // Strategy 3: Find any input in modal with vault picker
                    const vaultModal = document.querySelector('app-media-vault-picker-modal');
                    if (vaultModal) {
                        const input = vaultModal.querySelector('input[type="text"]');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = searchText;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            resolve(true);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''', search_text)

        if fallback_inserted:
            print(f"🔍 Successfully inserted search text via fallback: '{search_text}'")
            return True

        print(f"Could not insert search text '{search_text}' in album search - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in insert_text_to_find_specific_album: {str(e)} - continuing anyway.")
        return False

def click_to_select_sfs_video(page):
    """
    Attempt to find and click the 'SFS Instructions' album/video in the vault using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.vault-albums.margin-top-1 > div:nth-child(1) > div.vault-album-footer.margin-top-text.margin-bottom-text.xd-drag-ignore > div.semi-bold",
            # Simplified CSS selectors
            "app-media-vault-picker-modal div.vault-albums.margin-top-1 div:nth-child(1) div.vault-album-footer div.semi-bold",
            "div.vault-albums.margin-top-1 div:nth-child(1) div.semi-bold",
            "app-media-vault div.vault-albums div:first-child div.semi-bold",
            "div.vault-album-footer div.semi-bold",
            "app-media-vault div.semi-bold",
            # Parent selectors
            "div.vault-albums.margin-top-1 > div:nth-child(1) > div.vault-album-footer",
            "div.vault-albums.margin-top-1 > div:first-child",
            "div.vault-album-footer.margin-top-text.margin-bottom-text",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div > div.vault-albums.margin-top-1 > div:nth-child(1) > div.vault-album-footer.margin-top-text.margin-bottom-text.xd-drag-ignore > div.semi-bold")',
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div/div[3]/div[1]/div[2]/div[1]",
            # Alternative XPaths
            "//app-media-vault//div[@class='vault-albums margin-top-1']//div[1]//div[@class='semi-bold']",
            "//div[@class='vault-album-footer margin-top-text margin-bottom-text xd-drag-ignore']//div[@class='semi-bold']",
            "//div[@class='semi-bold' and contains(text(), 'SFS Instructions')]",
            "//div[contains(text(), '📜 SFS Instructions')]",
            "//app-media-vault//div[@class='vault-albums margin-top-1']/div[1]",
            "//div[@class='vault-albums margin-top-1']//div[@class='vault-album-footer']//div[@class='semi-bold']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    element_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element && element.textContent.trim().includes('SFS Instructions')) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    // Try clicking the element or its parent container
                                    const clickTarget = element.closest('div.vault-album-footer') || 
                                                      element.closest('div[class*="vault-albums"] > div') ||
                                                      element;
                                    clickTarget.click();
                                    clickTarget.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if element_clicked:
                        print("📜 Successfully selected 'SFS Instructions' album!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for vault to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "SFS Instructions"
                            element_text = xpath_elements.first.inner_text()
                            if "SFS Instructions" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📜 Successfully selected 'SFS Instructions' album!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for vault to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "SFS Instructions"
                            element_text = css_elements.first.inner_text()
                            if "SFS Instructions" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📜 Successfully selected 'SFS Instructions' album!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with SFS Instructions selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting SFS Instructions text
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by text content containing "SFS Instructions"
                    const sfsSelectors = [
                        'div.semi-bold',
                        'div.vault-album-footer div.semi-bold',
                        'div.vault-albums div.semi-bold'
                    ];

                    for (const selector of sfsSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.includes('SFS Instructions')) {
                                // Click on the parent album container
                                const albumContainer = element.closest('div.vault-albums > div') ||
                                                     element.closest('div.vault-album-footer')?.parentElement ||
                                                     element.parentElement;
                                if (albumContainer) {
                                    albumContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    setTimeout(() => {
                                        albumContainer.click();
                                        albumContainer.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                        resolve(true);
                                    }, 200);
                                    return;
                                }
                            }
                        }
                    }

                    // Strategy 2: Find first album in vault-albums
                    const vaultAlbums = document.querySelector('div.vault-albums');
                    if (vaultAlbums) {
                        const firstAlbum = vaultAlbums.querySelector('div:first-child');
                        if (firstAlbum && firstAlbum.textContent.includes('SFS')) {
                            firstAlbum.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                firstAlbum.click();
                                firstAlbum.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find by emoji and text
                    const allDivs = document.querySelectorAll('div');
                    for (const div of allDivs) {
                        if (div.textContent.includes('📜') && div.textContent.includes('SFS')) {
                            const albumContainer = div.closest('div.vault-albums > div') || div;
                            albumContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                albumContainer.click();
                                albumContainer.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📜 Successfully selected 'SFS Instructions' album via fallback!")
            return True

        print("Could not find or select 'SFS Instructions' album - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_select_sfs_video: {str(e)} - continuing anyway.")
        return False

def click_to_select_media(page):
    """
    Attempt to find and click the media selection circle icon in the vault using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div.vault-row > div.render-container > div.image-controls > div > i",
            # Simplified CSS selectors
            "app-media-vault-picker-modal div.vault-wrapper.margin-top-2 div.image-controls div i",
            "app-media-vault div.vault-wrapper div.image-controls i.fa-circle",
            "div.image-controls div i.fa-circle",
            "div.render-container div.image-controls i",
            "div.vault-row div.image-controls i",
            # Icon-based selectors
            "i.fa-circle",
            "i.fal.fa-circle",
            "i.fa-fw.fal.fa-circle",
            # Parent element selectors
            "div.image-controls > div",
            "div.image-controls",
            "div.render-container div.image-controls",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-content > app-media-vault > div.vault-wrapper.margin-top-2 > div > div.vault-row > div.render-container > div.image-controls > div > i")',
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[4]/div/div[2]/div[2]/div[3]/div/i",
            # Alternative XPaths
            "//app-media-vault//div[@class='vault-wrapper margin-top-2']//div[@class='image-controls']//i[@class='fa-fw fal fa-circle']",
            "//div[@class='image-controls']//i[@class='fa-fw fal fa-circle']",
            "//div[@class='render-container']//div[@class='image-controls']//i",
            "//i[@class='fa-fw fal fa-circle']",
            "//div[@class='vault-row']//div[@class='image-controls']//i",
            "//app-media-vault//i[contains(@class, 'fa-circle')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with click event
                    element_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element) {{
                            element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    // Try clicking the element or its parent
                                    const clickTarget = element.closest('div.image-controls') || 
                                                      element.parentElement || 
                                                      element;
                                    clickTarget.click();
                                    clickTarget.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if element_clicked:
                        print("✅ Successfully selected media item!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for vault to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.display = 'inline-block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully selected media item!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for vault to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'inline-block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully selected media item!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with media selection selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting fa-circle icon in image-controls
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by fa-circle icon class
                    const circleIcons = document.querySelectorAll('i.fa-circle');
                    if (circleIcons.length > 0) {
                        for (const icon of circleIcons) {
                            // Check if it's within image-controls
                            const imageControls = icon.closest('div.image-controls');
                            if (imageControls) {
                                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    icon.click();
                                    icon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find image-controls and click on it
                    const imageControls = document.querySelector('div.image-controls');
                    if (imageControls) {
                        const selectIcon = imageControls.querySelector('i') || 
                                         imageControls.querySelector('div > i');
                        if (selectIcon) {
                            selectIcon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                selectIcon.click();
                                selectIcon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find in vault-wrapper by render-container
                    const vaultWrapper = document.querySelector('div.vault-wrapper');
                    if (vaultWrapper) {
                        const renderContainer = vaultWrapper.querySelector('div.render-container');
                        if (renderContainer) {
                            const controls = renderContainer.querySelector('div.image-controls');
                            if (controls) {
                                const icon = controls.querySelector('i');
                                if (icon) {
                                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    setTimeout(() => {
                                        icon.click();
                                        icon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                        resolve(true);
                                    }, 200);
                                    return;
                                }
                            }
                        }
                    }

                    // Strategy 4: Click on first fa-circle found anywhere in vault modal
                    const allCircles = document.querySelectorAll('i[class*="fa-circle"]');
                    if (allCircles.length > 0) {
                        const firstCircle = allCircles[0];
                        firstCircle.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            firstCircle.click();
                            firstCircle.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 200);
                        return;
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully selected media item via fallback!")
            return True

        print("Could not find or select media item - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_select_media: {str(e)} - continuing anyway.")
        return False

def click_to_add_selected_media(page):
    """
    Attempt to find and click the 'Add' button in the media vault picker modal using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-footer.flex-col > div.btn.large.solid-blue",
            # Simplified CSS selectors
            "app-media-vault-picker-modal div.modal-footer.flex-col div.btn.large.solid-blue",
            "div.modal-footer.flex-col div.btn.large.solid-blue",
            "app-media-vault-picker-modal div.btn.large.solid-blue",
            "div.modal-wrapper div.btn.large.solid-blue",
            # Generic modal selectors
            "div.modal-footer div.btn.solid-blue",
            "div.btn.solid-blue.large",
            "app-media-vault-picker-modal div.btn.solid-blue",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-media-vault-picker-modal > div > div.modal-footer.flex-col > div.btn.large.solid-blue")',
            # XPath
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[3]/div[2]",
            # Alternative XPaths
            "//app-media-vault-picker-modal//div[@class='modal-footer flex-col']//div[@class='btn large solid-blue']",
            "//div[@class='modal-footer flex-col']//div[@class='btn large solid-blue']",
            "//div[@class='btn large solid-blue']//xd-localization-string[contains(text(), 'Add')]",
            "//app-media-vault-picker-modal//div[contains(@class, 'btn') and contains(@class, 'solid-blue')]",
            "//div[@class='modal-wrapper']//div[@class='btn large solid-blue']",
            "//div[contains(@class, 'modal-footer')]//div[contains(text(), 'Add')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button && button.textContent.includes('Add')) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("✅ Successfully clicked 'Add' button to add selected media!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Add"
                            element_text = xpath_elements.first.inner_text()
                            if "Add" not in element_text:
                                continue

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully clicked 'Add' button to add selected media!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Add"
                            element_text = css_elements.first.inner_text()
                            if "Add" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully clicked 'Add' button to add selected media!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Add button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "Add" button in modal footer
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by class combination in modal footer
                    const addButtonSelectors = [
                        'div.btn.solid-blue.large',
                        'app-media-vault-picker-modal div.btn.solid-blue',
                        'div.modal-footer div.btn.solid-blue',
                        'div[class*="solid-blue"]'
                    ];

                    for (const selector of addButtonSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            if (element && element.textContent.includes('Add')) {
                                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    element.click();
                                    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find modal footer and look for Add button
                    const modalFooter = document.querySelector('div.modal-footer.flex-col');
                    if (modalFooter) {
                        const addButton = modalFooter.querySelector('div.btn.solid-blue');
                        if (addButton && addButton.textContent.includes('Add')) {
                            addButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                addButton.click();
                                addButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find in vault picker modal specifically
                    const vaultModal = document.querySelector('app-media-vault-picker-modal');
                    if (vaultModal) {
                        const allButtons = vaultModal.querySelectorAll('div.btn');
                        for (const button of allButtons) {
                            if (button.textContent.includes('Add') && 
                                button.textContent.includes('Images')) {
                                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 4: Look for xd-localization-string with "Add" text
                    const locStrings = document.querySelectorAll('xd-localization-string');
                    for (const loc of locStrings) {
                        if (loc.textContent.trim() === 'Add') {
                            const buttonDiv = loc.closest('div.btn');
                            if (buttonDiv) {
                                buttonDiv.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    buttonDiv.click();
                                    buttonDiv.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully clicked 'Add' button via fallback!")
            return True

        print("Could not find or click 'Add' button in media vault picker - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_add_selected_media: {str(e)} - continuing anyway.")
        return False

def click_to_uncheck_require_subscription(page):
    """
    Attempt to find and uncheck the 'Require Subscription' checkbox if it's selected.
    Checks if already unchecked and skips if so.
    Returns True if unchecked successfully or already unchecked, False otherwise (but doesn't crash the program).
    """
    try:
        # First, check if the checkbox is already unchecked (fa-square instead of fa-check)
        unchecked_selectors = [
            "app-account-media-permission-flags-editor div.checkbox:not(.selected)",
            "div.permission-settings-container div.checkbox i.fa-square",
            "app-xd-checkbox div.checkbox i.fa-square",
            "//div[@class='checkbox']//i[contains(@class, 'fa-square')]",
            "//app-xd-checkbox//div[@class='checkbox']"
        ]

        for selector in unchecked_selectors:
            try:
                if selector.startswith('/'):
                    # XPath
                    unchecked_elements = page.locator(f"xpath={selector}")
                else:
                    # CSS
                    unchecked_elements = page.locator(selector)

                if unchecked_elements.count() > 0:
                    # Check if it's specifically the subscription checkbox (3rd child)
                    parent_text = page.evaluate('''() => {
                        const checkboxes = document.querySelectorAll('div.permission-settings-container > div');
                        if (checkboxes.length >= 3) {
                            const thirdCheckbox = checkboxes[2]; // 0-indexed
                            const checkbox = thirdCheckbox.querySelector('div.checkbox');
                            if (checkbox && !checkbox.classList.contains('selected')) {
                                return true;
                            }
                        }
                        return false;
                    }''')

                    if parent_text:
                        print("✅ 'Require Subscription' checkbox is already unchecked, skipping this step!")
                        return True
            except Exception as e:
                continue

        # If checkbox is selected (checked), proceed to uncheck it
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.permission-settings-container > div:nth-child(3) > app-xd-checkbox > div",
            # Simplified CSS selectors
            "app-account-media-permission-flags-editor div.permission-settings-container div:nth-child(3) app-xd-checkbox div",
            "div.permission-settings-container div:nth-child(3) app-xd-checkbox div.checkbox.selected",
            "app-account-media-permission-flags-editor div:nth-child(3) div.checkbox.selected",
            "div.permission-settings-container > div:nth-child(3) div.checkbox",
            "app-xd-checkbox div.checkbox.selected",
            # Icon-based selectors
            "div.checkbox.selected i.fa-check",
            "app-xd-checkbox div.checkbox i.fa-check",
            "div.permission-settings-container div.checkbox.selected",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.permission-settings-container > div:nth-child(3) > app-xd-checkbox > div")',
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[2]/div[3]/app-xd-checkbox/div",
            # Alternative XPaths
            "//app-account-media-permission-flags-editor//div[@class='permission-settings-container']//div[3]//app-xd-checkbox//div[@class='checkbox selected']",
            "//div[@class='permission-settings-container']/div[3]//div[@class='checkbox selected']",
            "//app-xd-checkbox//div[@class='checkbox selected']",
            "//div[@class='checkbox selected']//i[@class='fa-fw fas fa-check blue-1']",
            "//div[@class='permission-settings-container']//div[3]//app-xd-checkbox//div"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    checkbox_clicked = page.evaluate(f'''() => {{
                        const checkbox = {selector};
                        if (checkbox && checkbox.classList.contains('selected')) {{
                            checkbox.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    checkbox.click();
                                    checkbox.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if checkbox_clicked:
                        print("✅ Successfully unchecked 'Require Subscription' checkbox!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's selected
                            is_selected = xpath_elements.first.evaluate('''el => {
                                return el.classList.contains('selected') || 
                                       el.querySelector('i.fa-check') !== null;
                            }''')

                            if not is_selected:
                                continue

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
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully unchecked 'Require Subscription' checkbox!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's selected
                            is_selected = css_elements.first.evaluate('''el => {
                                return el.classList.contains('selected') || 
                                       el.querySelector('i.fa-check') !== null;
                            }''')

                            if not is_selected:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'flex';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("✅ Successfully unchecked 'Require Subscription' checkbox!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with checkbox selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting the 3rd checkbox in permission settings
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by nth-child(3) in permission-settings-container
                    const permissionSettings = document.querySelector('div.permission-settings-container');
                    if (permissionSettings) {
                        const children = permissionSettings.querySelectorAll(':scope > div');
                        if (children.length >= 3) {
                            const thirdChild = children[2]; // 0-indexed
                            const checkbox = thirdChild.querySelector('div.checkbox');
                            if (checkbox && checkbox.classList.contains('selected')) {
                                checkbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    checkbox.click();
                                    checkbox.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            } else if (checkbox && !checkbox.classList.contains('selected')) {
                                console.log('Checkbox already unchecked');
                                resolve(true);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find all selected checkboxes and click the 3rd one
                    const selectedCheckboxes = document.querySelectorAll('div.checkbox.selected');
                    if (selectedCheckboxes.length >= 3) {
                        const checkbox = selectedCheckboxes[2];
                        checkbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            checkbox.click();
                            checkbox.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 200);
                        return;
                    }

                    // Strategy 3: Find by app-xd-checkbox with selected class
                    const xdCheckboxes = document.querySelectorAll('app-xd-checkbox');
                    for (const xdCheckbox of xdCheckboxes) {
                        const checkbox = xdCheckbox.querySelector('div.checkbox.selected');
                        if (checkbox) {
                            // Check if it's in the 3rd position
                            const parent = xdCheckbox.parentElement;
                            const siblings = Array.from(parent.parentElement.children);
                            const index = siblings.indexOf(parent);
                            if (index === 2) { // 0-indexed, so 2 is 3rd
                                checkbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    checkbox.click();
                                    checkbox.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("✅ Successfully unchecked 'Require Subscription' checkbox via fallback!")
            return True

        print("Could not find or uncheck 'Require Subscription' checkbox - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_uncheck_require_subscription: {str(e)} - continuing anyway.")
        return False

def click_on_upload_button(page):
    """
    Attempt to find and click the 'Upload' button in the media upload modal using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-footer.flex-col > div:nth-child(3) > div.btn.solid-blue.large > xd-localization-string",
            # Simplified CSS selectors
            "app-account-media-upload div.modal-footer.flex-col div:nth-child(3) div.btn.solid-blue.large xd-localization-string",
            "div.modal-footer.flex-col div:nth-child(3) div.btn.solid-blue.large",
            "app-account-media-upload div.btn.solid-blue.large xd-localization-string",
            "div.modal-wrapper div.btn.solid-blue.large",
            # Parent button selectors
            "div.modal-footer div:nth-child(3) div.btn.solid-blue",
            "div.btn.solid-blue.large",
            "app-account-media-upload div.btn.solid-blue",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-footer.flex-col > div:nth-child(3) > div.btn.solid-blue.large > xd-localization-string")',
            # XPath
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[3]/div[2]/div[3]/xd-localization-string",
            # Alternative XPaths
            "//app-account-media-upload//div[@class='modal-footer flex-col']//div[3]//div[@class='btn solid-blue large']//xd-localization-string",
            "//div[@class='modal-footer flex-col']//div[3]//div[@class='btn solid-blue large']",
            "//div[@class='btn solid-blue large']//xd-localization-string[contains(text(), 'Upload')]",
            "//app-account-media-upload//div[contains(@class, 'btn') and contains(@class, 'solid-blue')]",
            "//xd-localization-string[text()='Upload']",
            "//div[contains(@class, 'modal-footer')]//div[contains(text(), 'Upload')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with validation
                    button_clicked = page.evaluate(f'''() => {{
                        const element = {selector};
                        if (element && element.textContent.trim() === 'Upload') {{
                            // Find the parent button
                            const button = element.closest('div.btn') || element.parentElement;
                            if (button) {{
                                button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                return new Promise(resolve => {{
                                    setTimeout(() => {{
                                        button.click();
                                        button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                        resolve(true);
                                    }}, 300);
                                }});
                            }}
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("📤 Successfully clicked 'Upload' button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Upload"
                            element_text = xpath_elements.first.inner_text()
                            if "Upload" not in element_text:
                                continue

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
                                    const button = element.closest('div.btn') || element.parentElement;
                                    if (button) {{
                                        button.style.opacity = '1';
                                        button.style.visibility = 'visible';
                                        button.style.display = 'flex';
                                        button.style.pointerEvents = 'auto';
                                    }}
                                }}
                            }}''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const button = element.closest('div.btn') || element;
                                    button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📤 Successfully clicked 'Upload' button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for modal to be stable
                            page.wait_for_timeout(500)

                            # Verify it contains "Upload"
                            element_text = css_elements.first.inner_text()
                            if "Upload" not in element_text:
                                continue

                            # Force visibility
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const button = element.closest ? (element.closest('div.btn') || element) : element;
                                    button.style.opacity = '1';
                                    button.style.visibility = 'visible';
                                    button.style.display = 'flex';
                                    button.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const button = element.closest ? (element.closest('div.btn') || element) : element;
                                    button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📤 Successfully clicked 'Upload' button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Upload button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting "Upload" button
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by xd-localization-string with "Upload" text
                    const locStrings = document.querySelectorAll('xd-localization-string');
                    for (const loc of locStrings) {
                        if (loc.textContent.trim() === 'Upload') {
                            const button = loc.closest('div.btn');
                            if (button) {
                                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find modal footer and look for Upload button
                    const modalFooter = document.querySelector('app-account-media-upload div.modal-footer');
                    if (modalFooter) {
                        const buttons = modalFooter.querySelectorAll('div.btn.solid-blue');
                        for (const button of buttons) {
                            if (button.textContent.includes('Upload')) {
                                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 3: Find 3rd child in modal footer
                    const modalFooterChildren = document.querySelectorAll('div.modal-footer.flex-col > div');
                    if (modalFooterChildren.length >= 3) {
                        const thirdChild = modalFooterChildren[2];
                        const uploadButton = thirdChild.querySelector('div.btn.solid-blue');
                        if (uploadButton && uploadButton.textContent.includes('Upload')) {
                            uploadButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                uploadButton.click();
                                uploadButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📤 Successfully clicked 'Upload' button via fallback!")
            return True

        print("Could not find or click 'Upload' button - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_upload_button: {str(e)} - continuing anyway.")
        return False

def click_on_send_message_button(page):
    """
    Attempt to find and click the 'Send Message' button (paper plane icon) using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > app-button",
            # Simplified CSS selectors
            "app-group-message-input div.flex-row.flex-align-center app-button.send-button.can-send",
            "app-group-message-input app-button.send-button",
            "app-button.send-button.can-send",
            "app-group-message-input app-button",
            "app-messages-conversation-route app-button.send-button",
            # Icon-based selectors
            "i.fa-solid.fa-paper-plane-top",
            "i.fa-paper-plane-top",
            "app-button i.fa-paper-plane-top",
            # Class-based selectors
            "app-button.can-send",
            ".send-button.can-send",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-hidden.nav-bar-top-mobile-hidden > div > app-messages-route > div > div > div.messages-content-wrapper > app-messages-conversation-route > app-group-message-container > app-group-message-input > div.flex-row.flex-align-center > app-button")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/app-button",
            # Alternative XPaths
            "//app-group-message-input//div[@class='flex-row flex-align-center']//app-button",
            "//app-button[@class='send-button can-send']",
            "//app-button[contains(@class, 'send-button')]",
            "//i[@class='fa-solid fa-paper-plane-top']",
            "//app-group-message-input//app-button",
            "//app-messages-conversation-route//app-button[contains(@class, 'can-send')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with click event
                    button_clicked = page.evaluate(f'''() => {{
                        const button = {selector};
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if button_clicked:
                        print("📨 Successfully clicked 'Send Message' button!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📨 Successfully clicked 'Send Message' button!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📨 Successfully clicked 'Send Message' button!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with Send Message button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting send button with multiple strategies
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by app-button with send-button class
                    const sendButtons = document.querySelectorAll('app-button.send-button');
                    if (sendButtons.length > 0) {
                        for (const button of sendButtons) {
                            if (button.classList.contains('can-send')) {
                                button.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    button.click();
                                    button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                    }

                    // Strategy 2: Find by paper plane icon and get parent app-button
                    const paperPlaneIcons = document.querySelectorAll('i.fa-paper-plane-top');
                    if (paperPlaneIcons.length > 0) {
                        const sendButton = paperPlaneIcons[0].closest('app-button');
                        if (sendButton) {
                            sendButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                sendButton.click();
                                sendButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 3: Find in app-group-message-input
                    const messageInput = document.querySelector('app-group-message-input');
                    if (messageInput) {
                        const sendButton = messageInput.querySelector('app-button.can-send');
                        if (sendButton) {
                            sendButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                sendButton.click();
                                sendButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 4: Find any app-button with can-send class
                    const canSendButtons = document.querySelectorAll('app-button.can-send');
                    if (canSendButtons.length > 0) {
                        const button = canSendButtons[0];
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            button.click();
                            button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 200);
                        return;
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📨 Successfully clicked 'Send Message' button via fallback!")
            return True

        print("Could not find or click 'Send Message' button - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_on_send_message_button: {str(e)} - continuing anyway.")
        return False

def click_to_change_creators_nickname(page):
    """
    Attempt to find and click the notes icon (sticky note) to change creator's nickname using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details-2 > div > app-account-username > a > span > i",
            # Simplified CSS selectors
            "app-account-username a span i.fal.fa-note-sticky",
            "app-account-username i.fa-note-sticky.pointer",
            "div.profile-details-2 i.fa-note-sticky",
            "app-profile-route i.notes-icon",
            "i.fa-note-sticky.notes-icon",
            # Icon-based selectors
            "i.fal.fa-note-sticky",
            "i.fa-note-sticky",
            "i.notes-icon",
            "i.pointer.blue-1-hover-only.notes-icon",
            # Parent selectors
            "app-account-username a span",
            "app-account-username a",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details-2 > div > app-account-username > a > span > i")',
            # XPath
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[3]/div/app-account-username/a/span/i",
            # Alternative XPaths
            "//app-account-username//a//span//i[@class='fal fa-note-sticky pointer blue-1-hover-only notes-icon']",
            "//i[@class='fal fa-note-sticky pointer blue-1-hover-only notes-icon']",
            "//div[@class='profile-details-2']//i[@class='fal fa-note-sticky pointer blue-1-hover-only notes-icon']",
            "//app-account-username//i[contains(@class, 'fa-note-sticky')]",
            "//i[contains(@class, 'notes-icon')]",
            "//app-profile-route//i[@class='fal fa-note-sticky pointer blue-1-hover-only notes-icon']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with click event
                    icon_clicked = page.evaluate(f'''() => {{
                        const icon = {selector};
                        if (icon) {{
                            icon.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            return new Promise(resolve => {{
                                setTimeout(() => {{
                                    icon.click();
                                    icon.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                    resolve(true);
                                }}, 300);
                            }});
                        }}
                        return false;
                    }}''')

                    if icon_clicked:
                        print("📝 Successfully clicked notes icon to change nickname!")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

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
                                    element.style.display = 'inline-block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📝 Successfully clicked notes icon to change nickname!")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Force visibility and enable pointer events
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'inline-block';
                                    element.style.pointerEvents = 'auto';
                                }}
                            }}''', selector)

                            # Scroll and click with force
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click(force=True)

                            # Trigger Angular click event
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print("📝 Successfully clicked notes icon to change nickname!")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with notes icon selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach targeting notes icon with multiple strategies
        fallback_clicked = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by fa-note-sticky icon class
                    const noteIcons = document.querySelectorAll('i.fa-note-sticky');
                    if (noteIcons.length > 0) {
                        for (const icon of noteIcons) {
                            if (icon.classList.contains('notes-icon')) {
                                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    icon.click();
                                    icon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    resolve(true);
                                }, 200);
                                return;
                            }
                        }
                        // If no notes-icon class, click the first one
                        noteIcons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            noteIcons[0].click();
                            noteIcons[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 200);
                        return;
                    }

                    // Strategy 2: Find by notes-icon class
                    const notesIcons = document.querySelectorAll('i.notes-icon');
                    if (notesIcons.length > 0) {
                        notesIcons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => {
                            notesIcons[0].click();
                            notesIcons[0].dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 200);
                        return;
                    }

                    // Strategy 3: Find in app-account-username component
                    const accountUsername = document.querySelector('app-account-username');
                    if (accountUsername) {
                        const noteIcon = accountUsername.querySelector('i.fa-note-sticky') ||
                                       accountUsername.querySelector('i[class*="note"]');
                        if (noteIcon) {
                            noteIcon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                noteIcon.click();
                                noteIcon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    // Strategy 4: Find in profile-details-2
                    const profileDetails = document.querySelector('div.profile-details-2');
                    if (profileDetails) {
                        const noteIcon = profileDetails.querySelector('i.fa-note-sticky');
                        if (noteIcon) {
                            noteIcon.scrollIntoView({behavior: 'smooth', block: 'center'});
                            setTimeout(() => {
                                noteIcon.click();
                                noteIcon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                resolve(true);
                            }, 200);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_clicked:
            print("📝 Successfully clicked notes icon to change nickname via fallback!")
            return True

        print("Could not find or click notes icon - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in click_to_change_creators_nickname: {str(e)} - continuing anyway.")
        return False

def insert_custom_name_for_creator(page, custom_name):
    """
    Attempt to find the notes/nickname input field and insert custom name using multiple approaches.
    Triggers proper Angular events to ensure the input is recognized.
    Returns True if text inserted successfully, False otherwise (but doesn't crash the program).

    Args:
        page: Playwright page object
        custom_name: The custom nickname to insert (e.g., "Abordada")
    """
    try:
        # List of selectors to try for the input
        selectors = [
            # Direct CSS selector
            "body > app-root > div > div.modal-wrapper > app-notes-edit-modal > div > div.modal-content.flex-col > div.material-input.icon-right > input",
            # Simplified CSS selectors
            "app-notes-edit-modal div.modal-content.flex-col div.material-input.icon-right input",
            "app-notes-edit-modal div.material-input input",
            "div.modal-content.flex-col div.material-input input",
            "app-notes-edit-modal input[type='text']",
            "div.material-input.icon-right input",
            "app-notes-edit-modal input",
            # Class-based selectors
            "input.ng-untouched.ng-pristine.ng-valid",
            "div.material-input input[type='text']",
            # JavaScript path
            'document.querySelector("body > app-root > div > div.modal-wrapper > app-notes-edit-modal > div > div.modal-content.flex-col > div.material-input.icon-right > input")',
            # XPath
            "/html/body/app-root/div/div[3]/app-notes-edit-modal/div/div[2]/div[1]/input",
            # Alternative XPaths
            "//app-notes-edit-modal//div[@class='modal-content flex-col']//div[@class='material-input icon-right']//input",
            "//app-notes-edit-modal//div[contains(@class, 'material-input')]//input",
            "//div[@class='material-input icon-right']//input[@type='text']",
            "//app-notes-edit-modal//input[@type='text']",
            "//div[contains(@class, 'modal-content')]//input[@type='text']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector with text insertion and event triggering
                    text_inserted = page.evaluate(f'''(customName) => {{
                        const input = {selector};
                        if (input) {{
                            input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            input.focus();

                            // Clear any existing value
                            input.value = '';

                            // Set the new value
                            input.value = customName;

                            // Trigger all necessary events for Angular
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                            input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('blur', {{ bubbles: true }}));

                            return true;
                        }}
                        return false;
                    }}''', custom_name)

                    if text_inserted:
                        print(f"📝 Successfully inserted custom name: '{custom_name}'")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's an input element
                            tag_name = xpath_elements.first.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name != "input":
                                continue

                            # Scroll into view and focus
                            xpath_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            xpath_elements.first.click()
                            page.wait_for_timeout(200)

                            # Clear and fill the input
                            xpath_elements.first.fill("")
                            page.wait_for_timeout(100)
                            xpath_elements.first.fill(custom_name)

                            # Trigger Angular events
                            page.evaluate(f'''(selector) => {{
                                const input = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (input) {{
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print(f"📝 Successfully inserted custom name: '{custom_name}'")
                            return True
                        except Exception as e:
                            print(f"XPath text insertion failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Wait for element to be stable
                            page.wait_for_timeout(500)

                            # Check if it's an input element
                            tag_name = css_elements.first.evaluate("el => el.tagName.toLowerCase()")
                            if tag_name != "input":
                                continue

                            # Scroll into view and focus
                            css_elements.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(300)
                            css_elements.first.click()
                            page.wait_for_timeout(200)

                            # Clear and fill the input
                            css_elements.first.fill("")
                            page.wait_for_timeout(100)
                            css_elements.first.fill(custom_name)

                            # Trigger Angular events
                            page.evaluate(f'''(selector) => {{
                                const input = document.querySelector(selector);
                                if (input) {{
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keydown', {{ bubbles: true }}));
                                    input.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
                                }}
                            }}''', selector)

                            print(f"📝 Successfully inserted custom name: '{custom_name}'")
                            return True
                        except Exception as e:
                            print(f"CSS selector text insertion failed: {str(e)}")

            except Exception as e:
                print(f"Failed with custom name input selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with character-by-character typing
        fallback_inserted = page.evaluate('''(customName) => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    // Strategy 1: Find by material-input class
                    const materialInput = document.querySelector('app-notes-edit-modal div.material-input');
                    if (materialInput) {
                        const input = materialInput.querySelector('input');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = '';

                            // Type character by character to trigger events
                            let index = 0;
                            const typeChar = () => {
                                if (index < customName.length) {
                                    input.value += customName[index];
                                    input.dispatchEvent(new Event('input', { bubbles: true }));
                                    index++;
                                    setTimeout(typeChar, 50);
                                } else {
                                    input.dispatchEvent(new Event('change', { bubbles: true }));
                                    input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                                    resolve(true);
                                }
                            };
                            typeChar();
                            return;
                        }
                    }

                    // Strategy 2: Find by app-notes-edit-modal
                    const notesModal = document.querySelector('app-notes-edit-modal');
                    if (notesModal) {
                        const input = notesModal.querySelector('input[type="text"]');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = customName;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }));
                            resolve(true);
                            return;
                        }
                    }

                    // Strategy 3: Find any input in modal with modal-content
                    const modalContent = document.querySelector('div.modal-content.flex-col');
                    if (modalContent) {
                        const input = modalContent.querySelector('input[type="text"]');
                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();
                            input.value = customName;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            resolve(true);
                            return;
                        }
                    }

                    resolve(false);
                }, 500);
            });
        }''', custom_name)

        if fallback_inserted:
            print(f"📝 Successfully inserted custom name via fallback: '{custom_name}'")
            return True

        print(f"Could not insert custom name '{custom_name}' - continuing anyway.")
        return False

    except Exception as e:
        print(f"Error in insert_custom_name_for_creator: {str(e)} - continuing anyway.")
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
    
    # Keep browser active - IMPORTANT!
    print("Browser started successfully!")
    print("IMPORTANT: Do not close this terminal to keep Chrome active")
    
    # Maximize browser window 
    pyautogui.press("f11")

    page.wait_for_timeout(2000)
    # endregion

    hashtag_picker_and_control()

    page.wait_for_timeout(2000)

    # region Try to insert hashtag and press Enter with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to insert hashtag and find...")
        if insert_hashtag_and_find(page, current_hashtag):  # Replace with your actual hashtag variable
            #print("Successfully inserted hashtag and pressed Enter!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(1)  # Wait 1 second before retrying
    else:
        print("Failed to insert hashtag and press Enter after all attempts.")
    page.wait_for_timeout(3000)
    # endregion

    page.wait_for_timeout(2000)

    # region Try to click follower card with retries
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1} to click follower card...")
        if click_on_follower_card(page):
            print("Successfully clicked the follower card!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(1)  # Wait 1 second before retrying
    else:
        print("Failed to click follower card after all attempts.")
    page.wait_for_timeout(50000)
    # endregion

    page.wait_for_timeout(2000)

    # # region Try to click the Follow button with retries
    # max_retries = 3
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click Follow button...")
    #     if click_on_follow_button(page):
    #         #print("Successfully clicked Follow button!")
    #         break
    #     else:
    #         print(f"Attempt {attempt + 1} failed.")
    #         if attempt < max_retries - 1:
    #             print("Waiting before next attempt...")
    #             page.wait_for_timeout(2000)
    # else:
    #     print("Failed to click Follow button after all attempts.")

    # page.wait_for_timeout(3000)
    # # endregion

    # # region Try to close the pay-to-follow modal window with retries (non-blocking)
    # max_retries = 3
    # modal_closed = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to close pay-to-follow modal...")
    #     if click_to_close_to_pay_to_follow_window(page):
    #         #print("Successfully closed pay-to-follow modal!")
    #         modal_closed = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not modal_closed:
    #     print("Could not close pay-to-follow modal after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of modal closure status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click the creator's interactions options with retries (non-blocking)
    # max_retries = 3
    # options_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click creator's interactions options...")
    #     if click_on_creators_interactions_options(page):
    #         #print("Successfully clicked creator's interactions options!")
    #         options_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not options_clicked:
    #     print("Could not click creator's interactions options after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Add To List' option in dropdown with retries (non-blocking)
    # max_retries = 3
    # add_to_list_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Add To List' option...")
    #     if click_to_add_to_list(page):
    #         #print("Successfully clicked 'Add To List' option!")
    #         add_to_list_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not add_to_list_clicked:
    #     print("Could not click 'Add To List' option after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to add creator to the 'Creators ⭐' list with retries (non-blocking)
    # max_retries = 3
    # added_to_list = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to add to Creators list...")
    #     if click_to_add_on_the_creators_list(page):
    #         #print("Successfully processed Creators list!")
    #         added_to_list = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not added_to_list:
    #     print("Could not add to Creators list after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of list addition status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click Save button in list addition modal with retries (non-blocking)
    # max_retries = 3
    # save_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click Save button...")
    #     if click_on_save_button_to_list_addition(page):
    #         #print("Successfully saved list addition!")
    #         save_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not save_clicked:
    #     print("Could not click Save button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of save status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Add To List' option in dropdown with retries (non-blocking)
    # max_retries = 3
    # add_to_list_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Add To List' option...")
    #     if click_to_add_to_list(page):
    #         #print("Successfully clicked 'Add To List' option!")
    #         add_to_list_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not add_to_list_clicked:
    #     print("Could not click 'Add To List' option after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to mute user with retries (non-blocking)
    # max_retries = 3
    # user_muted = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to mute user...")
    #     if click_on_mute_user_button(page):
    #         #print("Successfully processed mute action!")
    #         user_muted = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not user_muted:
    #     print("Could not mute user after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of mute status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click DM button with retries (non-blocking)
    # max_retries = 3
    # dm_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click DM button...")
    #     if click_on_send_DM_button(page):
    #         #print("Successfully clicked DM button!")
    #         dm_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not dm_clicked:
    #     print("Could not click DM button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Allow DM' button with retries (non-blocking)
    # max_retries = 3
    # allow_dm_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Allow DM' button...")
    #     if click_to_allow_send_me_DM(page):
    #         #print("Successfully allowed DM sending!")
    #         allow_dm_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not allow_dm_clicked:
    #     print("Could not click 'Allow DM' button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Yes' button in DM confirmation modal with retries (non-blocking)
    # max_retries = 3
    # yes_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Yes' button in DM confirmation...")
    #     if click_yes_to_accept_receiving_DM_from_this_creator(page):
    #         #print("Successfully accepted DM request!")
    #         yes_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not yes_clicked:
    #     print("Could not click 'Yes' button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to insert message text with retries (non-blocking)
    # contact_message = '💓 Hi sweetie! Let\'s SFS (Shoutout for shoutout) 24 hours for free? If you don\'t know how to do it, watch this video on attach! If you want, please, repost this link: https://fansly.com/post/732275677243383808'

    # max_retries = 3
    # text_inserted = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to insert message text...")
    #     if insert_text_to_be_sent(page, contact_message):
    #         #print("Successfully inserted message text!")
    #         text_inserted = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not text_inserted:
    #     print("Could not insert message text after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of text insertion status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click Add Media button with retries (non-blocking)
    # max_retries = 3
    # media_button_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click Add Media button...")
    #     if click_to_add_media_button(page):
    #         #print("Successfully clicked Add Media button!")
    #         media_button_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not media_button_clicked:
    #     print("Could not click Add Media button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'From Vault' option in dropdown with retries (non-blocking)
    # max_retries = 3
    # from_vault_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'From Vault' option...")
    #     if click_to_add_from_vault(page):
    #         #print("Successfully clicked 'From Vault' option!")
    #         from_vault_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not from_vault_clicked:
    #     print("Could not click 'From Vault' option after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to insert search text in album search with retries (non-blocking)
    # album_search_text = "SFS"

    # max_retries = 3
    # search_inserted = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to insert album search text...")
    #     if insert_text_to_find_specific_album(page, album_search_text):
    #         #print("Successfully inserted album search text!")
    #         search_inserted = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not search_inserted:
    #     print("Could not insert album search text after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of search insertion status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to select 'SFS Instructions' album with retries (non-blocking)
    # max_retries = 3
    # sfs_album_selected = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to select 'SFS Instructions' album...")
    #     if click_to_select_sfs_video(page):
    #         #print("Successfully selected 'SFS Instructions' album!")
    #         sfs_album_selected = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not sfs_album_selected:
    #     print("Could not select 'SFS Instructions' album after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of selection status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to select media item with retries (non-blocking)
    # max_retries = 3
    # media_selected = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to select media item...")
    #     if click_to_select_media(page):
    #         #print("Successfully selected media item!")
    #         media_selected = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not media_selected:
    #     print("Could not select media item after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of selection status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Add' button to add selected media with retries (non-blocking)
    # max_retries = 3
    # add_media_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Add' button...")
    #     if click_to_add_selected_media(page):
    #         #print("Successfully added selected media!")
    #         add_media_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not add_media_clicked:
    #     print("Could not click 'Add' button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to uncheck 'Require Subscription' checkbox with retries (non-blocking)
    # max_retries = 3
    # subscription_unchecked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to uncheck 'Require Subscription' checkbox...")
    #     if click_to_uncheck_require_subscription(page):
    #         #print("Successfully unchecked 'Require Subscription' checkbox!")
    #         subscription_unchecked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not subscription_unchecked:
    #     print("Could not uncheck 'Require Subscription' checkbox after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of checkbox status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Upload' button with retries (non-blocking)
    # max_retries = 3
    # upload_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Upload' button...")
    #     if click_on_upload_button(page):
    #         #print("Successfully clicked 'Upload' button!")
    #         upload_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not upload_clicked:
    #     print("Could not click 'Upload' button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(2000)  # Wait longer for upload to process

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to click 'Send Message' button with retries (non-blocking)
    # max_retries = 3
    # send_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click 'Send Message' button...")
    #     if click_on_send_message_button(page):
    #         #print("Successfully sent message!")
    #         send_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not send_clicked:
    #     print("Could not click 'Send Message' button after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(2000)  # Wait for message to send

    # # Continue with next instructions regardless of send status
    # # endregion

    # page.wait_for_timeout(2000)

    # # Go back to the previous page
    # page.go_back()

    # # region Try to click notes icon to change creator's nickname with retries (non-blocking)
    # max_retries = 3
    # notes_icon_clicked = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to click notes icon...")
    #     if click_to_change_creators_nickname(page):
    #         #print("Successfully clicked notes icon!")
    #         notes_icon_clicked = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not notes_icon_clicked:
    #     print("Could not click notes icon after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1500)

    # # Continue with next instructions regardless of click status
    # # endregion

    # page.wait_for_timeout(2000)

    # # region Try to insert custom name/nickname for creator with retries (non-blocking)
    # custom_name = "Abordada"

    # max_retries = 3
    # name_inserted = False
    # for attempt in range(max_retries):
    #     #print(f"\nAttempt {attempt + 1} to insert custom name...")
    #     if insert_custom_name_for_creator(page, custom_name):
    #         #print("Successfully inserted custom name!")
    #         name_inserted = True
    #         break
    #     else:
    #         if attempt < max_retries - 1:
    #             print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
    #             page.wait_for_timeout(2000)

    # if not name_inserted:
    #     print("Could not insert custom name after all attempts. Proceeding with next steps...")
    # else:
    #     page.wait_for_timeout(1000)

    # # Continue with next instructions regardless of insertion status
    # # endregion

    # page.wait_for_timeout(2000)

    # # Go back to the previous page
    # page.go_back()

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