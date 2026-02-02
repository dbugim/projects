from datetime import date, timedelta, datetime
import datetime as dt
import sys
import os
import random
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
    # For PyInstaller executable
    sys.path.append(os.path.join(sys._MEIPASS, "repository"))
except Exception:
    # For development
    sys.path.append(str(Path(__file__).resolve().parent.parent / "repository"))

# Global variables to keep references
playwright_instance = None
browser_context = None

def cleanup_playwright():
    """Function to clean up Playwright resources on exit"""
    global playwright_instance, browser_context
    try:
        if browser_context:
            browser_context.close()
        if playwright_instance:
            playwright_instance.stop()
    except:
        pass

# Register cleanup function to be called on exit
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

    print("Warning: Make sure Chrome is completely closed")

    try:
        print("Starting Playwright...")
        # IMPORTANT: DO NOT use 'with' here to keep the session active
        playwright_instance = sync_playwright().start()

        print("Launching Chrome with profile...")
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

        print("Browser launched successfully!")

        # Open a new tab
        page = browser_context.new_page()
        print("New tab opened")

        # Navigate to the page
        print("Navigating to Fanfever...")
        page.goto("https://m.fanfever.com/br/milfelectra", timeout=15000)

        print("Chrome opened successfully with all profile data!")
        print("You can now interact with cookies, history, and saved profile data")

        return browser_context, page

    except Exception as e:
        print(f"Error opening Chrome: {e}")
        print("Troubleshooting tips:")
        print("1. Ensure Chrome is completely closed (check Task Manager)")
        print("2. Run this script as administrator")
        print("3. Try using a different profile path if necessary")
        # Clean up resources in case of error
        cleanup_playwright()
        raise

def keep_browser_alive():
    """
    Keeps the browser active indefinitely.
    Call this function after open_chrome_with_profile() if you want to keep the browser open.
    """
    try:
        print("Keeping browser active... (Press Ctrl+C to terminate)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClosing browser...")
        cleanup_playwright()

def open_chrome_native():
    """
    Alternative: opens native Chrome without Playwright.
    Uses the Chrome executable directly with the specified profile.
    """
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data"
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Check if Chrome is installed
    if not os.path.exists(chrome_exe):
        raise FileNotFoundError(f"Chrome not found at: {chrome_exe}")

    # Check if the profile directory exists
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile directory not found: {profile_path}")

    # Command to open Chrome with profile
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
        "https://m.fanfever.com/br/milfelectra"  # URL to open
    ]

    try:
        print("Opening native Chrome...")
        print(f"Executable: {chrome_exe}")
        print(f"Profile: {profile_path}")

        # Start the Chrome process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

        print(f"Chrome started with PID: {process.pid}")
        print("Chrome opened successfully!")

        # Wait for Chrome to initialize
        time.sleep(3)

        # Check if the process is still running
        if process.poll() is None:
            print("Chrome is running correctly")
            return True
        else:
            print("Chrome closed unexpectedly")
            return False

    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return False

    except Exception as e:
        print(f"Error opening native Chrome: {e}")
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

def main():

    # Closes any Chrome Browser instances
    time.sleep(2)
    print("Closing browser instances...")
    os.system("taskkill /f /im chrome.exe")
    time.sleep(2)

    try:
        # Opens Chrome with the specified user profile
        browser_context, page = open_chrome_with_profile()
        #print("Successfully opened Chrome with user profile!")
        print("IMPORTANT: Do not close this terminal to keep Chrome active")
        # If you want the script to keep running indefinitely:
        # keep_browser_alive()
        # OR if you want the script to end but keep Chrome:
        # (Chrome will remain open even after the script ends)
    except Exception as e:
        print(f"Error with Playwright: {e}")
    pyautogui.press('f11')
            
    page.wait_for_timeout(2000)

    # region Calculate tomorrow's date dynamically (outside the loop, as it's the same for all hours)
    today = dt.date.today()  # Or set manually: today = dt.date(2026, 2, 1)
    tomorrow = today + dt.timedelta(days=1)

    # Format components as strings (dd, mm, yyyy) - fixed for the day
    day_str = f"{tomorrow.day:02d}"  # e.g., '02'
    month_str = f"{tomorrow.month:02d}"  # e.g., '02'
    year_str = f"{tomorrow.year:04d}"  # e.g., '2026'
    # endregion

    # Process 24 hours for this day (0-23)
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

        # endregion

        # Try to click the "Add New Story" button with retries
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
        # endregion

        # region copy and paste the file path
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

        # endregion

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
        #endregion

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
        # endregion

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
    
        # endregion
        
        page.wait_for_timeout(7000)

        page.goto('https://m.fanfever.com/br/milfelectra')

        page.wait_for_timeout(3000)

    print("All scheduled stories have been processed.")
    sys.exit(0)

if __name__ == "__main__":
    main()