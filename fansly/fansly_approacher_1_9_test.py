import sys
import os
import atexit
import pyautogui
import time
import csv
import subprocess
import pandas as pd
from pathlib import Path    
from playwright.sync_api import sync_playwright, Page

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

def hashtag_picker_and_control():
    """
    Reads hashtags from CSV, tracks current index, and returns the next hashtag.

    Returns:
        str: The selected hashtag WITHOUT the # symbol

    Raises:
        FileNotFoundError: If hashtags file doesn't exist
        ValueError: If hashtags file is empty
    """

    hashtags_file = r"G:\Meu Drive\Fansly\hashtags_list.csv"
    index_file = r"G:\Meu Drive\Fansly\hashtags_use_index.csv"

    # Validate hashtags file exists
    if not os.path.exists(hashtags_file):
        raise FileNotFoundError(f"Hashtags file not found: {hashtags_file}")

    # Read the list of hashtags
    hashtags = []
    with open(hashtags_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():
                # Remove # if present, we'll add it when needed
                clean_tag = row[0].strip().lstrip('#')
                if clean_tag:  # Only add if not empty after cleaning
                    hashtags.append(clean_tag)

    if not hashtags:
        raise ValueError("Hashtags list is empty or contains only blank lines.")

    #print(f"✅ Loaded {len(hashtags)} hashtags from file")

    # Read the current index
    current_index = 0
    if os.path.exists(index_file):
        try:
            with open(index_file, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        current_index = int(row[0].strip())
                        break
        except (ValueError, IndexError) as e:
            print(f"⚠️ Invalid index file format, resetting to 0. Error: {e}")
            current_index = 0

    # Validate index is within bounds
    if current_index >= len(hashtags):
        print(f"⚠️ Index {current_index} out of bounds, resetting to 0")
        current_index = 0

    # Get the current hashtag
    current_hashtag = hashtags[current_index]
    #print(f"🎯 Selected hashtag: '{current_hashtag}' (index {current_index}/{len(hashtags)-1})")

    # Increment the index, reset if at the end
    next_index = (current_index + 1) % len(hashtags)

    # Write the next index back to the file
    with open(index_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([next_index])

    #print(f"📝 Next index saved: {next_index}")

    return current_hashtag

def search_for_hashtag(page, hashtag: str, max_retries: int = 3) -> bool:
    """
    Searches for a specific hashtag on Fansly.

    Args:
        page: Playwright Page object
        hashtag: The hashtag to search for (WITHOUT the # symbol)
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if search succeeded, False otherwise
    """

    for attempt in range(1, max_retries + 1):
        try:
            #print(f"\n🔄 Attempt {attempt} to search for hashtag...")

            print(f"📌 Using hashtag: '{hashtag}'")

            # Rest of your search logic here...
            # (remove the hashtag = hashtag_picker_and_control() line)

        except Exception as e:
            print(f"❌ Error on attempt {attempt}: {e}")
            if attempt < max_retries:
                print(f"⏳ Waiting 3 seconds before retry...")
                time.sleep(3)
            continue

    return False

def insert_hashtag_and_find(page: Page, hashtag: str) -> bool:
    """
    Insert hashtag into Fansly search and trigger search.

    Args:
        page: Playwright Page object
        hashtag: The hashtag to search for (WITHOUT the # symbol)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use the hashtag parameter directly
        hashtag_text = hashtag
        #print(f"📌 Using hashtag: '{hashtag_text}'")

        # Ensure hashtag starts with #
        if not hashtag_text.startswith('#'):
            hashtag_text = f'#{hashtag_text}'

        # List of selectors to find the search input
        selectors = [
            # Direct CSS selector for the input
            "div.material-input input[type='text']",
            # More specific selector matching the Angular component
            "div.material-input.icon-left.icon-right.margin-bottom-2 input",
            # By class attributes
            "input.ng-untouched.ng-pristine.ng-invalid",
            # XPath alternatives
            "//div[contains(@class, 'material-input')]//input[@type='text']",
            "//div[@class='material-input icon-left icon-right margin-bottom-2']//input"
        ]

        # Try each selector
        for selector in selectors:
            try:
                #print(f"Trying search input selector: {selector}")

                if selector.startswith('//'):
                    # XPath selector
                    xpath_elements = page.locator(f"xpath={selector}")
                    if xpath_elements.count() > 0:
                        input_element = xpath_elements.first

                        # Scroll into view and focus
                        input_element.scroll_into_view_if_needed()
                        input_element.click()
                        page.wait_for_timeout(500)

                        # Clear existing content
                        input_element.fill('')
                        page.wait_for_timeout(300)

                        # Type the hashtag
                        input_element.type(hashtag_text, delay=100)
                        page.wait_for_timeout(500)

                        # Press Enter to trigger search
                        input_element.press('Enter')

                        print(f"✅ Successfully inserted '{hashtag_text}' and triggered search")
                        return True
                else:
                    # CSS selector
                    css_elements = page.locator(selector)
                    if css_elements.count() > 0:
                        input_element = css_elements.first

                        # Scroll into view and focus
                        input_element.scroll_into_view_if_needed()
                        input_element.click()
                        page.wait_for_timeout(500)

                        # Clear existing content
                        input_element.fill('')
                        page.wait_for_timeout(300)

                        # Type the hashtag
                        input_element.type(hashtag_text, delay=100)
                        page.wait_for_timeout(500)

                        # Press Enter to trigger search
                        input_element.press('Enter')

                        print(f"✅ Successfully inserted '{hashtag_text}' and triggered search")
                        return True

            except Exception as e:
                print(f"Failed with selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach
        print("Trying JavaScript fallback approach for search input...")
        fallback_success = page.evaluate(f'''(hashtagText) => {{
            // Try to find the input by various methods
            const inputSelectors = [
                'div.material-input input[type="text"]',
                'input.ng-untouched.ng-pristine',
                '.material-input.icon-left.icon-right input',
                'div.material-input.icon-left.icon-right.margin-bottom-2 input'
            ];

            for (const selector of inputSelectors) {{
                const input = document.querySelector(selector);
                if (input) {{
                    input.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    input.focus();
                    input.value = '';
                    input.value = hashtagText;

                    // Trigger Angular change detection events
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('blur', {{ bubbles: true }}));

                    // Trigger Enter key
                    const enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    }});
                    input.dispatchEvent(enterEvent);

                    return true;
                }}
            }}
            return false;
        }}''', hashtag_text)

        if fallback_success:
            print(f"✅ Successfully inserted '{hashtag_text}' using JavaScript fallback")
            return True

        print("❌ Could not find or interact with search input using any method.")
        return False

    except Exception as e:
        print(f"❌ Error in insert_hashtag_and_find: {str(e)}")
        return False

def click_on_creators_card(page: Page) -> bool:
    """
    Click on the first creator card to navigate to their profile page.
    Waits for elements to be fully loaded before interacting.
    Targets the first <span> element with class 'display-name'.

    Args:
        page: Playwright Page object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Wait for network to be idle (no ongoing requests)
        print("⏳ Waiting for page to stabilize...")
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception as e:
            print(f"⚠️ DOM load timeout (continuing anyway): {e}")

        # Additional wait for dynamic content
        page.wait_for_timeout(2000)

        # Wait for creator display names to be present
        print("⏳ Waiting for creator display names...")
        try:
            page.wait_for_selector("span.display-name", state="attached", timeout=10000)
        except Exception as e:
            print(f"❌ Creator display names not found: {e}")
            return False

        # Verify we found some
        display_name_count = page.locator("span.display-name").count()
        print(f"✅ Found {display_name_count} creator display name(s)")

        if display_name_count == 0:
            print("❌ No creator display names found on page")
            return False

        # Get the first creator's name for logging
        try:
            first_creator_name = page.locator("span.display-name").first.text_content()
            print(f"📍 First creator found: '{first_creator_name}'")
        except:
            first_creator_name = "Unknown"

        # List of selectors to try (all target the first element)
        selectors = [
            # Direct CSS selector for display name span
            "span.display-name",
            # With appaccountcard attribute
            "span[appaccountcard].display-name",
            # Inside app-account-username
            "app-account-username span.display-name",
            # XPath for the span
            "//span[contains(@class, 'display-name')]",
            # XPath with appaccountcard
            "//span[@appaccountcard and contains(@class, 'display-name')]",
        ]

        # Try each selector
        for selector in selectors:
            try:
                print(f"🔍 Trying selector: {selector}")

                if selector.startswith('/'):
                    # XPath selector
                    locator = page.locator(f"xpath={selector}")
                else:
                    # CSS selector
                    locator = page.locator(selector)

                # Check if element exists
                if locator.count() > 0:
                    # Get the text content for logging
                    try:
                        creator_name = locator.first.text_content()
                        print(f"📍 Clicking on creator: '{creator_name}'")
                    except:
                        creator_name = "Unknown"

                    # Scroll into view
                    locator.first.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)

                    # Click the element
                    locator.first.click()
                    print(f"✅ Successfully clicked on '{creator_name}'")

                    # Wait for navigation to complete
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    page.wait_for_timeout(2000)

                    # Verify we navigated
                    current_url = page.url
                    print(f"📍 Current URL after click: {current_url}")

                    return True

            except Exception as e:
                print(f"⚠️ Failed with selector {selector}: {str(e)}")
                continue

        # Fallback JavaScript approach - click the first display name
        print("🔄 Trying JavaScript fallback...")
        fallback_result = page.evaluate('''() => {
            // Find all display name spans
            const spans = document.querySelectorAll('span.display-name');

            if (spans.length > 0) {
                const firstSpan = spans[0];
                const creatorName = firstSpan.textContent.trim();
                console.log('Found first creator:', creatorName);

                // Scroll into view
                firstSpan.scrollIntoView({behavior: 'smooth', block: 'center'});

                // Click after small delay
                setTimeout(() => {
                    firstSpan.click();
                }, 300);

                return {success: true, name: creatorName};
            }
            return {success: false, name: null};
        }''')

        if fallback_result and fallback_result.get('success'):
            creator_name = fallback_result.get('name', 'Unknown')
            print(f"✅ Successfully clicked on '{creator_name}' using JavaScript fallback!")

            # Wait for navigation to complete
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_timeout(2000)

            # Verify we navigated
            current_url = page.url
            print(f"📍 Current URL after click: {current_url}")

            return True

        print("❌ Could not find or click any creator display name")
        return False

    except Exception as e:
        print(f"❌ Error in click_on_creators_card: {str(e)}")
        return False

def save_creator_url_to_sheet(current_url: str) -> bool:
    """
    Save the creator's profile URL to the next empty row in Excel file.

    Args:
        current_url: The URL of the creator's profile to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"💾 Saving creator URL: {current_url}")

        file_path = r"G:\Meu Drive\Fansly\creators_approached_list.xlsx"

        # Get today's date in DD/MM/YYYY format
        from datetime import datetime
        today_date = datetime.now().strftime("%d/%m/%Y")

        # Check if file exists
        if os.path.exists(file_path):
            # Read existing data
            df = pd.read_excel(file_path)

            # Add new URL and date to the dataframe
            new_row = pd.DataFrame({'URL': [current_url], 'DATE': [today_date]})
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            # Create new dataframe if file doesn't exist
            df = pd.DataFrame({'URL': [current_url], 'DATE': [today_date]})

        # Save to Excel
        df.to_excel(file_path, index=False)

        row_number = len(df)
        print(f"✅ URL saved successfully at row {row_number} with date {today_date}")
        return True

    except FileNotFoundError:
        print(f"❌ ERROR: Directory not found: G:\\Meu Drive\\Fansly\\")
        return False
    except PermissionError:
        print(f"❌ ERROR: File is open in another program. Please close it and try again.")
        return False
    except Exception as e:
        print(f"❌ ERROR saving URL to Excel: {e}")
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
    Attempt to find and click the 'Send DM' button (envelope icon) using multiple approaches.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        # Primary selectors - targeting the <i> element directly
        selectors = [
            # Direct icon selectors (most specific first)
            "div.dm-button > i.fa-envelope",
            "i.fa-fw.fal.fa-envelope",
            "i.fal.fa-envelope",
            "i.fa-envelope",

            # Parent container selectors
            "div.sm-mobile-visible.dm-button",
            "div.dm-profile.dm-allowed.new-style div.dm-button",
            "div.dm-button",

            # XPath targeting the icon
            "//div[contains(@class, 'dm-button')]/i[contains(@class, 'fa-envelope')]",
            "//i[@class='fa-fw fal fa-envelope']",
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[2]/div[3]/div[2]/i",
        ]

        # Try each selector
        for selector in selectors:
            try:
                if selector.startswith('/'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("📧 Successfully clicked DM button (XPath)!")
                        return True
                else:
                    # CSS selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("📧 Successfully clicked DM button (CSS)!")
                        return True

            except Exception as e:
                continue

        # Fallback JavaScript approach
        fallback_clicked = page.evaluate('''() => {
            // Strategy 1: Direct icon click
            const icon = document.querySelector('i.fa-fw.fal.fa-envelope') || 
                        document.querySelector('i.fal.fa-envelope') ||
                        document.querySelector('i.fa-envelope');

            if (icon) {
                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                setTimeout(() => icon.click(), 200);
                return true;
            }

            // Strategy 2: Find dm-button parent and click
            const dmButton = document.querySelector('div.sm-mobile-visible.dm-button') ||
                           document.querySelector('div.dm-button');

            if (dmButton) {
                dmButton.scrollIntoView({behavior: 'smooth', block: 'center'});
                setTimeout(() => dmButton.click(), 200);
                return true;
            }

            // Strategy 3: Find by envelope icon and click parent
            const envelopeIcons = document.querySelectorAll('i[class*="fa-envelope"]');
            if (envelopeIcons.length > 0) {
                const parent = envelopeIcons[0].parentElement;
                if (parent) {
                    parent.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => parent.click(), 200);
                    return true;
                }
            }

            return false;
        }''')

        if fallback_clicked:
            page.wait_for_timeout(500)  # Wait for click to register
            print("📧 Successfully clicked DM button (fallback)!")
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

    # Flag to track if we already clicked
    clicked = False

    try:
        # Primary selectors - targeting the <i> element and parent directly
        selectors = [
            # Direct icon selectors (most specific first)
            "div.dropdown-title.blue-1-hover-only > i.fa-image",
            "i.fal.fa-image.hover-effect",
            "i.fa-image.hover-effect",
            "i.fa-image",

            # Parent container selectors
            "div.input-addon.transparent-dropdown.margin-right-2 div.dropdown-title.blue-1-hover-only",
            "div.collapsable-actions div.dropdown-title.blue-1-hover-only",
            "app-group-message-input div.dropdown-title.blue-1-hover-only",
            "div.dropdown-title.blue-1-hover-only",

            # XPath targeting the icon
            "//div[@class='dropdown-title blue-1-hover-only']/i[contains(@class, 'fa-image')]",
            "//i[@class='fal fa-image hover-effect']",
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/div[1]/div/div[1]/div[1]/i",
            "//div[@class='collapsable-actions']//i[contains(@class, 'fa-image')]",
        ]

        # Try each selector
        for selector in selectors:
            if clicked:  # Se já clicou, para o loop
                break

            try:
                if selector.startswith('/'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("📷 Successfully clicked Add Media button (XPath)!")
                        return True  # Return imediatamente
                else:
                    # CSS selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("📷 Successfully clicked Add Media button (CSS)!")
                        return True  # Return imediatamente

            except Exception:
                continue

        # Só chega aqui se TODOS os seletores falharam
        if not clicked:
            # Fallback JavaScript approach
            fallback_clicked = page.evaluate('''() => {
                // Strategy 1: Direct icon or parent click
                const icon = document.querySelector('i.fal.fa-image.hover-effect') || 
                            document.querySelector('i.fa-image.hover-effect') ||
                            document.querySelector('i.fa-image');

                if (icon) {
                    const parent = icon.closest('div.dropdown-title');
                    const clickTarget = parent || icon;
                    clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => clickTarget.click(), 200);
                    return true;
                }

                // Strategy 2: Find dropdown-title in collapsable-actions
                const dropdownTitle = document.querySelector('div.collapsable-actions div.dropdown-title.blue-1-hover-only');
                if (dropdownTitle) {
                    dropdownTitle.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => dropdownTitle.click(), 200);
                    return true;
                }

                return false;
            }''')

            if fallback_clicked:
                page.wait_for_timeout(500)
                print("📷 Successfully clicked Add Media button (fallback)!")
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
        # Primary selectors - targeting the xd-localization-string element and parent div
        selectors = [
            # Direct element selectors (most specific first)
            "div.dropdown-list.top.left > div:nth-child(2) > xd-localization-string",
            "div.dropdown-list > div:nth-child(2) > xd-localization-string",
            "div.dropdown-open xd-localization-string",

            # Parent div selectors (2nd child in dropdown)
            "div.dropdown-list.top.left > div:nth-child(2)",
            "div.dropdown-list > div:nth-child(2)",

            # Generic dropdown selectors
            "div.dropdown-open div.dropdown-list xd-localization-string",
            "div.input-addon.dropdown-open xd-localization-string",

            # XPath targeting the element
            "//div[@class='dropdown-list top left']/div[2]/xd-localization-string",
            "/html/body/app-root/div/div[1]/div/app-messages-route/div/div/div[2]/app-messages-conversation-route/app-group-message-container/app-group-message-input/div[2]/div[1]/div/div[1]/div[2]/div[2]/xd-localization-string",
            "//div[@class='dropdown-list top left']/div[2]",
            "//xd-localization-string[contains(text(), 'From Vault')]",
        ]

        # Try each selector
        for selector in selectors:
            try:
                if selector.startswith('/'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                    if element.count() > 0:
                        # Verify text content if possible
                        try:
                            text = element.first.inner_text()
                            if text and "From Vault" not in text:
                                continue
                        except:
                            pass

                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)

                        # Try clicking the element, if fails try parent div
                        try:
                            element.first.click(force=True)
                        except:
                            parent = page.locator(f"xpath={selector}/parent::div")
                            if parent.count() > 0:
                                parent.first.click(force=True)

                        print("🗄️ Successfully clicked 'From Vault' option (XPath)!")
                        return True
                else:
                    # CSS selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        # Verify text content if possible
                        try:
                            text = element.first.inner_text()
                            if text and "From Vault" not in text:
                                continue
                        except:
                            pass

                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("🗄️ Successfully clicked 'From Vault' option (CSS)!")
                        return True

            except Exception:
                continue

        # Fallback JavaScript approach
        fallback_clicked = page.evaluate('''() => {
            // Strategy 1: Find xd-localization-string with "From Vault" text
            const localizationStrings = document.querySelectorAll('xd-localization-string');
            for (const element of localizationStrings) {
                if (element.textContent.trim() === 'From Vault') {
                    const clickTarget = element.closest('div.dropdown-list > div') || 
                                      element.parentElement || 
                                      element;
                    clickTarget.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => clickTarget.click(), 200);
                    return true;
                }
            }

            // Strategy 2: Find second child in dropdown-list
            const dropdownList = document.querySelector('div.dropdown-list.top.left') ||
                               document.querySelector('div.dropdown-list');
            if (dropdownList) {
                const items = dropdownList.querySelectorAll(':scope > div');
                if (items.length >= 2) {
                    const secondItem = items[1];
                    if (secondItem && secondItem.textContent.includes('From Vault')) {
                        secondItem.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => secondItem.click(), 200);
                        return true;
                    }
                }
            }

            // Strategy 3: Find in open dropdown by text
            const openDropdown = document.querySelector('div.dropdown-open');
            if (openDropdown) {
                const allDivs = openDropdown.querySelectorAll('div');
                for (const div of allDivs) {
                    if (div.textContent.trim() === 'From Vault') {
                        div.scrollIntoView({behavior: 'smooth', block: 'center'});
                        setTimeout(() => div.click(), 200);
                        return true;
                    }
                }
            }

            return false;
        }''')

        if fallback_clicked:
            page.wait_for_timeout(500)
            print("🗄️ Successfully clicked 'From Vault' option (fallback)!")
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
        # Primary selectors - targeting the <i> circle icon element
        selectors = [
            # Direct icon selectors (most specific first)
            "div.image-controls > div > i.fa-circle",
            "i.fa-fw.fal.fa-circle",
            "i.fal.fa-circle",
            "div.image-controls i.fa-circle",
            "i.fa-circle",

            # Parent container selectors
            "div.render-container div.image-controls > div",
            "div.vault-row div.image-controls i",
            "app-media-vault div.image-controls i",

            # XPath targeting the icon
            "//div[@class='image-controls']/div/i[contains(@class, 'fa-circle')]",
            "//i[@class='fa-fw fal fa-circle']",
            "/html/body/app-root/div/div[3]/app-media-vault-picker-modal/div/div[2]/app-media-vault/div[4]/div/div[2]/div[2]/div[3]/div/i",
            "//div[@class='render-container']//div[@class='image-controls']//i",
        ]

        # Try each selector
        for selector in selectors:
            try:
                if selector.startswith('/'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)

                        # Try clicking the icon, if fails try parent div
                        try:
                            element.first.click(force=True)
                        except:
                            parent = page.locator(f"xpath={selector}/parent::div")
                            if parent.count() > 0:
                                parent.first.click(force=True)

                        print("✅ Successfully selected media item (XPath)!")
                        return True
                else:
                    # CSS selector
                    element = page.locator(selector)
                    if element.count() > 0:
                        element.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(300)
                        element.first.click(force=True)
                        print("✅ Successfully selected media item (CSS)!")
                        return True

            except Exception:
                continue

        # Fallback JavaScript approach
        fallback_clicked = page.evaluate('''() => {
            // Strategy 1: Find fa-circle icon within image-controls
            const imageControls = document.querySelector('div.image-controls');
            if (imageControls) {
                const icon = imageControls.querySelector('i.fa-circle') ||
                           imageControls.querySelector('i.fal.fa-circle') ||
                           imageControls.querySelector('div > i');
                if (icon) {
                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => icon.click(), 200);
                    return true;
                }
            }

            // Strategy 2: Find by fa-circle icon class in vault
            const circleIcons = document.querySelectorAll('i.fa-fw.fal.fa-circle');
            if (circleIcons.length > 0) {
                const icon = circleIcons[0];
                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                setTimeout(() => icon.click(), 200);
                return true;
            }

            // Strategy 3: Find in render-container
            const renderContainer = document.querySelector('div.render-container');
            if (renderContainer) {
                const icon = renderContainer.querySelector('div.image-controls i');
                if (icon) {
                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    setTimeout(() => icon.click(), 200);
                    return true;
                }
            }

            // Strategy 4: Any fa-circle in vault modal
            const allCircles = document.querySelectorAll('i[class*="fa-circle"]');
            if (allCircles.length > 0) {
                const icon = allCircles[0];
                icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                setTimeout(() => icon.click(), 200);
                return true;
            }

            return false;
        }''')

        if fallback_clicked:
            page.wait_for_timeout(500)
            print("✅ Successfully selected media item (fallback)!")
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
    Returns True if unchecked successfully or already unchecked, False otherwise.
    """
    try:
        # First check if checkbox is already unchecked
        is_unchecked = page.evaluate('''() => {
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

        if is_unchecked:
            print("✅ 'Require Subscription' checkbox is already unchecked, skipping!")
            return True

        # List of selectors to try - targeting the parent div, not the icon
        selectors = [
            # Parent div selector (recommended target)
            "body > app-root > div > div.modal-wrapper > app-account-media-upload > div > div.modal-content > div.media-settings.flex-col.margin-bottom-2 > app-account-media-permission-flags-editor > div.permission-settings-container > div:nth-child(3) > app-xd-checkbox > div",
            # Simplified versions
            "div.permission-settings-container > div:nth-child(3) app-xd-checkbox div.checkbox",
            "app-account-media-permission-flags-editor div:nth-child(3) div.checkbox.selected",
            # XPath to parent div
            "/html/body/app-root/div/div[3]/app-account-media-upload/div/div[2]/div[2]/app-account-media-permission-flags-editor/div[2]/div[3]/app-xd-checkbox/div",
            "//div[@class='permission-settings-container']/div[3]//app-xd-checkbox//div[@class='checkbox selected']"
        ]

        # Try each selector
        for selector in selectors:
            try:
                if selector.startswith('/'):
                    # XPath selector
                    element = page.locator(f"xpath={selector}")
                else:
                    # CSS selector
                    element = page.locator(selector)

                if element.count() > 0:
                    # Wait for element to be stable
                    page.wait_for_timeout(500)

                    # Verify it's selected before clicking
                    is_selected = element.first.evaluate('''el => {
                        return el.classList.contains('selected') || 
                               el.querySelector('i.fa-check') !== null;
                    }''')

                    if not is_selected:
                        continue

                    # Scroll into view
                    element.first.scroll_into_view_if_needed()
                    page.wait_for_timeout(300)

                    # Click to uncheck
                    element.first.click(force=True)

                    # Verify it was unchecked
                    page.wait_for_timeout(500)
                    still_selected = element.first.evaluate('''el => {
                        return el.classList.contains('selected');
                    }''')

                    if not still_selected:
                        print("✅ Successfully unchecked 'Require Subscription' checkbox!")
                        return True

            except Exception as e:
                continue

        # Fallback JavaScript approach
        fallback_success = page.evaluate('''() => {
            return new Promise((resolve) => {
                setTimeout(() => {
                    const permissionSettings = document.querySelector('div.permission-settings-container');
                    if (permissionSettings) {
                        const children = permissionSettings.querySelectorAll(':scope > div');
                        if (children.length >= 3) {
                            const thirdChild = children[2];
                            const checkbox = thirdChild.querySelector('div.checkbox');
                            if (checkbox && checkbox.classList.contains('selected')) {
                                checkbox.scrollIntoView({behavior: 'smooth', block: 'center'});
                                setTimeout(() => {
                                    checkbox.click();
                                    // Verify it was unchecked
                                    setTimeout(() => {
                                        const stillSelected = checkbox.classList.contains('selected');
                                        resolve(!stillSelected);
                                    }, 300);
                                }, 200);
                                return;
                            }
                        }
                    }
                    resolve(false);
                }, 500);
            });
        }''')

        if fallback_success:
            print("✅ Successfully unchecked 'Require Subscription' checkbox via fallback!")
            return True

        print("⚠️ Could not find or uncheck 'Require Subscription' checkbox - continuing anyway.")
        return False

    except Exception as e:
        print(f"❌ Error in click_to_uncheck_require_subscription: {str(e)} - continuing anyway.")
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
    Attempt to find and click the notes icon (sticky note) to change creator's nickname.
    Returns True if clicked successfully, False otherwise (but doesn't crash the program).
    """
    try:
        print("🔍 Attempting to click notes icon...")

        # Wait a moment for the page to be fully stable
        page.wait_for_timeout(1000)

        # Strategy 1: Direct JavaScript click on the exact element
        try:
            js_clicked = page.evaluate('''() => {
                const icon = document.querySelector("body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible > div > app-profile-route > div > div > div > div.profile-header > div.profile-details-2 > div > app-account-username > a > span > i");
                if (icon) {
                    icon.scrollIntoView({behavior: 'smooth', block: 'center'});
                    return new Promise(resolve => {
                        setTimeout(() => {
                            icon.click();
                            icon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            resolve(true);
                        }, 300);
                    });
                }
                return false;
            }''')

            if js_clicked:
                print("📝 Successfully clicked notes icon (Strategy 1: Direct JS)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 1 failed: {str(e)}")

        # Strategy 2: Find by the specific class combination
        try:
            icon = page.locator("i.fal.fa-note-sticky.notes-icon.has-notes")
            if icon.count() > 0:
                icon.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                icon.first.click(force=True)
                print("📝 Successfully clicked notes icon (Strategy 2: Class combination)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 2 failed: {str(e)}")

        # Strategy 3: XPath
        try:
            xpath = "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[1]/div[3]/div/app-account-username/a/span/i"
            icon = page.locator(f"xpath={xpath}")
            if icon.count() > 0:
                icon.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                icon.first.click(force=True)
                print("📝 Successfully clicked notes icon (Strategy 3: XPath)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 3 failed: {str(e)}")

        # Strategy 4: Find within app-account-username component
        try:
            icon = page.locator("app-account-username i.fa-note-sticky")
            if icon.count() > 0:
                icon.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                icon.first.click(force=True)
                print("📝 Successfully clicked notes icon (Strategy 4: Component selector)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 4 failed: {str(e)}")

        # Strategy 5: Comprehensive JavaScript fallback
        try:
            fallback_clicked = page.evaluate('''() => {
                return new Promise((resolve) => {
                    setTimeout(() => {
                        // Try exact class match first
                        let icon = document.querySelector('i.fal.fa-note-sticky.notes-icon.has-notes');

                        // Try without has-notes class
                        if (!icon) {
                            icon = document.querySelector('i.fal.fa-note-sticky.notes-icon');
                        }

                        // Try broader match
                        if (!icon) {
                            icon = document.querySelector('app-account-username i.fa-note-sticky');
                        }

                        // Try in profile-details-2
                        if (!icon) {
                            icon = document.querySelector('div.profile-details-2 i.fa-note-sticky');
                        }

                        if (icon) {
                            // Make sure element is visible
                            icon.style.opacity = '1';
                            icon.style.visibility = 'visible';
                            icon.style.display = 'inline-block';
                            icon.style.pointerEvents = 'auto';

                            icon.scrollIntoView({behavior: 'smooth', block: 'center'});

                            setTimeout(() => {
                                icon.click();
                                icon.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                icon.dispatchEvent(new Event('click', { bubbles: true }));
                                resolve(true);
                            }, 300);
                        } else {
                            resolve(false);
                        }
                    }, 500);
                });
            }''')

            if fallback_clicked:
                print("📝 Successfully clicked notes icon (Strategy 5: Fallback JS)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 5 failed: {str(e)}")

        print("⚠️ Could not find or click notes icon - continuing anyway.")
        return False

    except Exception as e:
        print(f"❌ Error in click_to_change_creators_nickname: {str(e)} - continuing anyway.")
        return False

def insert_custom_name_for_creator(page, custom_name):
    """
    Attempt to find the notes/nickname input field and insert custom name.
    Uses character-by-character typing to ensure Angular properly detects changes.
    Returns True if text inserted successfully, False otherwise (but doesn't crash the program).

    Args:
        page: Playwright page object
        custom_name: The custom nickname to insert (e.g., "Abordada")
    """
    try:
        print(f"🔍 Attempting to insert custom name: '{custom_name}'...")

        # Wait a moment for the modal to be fully rendered
        page.wait_for_timeout(1000)

        # Strategy 1: Character-by-character typing (most reliable for Angular)
        try:
            typed_successfully = page.evaluate('''(customName) => {
                return new Promise((resolve) => {
                    const input = document.querySelector("body > app-root > div > div.modal-wrapper > app-notes-edit-modal > div > div.modal-content.flex-col > div.material-input.icon-right > input");

                    if (input) {
                        input.scrollIntoView({behavior: 'smooth', block: 'center'});

                        setTimeout(() => {
                            input.focus();
                            input.click();

                            // Clear existing value
                            input.value = '';
                            input.dispatchEvent(new Event('input', { bubbles: true }));

                            setTimeout(() => {
                                // Type character by character with events
                                let index = 0;
                                const typeNext = () => {
                                    if (index < customName.length) {
                                        input.value += customName[index];

                                        // Fire input event for each character
                                        input.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
                                        input.dispatchEvent(new InputEvent('input', { 
                                            bubbles: true, 
                                            cancelable: true,
                                            composed: true,
                                            data: customName[index]
                                        }));

                                        index++;
                                        setTimeout(typeNext, 50);
                                    } else {
                                        // Finish with change and blur events
                                        input.dispatchEvent(new Event('change', { bubbles: true }));
                                        input.dispatchEvent(new Event('blur', { bubbles: true }));
                                        input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));

                                        resolve(true);
                                    }
                                };

                                typeNext();
                            }, 200);
                        }, 300);
                    } else {
                        resolve(false);
                    }
                });
            }''', custom_name)

            if typed_successfully:
                print(f"📝 Successfully inserted custom name: '{custom_name}' (Strategy 1: Char-by-char typing)!")
                page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"Strategy 1 failed: {str(e)}")

        # Strategy 2: Playwright's type method (simulates real typing)
        try:
            input_field = page.locator("app-notes-edit-modal div.material-input input")
            if input_field.count() > 0:
                input_field.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)

                # Triple-click to select all text
                input_field.first.click(click_count=3)
                page.wait_for_timeout(100)

                # Type the new name (simulates real keyboard input)
                input_field.first.type(custom_name, delay=50)
                page.wait_for_timeout(300)

                # Press Tab to blur and trigger change detection
                input_field.first.press('Tab')

                print(f"📝 Successfully inserted custom name: '{custom_name}' (Strategy 2: Playwright type)!")
                page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"Strategy 2 failed: {str(e)}")

        # Strategy 3: XPath with simulated typing
        try:
            xpath = "/html/body/app-root/div/div[3]/app-notes-edit-modal/div/div[2]/div[1]/input"
            input_field = page.locator(f"xpath={xpath}")
            if input_field.count() > 0:
                input_field.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                input_field.first.click()
                page.wait_for_timeout(200)

                # Select all and delete
                input_field.first.press('Control+A')
                page.wait_for_timeout(50)
                input_field.first.press('Delete')
                page.wait_for_timeout(100)

                # Type new value
                input_field.first.type(custom_name, delay=50)
                page.wait_for_timeout(300)

                # Blur the field
                input_field.first.press('Tab')

                print(f"📝 Successfully inserted custom name: '{custom_name}' (Strategy 3: XPath typing)!")
                page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"Strategy 3 failed: {str(e)}")

        # Strategy 4: Force Angular to detect changes via ngModel
        try:
            forced_update = page.evaluate('''(customName) => {
                return new Promise((resolve) => {
                    setTimeout(() => {
                        let input = document.querySelector('app-notes-edit-modal div.material-input input');

                        if (!input) {
                            input = document.querySelector('app-notes-edit-modal input[type="text"]');
                        }

                        if (input) {
                            input.focus();
                            input.value = customName;

                            // Trigger Angular's change detection manually
                            const angularInput = new Event('input', { 
                                bubbles: true, 
                                cancelable: true,
                                composed: true 
                            });

                            const angularChange = new Event('change', { 
                                bubbles: true, 
                                cancelable: true 
                            });

                            // Fire events in sequence
                            input.dispatchEvent(angularInput);

                            setTimeout(() => {
                                input.dispatchEvent(angularChange);

                                setTimeout(() => {
                                    input.blur();
                                    input.dispatchEvent(new Event('blur', { bubbles: true }));

                                    // Try to trigger Angular's zone
                                    if (window.ng && window.ng.probe) {
                                        const debugElement = window.ng.probe(input);
                                        if (debugElement && debugElement.injector) {
                                            const appRef = debugElement.injector.get(window.ng.coreTokens.ApplicationRef);
                                            if (appRef) {
                                                appRef.tick();
                                            }
                                        }
                                    }

                                    resolve(true);
                                }, 100);
                            }, 100);
                        } else {
                            resolve(false);
                        }
                    }, 500);
                });
            }''', custom_name)

            if forced_update:
                print(f"📝 Successfully inserted custom name: '{custom_name}' (Strategy 4: Forced Angular detection)!")
                page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"Strategy 4 failed: {str(e)}")

        # Strategy 5: Comprehensive fallback with verification
        try:
            verified_insert = page.evaluate('''(customName) => {
                return new Promise((resolve) => {
                    setTimeout(() => {
                        const selectors = [
                            'app-notes-edit-modal div.material-input.icon-right input',
                            'app-notes-edit-modal input[type="text"]',
                            'div.modal-content.flex-col input',
                            'app-notes-edit-modal input'
                        ];

                        let input = null;
                        for (const selector of selectors) {
                            input = document.querySelector(selector);
                            if (input) break;
                        }

                        if (input) {
                            input.scrollIntoView({behavior: 'smooth', block: 'center'});
                            input.focus();

                            setTimeout(() => {
                                // Clear
                                input.value = '';
                                input.dispatchEvent(new Event('input', { bubbles: true }));

                                setTimeout(() => {
                                    // Set value
                                    input.value = customName;

                                    // Comprehensive event dispatch
                                    ['input', 'change', 'keyup', 'blur'].forEach(eventType => {
                                        input.dispatchEvent(new Event(eventType, { 
                                            bubbles: true, 
                                            cancelable: true,
                                            composed: true
                                        }));
                                    });

                                    // Verify the value was set
                                    setTimeout(() => {
                                        resolve(input.value === customName);
                                    }, 200);
                                }, 200);
                            }, 200);
                        } else {
                            resolve(false);
                        }
                    }, 500);
                });
            }''', custom_name)

            if verified_insert:
                print(f"📝 Successfully inserted custom name: '{custom_name}' (Strategy 5: Verified fallback)!")
                page.wait_for_timeout(1000)
                return True
        except Exception as e:
            print(f"Strategy 5 failed: {str(e)}")

        print(f"⚠️ Could not insert custom name '{custom_name}' - continuing anyway.")
        return False

    except Exception as e:
        print(f"❌ Error in insert_custom_name_for_creator: {str(e)} - continuing anyway.")
        return False

def close_custom_name_window(page):
    """
    Attempt to find and click the close button (X icon) to close the custom name modal.
    If clicking fails, tries pressing ESC key as fallback.
    Returns True if closed successfully, False otherwise (but doesn't crash the program).
    """
    try:
        print("🔍 Attempting to close custom name window...")

        # Wait a moment for any animations to complete
        page.wait_for_timeout(500)

        # Strategy 1: Press ESC key (most reliable for modals according to research)
        try:
            page.keyboard.press('Escape')
            page.wait_for_timeout(500)

            # Verify modal is closed by checking if it's still visible
            modal_gone = page.evaluate('''() => {
                const modal = document.querySelector('app-notes-edit-modal');
                return !modal || modal.offsetParent === null;
            }''')

            if modal_gone:
                print("✅ Successfully closed custom name window (Strategy 1: ESC key)!")
                return True
        except Exception as e:
            print(f"Strategy 1 (ESC) failed: {str(e)}")

        # Strategy 2: Direct JavaScript click with comprehensive event triggering
        try:
            js_clicked = page.evaluate('''() => {
                const closeBtn = document.querySelector("body > app-root > div > div.modal-wrapper > app-notes-edit-modal > div > div.modal-header.flex-col > div.actions > i");
                if (closeBtn) {
                    closeBtn.scrollIntoView({behavior: 'smooth', block: 'center'});

                    // Make absolutely sure it's clickable
                    closeBtn.style.pointerEvents = 'auto';
                    closeBtn.style.cursor = 'pointer';

                    return new Promise(resolve => {
                        setTimeout(() => {
                            // Fire multiple event types
                            closeBtn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                            closeBtn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                            closeBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            closeBtn.click();

                            // Check if modal closed
                            setTimeout(() => {
                                const modal = document.querySelector('app-notes-edit-modal');
                                resolve(!modal || modal.offsetParent === null);
                            }, 300);
                        }, 300);
                    });
                }
                return false;
            }''')

            if js_clicked:
                print("✅ Successfully closed custom name window (Strategy 2: Direct JS with events)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 2 failed: {str(e)}")

        # Strategy 3: Click on the parent button element instead of the icon
        try:
            parent_clicked = page.evaluate('''() => {
                const icon = document.querySelector('app-notes-edit-modal i.fa-xmark');
                if (icon && icon.parentElement) {
                    const parent = icon.parentElement;
                    parent.scrollIntoView({behavior: 'smooth', block: 'center'});

                    return new Promise(resolve => {
                        setTimeout(() => {
                            parent.click();
                            parent.dispatchEvent(new MouseEvent('click', { bubbles: true }));

                            setTimeout(() => {
                                const modal = document.querySelector('app-notes-edit-modal');
                                resolve(!modal || modal.offsetParent === null);
                            }, 300);
                        }, 300);
                    });
                }
                return false;
            }''')

            if parent_clicked:
                print("✅ Successfully closed custom name window (Strategy 3: Parent click)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 3 failed: {str(e)}")

        # Strategy 4: Playwright click with force
        try:
            close_btn = page.locator("app-notes-edit-modal i.fa-xmark")
            if close_btn.count() > 0:
                close_btn.first.scroll_into_view_if_needed()
                page.wait_for_timeout(300)

                # Try regular click first
                try:
                    close_btn.first.click(timeout=2000)
                except:
                    # Force click if regular fails
                    close_btn.first.click(force=True)

                page.wait_for_timeout(500)

                # Verify modal closed
                modal_gone = page.evaluate('''() => {
                    const modal = document.querySelector('app-notes-edit-modal');
                    return !modal || modal.offsetParent === null;
                }''')

                if modal_gone:
                    print("✅ Successfully closed custom name window (Strategy 4: Playwright click)!")
                    return True
        except Exception as e:
            print(f"Strategy 4 failed: {str(e)}")

        # Strategy 5: Click anywhere outside the modal (backdrop click)
        try:
            backdrop_clicked = page.evaluate('''() => {
                const modalWrapper = document.querySelector('div.modal-wrapper');
                if (modalWrapper) {
                    return new Promise(resolve => {
                        setTimeout(() => {
                            // Click on the wrapper (outside the modal content)
                            modalWrapper.click();
                            modalWrapper.dispatchEvent(new MouseEvent('click', { bubbles: true }));

                            setTimeout(() => {
                                const modal = document.querySelector('app-notes-edit-modal');
                                resolve(!modal || modal.offsetParent === null);
                            }, 300);
                        }, 300);
                    });
                }
                return false;
            }''')

            if backdrop_clicked:
                print("✅ Successfully closed custom name window (Strategy 5: Backdrop click)!")
                page.wait_for_timeout(500)
                return True
        except Exception as e:
            print(f"Strategy 5 failed: {str(e)}")

        # Strategy 6: Try ESC key again as final fallback
        try:
            page.keyboard.press('Escape')
            page.wait_for_timeout(800)

            modal_gone = page.evaluate('''() => {
                const modal = document.querySelector('app-notes-edit-modal');
                return !modal || modal.offsetParent === null;
            }''')

            if modal_gone:
                print("✅ Successfully closed custom name window (Strategy 6: ESC key final)!")
                return True
        except Exception as e:
            print(f"Strategy 6 (ESC final) failed: {str(e)}")

        print("⚠️ Could not close custom name window - continuing anyway.")
        return False

    except Exception as e:
        print(f"❌ Error in close_custom_name_window: {str(e)} - continuing anyway.")
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

    # region Get hashtag with validation
    try:
        hashtag = hashtag_picker_and_control()
        if not hashtag or not hashtag.strip():
            print("❌ ERROR: Hashtag is empty!")
            return  # Exit without closing page
    except Exception as e:
        print(f"❌ ERROR selecting hashtag: {e}")
        return  # Exit without closing page
    # endregion

    page.wait_for_timeout(2000)

    # region Insert hashtag and trigger search with retries
    max_retries = 3
    for attempt in range(max_retries):
        if insert_hashtag_and_find(page, hashtag):  # Pass hashtag as parameter
            break
        else:
            print(f"⚠️ Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("⏳ Waiting before next attempt...")
                page.wait_for_timeout(2000)
    else:
        print("❌ Failed to search hashtag after all attempts.")
        return  # Exit without closing page

    # Wait for search results to load
    page.wait_for_timeout(2000)
    # endregion

    # region Process multiple creators from hashtag search
    max_creators_to_process = 4  # Limit for testing
    current_creator_index = 0
    processed_count = 0  # Track actual processed creators

    while processed_count < max_creators_to_process:
        print(f"\n{'='*60}")
        print(f"🎯 Checking creator at index {current_creator_index}")
        print(f"   Processed so far: {processed_count}/{max_creators_to_process}")
        print(f"{'='*60}\n")

        # Wait for search results container
        try:
            page.wait_for_selector('div.search-result-container', timeout=5000)
        except:
            print("❌ Search results container not found. Exiting loop.")
            break

        # Get all creator cards
        creator_cards = page.locator('div.flex-row.follower').all()

        if len(creator_cards) == 0:
            print("❌ No creator cards found. Exiting loop.")
            break

        if current_creator_index >= len(creator_cards):
            print(f"⚠️ Reached end of creator list ({len(creator_cards)} total). Stopping.")
            break

        # Get the current creator's display name for validation
        try:
            # Try to get display name first
            display_name_element = creator_cards[current_creator_index].locator('span.display-name').first
            display_name = display_name_element.text_content().strip()
            print(f"📍 Checking creator display name: {display_name}")

            # Also get username for logging purposes
            try:
                username_element = creator_cards[current_creator_index].locator('span.user-name').first
                username = username_element.text_content().strip()
                print(f"   Username: {username}")
            except:
                username = "Unknown"
        except:
            # If display name not found, try username as fallback
            try:
                username_element = creator_cards[current_creator_index].locator('span.user-name').first
                display_name = username_element.text_content().strip()
                username = display_name
                print(f"📍 Checking creator (fallback to username): {display_name}")
            except:
                display_name = f"Creator #{current_creator_index + 1}"
                username = display_name
                print(f"📍 Checking creator: {display_name} (name not detected)")

        # region Skip creators with "Abordada" (case-insensitive), "/" or "$"
        display_name_lower = display_name.lower()

        if "abordada" in display_name_lower:
            print(f"⏭️ Skipping '{display_name}' - contains 'Abordada'")
            current_creator_index += 1
            continue

        if "/" in display_name:
            print(f"⏭️ Skipping '{display_name}' - contains '/'")
            current_creator_index += 1
            continue

        if "$" in display_name:
            print(f"⏭️ Skipping '{display_name}' - contains '$'")
            current_creator_index += 1
            continue

        if "electra" in display_name.lower():
            print(f"⏭️ Skipping '{display_name}' - contains 'electra'")
            current_creator_index += 1
            continue

        print(f"✅ Creator '{display_name}' passed validation checks")
        # endregion

        # region Try to click creator card with retries
        max_retries = 3
        clicked = False

        for attempt in range(max_retries):
            print(f"\n🔄 Attempt {attempt + 1} to click creator card...")
            try:
                # Scroll the specific creator card into view
                creator_cards[current_creator_index].scroll_into_view_if_needed()
                page.wait_for_timeout(500)

                # Try to click the creator's profile link
                profile_link = creator_cards[current_creator_index].locator('a.username-wrapper').first

                # Get href for verification
                href = profile_link.get_attribute('href')
                print(f"   → Clicking profile: {href}")

                # Click with force if needed
                profile_link.click(force=True, timeout=5000)

                # Wait for navigation
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                page.wait_for_timeout(2000)

                # Verify we're on the creator's page
                if href in page.url:
                    print(f"✅ Successfully navigated to creator profile: {page.url}")
                    clicked = True
                    break
                else:
                    print(f"⚠️ URL mismatch. Expected {href} but got {page.url}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print("⏳ Waiting before next attempt...")
                    page.wait_for_timeout(2000)
                    # Re-fetch creator cards in case DOM changed
                    page.wait_for_selector('div.search-result-container', timeout=5000)
                    creator_cards = page.locator('div.flex-row.follower').all()

        if not clicked:
            print(f"❌ Failed to click creator {username} after all attempts. Skipping...")
            current_creator_index += 1
            continue
        # endregion

        # Wait for creator profile page to fully load
        print("⏳ Waiting for creator profile page to load...")
        page.wait_for_timeout(2000)

        page.wait_for_timeout(2000)

        # region Save the new creator's URL into a list
        current_url = page.url
        if save_creator_url_to_sheet(current_url):
            print("✅ Creator URL saved to Excel!")
        else:
            print("⚠️ Failed to save URL to Excel")
        # endregion

        page.wait_for_timeout(3000)

        # region Manage Creators nickname customization
        # region Try to click the notes icon to change creator's nickname with retries (non-blocking)
        max_retries = 3
        notes_clicked = False
        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to click notes icon...")
            if click_to_change_creators_nickname(page):
                #print("Successfully clicked notes icon!")
                notes_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
                    page.wait_for_timeout(2000)

        if not notes_clicked:
            print("Could not click notes icon after all attempts. Proceeding with next steps...")
        else:
            page.wait_for_timeout(1000)

        # Continue with next instructions regardless of click status
        # endregion

        page.wait_for_timeout(2000)

        # region Try to insert custom name for creator with retries (non-blocking)
        custom_name = "Abordada"  # Or whatever name you want to use
        max_retries = 3
        name_inserted = False

        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to insert custom name...")
            if insert_custom_name_for_creator(page, custom_name):
                #print(f"Successfully inserted custom name: '{custom_name}'!")
                name_inserted = True
                break
            else:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
                    page.wait_for_timeout(2000)

        if not name_inserted:
            print(f"Could not insert custom name '{custom_name}' after all attempts. Proceeding with next steps...")
        else:
            page.wait_for_timeout(1000)

        # Continue with next instructions regardless of insertion status
        # endregion

        page.wait_for_timeout(2000)

        # region Try to close custom name window with retries (non-blocking)
        max_retries = 3
        window_closed = False

        for attempt in range(max_retries):
            #print(f"\nAttempt {attempt + 1} to close custom name window...")
            if close_custom_name_window(page):
                #print("Successfully closed custom name window!")
                window_closed = True
                break
            else:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Waiting before next attempt...")
                    page.wait_for_timeout(2000)

        if not window_closed:
            print("Could not close custom name window after all attempts. Proceeding with next steps...")
        else:
            page.wait_for_timeout(1000)

        # Continue with next instructions regardless of close status
        # endregion

        page.wait_for_timeout(2000)
        # endregion 

        # region Try to click the Follow button with retries
        max_retries = 3
        for attempt in range(max_retries):
            if click_on_follow_button(page):
                break
            else:
                print(f"Attempt {attempt + 1} failed.")
                if attempt < max_retries - 1:
                    print("Waiting before next attempt...")
                    page.wait_for_timeout(2000)
        else:
            print("Failed to click Follow button after all attempts.")
        page.wait_for_timeout(3000)
        # endregion

        # region Try to close the pay‑to‑follow modal window with retries (non‑blocking)
        max_retries = 3
        modal_closed = False
        for attempt in range(max_retries):
            if click_to_close_to_pay_to_follow_window(page):
                modal_closed = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not modal_closed:
            print("Could not close pay‑to‑follow modal after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click the creator's interactions options with retries (non‑blocking)
        max_retries = 3
        options_clicked = False
        for attempt in range(max_retries):
            if click_on_creators_interactions_options(page):
                options_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not options_clicked:
            print("Could not click creator's interactions options after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click 'Add To List' option with retries (non‑blocking)
        max_retries = 3
        add_to_list_clicked = False
        for attempt in range(max_retries):
            if click_to_add_to_list(page):
                add_to_list_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not add_to_list_clicked:
            print("Could not click 'Add To List' after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to add creator to the 'Creators ⭐' list with retries (non‑blocking)
        max_retries = 3
        added_to_list = False
        for attempt in range(max_retries):
            if click_to_add_on_the_creators_list(page):
                added_to_list = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not added_to_list:
            print("Could not add to Creators list after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click Save button in list‑addition modal with retries (non‑blocking)
        max_retries = 3
        save_clicked = False
        for attempt in range(max_retries):
            if click_on_save_button_to_list_addition(page):
                save_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not save_clicked:
            print("Could not click Save button after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1500)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click the creator's interactions options again (non‑blocking)
        max_retries = 3
        options_clicked = False
        for attempt in range(max_retries):
            if click_on_creators_interactions_options(page):
                options_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not options_clicked:
            print("Could not click creator's interactions options after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to mute user with retries (non‑blocking)
        max_retries = 3
        user_muted = False
        for attempt in range(max_retries):
            if click_on_mute_user_button(page):
                user_muted = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not user_muted:
            print("Could not mute user after all attempts. Proceeding...")
        else:
            page.wait_for_timeout(1000)
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click DM button with retries (non‑blocking)
        max_retries = 3
        dm_clicked = False
        for attempt in range(max_retries):
            if click_on_send_DM_button(page):
                dm_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not dm_clicked:
            print("Could not click DM button after all attempts. Going back...")
            try:
                page.go_back()
                page.wait_for_timeout(2000)
                print("✅ Navigated back to previous page.")
            except Exception as e:
                print(f"⚠️ Error going back: {e}")
        else:
            page.wait_for_timeout(1500)
        # endregion

        page.wait_for_timeout(2000)

        # region Check if DM permission alert is present
        dm_alert_present = False
        try:
            alert_text = "is currently not meeting your set dm permission requirements or has to pay to message you"
            alert_selectors = [
                "div.messaging-alert-container",
                "div.dark-blue-1.messaging-alert-container",
                f"//div[contains(text(), '{alert_text}')]",
                "//div[@class='dark-blue-1 messaging-alert-container flex-row font-size-sm']"
            ]
            for selector in alert_selectors:
                element = page.locator(f"xpath={selector}") if selector.startswith('/') else page.locator(selector)
                if element.count() > 0:
                    txt = element.first.inner_text()
                    if "permission requirements" in txt or "pay to message you" in txt:
                        dm_alert_present = True
                        print("⚠️ DM permission alert detected.")
                        break
            if not dm_alert_present:
                print("✅ No DM permission alert found. Skipping Allow DM flow.")
        except Exception as e:
            print(f"Error checking DM alert: {e}. Assuming alert may be present.")
            dm_alert_present = True
        # endregion

        # region If alert present, handle Allow DM and Yes flow
        if dm_alert_present:
            # Allow DM
            max_retries = 3
            allow_dm_clicked = False
            for attempt in range(max_retries):
                if click_to_allow_send_me_DM(page):
                    allow_dm_clicked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not allow_dm_clicked:
                print("Could not click 'Allow DM' after all attempts. Skipping 'Yes' step.")
            else:
                page.wait_for_timeout(1500)

            # Yes button
            if allow_dm_clicked:
                max_retries = 3
                yes_clicked = False
                for attempt in range(max_retries):
                    if click_yes_to_accept_receiving_DM_from_this_creator(page):
                        yes_clicked = True
                        break
                    else:
                        if attempt < max_retries - 1:
                            page.wait_for_timeout(2000)

                if not yes_clicked:
                    print("Could not click 'Yes' after all attempts.")
                else:
                    page.wait_for_timeout(1500)
        else:
            print("Skipping entire Allow DM flow – user already has permission.")
        # endregion

        page.wait_for_timeout(2000)

        # region Try to click Add Media button with retries (non‑blocking)
        max_retries = 3
        media_button_clicked = False
        for attempt in range(max_retries):
            if click_to_add_media_button(page):
                media_button_clicked = True
                break
            else:
                if attempt < max_retries - 1:
                    page.wait_for_timeout(2000)

        if not media_button_clicked:
            print("Could not click Add Media button after all attempts. Skipping message flow...")
            # Go back once to return to creator profile
            page.go_back()
            page.wait_for_timeout(2000)
        else:
            page.wait_for_timeout(1500)

            # region Click 'From Vault' option
            max_retries = 3
            from_vault_clicked = False
            for attempt in range(max_retries):
                if click_to_add_from_vault(page):
                    from_vault_clicked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not from_vault_clicked:
                print("Could not click 'From Vault' after all attempts.")
            else:
                page.wait_for_timeout(1500)
            # endregion

            page.wait_for_timeout(3000)

            # region Insert album search text ("SFS")
            album_search_text = "SFS"
            max_retries = 3
            search_inserted = False
            for attempt in range(max_retries):
                if insert_text_to_find_specific_album(page, album_search_text):
                    search_inserted = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not search_inserted:
                print("Could not insert album search text after all attempts.")
            else:
                page.wait_for_timeout(1500)
            # endregion

            page.wait_for_timeout(5000)

            # region Select 'SFS Instructions' album
            max_retries = 3
            sfs_album_selected = False
            for attempt in range(max_retries):
                if click_to_select_sfs_video(page):
                    sfs_album_selected = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not sfs_album_selected:
                print("Could not select 'SFS Instructions' album after all attempts.")
            else:
                page.wait_for_timeout(1500)
            # endregion

            page.wait_for_timeout(2000)

            # region Select media item
            max_retries = 3
            media_selected = False
            for attempt in range(max_retries):
                if click_to_select_media(page):
                    media_selected = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not media_selected:
                print("Could not select media item after all attempts.")
            else:
                page.wait_for_timeout(1500)
            # endregion

            page.wait_for_timeout(2000)

            # region Click 'Add' button to add selected media
            max_retries = 3
            add_media_clicked = False
            for attempt in range(max_retries):
                if click_to_add_selected_media(page):
                    add_media_clicked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not add_media_clicked:
                print("Could not click 'Add' after all attempts.")
            else:
                page.wait_for_timeout(1500)
            # endregion

            page.wait_for_timeout(2000)

            # region Uncheck 'Require Subscription' checkbox
            max_retries = 3
            subscription_unchecked = False
            for attempt in range(max_retries):
                if click_to_uncheck_require_subscription(page):
                    subscription_unchecked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not subscription_unchecked:
                print("Could not uncheck 'Require Subscription' after all attempts.")
            else:
                page.wait_for_timeout(1000)
            # endregion

            page.wait_for_timeout(2000)

            # region Click 'Upload' button
            max_retries = 3
            upload_clicked = False
            for attempt in range(max_retries):
                if click_on_upload_button(page):
                    upload_clicked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not upload_clicked:
                print("Could not click 'Upload' after all attempts.")
            else:
                page.wait_for_timeout(2000)  # give upload time to process
            # endregion

            # region Insert message text
            contact_message = (
                "💓 Hi sweetie! Let\'s SFS (Shoutout for shoutout) 24 hours for free? "
                "If you don\'t know how to do it, watch this video on attach! "
                "If you want, please, repost this link: https://fansly.com/post/732275677243383808 and I'll do the same for you! If you could follow me back, I would be happy! =D"
            )
            max_retries = 3
            text_inserted = False
            for attempt in range(max_retries):
                if insert_text_to_be_sent(page, contact_message):
                    text_inserted = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not text_inserted:
                print("Could not insert message text after all attempts.")
            else:
                page.wait_for_timeout(1000)
            # endregion

            page.wait_for_timeout(2000)

            # region Click 'Send Message' button
            max_retries = 3
            send_clicked = False
            for attempt in range(max_retries):
                if click_on_send_message_button(page):
                    send_clicked = True
                    break
                else:
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)

            if not send_clicked:
                print("Could not click 'Send Message' after all attempts.")
            else:
                page.wait_for_timeout(2000)  # wait for message to send
            # endregion

            # Go back to the creator profile page after sending message
            page.go_back()
            page.wait_for_timeout(2000)
        # endregion

        # Go back to search results
        print("\n⏪ Returning to search results...")
        page.go_back()
        page.wait_for_timeout(3000)  # Increased wait time for search results to reload

        # Verify we're back on search results
        try:
            page.wait_for_selector('div.search-result-container', timeout=5000)
            print("✅ Back on search results page")
        except:
            print("⚠️ Search results page not detected after going back")

        # Increment counters - only after successful processing
        current_creator_index += 1
        processed_count += 1

        print(f"\n✅ Successfully processed creator {processed_count}/{max_creators_to_process}")

    print("\n" + "="*60)
    print(f"🎉 Finished processing {processed_count} creator(s)")
    print("="*60 + "\n")
    # endregion

    # region Keep browser open for debugging
    try:
        print("Browser will remain open. Press 'Resume' in Playwright Inspector to continue...")
        page.pause()  # opens Playwright Inspector and keeps browser open

        # After you click 'Resume' or 'Step Forward' in the Inspector
        browser_context.close()
        print("Browser closed successfully.")
    except Exception as e:
        print(f"Error closing browser: {e}")

    print("Script terminated. Goodbye!")
    # endregion

    sys.exit(0)

if __name__ == "__main__":
    main()
