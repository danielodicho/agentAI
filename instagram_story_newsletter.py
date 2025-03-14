import os
import base64
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from openai import OpenAI
# Temporarily disable agentops
# import agentops
from datetime import datetime
import glob

# Load environment variables
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY is not set in your .env file")
    print("Please add your OpenAI API key to your .env file:")
    print("OPENAI_API_KEY=your_openai_api_key")
    exit(1)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Temporarily disable AgentOps
# Initialize AgentOps for tracking (only if key exists)
# agentops_key = os.getenv("AGENTOPS_API_KEY")
# if agentops_key:
#     agentops.init(agentops_key)
#     print("AgentOps initialized for tracing")
# else:
#     print("AgentOps API key not found, skipping trace export")

# Story extraction functions
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
            
            print(f"Logging in as {username}...")
            
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
                    browser.close()
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

def extract_instagram_story(cookies, story_username, num_stories=1):
    """Function to navigate to a specific user's Instagram stories and capture screenshots."""
    print(f"\n--- Extracting Instagram Stories for {story_username} ---")
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

# AI Processing Functions
def encode_image_to_base64(image_path):
    """Convert an image to base64 for sending to OpenAI API."""
    if not os.path.exists(image_path):
        print(f"Warning: Image file does not exist: {image_path}")
        return None
        
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_story_images(image_paths):
    """Use OpenAI API to analyze the content of Instagram story screenshots."""
    print("\n--- Analyzing Instagram Stories with OpenAI ---")
    
    # If no images were provided, use sample images for testing
    if not image_paths or len(image_paths) == 0:
        print("No images provided. Using sample images for testing...")
        sample_images = [
            "story_sample_1.png",
            "story_sample_2.png",
            "story_sample_3.png"
        ]
        
        # Check if sample images exist
        existing_samples = [img for img in sample_images if os.path.exists(img)]
        if existing_samples:
            image_paths = existing_samples
            print(f"Using {len(existing_samples)} sample images for analysis")
        else:
            print("No sample images found. Please provide image paths.")
            return "No image content available for analysis."
    
    # Create a prompt for OpenAI that includes all the images
    try:
        # Prepare messages with images
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in analyzing Instagram stories and creating engaging newsletters. Analyze the provided Instagram story screenshots and describe their content, context, themes, and any text visible in the images. Be detailed but concise."}
        ]
        
        # Add each image to the messages
        for i, img_path in enumerate(image_paths):
            base64_image = encode_image_to_base64(img_path)
            if base64_image:
                messages.append({
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": f"Analyze this Instagram story (image {i+1} of {len(image_paths)}):"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                })
            else:
                print(f"Skipping image {img_path} due to encoding error")
        
        # Ask for a summary of all images
        messages.append({
            "role": "user",
            "content": "Now provide a comprehensive analysis of all the Instagram stories, noting themes, content types, and how they connect. This will be used to generate a newsletter."
        })
        
        print("Sending images to OpenAI for analysis...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Updated to use the current vision-capable model
            messages=messages,
            max_tokens=1000
        )
        
        analysis = response.choices[0].message.content
        print("Analysis complete!")
        return analysis
    
    except Exception as e:
        print(f"Error during OpenAI analysis: {e}")
        return f"Error analyzing Instagram stories: {str(e)}"

def generate_newsletter(analysis, recipient_name="Subscriber"):
    """Generate a newsletter based on the analyzed Instagram stories."""
    print("\n--- Generating Instagram Newsletter ---")
    
    try:
        # Create the prompt for newsletter generation
        messages = [
            {"role": "system", "content": "You are an AI assistant specialized in creating engaging newsletters based on Instagram content. Your task is to create a well-formatted, engaging newsletter based on analyzed Instagram stories. The newsletter should be in HTML format and include a catchy subject line, personalized greeting, well-structured content sections, and a friendly sign-off."}, 
            {"role": "user", "content": f"Based on the following analysis of Instagram stories:\n\n{analysis}\n\nCreate an engaging, well-formatted newsletter email addressed to {recipient_name}. Include a catchy subject line, personalized greeting, summary of the Instagram highlights, and a friendly sign-off. Format the newsletter in HTML with appropriate styling."}
        ]
        
        print("Generating newsletter with OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Updated to use the current model
            messages=messages,
            max_tokens=1500
        )
        
        newsletter = response.choices[0].message.content
        print("Newsletter generation complete!")
        return newsletter
        
    except Exception as e:
        print(f"Error during newsletter generation: {e}")
        return f"Error generating newsletter: {str(e)}"

def extract_subject_line(newsletter_content):
    """Extract the subject line from the generated newsletter."""
    if "Subject:" in newsletter_content:
        lines = newsletter_content.split("\n")
        for line in lines:
            if line.startswith("Subject:"):
                return line.replace("Subject:", "").strip()
    
    # Default subject if none found
    return "Your Instagram Digest for " + datetime.now().strftime("%Y-%m-%d")

def save_newsletter_to_file(newsletter_content, filename="newsletter.html"):
    """Save the newsletter content to an HTML file."""
    # Clean up the newsletter content to extract just the HTML part
    if "<html>" in newsletter_content.lower():
        start_idx = newsletter_content.lower().find("<html>")
        end_idx = newsletter_content.lower().find("</html>") + 7
        if start_idx >= 0 and end_idx > start_idx:
            html_content = newsletter_content[start_idx:end_idx]
        else:
            html_content = newsletter_content
    else:
        html_content = f"<html><body>{newsletter_content}</body></html>"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Newsletter saved to {filename}")
    return filename

# Main Process Function
def run_instagram_newsletter(usernames=None, use_samples=False):
    """Main function to run the Instagram story newsletter process."""
    print("\n=== Instagram Story Newsletter Generator ===\n")
    
    if use_samples:
        print("Using sample images instead of extracting from Instagram...")
        sample_images = [
            "story_sample_1.png",
            "story_sample_2.png",
            "story_sample_3.png"
        ]
        
        # Check if sample images exist
        existing_samples = [img for img in sample_images if os.path.exists(img)]
        if existing_samples:
            print(f"Found {len(existing_samples)} sample images")
            screenshots = existing_samples
        else:
            print("No sample images found. Will extract from Instagram.")
            use_samples = False
    
    if not use_samples:
        # Step 1: Login to Instagram
        print("\nStep 1: Logging in to Instagram")
        cookies = login_instagram()
        if not cookies:
            print("Login failed. Cannot proceed.")
            return False
        
        # Step 2: Extract stories from specified Instagram accounts
        print("\nStep 2: Extracting Instagram stories")
        if not usernames or len(usernames) == 0:
            print("No usernames provided. Using default username.")
            usernames = ["isabelokunpicena_"]  # Default username
        
        screenshots = []
        for username in usernames:
            print(f"\nExtracting story for {username}...")
            user_screenshots = extract_instagram_story(cookies, username, 1)  # Capture 1 story per user
            screenshots.extend(user_screenshots)
        
        if not screenshots or len(screenshots) == 0:
            print("Failed to capture any screenshots. Using sample images if available.")
            sample_images = glob.glob("story_sample_*.png")
            if sample_images:
                print(f"Found {len(sample_images)} sample images")
                screenshots = sample_images
            else:
                print("No screenshots or sample images available. Cannot proceed.")
                return False
    
    # Step 3: Analyze the stories with OpenAI
    print("\nStep 3: Analyzing Instagram stories with OpenAI")
    analysis = analyze_story_images(screenshots)
    print(f"\nContent Analysis Summary:\n{analysis[:300]}..." + ("" if len(analysis) <= 300 else "\n[content trimmed]"))
    
    # Step 4: Generate a newsletter based on the analysis
    print("\nStep 4: Generating newsletter based on analysis")
    newsletter = generate_newsletter(analysis, "Instagram Subscriber")
    
    # Step 5: Save the newsletter to a file
    print("\nStep 5: Saving newsletter to file")
    subject_line = extract_subject_line(newsletter)
    print(f"Newsletter Subject: {subject_line}")
    
    # Create a unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    newsletter_file = f"instagram_newsletter_{timestamp}.html"
    save_newsletter_to_file(newsletter, newsletter_file)
    
    print(f"\nInstagram Newsletter process complete!")
    print(f"Newsletter saved to {newsletter_file}")
    
    return {
        "subject": subject_line,
        "newsletter_file": newsletter_file,
        "analysis": analysis,
        "screenshots": screenshots
    }

# Run the process if executed directly
if __name__ == "__main__":
    # Check if sample images exist
    sample_mode = os.path.exists("story_sample_1.png")
    if sample_mode:
        print("Sample images detected - running in sample mode")
    
    # Ask for usernames if not in sample mode
    usernames = []
    if not sample_mode:
        print("Enter Instagram usernames to extract stories from (or press Enter to use default):")
        user_input = input("> ")
        if user_input.strip():
            usernames = [u.strip() for u in user_input.split(',')]
    
    # Run the newsletter process
    result = run_instagram_newsletter(usernames, use_samples=sample_mode)
    
    if result:
        print("\nNewsletter generation successful!")
        print(f"Subject: {result['subject']}")
        print(f"Newsletter file: {result['newsletter_file']}")
        print("Open the HTML file in a browser to view the newsletter")
    else:
        print("\nNewsletter generation failed.")
