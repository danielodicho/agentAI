import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

# Load environment variables
load_dotenv()

# Debug: Print environment variables
def debug_env_vars():
    print("\n--- Environment Variables Debug ---")
    print(f"INSTAGRAM_USER set: {'Yes' if os.getenv('INSTAGRAM_USER') else 'No'}")
    print(f"INSTAGRAM_PASS set: {'Yes' if os.getenv('INSTAGRAM_PASS') else 'No'}")
    if os.getenv('INSTAGRAM_USER'):
        print(f"Instagram username: {os.getenv('INSTAGRAM_USER')}")

def login_instagram():
    """Function to log in to Instagram and return cookies for later use."""
    print("Starting Instagram login process...")
    
    # Debug: Check environment variables
    print("\n--- Environment Variables Debug ---")
    username = os.getenv("INSTAGRAM_USER")
    password = os.getenv("INSTAGRAM_PASS")
    
    print(f"INSTAGRAM_USER set: {'Yes' if username else 'No'}")
    print(f"INSTAGRAM_PASS set: {'Yes' if password else 'No'}")
    
    if not username or not password:
        print("Error: Instagram credentials not found in environment variables.")
        print("Please ensure INSTAGRAM_USER and INSTAGRAM_PASS are set.")
        return None
    
    print(f"Instagram username: {username}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Set to False for debugging
            context = browser.new_context()
            page = context.new_page()
            
            print("Opening Instagram login page...")
            page.goto("https://www.instagram.com/accounts/login/")
            
            # Wait for the page to fully load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Additional wait to ensure all elements are loaded
            
            # Check if we need to handle cookies consent dialog
            try:
                if page.query_selector("text=Accept All"):
                    print("Handling cookies consent dialog...")
                    page.click("text=Accept All")
                    page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Note: No cookies dialog or error handling it: {e}")
            
            print("Logging in as {username}...")
            
            # Enhanced selectors for username field
            username_selectors = [
                "input[name='username']",
                "[aria-label='Phone number, username, or email']",
                "input[type='text']",
                "//input[@name='username']",
                "//input[@aria-label='Phone number, username, or email']",
                ".x1lugfcp input",  # Class-based selector
                "._ab32"  # Another potential class
            ]
            
            # Try each selector until one works
            username_field_found = False
            for selector in username_selectors:
                try:
                    if page.query_selector(selector):
                        print(f"Found username field with selector: {selector}")
                        print("Filling username field...")
                        page.fill(selector, username)
                        username_field_found = True
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
            
            if not username_field_found:
                print("Username field not found! Taking screenshot for analysis.")
                page.screenshot(path="login_field_issue.png")
                
                # Try direct navigation to the feed as a logged-out user
                print("Trying direct navigation to Instagram feed...")
                page.goto("https://www.instagram.com/")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000)
                
                # Check if there's a login form on this page
                for selector in username_selectors:
                    try:
                        if page.query_selector(selector):
                            print(f"Found username field on main page with selector: {selector}")
                            page.fill(selector, username)
                            username_field_found = True
                            break
                    except Exception:
                        pass
                
                if not username_field_found:
                    print("Could not find username field on any page. Browser will stay open for investigation.")
                    print("Close it manually when done.")
                    input("Press Enter to continue...")
                    return None
            
            # Enhanced selectors for password field
            password_selectors = [
                "input[name='password']",
                "[aria-label='Password']",
                "input[type='password']",
                "//input[@name='password']",
                "//input[@aria-label='Password']"
            ]
            
            # Try each password selector until one works
            password_field_found = False
            for selector in password_selectors:
                try:
                    if page.query_selector(selector):
                        print("Filling password field...")
                        page.fill(selector, password)
                        password_field_found = True
                        break
                except Exception as e:
                    print(f"Password selector {selector} failed: {e}")
            
            if not password_field_found:
                print("Password field not found! Taking screenshot for analysis.")
                page.screenshot(path="password_field_issue.png")
                browser.close()
                return None
            
            # Enhanced selectors for login button
            login_button_selectors = [
                "button[type='submit']",
                "[type='submit']",
                "button:has-text('Log in')",
                "//button[@type='submit']",
                "//button[contains(text(),'Log in')]",
                ".x1i10hfl.xp7jhwk:has-text('Log in')"  # Class-based selector
            ]
            
            # Try each login button selector until one works
            login_button_clicked = False
            for selector in login_button_selectors:
                try:
                    if page.query_selector(selector):
                        print("Clicking submit button...")
                        page.click(selector)
                        login_button_clicked = True
                        break
                except Exception as e:
                    print(f"Login button selector {selector} failed: {e}")
            
            if not login_button_clicked:
                print("Submit button not found! Taking screenshot for analysis.")
                page.screenshot(path="submit_button_issue.png")
                browser.close()
                return None
            
            # Wait for login to complete and navigate to home feed
            print("Waiting for login to complete...")
            
            # Take screenshot of current state for debugging
            page.screenshot(path="login_progress.png")
            print("Screenshot of current state saved to login_progress.png")
            
            # Wait for elements that indicate successful login
            print("Waiting for home page elements...")
            success_selectors = [
                "[aria-label='Home']",
                "[role='main']",
                ".x1jx94hy",  # Common class for main content after login
                "nav a[href='/']"  # Home link in nav
            ]
            
            login_success = False
            for selector in success_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    print(f"Login confirmed with selector: {selector}")
                    login_success = True
                    break
                except Exception:
                    pass
            
            if not login_success:
                print("Could not verify successful login! Taking screenshot for analysis.")
                page.screenshot(path="login_verification_issue.png")
                browser.close()
                return None
            
            print("Login successful!")
            # Take screenshot of logged-in state
            page.screenshot(path="login_success.png")
            print("Screenshot of logged-in state saved to login_success.png")
            
            # Get cookies for later use
            cookies = context.cookies()
            browser.close()
            return cookies
            
    except Exception as e:
        print(f"Error setting up browser: {e}")
        return None

def improved_screenshot_stories(cookies, story_username="isabelokunpicena_", num_stories=1):
    """Improved function to navigate to a specific user's Instagram stories and capture screenshots."""
    print("\n--- Capturing Instagram Stories ---")
    screenshots = []
    
    if not cookies:
        print("Error: No cookies provided. Please login first.")
        return screenshots
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Visible browser for debugging
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            
            # Go directly to the specific user's stories
            print(f"Navigating directly to {story_username}'s stories...")
            page.goto(f"https://www.instagram.com/stories/{story_username}/")
            
            # Give page time to load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Additional time to ensure full load
            
            # Take a screenshot to verify we're on the right page
            page.screenshot(path="story_confirmation_page.png")
            print(f"Screenshot of confirmation page saved as story_confirmation_page.png")
            
            # Check for and click the "View story" button - using multiple approaches for reliability
            print("Looking for 'View story' button...")
            
            # Approach 1: Try text-based selectors
            view_story_selectors = [
                "text=View story", 
                "button:has-text('View story')",
                ".x1i10hfl:has-text('View story')",
                "[role='button']:has-text('View story')",
                "//div[contains(text(), 'View story')]",
                "//button[contains(text(), 'View story')]"
            ]
            
            view_button_clicked = False
            for selector in view_story_selectors:
                try:
                    if page.query_selector(selector):
                        print(f"Found 'View story' button with selector: {selector}")
                        page.click(selector)
                        print("Clicked 'View story' button")
                        # Wait for the story to load after clicking the button
                        page.wait_for_timeout(3000)
                        # Take a screenshot to confirm we're in the story view now
                        page.screenshot(path="after_view_story_click.png")
                        print("Screenshot after clicking 'View story' saved as after_view_story_click.png")
                        view_button_clicked = True
                        break
                except Exception as e:
                    print(f"Error with 'View story' button selector {selector}: {e}")
            
            # Approach 2: If no success with predefined selectors, try looking for buttons with "view story" text content
            if not view_button_clicked:
                print("Could not find 'View story' button with predefined selectors")
                print("Trying to find buttons with 'View story' text...")
                
                # Find all potential buttons
                buttons = page.query_selector_all("button, [role='button'], a[role='button'], div[role='button'], .x1i10hfl")
                print(f"Found {len(buttons)} potential clickable elements")
                
                # Try to find one with "View story" text
                for button in buttons:
                    try:
                        button_text = button.inner_text().lower()
                        if "view" in button_text and "story" in button_text:
                            print(f"Found button with text: {button_text}")
                            button.click()
                            page.wait_for_timeout(3000)
                            page.screenshot(path="after_text_button_click.png")
                            print("Clicked button with 'View story' text")
                            view_button_clicked = True
                            break
                    except Exception:
                        pass
            
            # Approach 3: Try a coordinate-based click in the middle of the page/story area
            if not view_button_clicked:
                print("Trying coordinate-based approach to click 'View story' button...")
                
                # First try to click center of the page - a common location for the View story button
                try:
                    page_width = page.viewport_size['width']
                    page_height = page.viewport_size['height']
                    center_x = page_width / 2
                    center_y = page_height / 2
                    
                    print(f"Clicking center of page at coordinates ({center_x}, {center_y})")
                    page.mouse.click(center_x, center_y)
                    page.wait_for_timeout(3000)
                    page.screenshot(path="after_center_click.png")
                    print("Clicked center of page")
                    
                    # Also try slightly below center where the View story button often appears
                    print("Trying position below center")
                    page.mouse.click(center_x, center_y + 60)
                    page.wait_for_timeout(3000)
                    page.screenshot(path="after_below_center_click.png")
                except Exception as e:
                    print(f"Error with coordinate-based approach: {e}")
            
            # Check if we're in story view after all click attempts
            print("Checking if we're in story view...")
            story_indicators = [
                "[aria-label='Pause']",  # Pause button
                "button[aria-label='Next']",  # Next button
                "button[aria-label='Previous']",  # Previous button
                ".x1i10hfl.xjqpnuy",  # Common class for story UI
                "._aa8j",  # Another potential story UI class
                "video"  # Videos are common in stories
            ]
            
            in_story_view = False
            for indicator in story_indicators:
                if page.query_selector(indicator):
                    print(f"Story view confirmed with element: {indicator}")
                    in_story_view = True
                    break
            
            if not in_story_view:
                print("Could not confirm we're in story view. Taking screenshot for analysis.")
                page.screenshot(path="story_view_check.png")
                print("Screenshot saved as story_view_check.png")
                print("Attempting to capture screenshots anyway...")
            
            # Capture the requested number of stories
            print("\nCapturing screenshots of stories...")
            for i in range(num_stories):
                print(f"Capturing story {i+1}/{num_stories}...")
                # Wait for story to load
                page.wait_for_timeout(2000)  # wait 2 seconds for the story to load
                screenshot_path = f"{story_username}_story_{i+1}.png"
                page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
                print(f"Screenshot saved as {screenshot_path}")
                
                if i < num_stories - 1:  # Don't try to move past the last story
                    # Move to next story
                    print("Moving to next story...")
                    page.keyboard.press('ArrowRight')
                    page.wait_for_timeout(1500)  # wait 1.5 seconds between stories
            
            # Wait a moment before closing to see the results
            page.wait_for_timeout(2000)
            browser.close()
            print(f"Successfully captured {len(screenshots)} screenshots")
    except Exception as e:
        print(f"Error capturing stories: {e}")
    
    return screenshots

# Main test function
def test_story_extraction():
    print("\n=== Testing Instagram Story Extraction ===\n")
    
    # Step 1: Login to Instagram
    print("Step 1: Logging in to Instagram")
    cookies = login_instagram()
    if not cookies:
        print("Login failed. Cannot proceed.")
        return False
    
    # Step 2: Screenshot stories with improved function - now focused on a specific user
    print("\nStep 2: Capturing specific user story screenshot")
    story_username = "isabelokunpicena_"  # Use the username provided by the user
    screenshots = improved_screenshot_stories(cookies, story_username, 1)  # Capture just 1 story
    if not screenshots:
        print("Failed to capture any screenshots")
        return False
    
    print(f"\nSuccessfully captured {len(screenshots)} story screenshots:")
    for screenshot in screenshots:
        print(f"- {screenshot}")
    
    return True

# Run the test
if __name__ == "__main__":
    test_story_extraction()
