import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

# Load environment variables
load_dotenv()

# Debug: Print all environment variables (without passwords)
def debug_env_vars():
    print("\n--- Environment Variables Debug ---")
    print(f"INSTAGRAM_USER set: {'Yes' if os.getenv('INSTAGRAM_USER') else 'No'}")
    print(f"INSTAGRAM_PASS set: {'Yes' if os.getenv('INSTAGRAM_PASS') else 'No'}")
    if os.getenv('INSTAGRAM_USER'):
        print(f"Instagram username: {os.getenv('INSTAGRAM_USER')}")

def login_instagram():
    """Automates Instagram login and returns session cookies."""
    print("Starting Instagram login process...")
    # Debug environment variables
    debug_env_vars()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Visible browser for debugging
            page = browser.new_page()
            print("Opening Instagram login page...")
            page.goto("https://instagram.com/accounts/login")
            
            # Wait for page to fully load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Extra wait to ensure login form is ready
            
            # Check for credentials before proceeding
            instagram_user = os.getenv('INSTAGRAM_USER')
            instagram_pass = os.getenv('INSTAGRAM_PASS')
            
            if not instagram_user or not instagram_pass:
                print("Error: Instagram credentials not found in .env file")
                print("Please add INSTAGRAM_USER and INSTAGRAM_PASS to your .env file")
                # Give time to see the error
                page.wait_for_timeout(5000)
                browser.close()
                return None
            
            print(f"Logging in as {instagram_user}...")
            
            # Debug: Take a screenshot of the login form before filling
            page.screenshot(path="before_login_fill.png")
            
            # Check if username field exists
            username_field = page.query_selector('input[name="username"]')
            if not username_field:
                print("Username field not found! Taking screenshot for analysis.")
                page.screenshot(path="login_form_error.png")
                print("Browser will stay open for investigation. Close it manually when done.")
                input("Press Enter to continue...")
                browser.close()
                return None
            
            # Fill in the login form with explicit waits
            print("Filling username field...")
            page.fill('input[name="username"]', instagram_user)
            page.wait_for_timeout(1000)  # Wait 1 second
            
            print("Filling password field...")
            page.fill('input[name="password"]', instagram_pass)
            page.wait_for_timeout(1000)  # Wait 1 second
            
            print("Clicking submit button...")
            # Try different submit button selectors
            submit_button = page.query_selector("button[type='submit']")
            if submit_button:
                submit_button.click()
            else:
                print("Submit button not found by type. Trying other selectors...")
                # Try by text content
                login_buttons = [
                    "text=Log In",
                    "text=Sign In",
                    "xpath=//button[contains(., 'Log In')]",
                    "xpath=//button[contains(., 'Sign In')]"
                ]
                
                clicked = False
                for btn_selector in login_buttons:
                    try:
                        if page.query_selector(btn_selector):
                            print(f"Found login button with selector: {btn_selector}")
                            page.click(btn_selector)
                            clicked = True
                            break
                    except Exception as e:
                        print(f"Error with button selector {btn_selector}: {e}")
                
                if not clicked:
                    print("Could not find or click any login button. Taking screenshot for analysis.")
                    page.screenshot(path="login_button_error.png")
                    print("Browser will stay open for investigation. Close it manually when done.")
                    input("Press Enter to continue...")
                    browser.close()
                    return None
            
            # Wait for navigation to complete after login
            try:
                print("Waiting for login to complete...")
                # Try multiple selectors that might indicate a successful login
                print("Checking for various post-login elements...")
                
                # Wait a bit for any security checkpoint to appear
                page.wait_for_timeout(5000)  # 5 seconds to load any security page
                
                # Take a screenshot to help identify the current page
                page.screenshot(path="login_progress.png")
                print("Screenshot of current state saved to login_progress.png")
                
                # Check if we need to handle a security checkpoint
                if page.query_selector("text=Suspicious Login Attempt") or page.query_selector("text=Enter Security Code") or page.query_selector("text=We detected an unusual login attempt"):
                    print("Security checkpoint detected.")
                    print("Please check the browser window and complete any security checks manually.")
                    # Give user time to handle the security checkpoint
                    input("Press Enter after completing the security verification in the browser window...")
                
                # Wait for any of these selectors that might indicate a successful login
                selectors = [
                    "xpath=//div[contains(text(),'Home')]",  # Text-based Home button
                    "[aria-label='Home']",                 # Aria-label Home button
                    "svg[aria-label='Home']",              # SVG Home icon
                    "[role='main']",                       # Main content area
                    "[data-testid='feed-timeline']"         # Feed timeline
                ]
                
                print("Waiting for home page elements...")
                success = False
                for selector in selectors:
                    try:
                        if page.wait_for_selector(selector, timeout=5000):
                            print(f"Login confirmed with selector: {selector}")
                            success = True
                            break
                    except Exception:
                        continue
                
                if not success:
                    # One more check - just wait a bit and see if we're on instagram.com
                    # (sometimes UI elements change but we're still logged in)
                    page.wait_for_timeout(3000)  # Wait 3 more seconds
                    current_url = page.url
                    if "instagram.com" in current_url and "accounts/login" not in current_url:
                        print(f"Appears to be logged in based on URL: {current_url}")
                        success = True
                
                if success:
                    print("Login successful!")
                    cookies = page.context.cookies()
                    
                    # Take a screenshot of successful login state
                    page.screenshot(path="login_success.png")
                    print("Screenshot of logged-in state saved to login_success.png")
                    
                    # Give a moment to see the result before closing
                    page.wait_for_timeout(2000)
                    browser.close()
                    return cookies
                else:
                    print("Could not confirm successful login.")
                    page.screenshot(path="login_failed.png")
                    print("Screenshot saved to login_failed.png")
                    browser.close()
                    return None
            except Exception as e:
                print(f"Error during login: {e}")
                print("Login might have failed. Check credentials or try again.")
                # Take a screenshot to help diagnose the issue
                screenshot_path = "login_error.png"
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
                browser.close()
                return None
    except Exception as e:
        print(f"Error setting up browser: {e}")
        return None

def screenshot_stories(cookies, num_stories=3):
    """Navigates to Instagram stories, captures screenshots, and returns a list of file paths."""
    print("\n--- Capturing Instagram Stories ---")
    screenshots = []
    
    if not cookies:
        print("Error: No cookies provided. Please login first.")
        return screenshots
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Changed to visible browser for debugging
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            
            print("Navigating to Instagram homepage...")
            page.goto("https://instagram.com")
            
            # Give page time to load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Additional time to ensure full load
            
            # Take a screenshot of homepage for debugging
            page.screenshot(path="instagram_home.png")
            print("Homepage screenshot saved as instagram_home.png")
            
            print("Looking for stories button...")
            # Try different selectors for the stories button
            try:
                # Try clicking on the first story in the stories tray
                print("Attempting to click on first story...")
                story_selectors = [
                    "xpath=//div[contains(@role,'button') and contains(@aria-label,'Story')]",
                    "xpath=//img[contains(@alt,'Story')]/ancestor::div[contains(@role,'button')]",
                    "css=div[role='button'][tabindex='0']:has(canvas)", # Stories often have a canvas element
                    "xpath=//section//div/div/div/div[1]/div/div/div/div/div/div/div[1]" # Direct child approach
                ]
                
                success = False
                for selector in story_selectors:
                    try:
                        if page.wait_for_selector(selector, timeout=5000):
                            print(f"Story found with selector: {selector}")
                            # Take before-click screenshot
                            page.screenshot(path="before_story_click.png")
                            print("Screenshot before clicking story saved as before_story_click.png")
                            
                            # Click the story
                            page.click(selector)
                            page.wait_for_timeout(2000)  # Wait for story to open
                            
                            # Check if we're in story view
                            page.screenshot(path="after_story_click.png")
                            print("Screenshot after clicking story saved as after_story_click.png")
                            
                            success = True
                            break
                    except Exception as e:
                        print(f"Selector {selector} failed: {e}")
                        continue
                
                if not success:
                    raise Exception("Could not find or click any stories using available selectors")
                
            except Exception as e:
                print(f"Could not access stories: {e}")
                browser.close()
                return screenshots
            
            print("Capturing screenshots of stories...")
            for i in range(num_stories):
                print(f"Capturing story {i+1}/{num_stories}...")
                # Wait for story to load
                page.wait_for_timeout(2000)  # wait 2 seconds for the story to load
                screenshot_path = f"story_{i+1}.png"
                page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
                print(f"Screenshot saved as {screenshot_path}")
                
                # Move to next story
                print("Moving to next story...")
                page.keyboard.press('ArrowRight')
                page.wait_for_timeout(1000)  # wait 1 second between stories
            
            # Wait a moment before closing to see the results
            page.wait_for_timeout(2000)
            browser.close()
            print(f"Successfully captured {len(screenshots)} screenshots")
    except Exception as e:
        print(f"Error capturing stories: {e}")
    
    return screenshots

# Run the test
def test_instagram_only():
    print("\n=== Testing Instagram Screenshot Functionality ===\n")
    
    # Step 1: Login to Instagram
    print("Step 1: Logging in to Instagram")
    cookies = login_instagram()
    if not cookies:
        print("Login failed. Cannot proceed.")
        return False
    
    # Step 2: Screenshot stories
    print("\nStep 2: Capturing story screenshots")
    screenshots = screenshot_stories(cookies, 3)  # Capture 3 stories
    if not screenshots:
        print("Failed to capture any screenshots")
        return False
    
    print(f"\nSuccessfully captured {len(screenshots)} story screenshots:")
    for screenshot in screenshots:
        print(f"- {screenshot}")
    
    return True

if __name__ == "__main__":
    test_instagram_only()
