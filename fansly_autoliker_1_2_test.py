import os
import subprocess
import time
import sys
import pyautogui # Assuming pyautogui is installed for F11
from playwright.sync_api import sync_playwright, BrowserContext, Page, Locator

# Global variables for Playwright and user data (defined here for clarity,
# but they are also declared in open_chrome_in_selected_creators_url)
playwright_instance = None
browser_context: BrowserContext = None
likes_quantity: str = ""
creator_url: str = ""

def cleanup_playwright():
    """
    Ensures Playwright resources are properly closed.
    """
    global browser_context, playwright_instance
    if browser_context:
        try:
            browser_context.close()
            print("Browser context closed.")
        except Exception as e:
            print(f"Error closing browser context: {e}")
        browser_context = None
    if playwright_instance:
        try:
            playwright_instance.stop()
            print("Playwright instance stopped.")
        except Exception as e:
            print(f"Error stopping Playwright instance: {e}")
        playwright_instance = None

def open_chrome_in_selected_creators_url() -> tuple[BrowserContext, Page]:
    """
    Opens a Google Chrome instance with all profile data,
    keeping the session active indefinitely, and navigates to a user-provided URL.
    """
    global playwright_instance, browser_context, likes_quantity, creator_url

    # Prompt for likes quantity and creator URL
    # Using .strip() to remove any leading/trailing whitespace, including newlines,
    # which can sometimes cause issues with subsequent input calls.
    likes_quantity = input("Please, insert the likes quantity and hit enter: ").strip()
    creator_url = input("Please, insert the Creator's URL and hit enter: ").strip()

    # Install Playwright if necessary
    print("Checking Playwright installation...")
    # The subprocess module is the recommended way to invoke subprocesses, replacing older functions like os.system() <sources>[1]</sources>.
    # Using shell=True is generally discouraged for security reasons, but for simple commands like 'playwright install' it might be acceptable.
    subprocess.run(["playwright", "install"], shell=True, capture_output=True)
    subprocess.run(["playwright", "install", "chromium"], shell=True, capture_output=True)

    # Chrome profile path
    profile_path = r"C:\Users\danie\AppData\Local\Google\Chrome\User Data\Default"

    # Check if the profile directory exists
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Profile directory not found: {profile_path}")

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
        # Open new tab
        page = browser_context.new_page()
        print("New tab opened")
        # Navigate to the user-provided URL
        print(f"Navigating to: {creator_url}...")
        page.goto(creator_url, timeout=15000)
        print("Chrome opened successfully with all profile data and navigated to the Creator's URL!")
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

from playwright.sync_api import Page

def click_on_creators_media_section(page: Page) -> bool:
    """
    Attempts to find and click the 'Media' section on a creator's profile page
    using multiple selector approaches.
    """
    #print("Attempting to click the 'Media' section...")
    try:
        # List of selectors to try for the "Media" section
        # Note: The provided selector for 'xd-localization-string' includes 'selected',
        # which might mean it's already selected. We'll use a more general one first
        # and then the specific one if needed.
        selectors = [
            # General CSS selector for the 'Media' tab (assuming it's not always 'selected')
            "div.tab-nav-items.border-color > div.tab-nav-item2.flex-1:has(xd-localization-string:text('Media'))",
            # Specific CSS selector from your input (might only match if already selected)
            "body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible.scrolling-down > div > app-profile-route > div > div > div > div.tab-nav-wrapper > div.tab-nav-items.border-color > div.tab-nav-item2.flex-1.selected > xd-localization-string",
            # XPath from your input
            "/html/body/app-root/div/div[1]/div/app-profile-route/div/div/div/div[4]/div[1]/div[2]/xd-localization-string",
            # JavaScript path from your input
            "document.querySelector(\"body > app-root > div > div.site-wrapper.nav-bar-visible.nav-bar-mobile-visible.nav-bar-top-visible.scrolling-down > div > app-profile-route > div > div > div > div.tab-nav-wrapper > div.tab-nav-items.border-color > div.tab-nav-item2.flex-1.selected > xd-localization-string\")"
        ]

        for selector in selectors:
            try:
                #print(f"Trying 'Media' section selector: {selector}")

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
                        #print(f"Successfully clicked 'Media' section with JS selector.")
                        return True

                elif selector.startswith('/'):
                    # XPath selector
                    xpath_locator = page.locator(f"xpath={selector}")
                    if xpath_locator.count() > 0:
                        try:
                            # Ensure visibility and click
                            xpath_locator.first.scroll_into_view_if_needed()
                            xpath_locator.first.click(force=True)
                            print(f"Successfully clicked 'Media' section with XPath.")
                            return True
                        except Exception as e:
                            print(f"XPath click failed: {str(e)}")

                else:
                    # CSS selector
                    css_locator = page.locator(selector)
                    if css_locator.count() > 0:
                        try:
                            # Ensure visibility and click
                            css_locator.first.scroll_into_view_if_needed()
                            css_locator.first.click(force=True)
                            print(f"Successfully clicked 'Media' section with CSS selector.")
                            return True
                        except Exception as e:
                            print(f"CSS selector click failed: {str(e)}")

            except Exception as e:
                print(f"Failed with 'Media' section selector {selector}: {str(e)}")
                continue

        print("Could not find or click 'Media' section using any method.")
        return False

    except Exception as e:
        print(f"Error in click_on_creators_media_section: {str(e)}")
        return False


def hit_like_by_index(page: Page, index: int) -> bool:
    """
    Attempts to find and click the 'like' icon at a specific index using multiple approaches.
    """
    try:
        primary_selector = "i.fa-fw.fas.fa-heart"

        like_buttons = page.locator(primary_selector)
        count = like_buttons.count()

        if count == 0:
            print(f"No like buttons found with selector: {primary_selector}")
            return False

        if index >= count:
            print(f"Requested like button index {index} is out of bounds. Only {count} buttons found.")
            return False

        target_button = like_buttons.nth(index)

        try:
            # Corrected: Pass selector and index as a single dictionary or tuple
            # and access them as arguments inside the JS function.
            # The JS function now expects two arguments: selector and idx.
            page.evaluate('''([selector, idx]) => {
                const elements = document.querySelectorAll(selector);
                if (elements[idx]) {
                    elements[idx].style.opacity = '1';
                    elements[idx].style.visibility = 'visible';
                    elements[idx].style.display = 'block';
                }
            }''', [primary_selector, index]) # Pass arguments as a list/tuple

            target_button.scroll_into_view_if_needed()
            target_button.click(force=True)
            print(f"Successfully clicked like button at index {index}.")
            return True
        except Exception as e:
            print(f"Click failed for like button at index {index}: {str(e)}")
            return False

    except Exception as e:
        print(f"Error in hit_like_by_index: {str(e)}")
        return False



def main():
    # region Closes any Chrome Browser instances
    time.sleep(2)
    print("Closing browser instances...")
    os.system("taskkill /f /im chrome.exe")
    time.sleep(2)
    # endregion

    # region Start browser with profile and navigate
    browser_context, page = open_chrome_in_selected_creators_url()

    print("Browser started successfully!")
    print("IMPORTANT: Do not close this terminal to keep Chrome active")
    print(f"Collected Likes Quantity: {likes_quantity}")
    print(f"Collected Creator URL: {creator_url}")

    pyautogui.press("f11")
    page.wait_for_timeout(7000)
    # endregion

    # region Try to click the Creator's Media section with retries
    max_retries = 3
    for attempt in range(max_retries):
        if click_on_creators_media_section(page):
            break
        else:
            print(f"Attempt {attempt + 1} failed.")
            if attempt < max_retries - 1:
                print("Waiting before next attempt...")
                page.wait_for_timeout(2000)
    else:
        print("Failed to click 'Media' section after all attempts.")

    page.wait_for_timeout(3000)
    # endregion Try to click the Creator's Media section with retries

    print("Scrolling the page down two viewports...")
    page.evaluate("window.scrollBy(0, window.innerHeight * 2);")
    page.wait_for_timeout(5000)

    # region Loop to click the like button multiple times
    try:
        num_likes_to_click = int(likes_quantity)
    except ValueError:
        print(f"Invalid likes quantity '{likes_quantity}'. Please enter a number.")
        cleanup_playwright()
        sys.exit(1)

    likes_clicked = 0
    clicked_indices = set()

    # Track the starting index for the search in each iteration
    # This helps avoid repeatedly trying index 0 if it's problematic
    next_available_index_to_try = 0 

    for i in range(num_likes_to_click):
        print(f"\nAttempting to click like button (Like {i + 1} of {num_likes_to_click})...")

        all_like_buttons = page.locator("i.fa-fw.fas.fa-heart")
        total_available_buttons = all_like_buttons.count()

        if total_available_buttons == 0:
            print("No more like buttons found on the page. Stopping.")
            break

        found_unclicked_button = False
        # Start searching for an unclicked button from 'next_available_index_to_try'
        # and wrap around if necessary, to ensure all buttons are considered.
        for _ in range(total_available_buttons): # Iterate up to total_available_buttons times
            current_index = next_available_index_to_try % total_available_buttons

            if current_index not in clicked_indices:
                if hit_like_by_index(page, current_index):
                    print(f"Successfully clicked like button {i + 1} at index {current_index}!")
                    likes_clicked += 1
                    clicked_indices.add(current_index)
                    found_unclicked_button = True
                    # Move the starting point for the next search
                    next_available_index_to_try = current_index + 1 
                    page.wait_for_timeout(1000)
                    break 
                else:
                    print(f"Failed to click like button at index {current_index}. Trying next available.")

            # If current_index was already clicked or failed, try the next one in the list
            next_available_index_to_try += 1

        if not found_unclicked_button:
            print(f"Could not find an unclicked like button for like {i + 1}. All available buttons might be clicked or inaccessible.")
            break 

    print(f"Finished. Total likes clicked: {likes_clicked} out of {num_likes_to_click} requested.")

    page.wait_for_timeout(3000)
    # endregion Loop to click the like button multiple times

    # region Keep browser open for debugging
    try:
        print("Browser will remain open. Press 'Resume' in Playwright Inspector to continue...")
        page.pause()

        browser_context.close()
        print("Browser closed successfully.")
    except Exception as e:
        print(f"Error closing browser: {e}")

    print("Script terminated. Goodbye!")
    # endregion

    sys.exit(0)

if __name__ == "__main__":
    main()

