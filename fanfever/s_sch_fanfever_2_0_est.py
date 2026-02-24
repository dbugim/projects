import datetime as dt
import sys
import os
import random
import pyperclip
import time
import pyautogui
import subprocess
from playwright.sync_api import sync_playwright, Page, expect
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="playwright_stealth")
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.append(str(Path(__file__).resolve().parent.parent))  # Adjust path to include the parent directory

# region Script to help build the executable with PyInstaller
try:
    # For PyInstaller executable
    sys.path.append(os.path.join(sys._MEIPASS, "repository"))
except Exception:
    # For development
    sys.path.append(str(Path(__file__).resolve().parent.parent / "repository"))

# Global variables to keep references
playwright_instance = None
browser_context = None
# endregion

# region playwright-stealth (fork mais atualizado recomendado em 2025/2026)
try:
    from playwright_stealth import stealth_sync
except ImportError:
    print("playwright-stealth não encontrado.")
    print("Instale com: pip install git+https://github.com/AtuboDad/playwright_stealth.git")
    sys.exit(1)
# endregion

def cleanup(pw=None, context=None, browser_process=None):
    """Cleanup resources properly"""
    if context:
        try:
            context.close()
        except Exception as e:
            print(f"Error closing context: {e}")
    if pw:
        try:
            pw.stop()
        except Exception as e:
            print(f"Error stopping Playwright: {e}")
    if browser_process:
        try:
            browser_process.terminate()
            browser_process.wait(timeout=5)
        except Exception as e:
            print(f"Error terminating browser process: {e}")
    print("Recursos liberados")

def open_chrome_in_fanfever_login_page():
    # 1. Paths
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    # We use a subfolder to avoid the 'default directory' security error
    user_data = os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\User Data\Automation")

    # 2. Kill any existing Chrome
    os.system("taskkill /f /im chrome.exe /t >nul 2>&1")
    time.sleep(2)

    # 3. Launch Chrome as a SEPARATE process (Native Launch)
    # We open a 'Remote Debugging Port' that Playwright will use to connect
    print("Launching Native Chrome Process...")
    browser_process = subprocess.Popen([
        chrome_path,
        f"--user-data-dir={user_data}",
        "--remote-debugging-port=9222",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "https://fanfever.com/br"
    ])

    # Give the browser 5 seconds to fully open and start the debugging server
    time.sleep(5)

    # 4. Connect Playwright to the ALREADY OPENED Chrome
    pw = sync_playwright().start()
    try:
        print("Hooking Playwright into the running Chrome...")
        # Instead of launch_persistent_context, we CONNECT to the port
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")

        # Access the already open context and page
        context = browser.contexts[0]
        page = context.pages[0]

        print("Successfully hooked! Browser is now under automation control.")
        return pw, context, browser_process

    except Exception as e:
        print(f"Hook failed: {e}")
        pw.stop()
        browser_process.kill()
        raise

def insert_username(page):
    """
    Attempt to find the username input field and insert 'hacksimone29@gmail.com'.
    Handles Shadow DOM and multiple selector strategies.
    """
    username_to_insert = "hacksimone29@gmail.com"
    try:
        # List of selectors to try (updated with new ID and paths, prioritizing the provided ones)
        selectors = [
            # NEW PRIMARY SELECTORS (from your provided element details)
            '#container > section > div > div > form > div.cp-form__sender.has-mgn-top-0 > div:nth-child(1) > div > div > input',
            'input[name="b54d137a93ea496826a1effd5213d020"]',
            'input.cp-form__field[placeholder="E-mail"]',
            'document.querySelector("#container > section > div > div > form > div.cp-form__sender.has-mgn-top-0 > div:nth-child(1) > div > div > input")',
            "//*[@id='container']/section/div/div/form/div[2]/div[1]/div/div/input",

            # Original selectors (modified to remove specific shadow host if not relevant)
            # If the element is NOT in a Shadow DOM, these might work
            "input[type='email']",
            "input.el-input__inner[type='email']",
            "input[type='email'][autocomplete='off']",
            "input[placeholder=' '][type='email']",
            "input[id^='floating-input-']", # Generalized for dynamic IDs if applicable
            "//*[@type='email' and contains(@id, 'floating-input')]",
            "//input[@class='el-input__inner' and @type='email']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector (handles shadow DOM if present, or direct query)
                    input_inserted = page.evaluate(f'''(text) => {{
                        try {{
                            const input = {selector};
                            if (input) {{
                                input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                input.focus();
                                input.value = text;
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                return true;
                            }}
                        }} catch(e) {{
                            console.error('Error inserting username with JS selector:', e);
                        }}
                        return false;
                    }}''', username_to_insert)
                    if input_inserted:
                        print(f"✓ Username inserted successfully with JavaScript selector: {selector}")
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
                            # Scroll, focus, and fill
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.focus()
                            xpath_elements.first.fill(username_to_insert)
                            print(f"✓ Username inserted successfully with XPath: {selector}")
                            return True
                        except Exception as e:
                            print(f"XPath insert failed for {selector}: {str(e)}")

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
                            # Scroll, focus, and fill
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.focus()
                            css_elements.first.fill(username_to_insert)
                            print(f"✓ Username inserted successfully with CSS selector: {selector}")
                            return True
                        except Exception as e:
                            print(f"CSS selector insert failed for {selector}: {str(e)}")

            except Exception as e:
                print(f"Failed with username input selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with comprehensive search (updated with new patterns)
        print("Trying JavaScript fallback approach for username input...")
        fallback_inserted = page.evaluate('''(text) => {
            // Try regular DOM as fallback, prioritizing new patterns
            const inputSelectors = [
                '#container > section > div > div > form > div.cp-form__sender.has-mgn-top-0 > div:nth-child(1) > div > div > input',
                'input[name="b54d137a93ea496826a1effd5213d020"]',
                'input.cp-form__field[placeholder="E-mail"]',
                'input[type="text"][placeholder="E-mail"]', # More generic for the new element
                'input[type="email"]',
                'input[id^="floating-input-"]',
                'input.el-input__inner[type="email"]',
                'input[autocomplete="off"][type="email"]',
                'input[tabindex="0"][type="email"]',
                'input[placeholder=" "][type="email"]'
            ];

            for (const selector of inputSelectors) {
                const inputs = document.querySelectorAll(selector);
                for (const input of inputs) {
                    if (input && input.offsetParent !== null) { // Check if visible
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.value = text;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.dispatchEvent(new Event('blur', { bubbles: true }));
                        return true;
                    }
                }
            }

            // If a Shadow DOM host was explicitly identified, try within it
            // (Removed specific #privacy-web-auth as it doesn't match new element)
            // If you know a specific Shadow DOM host for this new element, you'd re-add it here.

            return false;
        }''', username_to_insert)

        if fallback_inserted:
            print("✓ Username inserted successfully using JavaScript fallback!")
            return True

        print("❌ Could not find or insert into username input using any method.")
        return False

    except Exception as e:
        print(f"❌ Error in insert_username: {str(e)}")
        return False

def insert_password(page):
    """
    Attempt to find the password input field and insert 'Booegabi10!'.
    Handles Shadow DOM and multiple selector strategies.
    """
    password_to_insert = "Booegabi10!"
    try:
        # List of selectors to try (updated with new ID and paths, prioritizing the provided ones)
        selectors = [
            # NEW PRIMARY SELECTORS (from your provided element details)
            '#password',
            'input[name="4ab66e59aed0f3bdb2e5c0410ec32a7b"]',
            'input.js-toggle-pass-input[placeholder="Senha"]',
            'document.querySelector("#password")',
            "//*[@id='password']",

            # Original selectors (modified to remove specific shadow host if not relevant)
            # If the element is NOT in a Shadow DOM, these might work
            'input[type="password"]',
            'input.el-input__inner[type="password"]',
            'input[type="password"][autocomplete="off"]',
            'input[placeholder=" "][type="password"]',
            'div.el-form-item.is-required input[type="password"]',
            'input[id^="floating-input-"]', # Generalized for dynamic IDs if applicable
            "//*[@type='password' and contains(@id, 'floating-input')]",
            "//input[@class='el-input__inner' and @type='password']",
            "//div[contains(@class, 'is-required')]//input[@type='password']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector (handles shadow DOM if present, or direct query)
                    input_inserted = page.evaluate(f'''(text) => {{
                        try {{
                            const input = {selector};
                            if (input) {{
                                input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                input.focus();
                                input.value = text;
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                return true;
                            }}
                        }} catch(e) {{
                            console.error('Error inserting password with JS selector:', e);
                        }}
                        return false;
                    }}''', password_to_insert)
                    if input_inserted:
                        print(f"✓ Password inserted successfully with JavaScript selector: {selector}")
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
                            # Scroll, focus, and fill
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.focus()
                            xpath_elements.first.fill(password_to_insert)
                            print(f"✓ Password inserted successfully with XPath: {selector}")
                            return True
                        except Exception as e:
                            print(f"XPath insert failed for {selector}: {str(e)}")

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
                            # Scroll, focus, and fill
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.focus()
                            css_elements.first.fill(password_to_insert)
                            print(f"✓ Password inserted successfully with CSS selector: {selector}")
                            return True
                        except Exception as e:
                            print(f"CSS selector insert failed for {selector}: {str(e)}")

            except Exception as e:
                print(f"Failed with password input selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach with comprehensive search (updated with new patterns)
        print("Trying JavaScript fallback approach for password input...")
        fallback_inserted = page.evaluate('''(text) => {
            // Try regular DOM as fallback, prioritizing new patterns
            const inputSelectors = [
                '#password',
                'input[name="4ab66e59aed0f3bdb2e5c0410ec32a7b"]',
                'input.js-toggle-pass-input[placeholder="Senha"]',
                'input[type="password"]',
                'input[id^="floating-input-"]',
                'input.el-input__inner[type="password"]',
                'input[autocomplete="off"][type="password"]',
                'input[tabindex="0"][type="password"]',
                'input[placeholder=" "][type="password"]',
                'div.el-form-item.is-required input[type="password"]'
            ];

            for (const selector of inputSelectors) {
                const inputs = document.querySelectorAll(selector);
                for (const input of inputs) {
                    if (input && input.offsetParent !== null) { // Check if visible
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});
                        input.focus();
                        input.value = text;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.dispatchEvent(new Event('blur', { bubbles: true }));
                        return true;
                    }
                }
            }

            // If a Shadow DOM host was explicitly identified, try within it
            // (Removed specific #privacy-web-auth as it doesn't match new element)
            // If you know a specific Shadow DOM host for this new element, you'd re-add it here.

            return false;
        }''', password_to_insert)

        if fallback_inserted:
            print("✓ Password inserted successfully using JavaScript fallback!")
            return True

        print("❌ Could not find or insert into password input using any method.")
        return False

    except Exception as e:
        print(f"❌ Error in insert_password: {str(e)}")
        return False

def click_login_button(page):
    """
    Attempt to find and click the login button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#container > section > div > div > form > div.cp-form__sender.has-mgn-top-5 > div.cp-form__item.has-pad-top-0 > div > button",
            # Alternative CSS selectors
            "button.cp-form__button.is-primary[type='submit'][name='model']",
            "button[type='submit'][name='model']",
            "button.cp-form__button.is-primary",
            "form button[type='submit']",
            # JavaScript path
            "document.querySelector(\"#container > section > div > div > form > div.cp-form__sender.has-mgn-top-5 > div.cp-form__item.has-pad-top-0 > div > button\")",
            # XPath
            "//*[@id=\"container\"]/section/div/div/form/div[3]/div[1]/div/button",
            # Alternative XPath
            "//button[@type='submit' and @name='model']",
            "//button[contains(@class, 'cp-form__button') and contains(@class, 'is-primary')]",
            "//form//button[@type='submit']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying login button selector: {selector}")

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
                        #print(f"Successfully clicked login button with JS selector")
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
                            #print(f"Successfully clicked login button with XPath")
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
                            #print(f"Successfully clicked login button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with login button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        #print("Trying JavaScript fallback approach for login button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with login/submit-related attributes or classes
            const buttonSelectors = [
                'button.cp-form__button.is-primary',
                'button[type="submit"][name="model"]',
                'button[type="submit"]',
                'form button.is-primary',
                'form button[type="submit"]'
            ];

            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && button.textContent.trim().toLowerCase().includes('entrar')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }

            // Try finding any submit button in the form
            const submitButtons = document.querySelectorAll('button[type="submit"]');
            if (submitButtons.length > 0) {
                submitButtons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                submitButtons[0].click();
                return true;
            }

            return false;
        }''')

        if fallback_clicked:
            #print("Successfully clicked login button using JavaScript fallback!")
            return True

        print("Could not find or click login button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_login_button: {str(e)}")
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
                        #print(f"Successfully clicked plus button with JS selector")
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
                            #print(f"Successfully clicked plus button with XPath")
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
                            #print(f"Successfully clicked plus button with CSS selector")
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
                        #print(f"Successfully clicked 'Add New Story' button with JS selector")
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
                            #print(f"Successfully clicked 'Add New Story' button with XPath")
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
                            #print(f"Successfully clicked 'Add New Story' button with CSS selector")
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

def select_random_media():
    folder_path = r'G:\Meu Drive\SFS'
    
    # Define the allowed media extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.mp4', '.mpg', '.mov', '.avi')
    
    try:
        # Filter files: must be a file AND end with a valid extension
        files_only = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) 
            and f.lower().endswith(valid_extensions)
        ]
    except FileNotFoundError:
        print(f"Folder not found: {folder_path}")
        return None
    
    if not files_only:
        print("No valid media files found in the folder")
        return None
    
    chosen_file = random.choice(files_only)
    return os.path.join(folder_path, chosen_file)

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
                        #print(f"Successfully clicked Schedule button with JS selector")
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
                            #print(f"Successfully clicked Schedule button with XPath")
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
                            #print(f"Successfully clicked Schedule button with CSS selector")
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
                        #print(f"Successfully clicked DateTime input with JS selector")
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
                            #print(f"Successfully clicked DateTime input with XPath")
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
                            #print(f"Successfully clicked DateTime input with CSS selector")
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
                        #print(f"Successfully clicked send story button with JS selector")
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
                            #print(f"Successfully clicked send story button with XPath")
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
                            #print(f"Successfully clicked send story button with CSS selector")
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

def click_on_menu(page):
    """
    Attempt to find and click the menu SVG element using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#main > div.cp-wrapper.js-majority-blurred > header > div > nav > a.fs-header__menu-item.js-sidebar__open > svg",
            # Alternative CSS selectors
            "svg.is-profile",
            "a.fs-header__menu-item.js-sidebar__open > svg",
            "a.js-sidebar__open svg",
            "nav a.fs-header__menu-item svg.is-profile",
            # Parent anchor element
            "a.fs-header__menu-item.js-sidebar__open",
            # JavaScript path
            "document.querySelector(\"#main > div.cp-wrapper.js-majority-blurred > header > div > nav > a.fs-header__menu-item.js-sidebar__open > svg\")",
            # XPath for SVG
            "//*[@id=\"main\"]/div[2]/header/div/nav/a[4]/svg",
            "//*[name()='svg' and @class='is-profile']",
            # Alternative XPath
            "//a[@class='fs-header__menu-item js-sidebar__open']/*[name()='svg']",
            "//svg[@class='is-profile']",
            "//a[contains(@class, 'js-sidebar__open')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying menu SVG selector: {selector}")

                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector - click parent anchor instead of SVG
                    menu_clicked = page.evaluate('''() => {
                        const svg = document.querySelector("#main > div.cp-wrapper.js-majority-blurred > header > div > nav > a.fs-header__menu-item.js-sidebar__open > svg");
                        if (svg) {
                            const parentAnchor = svg.closest('a');
                            if (parentAnchor) {
                                parentAnchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                                parentAnchor.click();
                                return true;
                            }
                            svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                            svg.click();
                            return true;
                        }
                        return false;
                    }''')

                    if menu_clicked:
                        #print(f"Successfully clicked menu with JS selector")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate('''(selector) => {
                                const element = document.evaluate(
                                    selector, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }
                            }''', selector)

                            # Scroll and click
                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click(force=True)
                            #print(f"Successfully clicked menu with XPath")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility
                            page.evaluate('''(selector) => {
                                const element = document.querySelector(selector);
                                if (element) {
                                    element.style.opacity = '1';
                                    element.style.visibility = 'visible';
                                    element.style.display = 'block';
                                }
                            }''', selector)

                            # Scroll and click
                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click(force=True)
                            #print(f"Successfully clicked menu with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with menu SVG selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        #print("Trying JavaScript fallback approach for menu SVG...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding SVG elements with menu-related classes
            const svgSelectors = [
                'svg.is-profile',
                'a.js-sidebar__open svg',
                'a.fs-header__menu-item svg',
                'nav svg.is-profile'
            ];

            for (let i = 0; i < svgSelectors.length; i++) {
                const selector = svgSelectors[i];
                const svgList = document.querySelectorAll(selector);
                for (let j = 0; j < svgList.length; j++) {
                    const svg = svgList[j];
                    if (svg) {
                        // Try to click parent anchor first
                        const parentAnchor = svg.closest('a');
                        if (parentAnchor && parentAnchor.classList.contains('js-sidebar__open')) {
                            parentAnchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentAnchor.click();
                            return true;
                        }
                        // Otherwise click SVG directly
                        svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                        svg.click();
                        return true;
                    }
                }
            }

            // Try finding by SVG use elements with specific xlink:href
            const useElements = document.querySelectorAll('svg use[xlink\\:href="#icon-header-profile"]');
            if (useElements.length > 0) {
                const parentSvg = useElements[0].closest('svg');
                if (parentSvg) {
                    const parentAnchor = parentSvg.closest('a');
                    if (parentAnchor) {
                        parentAnchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parentAnchor.click();
                        return true;
                    }
                }
            }

            // Last resort: try any anchor with js-sidebar__open class
            const sidebarOpeners = document.querySelectorAll('a.js-sidebar__open');
            if (sidebarOpeners.length > 0) {
                sidebarOpeners[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                sidebarOpeners[0].click();
                return true;
            }

            return false;
        }''')

        if fallback_clicked:
            #print("Successfully clicked menu using JavaScript fallback!")
            return True

        print("Could not find or click menu SVG using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_menu: {str(e)}")
        return False

def click_on_logout(page: Page):
    """
    Attempt to find and click the Logout button using multiple approaches.
    """
    try:
        # Primeiro, uma espera geral para garantir que a sidebar esteja carregada
        # Isso pode ajudar se a sidebar inteira demora a aparecer
        try:
            page.wait_for_selector("aside.fs-sidebar-user.js-sidebar", timeout=10000)
            #print("Sidebar user is visible, proceeding to find Logout button.")
        except Exception:
            print("Sidebar user not found within timeout. It might not be loaded yet.")
            return False

        # Lista de seletores a tentar, priorizando aqueles que buscam o texto "Logout"
        selectors = [
            # XPath mais robusto que busca o texto "Logout" dentro de um span, que está dentro de um link
            "//a[.//span[text()='Logout']]",
            # CSS selector para o link que contém o texto "Logout" (Playwright extension)
            "nav a:has-text('Logout')",
            # XPath direto para o span com texto "Logout"
            "//span[text()='Logout']",
            # CSS selector para o span com a classe e texto "Logout"
            "span.fs-sidebar-user__menu-text:has-text('Logout')",
            # CSS selector mais específico para o <a> que contém o span com o texto "Logout"
            "aside.fs-sidebar-user nav a:has(span.fs-sidebar-user__menu-text)",
            # CSS selector original (se a posição for estável)
            "#main > div.cp-wrapper.js-majority-blurred > aside.fs-sidebar-user.js-sidebar > div.fs-sidebar-user__content.sidebar-menu > nav > a:nth-child(15)",
            # CSS selector para o span original (se a posição for estável)
            "#main > div.cp-wrapper.js-majority-blurred > aside.fs-sidebar-user.js-sidebar > div.fs-sidebar-user__content.sidebar-menu > nav > a:nth-child(15) > span",
            # Outros seletores CSS alternativos
            "span.fs-sidebar-user__menu-text",
            "aside.fs-sidebar-user nav a span.fs-sidebar-user__menu-text",
            "nav a span.fs-sidebar-user__menu-text",
            ".sidebar-menu nav a span",
            # Outros seletores XPath alternativos
            "//*[@id=\"main\"]/div[2]/aside[1]/div[2]/nav/a[8]/span", # Este XPath parece ser posicional e pode mudar
            "//aside[@class='fs-sidebar-user js-sidebar']//span[text()='Logout']",
            "//nav//a//span[text()='Logout']"
        ]

        # Tenta cada seletor
        for selector in selectors:
            try:
                #print(f"Trying Logout button selector: {selector}")

                # Para seletores JavaScript (que não são o foco principal do Playwright para clique direto)
                if selector.startswith("document.querySelector"):
                    # Mantemos a lógica JS original para este caso específico, se for realmente necessário
                    logout_clicked = page.evaluate('''() => {
                        const span = document.querySelector("#main > div.cp-wrapper.js-majority-blurred > aside.fs-sidebar-user.js-sidebar > div.fs-sidebar-user__content.sidebar-menu > nav > a:nth-child(15) > span");
                        if (span) {
                            const parentAnchor = span.closest('a');
                            if (parentAnchor) {
                                parentAnchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                                parentAnchor.click();
                                return true;
                            }
                            span.scrollIntoView({behavior: 'smooth', block: 'center'});
                            span.click();
                            return true;
                        }
                        return false;
                    }''')

                    if logout_clicked:
                        #print(f"Successfully clicked Logout with JS selector")
                        return True
                else:
                    # Para seletores CSS e XPath, usamos o locator do Playwright
                    # Adicionamos uma espera explícita para o elemento ser visível e habilitado
                    # antes de tentar o clique.
                    logout_locator = page.locator(selector)

                    # Verifica se o locator encontrou algum elemento
                    if logout_locator.count() > 0:
                        try:
                            # Espera que o elemento esteja visível e habilitado
                            expect(logout_locator.first).to_be_visible(timeout=5000)
                            expect(logout_locator.first).to_be_enabled(timeout=5000)

                            # Rola para o elemento e tenta clicar com force=True
                            logout_locator.first.scroll_into_view_if_needed()
                            logout_locator.first.click(force=True)
                            #print(f"Successfully clicked Logout with selector: {selector}")
                            return True
                        except Exception as e:
                            #print(f"Playwright locator click failed for selector {selector}: {str(e)}")
                            pass # Continua para o próximo seletor se falhar
                    #else:
                        #print(f"Selector {selector} did not find any elements.")

            except Exception as e:
                print(f"Failed with Logout button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach (mantido como estava, pois é uma boa estratégia final)
        #print("Trying JavaScript fallback approach for Logout button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding span elements with Logout text
            const spanSelectors = [
                'span.fs-sidebar-user__menu-text',
                'aside.fs-sidebar-user span',
                'nav span',
                '.sidebar-menu span'
            ];

            for (let i = 0; i < spanSelectors.length; i++) {
                const selector = spanSelectors[i];
                const spanList = document.querySelectorAll(selector);
                for (let j = 0; j < spanList.length; j++) {
                    const span = spanList[j];
                    if (span && span.textContent.trim() === 'Logout') {
                        // Try to click parent anchor first
                        const parentAnchor = span.closest('a');
                        if (parentAnchor) {
                            parentAnchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentAnchor.click();
                            return true;
                        }
                        // Otherwise click span directly
                        span.scrollIntoView({behavior: 'smooth', block: 'center'});
                        span.click();
                        return true;
                    }
                }
            }

            // Try finding any element containing "Logout" text in sidebar
            const allAnchors = document.querySelectorAll('aside.fs-sidebar-user nav a');
            for (let k = 0; k < allAnchors.length; k++) {
                const anchor = allAnchors[k];
                if (anchor.textContent.trim() === 'Logout') {
                    anchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                    anchor.click();
                    return true;
                }
            }

            return false;
        }''')

        if fallback_clicked:
            #print("Successfully clicked Logout using JavaScript fallback!")
            return True

        print("Could not find or click Logout button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_logout: {str(e)}")
        return False

def main():
    pw = None
    context = None
    page = None
    browser_process = None

    # ADIÇÃO: Definir user_data aqui para acessá-lo no finally (para limpeza)
    user_data = os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\User Data\Automation")

    # region Launch Browser via the Native Hook method
    try:
        pw, context, browser_process = open_chrome_in_fanfever_login_page()
        page = context.pages[0]  # Grab the active Privacy board page
        print("✓ Browser launched successfully")
    except Exception as e:
        print(f"❌ Failed to launch or hook browser: {e}")
        cleanup(pw, context, browser_process)
        return
    # endregion

    print("Waiting for page load...")
    page.wait_for_load_state("domcontentloaded")

    # Fullscreen Mode
    try:
        pyautogui.press('f11')
        page.wait_for_timeout(3000)
    except ImportError:
        print("Warning: pyautogui not installed, skipping fullscreen")

    # region Login attempt operation

    # region Try to insert username with retries
    print("\nAttempting to insert username...")
    max_retries = 3
    username_inserted = False

    for attempt in range(max_retries):
        print(f"Username attempt {attempt + 1}/{max_retries}")
        if insert_username(page):
            username_inserted = True
            print("✓ Username inserted successfully!")
            break
        else:
            print(f"✗ Username attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                time.sleep(2)

    if not username_inserted:
        print("❌ Failed to insert username after all attempts. Skipping password and login button steps.")
        print("Maybe you are already logged in or there's an issue with the username field.")
        time.sleep(2) # Still wait a bit before exiting this login attempt block
    else:
        # If username was successfully inserted, proceed with password and login button
        time.sleep(2)
        # endregion

        # region Try to insert password with retries
        print("\nAttempting to insert password...")
        max_retries = 3
        password_inserted = False

        for attempt in range(max_retries):
            print(f"Password attempt {attempt + 1}/{max_retries}")
            if insert_password(page):
                password_inserted = True
                print("✓ Password inserted successfully!")
                break
            else:
                print(f"✗ Password attempt {attempt + 1} failed.")
                if attempt < max_retries - 1:
                    print("Waiting before next attempt...")
                    time.sleep(2)

        if not password_inserted:
            print("❌ Failed to insert password after all attempts. Skipping login button step.")
            print("Maybe you are already logged in or there's an issue with the password field.")

        time.sleep(2)
        # endregion

        # region Try to click the login button with retries
        if password_inserted: # Only try to click login if password was inserted
            print("\nAttempting to click the login button...")
            max_retries = 3
            login_button_clicked = False
            for attempt in range(max_retries):
                print(f"Login button attempt {attempt + 1}/{max_retries}")
                if click_login_button(page):
                    print("✓ Successfully clicked login button!")
                    login_button_clicked = True
                    break
                else:
                    print(f"✗ Login button attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        page.wait_for_timeout(2000)

            if not login_button_clicked:
                print("❌ Failed to click login button after all attempts.")
        else:
            print("Skipping login button click because password was not inserted successfully.")

        page.wait_for_timeout(3000)
        # endregion

    # endregion Login attempt operation

    # Go to the posting page
    page.goto('https://m.fanfever.com/br/milfelectra')
    page.wait_for_timeout(3000)

    # region Main operation

    # region Calculate tomorrow's date dynamically (outside the loop, as it's the same for all hours)
    today = dt.date.today()  # Or set manually: today = dt.date(2026, 2, 1)
    tomorrow = today + dt.timedelta(days=1)

    # Format components as strings (dd, mm, yyyy) - fixed for the day
    day_str = f"{tomorrow.day:02d}"  # e.g., '02'
    month_str = f"{tomorrow.month:02d}"  # e.g., '02'
    year_str = f"{tomorrow.year:04d}"  # e.g., '2026'
    # endregion

    # region Process 24 hours for this day (0-23)
    for hour in range(0, 24, 1):  # Explicit step of 1 to ensure single increments
        print(f"  Processing hour {hour:02d}:00")  # Shows as 00:00, 01:00, etc.

        # region Try to click the "plus_button" with retries
        max_retries = 3
        clique_sucesso = False

        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to click plus button...")

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

        page.wait_for_timeout(2000)

        # endregion Try to click the "plus_button" with retries

        # region Try to click the "Add New Story" button with retries
        max_retries = 3
        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to click 'Add New Story' button...")
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
        # endregion Try to click the "Add New Story" button with retries

        # region Copy and paste the file path
        media_path = select_random_media()

        if media_path:
            # Copy the full path to clipboard
            pyperclip.copy(media_path)

            page.wait_for_timeout(1500)

            # Paste and press enter
            pyautogui.hotkey('ctrl', 'v')
            page.wait_for_timeout(1000)

            pyautogui.press('enter')
            page.wait_for_timeout(1500)
        else:
            print("Could not select any media file – check folder path or file types")

        # endregion Copy and paste the file path

        # region Try to click the Schedule button with retries
        max_retries = 3
        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to click Schedule button...")
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
        #endregion Try to click the Schedule button with retries

        # region Try to click the DateTime input with retries
        max_retries = 3
        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to click DateTime input...")
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
        # endregion Try to click the DateTime input with retries

        # region Manage date and time inputs
        
        # region Type date components
        pyautogui.typewrite(day_str)  # Day
        pyautogui.typewrite(month_str)  # Month
        pyautogui.typewrite(year_str)  # Year
        pyautogui.press('tab')  # Move to hour field

        # FIXED HOUR TYPING - ENSURES SINGLE INCREMENT
        hour_str = f"{hour:02d}"  # Formats as 00, 01, 02...23 (uses the loop variable)
        pyautogui.typewrite(hour_str)  # Type the hour
        print(f"Typed hour: {hour_str}")  # Debug output
        pyautogui.typewrite('03')  # Minutes
        page.wait_for_timeout(1000)
        # endregion

        # endregion Manage date and time inputs

        # region Try to click the send story button with retries
        max_retries = 3
        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to send story...")
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

        # endregion Try to click the send story button with retries

        page.wait_for_timeout(7000)

        page.goto('https://m.fanfever.com/br/milfelectra')

        page.wait_for_timeout(3000)
    
    # endregion for loop through hours

    print("All scheduled stories have been processed.")

    # endregion Main operation

    # region Closing session operation

    # region Try to click the menu with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click menu...")
        if click_on_menu(page):
            #print("Successfully clicked menu!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                page.wait_for_timeout(2000)
    else:
        print("Failed to click menu after all attempts.")

    page.wait_for_timeout(3000)
    # endregion Try to click the menu with retries

    sidebar = page.locator(".fs-sidebar-user__content.sidebar-menu")
    sidebar.evaluate("element => element.scrollTop = element.scrollHeight")

    # region Try to click the Logout button with retries
    max_retries = 3
    for attempt in range(max_retries):
        #print(f"\nAttempt {attempt + 1} to click Logout button...")
        if click_on_logout(page):
            #print("Successfully clicked Logout button!")
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                page.wait_for_timeout(2000)
    else:
        print("Failed to click Logout button after all attempts.")

    page.wait_for_timeout(3000)
    # endregion Try to click the Logout button with retries

    # endregion Closing session operation

    # region Cleanup Browser Resources
    try:
        if 'page' in locals() and page:
            page.close()
        if 'context' in locals() and context:
            context.close()
        if 'browser' in locals() and browser_process:
            browser_process.close()
        print("Browser closed successfully.")
    except Exception as close_err:
        print(f"Error closing browser: {close_err}")
    # endregion Cleanup Browser Resources

    # Exit the script (0 for success, as per search recommendations)
    sys.exit(0)    

if __name__ == "__main__":
    main()
