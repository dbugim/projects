import sys
import os
import time
import csv
import pyperclip
import pyautogui
import subprocess
import datetime
from contextlib import contextmanager
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

import warnings
from playwright.sync_api import sync_playwright

warnings.filterwarnings("ignore", category=UserWarning, module="playwright_stealth")
warnings.filterwarnings("ignore", category=DeprecationWarning)

@contextmanager
def capture_and_save_log(file_path):
    """
    Redirects the Python script's standard output (stdout) and standard error (stderr)
    to a file, while also displaying them in the console.
    Adds start and end timestamps to the log file.

    Args:
        file_path (str): The full path to the file where the log will be saved.
    """
    # Save the original stdout and stderr streams
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_file = None

    try:
        # Ensure the directory exists before attempting to open the file
        log_directory = os.path.dirname(file_path)
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            # Print to the original console, as sys.stdout has not yet been redirected
            original_stdout.write(f"Log directory created: {log_directory}\n")

        # Open the log file in append mode ('a')
        log_file = open(file_path, 'a', encoding='utf-8')

        # Redirect stdout and stderr to the Tee class, which writes to both locations
        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)

        # Add a start header to the log (and console)
        now_start = datetime.datetime.now()
        start_timestamp = now_start.strftime("%d:%m:%Y at %H:%M")
        print(f"\n--- SCRIPT EXECUTION STARTED AT {start_timestamp} ---\n")

        # The 'yield' is where the code inside the 'with' block will be executed
        yield

    except Exception as e:
        # Capture exceptions that occur within the 'with' block
        print(f"An unexpected error occurred during script execution: {e}", file=sys.stderr)
        raise # Re-raise the exception so the normal error flow continues

    finally:
        # Add the final timestamp to the log (and console)
        if log_file:
            now_end = datetime.datetime.now()
            end_timestamp = now_end.strftime("%d:%m:%Y at %H:%M")
            print(f"\n^^^^^^^^^^ ERROR LOGS OF {end_timestamp} ^^^^^^^^^^\n")
            log_file.close()

        # Restore stdout and stderr to the original console
        sys.stdout = original_stdout
        sys.stderr = original_stderr

# Helper class to "tee" the output (write to two places simultaneously)
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # Ensures content is written immediately
    def flush(self):
        for f in self.files:
            f.flush()

# region playwright-stealth (fork mais atualizado recomendado em 2025/2026)
try:
    from playwright_stealth import stealth_sync
except ImportError:
    print("playwright-stealth não encontrado.")
    print("Instale com: pip install git+https://github.com/AtuboDad/playwright_stealth.git")
    sys.exit(1)
# endregion playwright-stealth (fork mais atualizado recomendado em 2025/2026)

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

def open_chrome_in_onlyfans_login_page():
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
        "https://onlyfans.com"
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
    Updated to target standard Google login inputs (specifically #input-13).
    """
    try:
        # List of selectors to try (updated with new ID #input-13 and standard attributes)
        selectors = [
            # 1. Direct ID match (Most specific based on your update)
            "#input-13",
            "input#input-13",

            # 2. Standard Google Email Input attributes (High reliability)
            "input[type='email'][name='email']",
            "input[name='email']",
            "input[type='email']",

            # 3. XPath specific to the new ID
            "//*[@id='input-13']",

            # 4. XPath general for email inputs
            "//input[@type='email' and @name='email']",
            "//input[@name='email']",

            # 5. Legacy/Shadow DOM selectors (Kept just in case the structure reverts or varies)
            'document.querySelector("#privacy-web-auth").shadowRoot.querySelector("input[type=\'email\']")',
            'document.querySelector("#privacy-web-auth").shadowRoot.querySelector("#floating-input-jnygnm9")'
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector (handles shadow DOM)
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
                            // Silent fail for this selector
                        }}
                        return false;
                    }}''', "hacksimone29@gmail.com")
                    if input_inserted:
                        print("✓ Username inserted successfully with JS/Shadow selector")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility just in case
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

                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click() # Click ensures focus
                            xpath_elements.first.fill("hacksimone29@gmail.com")
                            print(f"✓ Username inserted successfully with XPath: {selector}")
                            return True
                        except Exception as e:
                            print(f"XPath insert failed: {str(e)}")

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

                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click() # Click ensures focus
                            css_elements.first.fill("hacksimone29@gmail.com")
                            print(f"✓ Username inserted successfully with CSS selector: {selector}")
                            return True
                        except Exception as e:
                            print(f"CSS selector insert failed: {str(e)}")

            except Exception as e:
                # Continue to next selector if one fails
                continue

        # Fallback JavaScript approach with comprehensive search (Updated for #input-13)
        print("Trying JavaScript fallback approach for username input...")
        fallback_inserted = page.evaluate('''(text) => {
            // 1. Try Direct ID first (Fastest)
            const directInput = document.getElementById('input-13');
            if (directInput) {
                directInput.scrollIntoView({behavior: 'smooth', block: 'center'});
                directInput.focus();
                directInput.value = text;
                directInput.dispatchEvent(new Event('input', { bubbles: true }));
                directInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }

            // 2. Try Standard Name/Type attributes
            const standardInput = document.querySelector('input[name="email"]') || document.querySelector('input[type="email"]');
            if (standardInput) {
                standardInput.scrollIntoView({behavior: 'smooth', block: 'center'});
                standardInput.focus();
                standardInput.value = text;
                standardInput.dispatchEvent(new Event('input', { bubbles: true }));
                standardInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }

            // 3. Try Shadow DOM (Legacy support)
            const shadowHost = document.querySelector("#privacy-web-auth");
            if (shadowHost && shadowHost.shadowRoot) {
                const shadowInput = shadowHost.shadowRoot.querySelector('input[type="email"]');
                if (shadowInput) {
                    shadowInput.value = text;
                    shadowInput.dispatchEvent(new Event('input', { bubbles: true }));
                    return true;
                }
            }

            return false;
        }''', "hacksimone29@gmail.com")

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
    Updated to target standard Google login inputs (specifically #input-16).
    """
    # The new defined password
    PASSWORD_TEXT = "Booegabi10!"

    try:
        # List of selectors to try (updated with new ID #input-16 and standard attributes)
        selectors = [
            # 1. Direct ID match (Most specific based on your update)
            "#input-16",
            "input#input-16",

            # 2. Standard Password Input attributes (High reliability)
            "input[name='password']",
            "input[type='password']",

            # 3. Handle case where type might be 'text' (as seen in your snippet) but name is password
            "input[type='text'][name='password']",

            # 4. XPath specific to the new ID
            "//*[@id='input-16']",

            # 5. XPath general for password inputs
            "//input[@name='password']",
            "//input[@type='password']",

            # 6. Legacy/Shadow DOM selectors (Kept just in case)
            'document.querySelector("#privacy-web-auth").shadowRoot.querySelector("input[type=\'password\']")',
            'document.querySelector("#privacy-web-auth").shadowRoot.querySelector("#floating-input-sekcpj1")'
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector (handles shadow DOM)
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
                            // Silent fail
                        }}
                        return false;
                    }}''', PASSWORD_TEXT)
                    if input_inserted:
                        print("✓ Password inserted successfully with JS/Shadow selector")
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

                            xpath_elements.first.scroll_into_view_if_needed()
                            xpath_elements.first.click()
                            xpath_elements.first.fill(PASSWORD_TEXT)
                            print(f"✓ Password inserted successfully with XPath: {selector}")
                            return True
                        except Exception as e:
                            print(f"XPath insert failed: {str(e)}")

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

                            css_elements.first.scroll_into_view_if_needed()
                            css_elements.first.click()
                            css_elements.first.fill(PASSWORD_TEXT)
                            print(f"✓ Password inserted successfully with CSS selector: {selector}")
                            return True
                        except Exception as e:
                            print(f"CSS selector insert failed: {str(e)}")

            except Exception as e:
                continue

        # Fallback JavaScript approach with comprehensive search (Updated for #input-16)
        print("Trying JavaScript fallback approach for password input...")
        fallback_inserted = page.evaluate('''(text) => {
            // 1. Try Direct ID first
            const directInput = document.getElementById('input-16');
            if (directInput) {
                directInput.scrollIntoView({behavior: 'smooth', block: 'center'});
                directInput.focus();
                directInput.value = text;
                directInput.dispatchEvent(new Event('input', { bubbles: true }));
                directInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }

            // 2. Try Standard Name/Type attributes
            // Note: We check name="password" first as it's safer than type="text"
            const standardInput = document.querySelector('input[name="password"]') ||
                                  document.querySelector('input[type="password"]');

            if (standardInput) {
                standardInput.scrollIntoView({behavior: 'smooth', block: 'center'});
                standardInput.focus();
                standardInput.value = text;
                standardInput.dispatchEvent(new Event('input', { bubbles: true }));
                standardInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }

            // 3. Try Shadow DOM (Legacy support)
            const shadowHost = document.querySelector("#privacy-web-auth");
            if (shadowHost && shadowHost.shadowRoot) {
                const shadowInput = shadowHost.shadowRoot.querySelector('input[type="password"]');
                if (shadowInput) {
                    shadowInput.value = text;
                    shadowInput.dispatchEvent(new Event('input', { bubbles: true }));
                    return true;
                }
            }

            return false;
        }''', PASSWORD_TEXT)

        if fallback_inserted:
            print("✓ Password inserted successfully using JavaScript fallback!")
            return True

        print("❌ Could not find or insert into password input using any method.")
        return False

    except Exception as e:
        print(f"❌ Error in insert_password: {str(e)}")
        return False

def click_on_login_button(page):
    """
    Attempt to find and click the 'Log in' button.
    Strategies: Custom attributes, text content, and standard submit types.
    """
    try:
        # List of selectors to try
        selectors = [
            # 1. Custom attribute (Very specific and likely stable)
            "button[at-attr='submit']",

            # 2. Text content (Playwright specific, very robust)
            "button:has-text('Log in')",

            # 3. Standard Submit Button
            "button[type='submit']",

            # 4. CSS Classes (Combination of classes)
            "button.g-btn.m-rounded.m-block",

            # 5. XPath by text
            "//button[contains(text(), 'Log in')]",

            # 6. XPath by type
            "//button[@type='submit']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                # Check if element exists and is visible
                if page.locator(selector).count() > 0:
                    btn = page.locator(selector).first
                    if btn.is_visible():
                        print(f"✓ Found login button with selector: {selector}")

                        # Scroll and Click
                        btn.scroll_into_view_if_needed()

                        # Optional: Force wait for button to be enabled
                        if btn.is_enabled():
                            btn.click()
                            print("✓ Clicked login button successfully.")
                            return True
                        else:
                            print(f"⚠ Button found ({selector}) but is disabled.")
            except Exception as e:
                # Ignore minor errors during search
                continue

        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for login button...")
        fallback_clicked = page.evaluate('''() => {
            // 1. Try by custom attribute
            const btnAttr = document.querySelector("button[at-attr='submit']");
            if (btnAttr) {
                btnAttr.click();
                return true;
            }

            // 2. Try by text content
            const buttons = Array.from(document.querySelectorAll('button'));
            const loginBtn = buttons.find(b => b.innerText.includes('Log in'));
            if (loginBtn) {
                loginBtn.click();
                return true;
            }

            // 3. Try by type submit
            const btnSubmit = document.querySelector("button[type='submit']");
            if (btnSubmit) {
                btnSubmit.click();
                return true;
            }

            return false;
        }''')

        if fallback_clicked:
            print("✓ Login button clicked successfully using JavaScript fallback!")
            return True

        print("❌ Could not find or click the login button using any method.")
        return False

    except Exception as e:
        print(f"❌ Error in click_on_login_button: {str(e)}")
        return False

def click_to_send_msg(page):
    """
    Attempt to find and click the 'Nova mensagem' button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#content > div.b-chats > div > div.b-chats__conversations-content.m-empty-chat > div > div.conversations-start__content > a",
            # Alternative CSS selectors
            "a[href='/my/chats/send']",
            "a.g-btn.m-rounded.m-lg.m-block.m-fix-width.m-mall-auto",
            # JavaScript path
            "document.querySelector(\"#content > div.b-chats > div > div.b-chats__conversations-content.m-empty-chat > div > div.conversations-start__content > a\")",
            # XPath
            "//*[@id=\"content\"]/div[1]/div/div[2]/div/div[2]/a",
            # Alternative XPaths
            "//a[@href='/my/chats/send']",
            "//a[contains(@class, 'g-btn') and contains(text(), 'Nova mensagem')]",
            "//a[text()=' Nova mensagem ']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Send Message button selector: {selector}")
                
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
                        print(f"Successfully clicked Send Message button with JS selector")
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
                            print(f"Successfully clicked Send Message button with XPath")
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
                            print(f"Successfully clicked Send Message button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Send Message button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Send Message button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding anchor elements with message-related attributes or classes
            const anchorSelectors = [
                'a[href*="/chats/send"]',
                'a[href*="/chats"]',
                'a.g-btn',
                'a.m-rounded',
                'a.m-block'
            ];
            
            for (const selector of anchorSelectors) {
                const anchors = document.querySelectorAll(selector);
                for (const anchor of anchors) {
                    if (anchor && (anchor.textContent.includes('Nova mensagem') || 
                                   anchor.textContent.includes('mensagem') ||
                                   anchor.textContent.includes('Nova'))) {
                        anchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                        anchor.click();
                        return true;
                    }
                }
            }
            
            // Try finding by text content
            const allAnchors = document.querySelectorAll('a');
            for (const anchor of allAnchors) {
                if (anchor.textContent.includes('Nova mensagem') || 
                    anchor.textContent.trim() === 'Nova mensagem') {
                    anchor.scrollIntoView({behavior: 'smooth', block: 'center'});
                    anchor.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Send Message button using JavaScript fallback!")
            return True
        
        print("Could not find or click Send Message button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_send_msg: {str(e)}")
        return False

def clean_media_set(page):
    """
    Clicks all visible delete buttons in the media preview area until none remain.
    Uses the exact button you provided.
    """
    print("Starting media cleanup...")

    selector = 'button.b-dropzone__preview__delete[aria-label="Excluir"]'

    while True:
        # Get first matching visible button
        delete_btn = page.locator(selector).first

        # Quick check if it exists and is visible
        if not delete_btn.is_visible(timeout=400):  # short timeout in ms
            break

        try:
            delete_btn.scroll_into_view_if_needed()
            time.sleep(0.1)              # small delay for stability

            delete_btn.click(delay=50)   # slight human-like delay
            time.sleep(0.4)              # wait for removal / UI update

            print("Deleted one media item")

        except Exception as e:
            print(f"Stopped during click: {e}")
            break

    print("Cleanup finished.")

def clean_price(page):
    """
    Repeatedly finds and clicks price preview delete buttons until none are left.
    
    Target: <button class="b-dropzone__preview__delete" title="Excluir" at-attr="delete_msg_price">
              <svg data-icon-name="icon-close">...</svg>
            </button>
    """
    print("Starting price cleanup...")

    # Most reliable selector using the unique attributes + class + svg
    selector = 'button.b-dropzone__preview__delete[title="Excluir"][at-attr="delete_msg_price"] svg[data-icon-name="icon-close"]'

    while True:
        # Locate the close icon inside the target button
        close_icon = page.locator(selector).first

        # If no matching icon exists anymore → we're done
        if close_icon.count() == 0:
            break

        # Quick visibility check (short timeout in ms)
        try:
            if not close_icon.is_visible(timeout=500):
                break
        except:
            break

        try:
            # Click the parent button (more reliable than clicking the svg directly)
            delete_button = close_icon.locator("..")   # go up to the <button>

            delete_button.scroll_into_view_if_needed()
            time.sleep(0.12)               # tiny stability delay

            delete_button.click(delay=70)  # slight human-like delay
            time.sleep(0.4)                # wait for DOM update / removal / animation

            print("Clicked one price delete button")

        except Exception as e:
            print(f"Error during price delete click: {e}")
            time.sleep(0.6)  # give it a bit more time before next attempt
            continue           # try again instead of breaking — more robust

    print("Cleanup finished.")

def click_on_non_creators_list(page):
    """
    Attempt to find the 'Non-creators 💓' list. 
    If already checked, does nothing. If not, clicks it.
    """
    try:
        # Define the primary selector that targets the specific list by its text
        # This selector finds the label that contains the name "Non-creators"
        label_selector = "label.b-rows-lists__item:has-text('Non-creators')"
        
        # Locate the checkbox inside that label
        checkbox = page.locator(label_selector).locator("input[type='checkbox']")

        if checkbox.count() > 0:
            # Check if it is already checked
            if checkbox.is_checked():
                print("Non-creators list is already checked. Skipping click.")
                return True
            else:
                print("Non-creators list not checked. Clicking now...")
                # Click the label to toggle the checkbox
                page.locator(label_selector).click()
                return True

        # --- Fallback for dynamic/complex selectors if the above fails ---
        fallback_js = '''() => {
            const labels = document.querySelectorAll('label.b-rows-lists__item');
            for (const label of labels) {
                if (label.textContent.includes('Non-creators')) {
                    const input = label.querySelector('input[type="checkbox"]');
                    if (input && input.checked) {
                        return "already_checked";
                    }
                    label.click();
                    return "clicked";
                }
            }
            return "not_found";
        }'''
        
        result = page.evaluate(fallback_js)
        if result in ["already_checked", "clicked"]:
            return True
            
        return False

    except Exception as e:
        print(f"Error in click_on_non_creators_list: {str(e)}")
        return False

def click_on_paid_users_list(page):
    """
    Attempt to find the 'Paid Users' ($) list. 
    If already checked, does nothing. If not, clicks it.
    """
    try:
        # Primary selector targeting the label that specifically contains the "$" text
        label_selector = "label.b-rows-lists__item:has-text(' $ ')"
        
        # Locate the specific checkbox inside that label
        checkbox = page.locator(label_selector).locator("input[type='checkbox']")

        if checkbox.count() > 0:
            # Check if it is already checked
            if checkbox.is_checked():
                print("Paid Users ($) list is already checked. Skipping click.")
                return True
            else:
                print("Paid Users ($) list not checked. Clicking now...")
                # Click the label to toggle the checkbox
                page.locator(label_selector).click()
                return True

        # --- Fallback JavaScript approach if simple selectors fail ---
        fallback_js = '''() => {
            const labels = document.querySelectorAll('label.b-rows-lists__item');
            for (const label of labels) {
                const name = label.querySelector('.b-rows-lists__item__name');
                if (name && name.textContent.trim() === '$') {
                    const input = label.querySelector('input[type="checkbox"]');
                    if (input && input.checked) {
                        return "already_checked";
                    }
                    label.click();
                    return "clicked";
                }
            }
            return "not_found";
        }'''
        
        result = page.evaluate(fallback_js)
        if result in ["already_checked", "clicked"]:
            return True
            
        return False

    except Exception as e:
        print(f"Error in click_on_paid_users_list: {str(e)}")
        return False

CSV_FILE = "G:\\Meu Drive\\Onlyfans\\bundles_caption.csv"      # Name of your CSV file containing the captions
INDEX_FILE = "G:\\Meu Drive\\Onlyfans\\caption_index.txt"      # File that stores the current index between script runs

def get_next_caption():

#Load all captions from the CSV (only once, or if the file changes)
    if not hasattr(get_next_caption, "captions"):
        if not os.path.exists(CSV_FILE):
            raise FileNotFoundError(f"File not found: {CSV_FILE}")
        
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Extract the text, remove surrounding quotes and whitespace
            get_next_caption.captions = [row[0].strip().strip('"') for row in reader if row]
        
        print(f"Loaded {len(get_next_caption.captions)} captions from the file.")

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

    print(f"Using caption #{current_index + 1}/{total}: {caption[:50]}...")
    return caption

def get_current_bundle_name():
    """
    Reads the current caption index from the index file and returns it formatted as 'BundleX'.
    Example: if caption_index.txt contains '6' → returns 'Bundle6'
    """
    INDEX_FILE = r"G:\Meu Drive\Onlyfans\\caption_index.txt"
    
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
    print(f"Current bundle name: {bundle_name}")
    return bundle_name

def click_and_insert_caption_in_the_input_field(page, caption_to_paste):
    """
    Finds the input field, clears existing text, and inserts the new caption.
    """
    try:
        # We prioritize the most reliable selector for the text editor
        selector = "div[contenteditable='true'][role='textbox'], div.tiptap.ProseMirror"
        
        target = page.locator(selector).first
        
        if target.count() > 0:
            # 1. Scroll and Focus
            target.scroll_into_view_if_needed()
            target.click()
            time.sleep(1)
            
            # 2. Clear existing information
            # Using hotkeys is the most reliable way for 'contenteditable' divs
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('backspace', presses=50, interval=0.01) # Safety clear
            
            # 3. Insert new caption
            pyperclip.copy(caption_to_paste)
            pyautogui.hotkey('ctrl', 'v')
            
            print("Successfully cleared and inserted caption.")
            return True
            
        # Fallback JavaScript for deep clearing if locator fails
        fallback_js = f'''(caption) => {{
            const el = document.querySelector('div[contenteditable="true"]');
            if (el) {{
                el.focus();
                el.innerHTML = ""; // Clear via JS
                return true;
            }}
            return false;
        }}'''
        
        if page.evaluate(fallback_js, caption_to_paste):
            pyautogui.hotkey('ctrl', 'v')
            return True

        return False

    except Exception as e:
        print(f"Error in click_and_insert_caption: {str(e)}")
        return False

def click_on_send_btn(page):
    """
    Attempt to find and click the 'Send' (ENVIAR) button using multiple approaches.
    """
    try:
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post__sticky-panel > div > button",

            # Attribute-based CSS
            "button[at-attr='send_btn']",
            "button.b-chat__btn-submit",

            # JavaScript selector
            "document.querySelector(\"#make_post_form > div.b-make-post__sticky-panel > div > button\")",

            # XPath selectors
            "//*[@id='make_post_form']/div[3]/div/button",
            "//button[@at-attr='send_btn']",
            "//button[contains(@class,'b-chat__btn-submit')]",
            "//button[normalize-space()='ENVIAR']"
        ]

        for selector in selectors:
            try:
                # JavaScript selector
                if selector.startswith("document.querySelector"):
                    clicked = page.evaluate(f'''() => {{
                        const btn = {selector};
                        if (btn) {{
                            btn.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            btn.click();
                            return true;
                        }}
                        return false;
                    }}''')

                    if clicked:
                        return True

                # XPath selector
                elif selector.startswith('/'):
                    locator = page.locator(f"xpath={selector}")
                    if locator.count() > 0:
                        page.evaluate(f'''(xpath) => {{
                            const el = document.evaluate(
                                xpath,
                                document,
                                null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE,
                                null
                            ).singleNodeValue;
                            if (el) {{
                                el.style.opacity = '1';
                                el.style.visibility = 'visible';
                                el.style.display = 'block';
                            }}
                        }}''', selector)

                        locator.first.scroll_into_view_if_needed()
                        locator.first.click(force=True)
                        return True

                # CSS selector
                else:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        page.evaluate(f'''(selector) => {{
                            const el = document.querySelector(selector);
                            if (el) {{
                                el.style.opacity = '1';
                                el.style.visibility = 'visible';
                                el.style.display = 'block';
                            }}
                        }}''', selector)

                        locator.first.scroll_into_view_if_needed()
                        locator.first.click(force=True)
                        return True

            except Exception as e:
                print(f"Send button selector failed ({selector}): {str(e)}")
                continue

        # JavaScript fallback (last resort)
        fallback_clicked = page.evaluate('''() => {
            const candidates = document.querySelectorAll("button");
            for (const btn of candidates) {
                if (
                    btn.getAttribute("at-attr") === "send_btn" ||
                    btn.textContent.trim().toUpperCase() === "ENVIAR"
                ) {
                    btn.scrollIntoView({ behavior: "smooth", block: "center" });
                    btn.click();
                    return true;
                }
            }
            return false;
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click Send button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_send_btn: {str(e)}")
        return False

def click_on_vault_btn(page):
    """
    Attempt to find and click the vault button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(6) > svg",
            # Alternative CSS selectors
            "svg[data-icon-name='icon-vault']",
            "svg[href='#icon-vault']",
            "button:nth-child(6) > svg",
            "button[class*='b-make-post__actions__btns'] > svg",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(6) > svg\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[2]/div/div[1]/button[6]/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-vault']",
            "//svg[@href='#icon-vault']",
            "//button[contains(@class, 'b-make-post__actions__btns')]/svg",
            "//div[contains(@class, 'b-make-post__actions__btns')]//button[6]/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying vault button selector: {selector}")
                
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
                        #print(f"Successfully clicked vault button with JS selector")
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
                            #print(f"Successfully clicked vault button with XPath")
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
                            #print(f"Successfully clicked vault button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with vault button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for vault button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding SVG elements with vault icon
            const svgSelectors = [
                'svg[data-icon-name="icon-vault"]',
                'svg[href="#icon-vault"]',
                'svg use[href="#icon-vault"]'
            ];
            
            for (const selector of svgSelectors) {
                const svgs = document.querySelectorAll(selector);
                for (const svg of svgs) {
                    if (svg) {
                        // Click the SVG or find its parent button
                        const parentButton = svg.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        } else {
                            svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                            svg.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding buttons in the actions panel
            const actionPanel = document.querySelector('.b-make-post__actions__btns');
            if (actionPanel) {
                const buttons = actionPanel.querySelectorAll('button');
                // Try the 6th button specifically
                if (buttons.length >= 6) {
                    const sixthButton = buttons[5];
                    const hasVaultIcon = sixthButton.querySelector('svg[data-icon-name="icon-vault"]') || 
                                        sixthButton.querySelector('svg[href="#icon-vault"]');
                    if (hasVaultIcon) {
                        sixthButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        sixthButton.click();
                        return true;
                    }
                }
                
                // Try any button with vault icon
                for (const button of buttons) {
                    const hasVaultIcon = button.querySelector('svg[data-icon-name="icon-vault"]');
                    if (hasVaultIcon) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding within the make_post_form specifically
            const form = document.getElementById('make_post_form');
            if (form) {
                const vaultButtons = form.querySelectorAll('button');
                for (const button of vaultButtons) {
                    const hasVaultIcon = button.querySelector('svg[data-icon-name="icon-vault"]');
                    if (hasVaultIcon) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked vault button using JavaScript fallback!")
            return True
        
        print("Could not find or click vault button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_vault_btn: {str(e)}")
        return False

def click_to_search_bundle(page):
    """
    Attempt to find and click the search bundle button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ModalMediaVault___BV_modal_body_ > div > div.l-sidebar-column.d-flex.flex-column.m-l-side.g-overflow-hidden > div.g-page__header.mb-0.m-reset-sides-gaps.m-header-height-md.modal-header > div > button > svg",
            # Alternative CSS selectors
            "svg[data-icon-name='icon-search']",
            "svg[href='#icon-search']",
            "button > svg[data-icon-name='icon-search']",
            ".modal-header button > svg",
            ".g-page__header button > svg",
            # JavaScript path
            "document.querySelector(\"#ModalMediaVault___BV_modal_body_ > div > div.l-sidebar-column.d-flex.flex-column.m-l-side.g-overflow-hidden > div.g-page__header.mb-0.m-reset-sides-gaps.m-header-height-md.modal-header > div > button > svg\")",
            # XPath
            "//*[@id=\"ModalMediaVault___BV_modal_body_\"]/div/div[1]/div[1]/div/button/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-search']",
            "//svg[@href='#icon-search']",
            "//button/svg[@data-icon-name='icon-search']",
            "//div[contains(@class, 'modal-header')]//button/svg",
            "//div[contains(@class, 'g-page__header')]//button/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying search bundle button selector: {selector}")
                
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
                        #print(f"Successfully clicked search bundle button with JS selector")
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
                            #print(f"Successfully clicked search bundle button with XPath")
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
                            #print(f"Successfully clicked search bundle button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with search bundle button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for search bundle button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding SVG elements with search icon
            const svgSelectors = [
                'svg[data-icon-name="icon-search"]',
                'svg[href="#icon-search"]',
                'svg use[href="#icon-search"]'
            ];
            
            for (const selector of svgSelectors) {
                const svgs = document.querySelectorAll(selector);
                for (const svg of svgs) {
                    if (svg) {
                        // Click the SVG or find its parent button
                        const parentButton = svg.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        } else {
                            svg.scrollIntoView({behavior: 'smooth', block: 'center'});
                            svg.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding within the modal vault specifically
            const modalVault = document.getElementById('ModalMediaVault___BV_modal_body_');
            if (modalVault) {
                // Look for search buttons in the modal header
                const modalHeaders = modalVault.querySelectorAll('.modal-header, .g-page__header');
                for (const header of modalHeaders) {
                    const searchButtons = header.querySelectorAll('button');
                    for (const button of searchButtons) {
                        const hasSearchIcon = button.querySelector('svg[data-icon-name="icon-search"]') || 
                                            button.querySelector('svg[href="#icon-search"]');
                        if (hasSearchIcon) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                    }
                }
                
                // Also check the sidebar column
                const sidebarColumns = modalVault.querySelectorAll('.l-sidebar-column');
                for (const sidebar of sidebarColumns) {
                    const searchButtons = sidebar.querySelectorAll('button');
                    for (const button of searchButtons) {
                        const hasSearchIcon = button.querySelector('svg[data-icon-name="icon-search"]');
                        if (hasSearchIcon) {
                            button.scrollIntoView({behavior: 'smooth', block: 'center'});
                            button.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding any search button in modal contexts
            const modals = document.querySelectorAll('.modal-content, [class*="modal"]');
            for (const modal of modals) {
                const searchButtons = modal.querySelectorAll('button');
                for (const button of searchButtons) {
                    const hasSearchIcon = button.querySelector('svg[data-icon-name="icon-search"]');
                    if (hasSearchIcon) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked search bundle button using JavaScript fallback!")
            return True
        
        print("Could not find or click search bundle button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_search_bundle: {str(e)}")
        return False

def click_to_search_bundle_and_type(page, text_to_search):
    """
    Finds the search button, clicks it, clears the field, and pastes the bundle name.
    """
    try:
        # Step 1: Click the Search Button
        # We use a simplified version of your selector list for the initial click
        selector = "button > svg[data-icon-name='icon-search'], .modal-header button"
        target = page.locator(selector).first
        
        if target.count() > 0:
            target.scroll_into_view_if_needed()
            target.click()
            time.sleep(1)
            
            # Step 2: Clear and Type/Paste
            # Using the same hotkey approach as the caption function
            pyperclip.copy(text_to_search)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('backspace')
            
            # Paste the bundle name and submit
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            
            print(f"Successfully searched for bundle: {text_to_search}")
            return True
            
        # Fallback JavaScript if the initial click/locator fails
        fallback_js = '''() => {
            const btn = document.querySelector('button[class*="search"], .modal-header button');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        }'''
        
        if page.evaluate(fallback_js):
            time.sleep(1)
            pyperclip.copy(text_to_search)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            return True

        return False

    except Exception as e:
        print(f"Error in click_to_search_bundle_and_type: {str(e)}")
        return False

def click_on_set_price_icon(page):
    """
    Attempt to find and click the 'Set Price' icon using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(8) > svg",
            # Alternative CSS selectors
            "svg.g-icon[data-icon-name='icon-price']",
            "svg use[href='#icon-price']",
            "svg use[xlink\\:href='#icon-price']",
            ".b-make-post__actions__btns button:nth-child(8) svg",
            ".b-make-post__sticky-panel svg[data-icon-name='icon-price']",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(8) > svg\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[2]/div/div[1]/button[8]/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-price']",
            "//svg[@class='g-icon' and @data-icon-name='icon-price']",
            "//use[@href='#icon-price']/parent::svg",
            "//use[@xlink:href='#icon-price']/parent::svg",
            "//div[contains(@class, 'b-make-post__actions__btns')]/button[8]/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Set Price icon selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    icon_clicked = page.evaluate(f'''() => {{
                        const svg = {selector};
                        if (svg) {{
                            // Click the parent button instead of the SVG
                            const parentButton = svg.closest('button');
                            if (parentButton) {{
                                parentButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                parentButton.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    
                    if icon_clicked:
                        print(f"Successfully clicked Set Price icon with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"xpath={selector}/ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Set Price icon with XPath")
                                return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            css_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"{selector} >> xpath=./ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Set Price icon with CSS selector")
                                return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Set Price icon selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Set Price icon...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the price icon by various attributes
            const iconSelectors = [
                'svg[data-icon-name="icon-price"]',
                'svg.g-icon use[href="#icon-price"]',
                'svg use[xlink\\:href="#icon-price"]'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        const parentButton = icon.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by button position in actions panel
            const actionButtons = document.querySelectorAll('.b-make-post__actions__btns button');
            if (actionButtons.length >= 8) {
                // Assuming 8th button is the price button (0-indexed 7)
                actionButtons[7].scrollIntoView({behavior: 'smooth', block: 'center'});
                actionButtons[7].click();
                return true;
            }
            
            // Try finding any button containing price icon
            const allButtons = document.querySelectorAll('.b-make-post__sticky-panel button');
            for (const button of allButtons) {
                const priceIcon = button.querySelector('svg[data-icon-name="icon-price"]');
                if (priceIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding by icon name in any button
            const buttonsWithIcons = document.querySelectorAll('button svg[data-icon-name]');
            for (const icon of buttonsWithIcons) {
                if (icon.getAttribute('data-icon-name') === 'icon-price') {
                    const parentButton = icon.closest('button');
                    if (parentButton) {
                        parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parentButton.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Set Price icon using JavaScript fallback!")
            return True
        
        print("Could not find or click Set Price icon using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_set_price_icon: {str(e)}")
        return False

def click_to_save_bundles_price(page):
    """
    Attempt to find and click the 'Salvar' button in the price modal using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ModalPostPrice___BV_modal_footer_ > button:nth-child(2)",
            # Alternative CSS selectors
            "button.g-btn.m-flat.m-btn-gaps.m-reset-width",
            "button[type='button'].g-btn.m-flat.m-btn-gaps.m-reset-width",
            "button:has-text('Salvar')",
            # JavaScript path
            "document.querySelector(\"#ModalPostPrice___BV_modal_footer_ > button:nth-child(2)\")",
            "document.querySelector(\"button.g-btn.m-flat.m-btn-gaps.m-reset-width\")",
            # XPath
            "//*[@id=\"ModalPostPrice___BV_modal_footer_\"]/button[2]",
            "//button[@class='g-btn m-flat m-btn-gaps m-reset-width']",
            "//button[contains(@class, 'g-btn') and contains(text(), 'Salvar')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Save button selector: {selector}")
                
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
                        #print(f"Successfully clicked Save button with JS selector")
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
                            #print(f"Successfully clicked Save button with XPath")
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
                            #print(f"Successfully clicked Save button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Save button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Save button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with save-related attributes or classes
            const buttonSelectors = [
                'button.g-btn.m-flat.m-btn-gaps.m-reset-width',
                'button[type="button"]',
                'button:contains("Salvar")',
                '#ModalPostPrice___BV_modal_footer_ button'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && (button.textContent.includes('Salvar') || button.classList.contains('m-flat'))) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by modal footer context
            const modalFooter = document.querySelector('#ModalPostPrice___BV_modal_footer_');
            if (modalFooter) {
                const buttons = modalFooter.querySelectorAll('button');
                for (const button of buttons) {
                    if (button.textContent.includes('Salvar')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Save button using JavaScript fallback!")
            return True
        
        print("Could not find or click Save button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_save_bundles_price: {str(e)}")
        return False

def click_on_select_all_icon(page):
    """
    Attempt to find and click the 'Select All' icon using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ModalMediaVault___BV_modal_body_ > div > div.l-main-content.m-r-side.h-100 > div > div > div.g-page__header.g-negative-sides-gaps.m-nowrap.mb-0.m-real-sticky.js-sticky-header.m-header-height-md > div > button:nth-child(1) > svg > use",
            # Alternative CSS selectors targeting the use element
            "use[href='#icon-all']",
            "use[xlink\\:href='#icon-all']",
            "use[href*='icon-all']",
            # Target the button containing the icon
            "#ModalMediaVault___BV_modal_body_ button:first-child use",
            ".g-page__header button:first-child use",
            # JavaScript path
            "document.querySelector(\"#ModalMediaVault___BV_modal_body_ > div > div.l-main-content.m-r-side.h-100 > div > div > div.g-page__header.g-negative-sides-gaps.m-nowrap.mb-0.m-real-sticky.js-sticky-header.m-header-height-md > div > button:nth-child(1) > svg > use\")",
            # XPath
            "//*[@id=\"ModalMediaVault___BV_modal_body_\"]/div/div[2]/div/div/div[1]/div/button[1]/svg/use",
            # Alternative XPaths
            "//use[@href='#icon-all']",
            "//use[@xlink:href='#icon-all']",
            "//button[1]//use[contains(@href, 'icon-all')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Select All icon selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    icon_clicked = page.evaluate(f'''() => {{
                        const icon = {selector};
                        if (icon) {{
                            // Click the parent button instead of the use element
                            const parentButton = icon.closest('button');
                            if (parentButton) {{
                                parentButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                parentButton.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    
                    if icon_clicked:
                        print(f"Successfully clicked Select All icon with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the use element
                            parent_button = page.locator(f"xpath={selector}/ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Select All icon with XPath")
                                return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            css_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the use element
                            parent_button = page.locator(f"{selector} >> xpath=./ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Select All icon with CSS selector")
                                return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Select All icon selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Select All icon...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the icon by href attributes
            const iconSelectors = [
                'use[href="#icon-all"]',
                'use[xlink\\:href="#icon-all"]',
                'use[href*="icon-all"]'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        const parentButton = icon.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by button position in header
            const headerButtons = document.querySelectorAll('.g-page__header button');
            if (headerButtons.length > 0) {
                // Assuming first button is select all
                headerButtons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                headerButtons[0].click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Select All icon using JavaScript fallback!")
            return True
        
        print("Could not find or click Select All icon using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_select_all_icon: {str(e)}")
        return False

def click_to_accept_selection(page):
    """
    Attempt to find and click the 'Adicionar' (Add/Accept) button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ModalMediaVault___BV_modal_body_ > div > div.l-main-content.m-r-side.h-100 > div > div > div.b-placeholder-item-selected.m-absolute-position.ml-0.mr-0 > div > div > div.b-row-selected__controls > button",
            # Alternative CSS selectors
            "button.g-btn.m-reset-width.m-rounded.m-sm",
            ".b-row-selected__controls button",
            ".b-placeholder-item-selected button",
            "button:has-text('Adicionar')",
            # JavaScript path
            "document.querySelector(\"#ModalMediaVault___BV_modal_body_ > div > div.l-main-content.m-r-side.h-100 > div > div > div.b-placeholder-item-selected.m-absolute-position.ml-0.mr-0 > div > div > div.b-row-selected__controls > button\")",
            # XPath
            "//*[@id=\"ModalMediaVault___BV_modal_body_\"]/div/div[2]/div/div/div[5]/div/div/div[2]/button",
            # Alternative XPaths
            "//button[contains(@class, 'g-btn') and contains(@class, 'm-reset-width')]",
            "//button[text()='Adicionar']",
            "//div[contains(@class, 'b-row-selected__controls')]/button",
            "//div[contains(@class, 'b-placeholder-item-selected')]//button"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Accept Selection button selector: {selector}")
                
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
                        print(f"Successfully clicked Accept Selection button with JS selector")
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
                            print(f"Successfully clicked Accept Selection button with XPath")
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
                            print(f"Successfully clicked Accept Selection button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Accept Selection button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Accept Selection button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with specific classes and text
            const buttonSelectors = [
                'button.g-btn.m-reset-width.m-rounded.m-sm',
                '.b-row-selected__controls button',
                '.b-placeholder-item-selected button'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && button.textContent.includes('Adicionar')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by text content
            const allButtons = document.querySelectorAll('button');
            for (const button of allButtons) {
                if (button.textContent.trim() === 'Adicionar') {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding any button in the selection controls area
            const selectionControls = document.querySelector('.b-row-selected__controls');
            if (selectionControls) {
                const controlButton = selectionControls.querySelector('button');
                if (controlButton) {
                    controlButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    controlButton.click();
                    return true;
                }
            }
            
            // Try finding any button in the placeholder selected area
            const placeholderSelected = document.querySelector('.b-placeholder-item-selected');
            if (placeholderSelected) {
                const placeholderButton = placeholderSelected.querySelector('button');
                if (placeholderButton) {
                    placeholderButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    placeholderButton.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Accept Selection button using JavaScript fallback!")
            return True
        
        print("Could not find or click Accept Selection button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_accept_selection: {str(e)}")
        return False

def click_on_hell_paradise_creator(page):
    """
    Attempt to find and click the 'Hell 😈 Paradise 👼🏼' creator element using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ReleaseFormsModal___BV_modal_body_ > div > div.b-release-form__docs.m-modal-height.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar > div > label:nth-child(1) > div.b-rows-lists__item__text.m-complex-structure > div.b-rows-lists__item__name.g-text-ellipsis.pb-0",
            # Alternative CSS selectors
            "div.b-rows-lists__item__name.g-text-ellipsis.pb-0",
            "div[at-attr].b-rows-lists__item__name.g-text-ellipsis.pb-0",
            "div:has-text('Hell 😈 Paradise 👼🏼')",
            # JavaScript path
            "document.querySelector(\"#ReleaseFormsModal___BV_modal_body_ > div > div.b-release-form__docs.m-modal-height.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar > div > label:nth-child(1) > div.b-rows-lists__item__text.m-complex-structure > div.b-rows-lists__item__name.g-text-ellipsis.pb-0\")",
            "document.querySelector(\"div.b-rows-lists__item__name.g-text-ellipsis.pb-0\")",
            # XPath
            "//*[@id=\"ReleaseFormsModal___BV_modal_body_\"]/div/div[3]/div/label[1]/div[2]/div[1]",
            "//div[@class='b-rows-lists__item__name g-text-ellipsis pb-0']",
            "//div[contains(@class, 'b-rows-lists__item__name') and contains(text(), 'Hell 😈 Paradise 👼🏼')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Hell Paradise creator selector: {selector}")
                
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
                        #print(f"Successfully clicked Hell Paradise creator with JS selector")
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
                            #print(f"Successfully clicked Hell Paradise creator with XPath")
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
                            #print(f"Successfully clicked Hell Paradise creator with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Hell Paradise creator selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Hell Paradise creator...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding elements with Hell Paradise text
            const textSelectors = [
                'div.b-rows-lists__item__name',
                'div.g-text-ellipsis.pb-0',
                'div[at-attr]',
                '.b-rows-lists__item__text.m-complex-structure div'
            ];
            
            for (const selector of textSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.textContent.includes('Hell 😈 Paradise 👼🏼')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding within modal context
            const modalBody = document.querySelector('#ReleaseFormsModal___BV_modal_body_');
            if (modalBody) {
                const elements = modalBody.querySelectorAll('div.b-rows-lists__item__name');
                for (const element of elements) {
                    if (element.textContent.includes('Hell 😈 Paradise 👼🏼')) {
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        element.click();
                        return true;
                    }
                }
            }
            
            // Try finding by parent label structure
            const labels = document.querySelectorAll('label');
            for (const label of labels) {
                const nameElement = label.querySelector('div.b-rows-lists__item__name');
                if (nameElement && nameElement.textContent.includes('Hell 😈 Paradise 👼🏼')) {
                    nameElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                    nameElement.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Hell Paradise creator using JavaScript fallback!")
            return True
        
        print("Could not find or click Hell Paradise creator using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_on_hell_paradise_creator: {str(e)}")
        return False

def click_to_save_scheduled_msg(page):
    """
    Attempt to find and click the 'Salvar' button for scheduled messages using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post__sticky-panel > div > button",
            # Alternative CSS selectors
            "button.g-btn.m-rounded.b-chat__btn-submit",
            "button[data-v-360fe490].g-btn.m-rounded.b-chat__btn-submit",
            "button[at-attr='send_btn']",
            "button:has-text('Salvar')",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post__sticky-panel > div > button\")",
            "document.querySelector(\"button.g-btn.m-rounded.b-chat__btn-submit\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[2]/div/button",
            "//button[@class='g-btn m-rounded b-chat__btn-submit']",
            "//button[@at-attr='send_btn']",
            "//button[contains(@class, 'b-chat__btn-submit') and contains(text(), 'Salvar')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Save scheduled message button selector: {selector}")
                
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
                        #print(f"Successfully clicked Save scheduled message button with JS selector")
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
                            #print(f"Successfully clicked Save scheduled message button with XPath")
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
                            #print(f"Successfully clicked Save scheduled message button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Save scheduled message button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Save scheduled message button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with save-related attributes or classes
            const buttonSelectors = [
                'button.g-btn.m-rounded.b-chat__btn-submit',
                'button[at-attr="send_btn"]',
                'button[type="button"]',
                'button:contains("Salvar")',
                '#make_post_form button'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && (button.textContent.includes('Salvar') || button.getAttribute('at-attr') === 'send_btn')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding within sticky panel context
            const stickyPanel = document.querySelector('#make_post_form > div.b-make-post__sticky-panel');
            if (stickyPanel) {
                const buttons = stickyPanel.querySelectorAll('button');
                for (const button of buttons) {
                    if (button.textContent.includes('Salvar')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by data attributes
            const dataAttributeButtons = document.querySelectorAll('button[data-v-360fe490]');
            for (const button of dataAttributeButtons) {
                if (button.textContent.includes('Salvar') && button.classList.contains('b-chat__btn-submit')) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Save scheduled message button using JavaScript fallback!")
            return True
        
        print("Could not find or click Save scheduled message button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_save_scheduled_msg: {str(e)}")
        return False

def click_to_set_bundles_cover(page):
    """
    Attempt to find and click the 'Set Bundles Cover' button (left arrow icon) using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll > div.d-flex.align-items-start.w-100 > div.b-make-post__media-slider.m-free.m-empty > button > span > svg",
            # Alternative CSS selectors
            "svg[data-icon-name='icon-arrow-left']",
            "svg.g-icon use[href='#icon-arrow-left']",
            "svg use[xlink\\:href='#icon-arrow-left']",
            ".b-make-post__media-slider button svg",
            ".b-make-post__media-wrapper svg[data-icon-name='icon-arrow-left']",
            ".b-dragscroll button:first-child svg",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll > div.d-flex.align-items-start.w-100 > div.b-make-post__media-slider.m-free.m-empty > button > span > svg\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[1]/div/div[2]/div[1]/div[3]/div[2]/div[1]/button/span/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-arrow-left']",
            "//svg[@class='g-icon' and @data-icon-name='icon-arrow-left']",
            "//use[@href='#icon-arrow-left']/parent::svg",
            "//use[@xlink:href='#icon-arrow-left']/parent::svg",
            "//div[contains(@class, 'b-make-post__media-slider')]//button//svg",
            "//div[contains(@class, 'b-make-post__media-wrapper')]//svg[@data-icon-name='icon-arrow-left']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Set Bundles Cover button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const svg = {selector};
                        if (svg) {{
                            // Click the parent button instead of the SVG
                            const parentButton = svg.closest('button');
                            if (parentButton) {{
                                parentButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                parentButton.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked Set Bundles Cover button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"xpath={selector}/ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Set Bundles Cover button with XPath")
                                return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            css_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"{selector} >> xpath=./ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Set Bundles Cover button with CSS selector")
                                return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Set Bundles Cover button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Set Bundles Cover button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the left arrow icon by various attributes
            const iconSelectors = [
                'svg[data-icon-name="icon-arrow-left"]',
                'svg.g-icon use[href="#icon-arrow-left"]',
                'svg use[xlink\\:href="#icon-arrow-left"]'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        const parentButton = icon.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding buttons in media slider area
            const mediaSliderButtons = document.querySelectorAll('.b-make-post__media-slider button');
            for (const button of mediaSliderButtons) {
                const leftArrowIcon = button.querySelector('svg[data-icon-name="icon-arrow-left"]');
                if (leftArrowIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding first button in media slider
            const mediaSlider = document.querySelector('.b-make-post__media-slider');
            if (mediaSlider) {
                const firstButton = mediaSlider.querySelector('button');
                if (firstButton) {
                    firstButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    firstButton.click();
                    return true;
                }
            }
            
            // Try finding by icon name in media wrapper area
            const mediaWrapper = document.querySelector('.b-make-post__media-wrapper');
            if (mediaWrapper) {
                const arrowButtons = mediaWrapper.querySelectorAll('button svg[data-icon-name="icon-arrow-left"]');
                for (const icon of arrowButtons) {
                    const parentButton = icon.closest('button');
                    if (parentButton) {
                        parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parentButton.click();
                        return true;
                    }
                }
            }
            
            // Try finding any button with left arrow icon in the make post form
            const allButtons = document.querySelectorAll('#make_post_form button');
            for (const button of allButtons) {
                const leftIcon = button.querySelector('svg[data-icon-name="icon-arrow-left"]');
                if (leftIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Set Bundles Cover button using JavaScript fallback!")
            return True
        
        print("Could not find or click Set Bundles Cover button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_set_bundles_cover: {str(e)}")
        return False

def click_to_select_media_bundle_cover(page):
    """
    Attempt to find and click the 'Select Media Bundle Cover' checkbox button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll > div.d-flex.align-items-start.w-100 > div.b-make-post__media-slider.m-custom-scrollbar.m-draggable.m-paid > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media-slider__inner.m-wrap-items-text.flex-fill-1.m-scroll-behavior.m-reset-overscroll > div > div:nth-child(1) > button.checkbox-item.m-pos-left-top.b-make-post__set-order-btn",
            # Alternative CSS selectors
            "button.checkbox-item.m-pos-left-top.b-make-post__set-order-btn",
            ".b-make-post__set-order-btn",
            ".checkbox-item.m-pos-left-top",
            ".b-make-post__media-slider button.checkbox-item",
            "div.b-make-post__media-slider__inner > div > div:first-child > button",
            ".b-make-post__media-slider .checkbox-item:first-child",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll > div.d-flex.align-items-start.w-100 > div.b-make-post__media-slider.m-custom-scrollbar.m-draggable.m-paid > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media-slider__inner.m-wrap-items-text.flex-fill-1.m-scroll-behavior.m-reset-overscroll > div > div:nth-child(1) > button.checkbox-item.m-pos-left-top.b-make-post__set-order-btn\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[1]/div/div[2]/div[1]/div[3]/div[2]/div[2]/div[3]/div/div[1]/button[1]",
            # Alternative XPaths
            "//button[contains(@class, 'checkbox-item') and contains(@class, 'b-make-post__set-order-btn')]",
            "//button[contains(@class, 'checkbox-item') and contains(@class, 'm-pos-left-top')]",
            "//div[contains(@class, 'b-make-post__media-slider__inner')]//div[1]//button[contains(@class, 'checkbox-item')]",
            "//button[contains(@class, 'b-make-post__set-order-btn')]",
            "//div[contains(@class, 'b-make-post__media-slider')]//button[contains(@class, 'checkbox-item')][1]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Select Media Bundle Cover button selector: {selector}")
                
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
                        print(f"Successfully clicked Select Media Bundle Cover button with JS selector")
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
                            print(f"Successfully clicked Select Media Bundle Cover button with XPath")
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
                            print(f"Successfully clicked Select Media Bundle Cover button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Select Media Bundle Cover button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Select Media Bundle Cover button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding checkbox buttons with specific classes
            const buttonSelectors = [
                'button.checkbox-item.m-pos-left-top.b-make-post__set-order-btn',
                'button.b-make-post__set-order-btn',
                'button.checkbox-item.m-pos-left-top'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding first checkbox button in media slider
            const mediaSlider = document.querySelector('.b-make-post__media-slider');
            if (mediaSlider) {
                const firstCheckbox = mediaSlider.querySelector('button.checkbox-item');
                if (firstCheckbox) {
                    firstCheckbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                    firstCheckbox.click();
                    return true;
                }
            }
            
            // Try finding by position in media slider inner
            const mediaSliderInner = document.querySelector('.b-make-post__media-slider__inner');
            if (mediaSliderInner) {
                const firstItemButton = mediaSliderInner.querySelector('div > div:first-child > button.checkbox-item');
                if (firstItemButton) {
                    firstItemButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    firstItemButton.click();
                    return true;
                }
            }
            
            // Try finding any checkbox button in the media area
            const mediaWrapper = document.querySelector('.b-make-post__media-wrapper');
            if (mediaWrapper) {
                const checkboxButtons = mediaWrapper.querySelectorAll('button.checkbox-item');
                if (checkboxButtons.length > 0) {
                    checkboxButtons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                    checkboxButtons[0].click();
                    return true;
                }
            }
            
            // Try finding by checkbox structure (with checkbox-item__inside class)
            const checkboxInsides = document.querySelectorAll('.checkbox-item__inside');
            for (const checkboxInside of checkboxInsides) {
                const parentButton = checkboxInside.closest('button');
                if (parentButton && parentButton.classList.contains('checkbox-item')) {
                    parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentButton.click();
                    return true;
                }
            }
            
            // Try finding first button with position classes
            const positionButtons = document.querySelectorAll('button.m-pos-left-top');
            if (positionButtons.length > 0) {
                positionButtons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                positionButtons[0].click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Select Media Bundle Cover button using JavaScript fallback!")
            return True
        
        print("Could not find or click Select Media Bundle Cover button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_select_media_bundle_cover: {str(e)}")
        return False

def click_done_to_set_cover(page):
    """
    Attempt to find and click the 'Done' button to set cover using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll.m-free-media > div.d-flex.align-items-start.w-100 > div.b-make-post__sort-btns > button.b-make-post__sort-done-btn",
            # Alternative CSS selectors
            "button.b-make-post__sort-done-btn",
            ".b-make-post__sort-btns button",
            "button[aria-label='Salve']",
            "button[data-no-dragscroll]",
            ".b-make-post__sort-done-btn svg[data-icon-name='icon-done']",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post.m-with-paid-options.m-free-text.m-chats-footer.d-flex.flex-column-reverse.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar.m-scroll-behavior-auto > div > div.b-make-post__main-wrapper > div.b-make-post__media-wrapper > div.b-dragscroll.m-native-custom-scrollbar.m-scrollbar-x.m-invisible-scrollbar.b-make-post__media.files.b-dropzone__previews.b-paid-post-content.m-scroll-behavior.m-disable-elastic-scroll.m-free-media > div.d-flex.align-items-start.w-100 > div.b-make-post__sort-btns > button.b-make-post__sort-done-btn\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[1]/div/div[2]/div[1]/div[3]/div[2]/div[3]/button[3]",
            # Alternative XPaths
            "//button[contains(@class, 'b-make-post__sort-done-btn')]",
            "//button[@aria-label='Salve']",
            "//button[@data-no-dragscroll]",
            "//div[contains(@class, 'b-make-post__sort-btns')]/button[contains(@class, 'b-make-post__sort-done-btn')]",
            "//button[.//svg[@data-icon-name='icon-done']]",
            "//svg[@data-icon-name='icon-done']/parent::button"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Done button selector: {selector}")
                
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
                        print(f"Successfully clicked Done button with JS selector")
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
                            print(f"Successfully clicked Done button with XPath")
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
                            print(f"Successfully clicked Done button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Done button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Done button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding done button with specific classes and attributes
            const buttonSelectors = [
                'button.b-make-post__sort-done-btn',
                '.b-make-post__sort-btns button',
                'button[aria-label="Salve"]',
                'button[data-no-dragscroll]'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by done icon
            const doneIcons = document.querySelectorAll('svg[data-icon-name="icon-done"]');
            for (const icon of doneIcons) {
                const parentButton = icon.closest('button');
                if (parentButton) {
                    parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentButton.click();
                    return true;
                }
            }
            
            // Try finding buttons in sort-btns area
            const sortBtns = document.querySelector('.b-make-post__sort-btns');
            if (sortBtns) {
                const buttons = sortBtns.querySelectorAll('button');
                // Try the last button (often the done/confirm button)
                if (buttons.length > 0) {
                    buttons[buttons.length - 1].scrollIntoView({behavior: 'smooth', block: 'center'});
                    buttons[buttons.length - 1].click();
                    return true;
                }
            }
            
            // Try finding by button with done icon specifically
            const buttonsWithDoneIcon = document.querySelectorAll('button svg use[href="#icon-done"]');
            if (buttonsWithDoneIcon.length > 0) {
                const parentButton = buttonsWithDoneIcon[0].closest('button');
                if (parentButton) {
                    parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentButton.click();
                    return true;
                }
            }
            
            // Try finding by aria-label containing save/done
            const saveButtons = document.querySelectorAll('button[aria-label*="Salve"], button[aria-label*="Save"], button[aria-label*="Done"]');
            for (const button of saveButtons) {
                if (button) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Done button using JavaScript fallback!")
            return True
        
        print("Could not find or click Done button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_done_to_set_cover: {str(e)}")
        return False

def click_to_confirm_operation(page):
    """
    Attempt to find and click the 'Sim' confirmation button using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ModalConfirm___BV_modal_footer_ > button:nth-child(2)",
            # Alternative CSS selectors
            "button.g-btn.m-flat.m-btn-gaps.m-reset-width",
            "button[type='button'].g-btn.m-flat.m-btn-gaps.m-reset-width",
            "button:has-text('Sim')",
            # JavaScript path
            "document.querySelector(\"#ModalConfirm___BV_modal_footer_ > button:nth-child(2)\")",
            "document.querySelector(\"button.g-btn.m-flat.m-btn-gaps.m-reset-width\")",
            # XPath
            "//*[@id=\"ModalConfirm___BV_modal_footer_\"]/button[2]",
            "//button[@class='g-btn m-flat m-btn-gaps m-reset-width']",
            "//button[contains(@class, 'g-btn') and contains(text(), 'Sim')]"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Confirm operation button selector: {selector}")
                
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
                        #print(f"Successfully clicked Confirm operation button with JS selector")
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
                            #print(f"Successfully clicked Confirm operation button with XPath")
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
                            #print(f"Successfully clicked Confirm operation button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Confirm operation button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Confirm operation button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with confirmation-related attributes or classes
            const buttonSelectors = [
                'button.g-btn.m-flat.m-btn-gaps.m-reset-width',
                'button[type="button"]',
                'button:contains("Sim")',
                '#ModalConfirm___BV_modal_footer_ button'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && (button.textContent.includes('Sim') || button.classList.contains('m-flat'))) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding within modal footer context
            const modalFooter = document.querySelector('#ModalConfirm___BV_modal_footer_');
            if (modalFooter) {
                const buttons = modalFooter.querySelectorAll('button');
                // Look for the second button (usually the confirmation)
                if (buttons.length >= 2) {
                    const confirmButton = buttons[1];
                    if (confirmButton.textContent.includes('Sim')) {
                        confirmButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        confirmButton.click();
                        return true;
                    }
                }
                // Fallback: look for any button with "Sim" text
                for (const button of buttons) {
                    if (button.textContent.includes('Sim')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by button text content
            const allButtons = document.querySelectorAll('button');
            for (const button of allButtons) {
                if (button.textContent.trim() === 'Sim' && button.classList.contains('g-btn')) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Confirm operation button using JavaScript fallback!")
            return True
        
        print("Could not find or click Confirm operation button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_confirm_operation: {str(e)}")
        return False

def click_to_add_a_co_partner(page):
    """
    Attempt to find and click the 'Add Co-partner' button (account icon) using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(9) > svg",
            # Alternative CSS selectors
            "svg[data-icon-name='icon-account']",
            "svg.g-icon use[href='#icon-account']",
            "svg use[xlink\\:href='#icon-account']",
            ".b-make-post__actions__btns button:nth-child(9) svg",
            ".b-make-post__sticky-panel svg[data-icon-name='icon-account']",
            # JavaScript path
            "document.querySelector(\"#make_post_form > div.b-make-post__sticky-panel > div > div.b-make-post__actions__btns > button:nth-child(9) > svg\")",
            # XPath
            "//*[@id=\"make_post_form\"]/div[2]/div/div[1]/button[9]/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-account']",
            "//svg[@class='g-icon' and @data-icon-name='icon-account']",
            "//use[@href='#icon-account']/parent::svg",
            "//use[@xlink:href='#icon-account']/parent::svg",
            "//div[contains(@class, 'b-make-post__actions__btns')]/button[9]/svg"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Add Co-partner button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const svg = {selector};
                        if (svg) {{
                            // Click the parent button instead of the SVG
                            const parentButton = svg.closest('button');
                            if (parentButton) {{
                                parentButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                parentButton.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked Add Co-partner button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"xpath={selector}/ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Add Co-partner button with XPath")
                                return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            css_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"{selector} >> xpath=./ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Add Co-partner button with CSS selector")
                                return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Add Co-partner button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Add Co-partner button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the account icon by various attributes
            const iconSelectors = [
                'svg[data-icon-name="icon-account"]',
                'svg.g-icon use[href="#icon-account"]',
                'svg use[xlink\\:href="#icon-account"]'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        const parentButton = icon.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding by button position in actions panel
            const actionButtons = document.querySelectorAll('.b-make-post__actions__btns button');
            if (actionButtons.length >= 9) {
                // Assuming 9th button is the co-partner button (0-indexed 8)
                actionButtons[8].scrollIntoView({behavior: 'smooth', block: 'center'});
                actionButtons[8].click();
                return true;
            }
            
            // Try finding any button containing account icon
            const allButtons = document.querySelectorAll('.b-make-post__sticky-panel button');
            for (const button of allButtons) {
                const accountIcon = button.querySelector('svg[data-icon-name="icon-account"]');
                if (accountIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding by icon name in any button
            const buttonsWithIcons = document.querySelectorAll('button svg[data-icon-name]');
            for (const icon of buttonsWithIcons) {
                if (icon.getAttribute('data-icon-name') === 'icon-account') {
                    const parentButton = icon.closest('button');
                    if (parentButton) {
                        parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parentButton.click();
                        return true;
                    }
                }
            }
            
            // Try finding buttons with account-related functionality
            const accountButtons = document.querySelectorAll('button');
            for (const button of accountButtons) {
                const icon = button.querySelector('use[href="#icon-account"]');
                if (icon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Add Co-partner button using JavaScript fallback!")
            return True
        
        print("Could not find or click Add Co-partner button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_add_a_co_partner: {str(e)}")
        return False

def click_to_search_a_co_partner(page):
    """
    Attempt to find and click the 'Search Co-partner' button (search icon) using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ReleaseFormsModal___BV_modal_header_ > div > div > div > button > svg",
            # Alternative CSS selectors
            "svg[data-icon-name='icon-search']",
            "svg.g-icon use[href='#icon-search']",
            "svg use[xlink\\:href='#icon-search']",
            "#ReleaseFormsModal___BV_modal_header_ button svg",
            ".modal-header button svg[data-icon-name='icon-search']",
            # JavaScript path
            "document.querySelector(\"#ReleaseFormsModal___BV_modal_header_ > div > div > div > button > svg\")",
            # XPath
            "//*[@id=\"ReleaseFormsModal___BV_modal_header_\"]/div/div/div/button/svg",
            # Alternative XPaths
            "//svg[@data-icon-name='icon-search']",
            "//svg[@class='g-icon' and @data-icon-name='icon-search']",
            "//use[@href='#icon-search']/parent::svg",
            "//use[@xlink:href='#icon-search']/parent::svg",
            "//div[@id='ReleaseFormsModal___BV_modal_header_']//button//svg",
            "//div[contains(@class, 'modal-header')]//button//svg[@data-icon-name='icon-search']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Search Co-partner button selector: {selector}")
                
                # Handle different selector types
                if selector.startswith("document.querySelector"):
                    # JavaScript selector
                    button_clicked = page.evaluate(f'''() => {{
                        const svg = {selector};
                        if (svg) {{
                            // Click the parent button instead of the SVG
                            const parentButton = svg.closest('button');
                            if (parentButton) {{
                                parentButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                parentButton.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}''')
                    
                    if button_clicked:
                        print(f"Successfully clicked Search Co-partner button with JS selector")
                        return True
                
                elif selector.startswith('/'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.evaluate(
                                    `{selector}`, 
                                    document, 
                                    null, 
                                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                                    null
                                ).singleNodeValue;
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            xpath_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"xpath={selector}/ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Search Co-partner button with XPath")
                                return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")
                
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        try:
                            # Force visibility of parent elements
                            page.evaluate(f'''(selector) => {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const parentButton = element.closest('button');
                                    if (parentButton) {{
                                        parentButton.style.opacity = '1';
                                        parentButton.style.visibility = 'visible';
                                        parentButton.style.display = 'block';
                                    }}
                                }}
                            }}''', selector)
                            
                            # Scroll and click the parent button
                            css_elements.first.scroll_into_view_if_needed()
                            # Click the parent button instead of the SVG
                            parent_button = page.locator(f"{selector} >> xpath=./ancestor::button[1]")
                            if parent_button.count() > 0:
                                parent_button.first.click(force=True)
                                print(f"Successfully clicked Search Co-partner button with CSS selector")
                                return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Search Co-partner button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Search Co-partner button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding the search icon by various attributes
            const iconSelectors = [
                'svg[data-icon-name="icon-search"]',
                'svg.g-icon use[href="#icon-search"]',
                'svg use[xlink\\:href="#icon-search"]'
            ];
            
            for (const selector of iconSelectors) {
                const icons = document.querySelectorAll(selector);
                for (const icon of icons) {
                    if (icon) {
                        const parentButton = icon.closest('button');
                        if (parentButton) {
                            parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                            parentButton.click();
                            return true;
                        }
                    }
                }
            }
            
            // Try finding buttons in modal header
            const modalHeader = document.querySelector('#ReleaseFormsModal___BV_modal_header_');
            if (modalHeader) {
                const buttons = modalHeader.querySelectorAll('button');
                for (const button of buttons) {
                    const searchIcon = button.querySelector('svg[data-icon-name="icon-search"]');
                    if (searchIcon) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding any button with search icon in modal
            const modalButtons = document.querySelectorAll('#ReleaseFormsModal___BV_modal_header_ button');
            for (const button of modalButtons) {
                const searchIcon = button.querySelector('svg[data-icon-name="icon-search"]');
                if (searchIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding by icon name in modal area
            const modalSearchIcons = document.querySelectorAll('#ReleaseFormsModal___BV_modal_header_ svg[data-icon-name="icon-search"]');
            for (const icon of modalSearchIcons) {
                const parentButton = icon.closest('button');
                if (parentButton) {
                    parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    parentButton.click();
                    return true;
                }
            }
            
            // Try finding search button by structure in modal header
            const modalHeaderDivs = document.querySelectorAll('#ReleaseFormsModal___BV_modal_header_ > div > div > div > button');
            for (const button of modalHeaderDivs) {
                const searchIcon = button.querySelector('svg[data-icon-name="icon-search"]');
                if (searchIcon) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding any search icon button in the entire document
            const allSearchIcons = document.querySelectorAll('svg[data-icon-name="icon-search"]');
            for (const icon of allSearchIcons) {
                const parentButton = icon.closest('button');
                if (parentButton) {
                    // Check if it's in a modal context
                    const modal = parentButton.closest('.modal, [id*="modal"]');
                    if (modal) {
                        parentButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                        parentButton.click();
                        return true;
                    }
                }
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Search Co-partner button using JavaScript fallback!")
            return True
        
        print("Could not find or click Search Co-partner button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_search_a_co_partner: {str(e)}")
        return False

def click_to_confirm_co_partner_addition(page):
    """
    Attempt to find and click the 'Adicionar' (Add) button to confirm co-partner addition using multiple approaches.
    """
    try:
        # List of selectors to try
        selectors = [
            # Direct CSS selector
            "#ReleaseFormsModal___BV_modal_body_ > div > div.b-placeholder-item-selected > div > div > div.b-row-selected__controls > button",
            # Alternative CSS selectors
            "button.g-btn.m-reset-width.m-rounded.m-sm",
            ".b-row-selected__controls button",
            ".b-placeholder-item-selected button",
            "button:has-text('Adicionar')",
            "#ReleaseFormsModal___BV_modal_body_ button:has-text('Adicionar')",
            ".modal-body button.g-btn",
            # JavaScript path
            "document.querySelector(\"#ReleaseFormsModal___BV_modal_body_ > div > div.b-placeholder-item-selected > div > div > div.b-row-selected__controls > button\")",
            # XPath
            "//*[@id=\"ReleaseFormsModal___BV_modal_body_\"]/div/div[3]/div/div/div[2]/button",
            # Alternative XPaths
            "//button[contains(@class, 'g-btn') and contains(@class, 'm-reset-width') and text()=' Adicionar ']",
            "//button[text()=' Adicionar ']",
            "//div[contains(@class, 'b-row-selected__controls')]/button",
            "//div[contains(@class, 'b-placeholder-item-selected')]//button[text()=' Adicionar ']",
            "//div[@id='ReleaseFormsModal___BV_modal_body_']//button[text()=' Adicionar ']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Confirm Co-partner Addition button selector: {selector}")
                
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
                        print(f"Successfully clicked Confirm Co-partner Addition button with JS selector")
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
                            print(f"Successfully clicked Confirm Co-partner Addition button with XPath")
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
                            print(f"Successfully clicked Confirm Co-partner Addition button with CSS selector")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")
                
            except Exception as e:
                print(f"Failed with Confirm Co-partner Addition button selector {selector}: {str(e)}")
                continue
        
        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for Confirm Co-partner Addition button...")
        fallback_clicked = page.evaluate('''() => {
            // Try finding button elements with specific classes and text in modal context
            const buttonSelectors = [
                'button.g-btn.m-reset-width.m-rounded.m-sm',
                '.b-row-selected__controls button',
                '.b-placeholder-item-selected button'
            ];
            
            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && button.textContent.includes('Adicionar')) {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding by text content in modal body
            const modalBody = document.querySelector('#ReleaseFormsModal___BV_modal_body_');
            if (modalBody) {
                const addButtons = modalBody.querySelectorAll('button');
                for (const button of addButtons) {
                    if (button.textContent.trim() === 'Adicionar') {
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }
            
            // Try finding any button in the selection controls area within modal
            const selectionControls = document.querySelector('#ReleaseFormsModal___BV_modal_body_ .b-row-selected__controls');
            if (selectionControls) {
                const controlButton = selectionControls.querySelector('button');
                if (controlButton) {
                    controlButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    controlButton.click();
                    return true;
                }
            }
            
            // Try finding any button in the placeholder selected area within modal
            const placeholderSelected = document.querySelector('#ReleaseFormsModal___BV_modal_body_ .b-placeholder-item-selected');
            if (placeholderSelected) {
                const placeholderButton = placeholderSelected.querySelector('button');
                if (placeholderButton) {
                    placeholderButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                    placeholderButton.click();
                    return true;
                }
            }
            
            // Try finding any add button in modal
            const modalAddButtons = document.querySelectorAll('#ReleaseFormsModal___BV_modal_body_ button');
            for (const button of modalAddButtons) {
                if (button.textContent.includes('Adicionar') || button.textContent.includes('Add')) {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
            }
            
            // Try finding primary action button in modal
            const primaryButtons = document.querySelectorAll('#ReleaseFormsModal___BV_modal_body_ button.g-btn');
            if (primaryButtons.length > 0) {
                // Assuming the last primary button is the confirm/add button
                primaryButtons[primaryButtons.length - 1].scrollIntoView({behavior: 'smooth', block: 'center'});
                primaryButtons[primaryButtons.length - 1].click();
                return true;
            }
            
            return false;
        }''')
        
        if fallback_clicked:
            print("Successfully clicked Confirm Co-partner Addition button using JavaScript fallback!")
            return True
        
        print("Could not find or click Confirm Co-partner Addition button using any method.")
        return False
    
    except Exception as e:
        print(f"Error in click_to_confirm_co_partner_addition: {str(e)}")
        return False

#def check_if_price_icon_is_visible(page):
    price_icon = page.locator('use[href="#icon-price"]').first

    if price_icon.is_visible():
        print("The bundle's price is set up correctly!")
    else:
        print("Maybe the bundle's price is not set up, reloading page...")
        page.reload()

#def check_if_price_icon_is_visible(page):
    # Specifically target the icon inside the "m-paid" label
    price_icon = page.locator('.m-paid use[href="#icon-price"]')

    if price_icon.is_visible():
        print("The bundle's price is set up correctly!")
        return 

    # If the icon isn't there, we reload
    print("Maybe the bundle's price is not set up, reloading page...")
    page.reload()

def check_if_price_icon_is_visible(page):
    # Specifically target the icon inside the "m-paid" label
    price_icon = page.locator('.m-paid use[href="#icon-price"]').first

    if price_icon.is_visible():
        print("The bundle's price is set up correctly!")
        return True # Everything is fine, keep going
    else:
        print("Maybe the bundle's price is not set up, reloading page...")
        page.reload()
        page.wait_for_load_state("networkidle")
        return False # Signal that we reloaded

def click_to_confirm_send_msg(page):
    """
    Attempt to find and click the 'Confirm / Sim' button using multiple approaches.
    """
    try:
        selectors = [
            # Direct CSS selector
            "#ModalConfirm___BV_modal_footer_ > button:nth-child(2)",

            # Alternative CSS selectors
            "#ModalConfirm___BV_modal_footer_ button",
            "button.g-btn.m-flat.m-btn-gaps.m-reset-width",

            # JavaScript path
            "document.querySelector(\"#ModalConfirm___BV_modal_footer_ > button:nth-child(2)\")",

            # XPath selectors
            "//*[@id='ModalConfirm___BV_modal_footer_']/button[2]",
            "//div[@id='ModalConfirm___BV_modal_footer_']//button[normalize-space()='Sim']",
            "//button[normalize-space()='Sim']"
        ]

        for selector in selectors:
            try:
                # JavaScript selector
                if selector.startswith("document.querySelector"):
                    clicked = page.evaluate(f'''() => {{
                        const btn = {selector};
                        if (btn) {{
                            btn.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            btn.click();
                            return true;
                        }}
                        return false;
                    }}''')

                    if clicked:
                        return True

                # XPath selector
                elif selector.startswith('/'):
                    locator = page.locator(f"xpath={selector}")
                    if locator.count() > 0:
                        page.evaluate(f'''(xpath) => {{
                            const el = document.evaluate(
                                xpath,
                                document,
                                null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE,
                                null
                            ).singleNodeValue;
                            if (el) {{
                                el.style.opacity = '1';
                                el.style.visibility = 'visible';
                                el.style.display = 'block';
                            }}
                        }}''', selector)

                        locator.first.scroll_into_view_if_needed()
                        locator.first.click(force=True)
                        return True

                # CSS selector
                else:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        page.evaluate(f'''(selector) => {{
                            const el = document.querySelector(selector);
                            if (el) {{
                                el.style.opacity = '1';
                                el.style.visibility = 'visible';
                                el.style.display = 'block';
                            }}
                        }}''', selector)

                        locator.first.scroll_into_view_if_needed()
                        locator.first.click(force=True)
                        return True

            except Exception as e:
                print(f"Confirm button selector failed ({selector}): {str(e)}")
                continue

        # JavaScript fallback (modal-aware)
        fallback_clicked = page.evaluate('''() => {
            const footer = document.getElementById("ModalConfirm___BV_modal_footer_");
            if (!footer) return false;

            const buttons = footer.querySelectorAll("button");
            for (const btn of buttons) {
                if (btn.textContent.trim().toLowerCase() === "sim") {
                    btn.scrollIntoView({ behavior: "smooth", block: "center" });
                    btn.click();
                    return true;
                }
            }
            return false;
        }''')

        if fallback_clicked:
            return True

        print("Could not find or click Confirm (Sim) button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_to_confirm_send_msg: {str(e)}")
        return False

def click_on_more_options(page):
    """
    Attempt to find and click the 'More Options' button (often an SVG icon)
    using multiple approaches.
    """
    try:
        # List of selectors to try for the 'More Options' button
        selectors = [
            # 1. Direct CSS selector for the button containing the SVG
            "#app > div.container.m-main-container > header > nav > button.l-header__menu__item.m-size-lg-hover.m-with-round-hover.m-width-fluid-hover",
            # 2. XPath for the button containing the SVG
            "//*[@id='app']/div[1]/header/nav/button[2]",
            # 3. CSS selector targeting the SVG itself, then its parent button
            "button.l-header__menu__item > span.l-header__menu__item__icon > svg[data-icon-name='icon-menu-more']",
            # 4. XPath targeting the SVG itself, then its parent button
            "//button[contains(@class, 'l-header__menu__item')]///*[name()='svg' and @data-icon-name='icon-menu-more']",
            # 5. Fallback: Targeting any button with a 'more' or 'menu' related class/attribute that contains an SVG
            "button[class*='menu__item'][class*='more']",
            "button[aria-label*='more options']", # If an aria-label exists
            "button:has(svg[data-icon-name='icon-menu-more'])", # Playwright's :has pseudo-class
            "button:has(use[href='#icon-menu-more'])" # Targeting the use element
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying More Options button selector: {selector}")

                # Check if it's an XPath selector
                if selector.startswith('//') or selector.startswith('(//'):
                    elements = page.locator(f"xpath={selector}")
                else:
                    elements = page.locator(selector)

                if elements.count() > 0:
                    try:
                        # Ensure visibility and click
                        # We'll try to click the button element directly if possible,
                        # as clicking the SVG itself might not always trigger the desired action.
                        # If the selector targets the SVG, we'll try to find its closest button parent.
                        target_element = elements.first
                        if "svg" in selector and target_element.evaluate("el => el.tagName.toLowerCase()") == "svg":
                            # If we selected the SVG, try to click its closest button parent
                            button_parent = target_element.locator("xpath=ancestor::button").first
                            if button_parent.is_visible():
                                button_parent.scroll_into_view_if_needed()
                                button_parent.click(force=True)
                                print(f"Successfully clicked More Options button via SVG's parent button with selector: {selector}")
                                return True
                        elif target_element.is_visible():
                            # If we selected a button or another clickable element, click it directly
                            target_element.scroll_into_view_if_needed()
                            target_element.click(force=True)
                            print(f"Successfully clicked More Options button with selector: {selector}")
                            return True
                    except Exception as e:
                        print(f"Click failed for selector {selector}: {str(e)}")

            except Exception as e:
                print(f"Failed with More Options button selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach for ultimate resilience
        print("Trying JavaScript fallback approach for More Options button...")
        fallback_clicked = page.evaluate('''() => {
            const buttonSelectors = [
                "button.l-header__menu__item.m-size-lg-hover.m-with-round-hover.m-width-fluid-hover",
                "button:has(svg[data-icon-name='icon-menu-more'])",
                "button:has(use[href='#icon-menu-more'])",
                "button[class*='menu__item'][class*='more']",
                "button[aria-label*='more options']",
                "button[aria-haspopup='true']" // Common for dropdowns
            ];

            for (const selector of buttonSelectors) {
                const buttons = document.querySelectorAll(selector);
                for (const button of buttons) {
                    if (button && button.offsetParent !== null) { // Check if element is visible
                        button.scrollIntoView({behavior: 'smooth', block: 'center'});
                        button.click();
                        return true;
                    }
                }
            }

            // If no button found, try clicking the SVG itself if it's clickable
            const svgElement = document.querySelector("svg[data-icon-name='icon-menu-more']");
            if (svgElement && svgElement.offsetParent !== null) {
                svgElement.scrollIntoView({behavior: 'smooth', block: 'center'});
                svgElement.click();
                return true;
            }

            return false;
        }''')

        if fallback_clicked:
            print("Successfully clicked More Options button using JavaScript fallback!")
            return True

        print("Could not find or click More Options button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_more_options: {str(e)}")
        return False

def click_to_logout(page):
    """
    Attempt to find and click the 'Log out' button using multiple approaches.
    """
    try:
        # List of selectors to try for the 'Log out' button
        selectors = [
            # 1. Direct CSS selector for the span, then click its parent button
            "#app > div.container.m-main-container > header > div > div.l-sidebar__inner.m-native-custom-scrollbar.m-scrollbar-y.m-invisible-scrollbar > div.l-sidebar__menu > button.l-sidebar__menu__item.m-break-word.m-logout > span",
            # 2. XPath for the span, then click its parent button
            "//*[@id='app']/div[1]/header/div/div[3]/div[3]/button[2]/span",
            # 3. CSS selector for the button directly, using its classes
            "button.l-sidebar__menu__item.m-logout",
            # 4. XPath for the button directly, using its classes
            "//button[contains(@class, 'l-sidebar__menu__item') and contains(@class, 'm-logout')]",
            # 5. CSS selector targeting the span by its text content (Playwright specific)
            "span.l-sidebar__menu__text:has-text('Log out')",
            # 6. XPath targeting the span by its text content
            "//span[contains(@class, 'l-sidebar__menu__text') and text()='Log out']",
            # 7. Fallback: Targeting any button that contains the text 'Log out'
            "button:has-text('Log out')",
            # 8. Fallback: Targeting any element with 'Log out' as link text (if it were an <a> tag)
            "text='Log out'" # Playwright's text selector
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"Trying Log out button selector: {selector}")

                # Check if it's an XPath selector
                if selector.startswith('//') or selector.startswith('(//'):
                    elements = page.locator(f"xpath={selector}")
                elif selector.startswith("text="): # Playwright's text selector
                    elements = page.locator(selector)
                else:
                    elements = page.locator(selector)

                if elements.count() > 0:
                    try:
                        target_element = elements.first

                        # If the selector targets a span, try to click its closest button parent
                        # This is important because clicking a span might not always trigger the button's action
                        if "span" in selector and target_element.evaluate("el => el.tagName.toLowerCase()") == "span":
                            button_parent = target_element.locator("xpath=ancestor::button").first
                            if button_parent.is_visible():
                                button_parent.scroll_into_view_if_needed()
                                button_parent.click(force=True)
                                print(f"Successfully clicked Log out button via span's parent button with selector: {selector}")
                                return True
                        elif target_element.is_visible():
                            # If we selected a button or another clickable element, click it directly
                            target_element.scroll_into_view_if_needed()
                            target_element.click(force=True)
                            print(f"Successfully clicked Log out button with selector: {selector}")
                            return True
                    except Exception as e:
                        print(f"Click failed for selector {selector}: {str(e)}")

            except Exception as e:
                print(f"Failed with Log out button selector {selector}: {str(e)}")
                

        # Fallback JavaScript approach for ultimate resilience
        print("Trying JavaScript fallback approach for Log out button...")
        fallback_clicked = page.evaluate('''() => {
            const buttonSelectors = [
                "button.l-sidebar__menu__item.m-logout",
                "button:has(span.l-sidebar__menu__text:has-text('Log out'))",
                "button:has-text('Log out')",
                "span.l-sidebar__menu__text:has-text('Log out')"
            ];

            for (const selector of buttonSelectors) {
                const elements = document.querySelectorAll(selector);
                for (const element of elements) {
                    if (element && element.offsetParent !== null) { // Check if element is visible
                        // If it's a span, try to click its closest button parent
                        if (element.tagName.toLowerCase() === 'span' && element.closest('button')) {
                            element.closest('button').scrollIntoView({behavior: 'smooth', block: 'center'});
                            element.closest('button').click();
                            return true;
                        } else if (element.tagName.toLowerCase() === 'button') {
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
            print("Successfully clicked Log out button using JavaScript fallback!")
            return True

        print("Could not find or click Log out button using any method.")
        return False

    except Exception as e:
        print(f"Error in click_to_logout: {str(e)}")
        return False

def main():
    
    log_file_path = r"G:\Meu Drive\Onlyfans\of_free_fan_mass_dm_errors_log.txt"

    with capture_and_save_log(log_file_path):
            
        pw = None
        context = None
        page = None
        browser_process = None


        # ADIÇÃO: Definir user_data aqui para acessá-lo no finally (para limpeza)
        user_data = os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\User Data\Automation")

        # 2. Launch Browser via the Native Hook method
        try:
            pw, context, browser_process = open_chrome_in_onlyfans_login_page()
            page = context.pages[0]  # Grab the active OnlyFans login page
            print("✓ Browser launched successfully")
        except Exception as e:
            print(f"❌ Failed to launch or hook browser: {e}")
            cleanup(pw, context, browser_process)
            return

        # 3. Automation and Interaction
        try:
            print("Waiting for page load...")
            page.wait_for_load_state("domcontentloaded")

            # Fullscreen Mode
            try:
                import pyautogui
                pyautogui.press('f11')
                page.wait_for_timeout(3000)
            except ImportError:
                print("Warning: pyautogui not installed, skipping fullscreen")

            # region Login operation procedures

            # region Try to insert username with retries
            print("\nAttempting to insert username...")
            max_retries = 3
            username_inserted = False

            for attempt in range(max_retries):
                print(f"Username attempt {attempt + 1}/{max_retries}")
                if insert_username(page):
                    username_inserted = True
                    break
                else:
                    print(f"✗ Username attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        time.sleep(2)

            if not username_inserted:
                print("❌ Maybe you are already logged in!")

            time.sleep(2)
            # endregion Try to insert username with retries

            # region Try to insert password with retries
            print("\nAttempting to insert password...")
            max_retries = 3
            password_inserted = False

            for attempt in range(max_retries):
                print(f"Password attempt {attempt + 1}/{max_retries}")
                if insert_password(page):
                    password_inserted = True
                    break
                else:
                    print(f"✗ Password attempt {attempt + 1} failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        time.sleep(2)

            if not password_inserted:
                print("❌ Maybe you are already logged in!")

            time.sleep(2)
            # endregion Try to insert password with retries

            # region Try to click the Login button with retries
            print("\nAttempting to click Entrar button...")
            max_retries = 3
            login_successful = False

            for attempt in range(max_retries):
                print(f"Attempt {attempt + 1}: Clicking Login button...")
                if click_on_login_button(page):
                    print("✓ Success: Login button clicked.")
                    login_successful = True
                    break
                else:
                    print(f"✗ Attempt {attempt + 1} failed. Maybe you are already logged in!")
                    if attempt < max_retries - 1:
                        time.sleep(2)
            # endregion Try to click the Login button with retries

            page.wait_for_timeout(10000) # Wait for potential login processing

            # region Try to click the Login button second time with retries
            print("\nAttempting to click Login button for the second time...")
            max_retries = 3
            login_successful = False

            for attempt in range(max_retries):
                print(f"Attempt {attempt + 1}: Clicking Login button for the second time...")
                if click_on_login_button(page):
                    print("✓ Success: Login button clicked in the second attempt.")
                    login_successful = True
                    break
                else:
                    print(f"✗ Attempt {attempt + 1} failed. Maybe you are already logged in!")
                    if attempt < max_retries - 1:
                        time.sleep(2)    
            # endregion Try to click the Login button second time with retries

            # region Wait for login to complete
            if login_successful:
                print("\nWaiting for login to complete...")
                page.wait_for_timeout(10000)
                print(f"Current URL: {page.url}")
                print("✓ Login process completed!")
            # endregion Wait for login to complete

            # region Navigate to the OnlyFans chat page
            print("\nNavigating to OnlyFans chat page...")
            page.goto("https://onlyfans.com/my/chats/")
            page.wait_for_timeout(7000)
            print(f"✓ Navigated to: {page.url}")
            # endregion Navigate to the OnlyFans chat page

            # endregion Login operation procedures

            # region MAIN OPERATION

            # region Try to click the Send Message button with retries
            max_retries = 3
            success = False
            for attempt in range(max_retries):
                if click_to_send_msg(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} failed.")
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Send Message button with retries

            # region Clean the media set if is already filled
            clean_media_set(page)
            # endregion Clean the media set if is already filled        

            page.wait_for_timeout(2000)

            # region Clean the price if is already filled
            clean_price(page)
            # endregion Clean the price if is already filled

            page.wait_for_timeout(2000)

            # region Try to click the Non-creators list with retries
            success = False
            for attempt in range(max_retries):
                # click_on_non_creators_list now returns True if checked OR if successfully clicked
                if click_on_non_creators_list(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to select Non-creators failed.")
                    time.sleep(1)

            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Non-creators list with retries

            # region Try to click the Paid Users list with retries
            success = False
            for attempt in range(max_retries):
                # click_on_paid_users_list returns True if already checked OR if clicked successfully
                if click_on_paid_users_list(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to select Paid Users failed.")
                    time.sleep(1)

            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Paid Users list with retries

            # region Try to insert caption into input field
            caption_to_paste = get_next_caption() # Get the caption first

            success = False
            for attempt in range(max_retries):
                # Pass the caption directly to the new method
                if click_and_insert_caption_in_the_input_field(page, caption_to_paste):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to insert caption failed.")
                    time.sleep(1)

            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to insert caption into input field

            # region Try to click the vault button with retries
            success = False
            for attempt in range(max_retries):
                if click_on_vault_btn(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the vault button with retries

            # region Try to search bundle with retries
            # Get the bundle name from the file
            file_path = r"G:\Meu Drive\Onlyfans\caption_index.txt"
            with open(file_path, "r", encoding="utf-8") as file:
                bundle_name = file.read().strip()

            success = False
            for attempt in range(max_retries):
                # Pass the bundle name directly to the method
                if click_to_search_bundle_and_type(page, bundle_name):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to search bundle failed.")
                    time.sleep(1)

            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to search bundle with retries

            # region Click on the bundle element with dynamic number
            try:
                page.click(f'text=Bundle #{bundle_name}')
            except:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            # endregion Click on the bundle element with dynamic number

            time.sleep(5)

            # region Try to click the Select All icon with retries
            success = False
            for attempt in range(max_retries):
                if click_on_select_all_icon(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Select All icon with retries

            # region Try to click the Accept Selection button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_accept_selection(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Accept Selection button with retries

            # region Try to click the Set Price icon with retries
            success = False
            for attempt in range(max_retries):
                if click_on_set_price_icon(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Set Price icon with retries

            pyautogui.typewrite("5")
            time.sleep(5)

            # region Try to click the Save button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_save_bundles_price(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Save button with retries

            # region Try to click the Set Bundles Cover button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_set_bundles_cover(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to click Set Bundles Cover failed.")
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Set Bundles Cover button with retries

            # region Try to click the Select Media Bundle Cover button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_select_media_bundle_cover(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to click Select Media Bundle Cover failed.")
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Select Media Bundle Cover button with retries

            # region Try to click the Set Bundles Cover button (Second Time) with retries
            success = False
            for attempt in range(max_retries):
                if click_to_set_bundles_cover(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} (Step 2) for Bundles Cover failed.")
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Set Bundles Cover button (Second Time) with retries

            # region Try to click the Done button with retries
            success = False
            for attempt in range(max_retries):
                if click_done_to_set_cover(page):
                    success = True
                    break
                else:
                    print(f"Attempt {attempt + 1} to click Done failed.")
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Done button with retries

            # region Try to click the Add Co-partner button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_add_a_co_partner(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Add Co-partner button with retries

            # region Try to click the Search Co-partner button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_search_a_co_partner(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Search Co-partner button with retries

            pyautogui.typewrite("Hell")
            time.sleep(5)

            # region Try to click the Hell Paradise creator with retries
            success = False
            for attempt in range(max_retries):
                if click_on_hell_paradise_creator(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Hell Paradise creator with retries

            # region Try to click the Confirm Co-partner Addition button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_confirm_co_partner_addition(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return

            time.sleep(5)
            # endregion Try to click the Confirm Co-partner Addition button with retries

            # region Check Price Visibility
            if not check_if_price_icon_is_visible(page):
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            # endregion Check Price Visibility

            time.sleep(5)

            # region Try to click the Send button with retries
            success = False
            for attempt in range(max_retries):
                if click_on_send_btn(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Send button with retries

            # region Try to click the Confirm (Sim) button with retries
            success = False
            for attempt in range(max_retries):
                if click_to_confirm_send_msg(page):
                    success = True
                    break
                else:
                    time.sleep(1)
            if not success:
                print("Não é possível efetuar a operação, saindo do programa!")
                # Begin "More Options" and "Log Out" flow
                max_retries_logout = 3
                for attempt in range(max_retries_logout):
                    if click_on_more_options(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click More Options button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click More Options button after all attempts.")

                page.wait_for_timeout(3000)

                for attempt in range(max_retries_logout):
                    if click_to_logout(page):
                        break
                    else:
                        print(f"Attempt {attempt + 1} to click Log out button failed.")
                        if attempt < max_retries_logout - 1:
                            page.wait_for_timeout(2000)
                else:
                    print("Failed to click Log out button after all attempts.")

                page.wait_for_timeout(3000)
                # End of  "More Options" and "Log Out" flow
                return
            time.sleep(5)
            # endregion Try to click the Confirm (Sim) button with retries

            # region Try to click the More Options button with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click More Options button...")
                if click_on_more_options(page):
                    print("Successfully clicked More Options button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} to click More Options button failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        page.wait_for_timeout(2000) # Wait for 2 seconds before retrying
            else:
                print("Failed to click More Options button after all attempts.")

            page.wait_for_timeout(3000)
            # endregion Try to click the More Options button with retries

            # region Try to click the Log out button with retries
            max_retries = 3
            for attempt in range(max_retries):
                print(f"\nAttempt {attempt + 1} to click Log out button...")
                if click_to_logout(page):
                    print("Successfully clicked Log out button!")
                    break
                else:
                    print(f"Attempt {attempt + 1} to click Log out button failed.")
                    if attempt < max_retries - 1:
                        print("Waiting before next attempt...")
                        page.wait_for_timeout(2000)
            else:
                print("Failed to click Log out button after all attempts.")

            page.wait_for_timeout(3000) # Wait for 3 seconds after clicking Log out, assuming it might trigger a page reload or transition
            # region Try to click the Log out button with retries

            # endregion MAIN OPERATION

        except Exception as e:
                print(f"An error occurred: {e}")

        finally:
            # Cleanup: Close browser and resources (adjust based on your Playwright setup)
            try:
                if 'page' in locals() and page:
                    page.close()
                if 'context' in locals() and context:
                    context.close()
                if 'browser' in locals() and page:
                    page.close()
                if 'browser' in locals() and browser_process:
                    browser_process.close()
                print("Browser closed successfully.")
            except Exception as close_err:
                print(f"Error closing browser: {close_err}")

            # Exit the script (0 for success, as per search recommendations)
            sys.exit(0)    

if __name__ == "__main__":
    main()
