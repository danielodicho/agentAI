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

def save_newsletter_to_file(newsletter_content, filename="newsletter.html", screenshots=None, include_images=True, stories_info=None):
    """Save the newsletter content to an HTML file, optionally embedding the screenshots."""
    # Clean up the newsletter content to extract just the HTML part
    if "<html>" in newsletter_content.lower():
        # Find the starting <!DOCTYPE html> or <html> tag
        if "<!doctype html>" in newsletter_content.lower():
            start_idx = newsletter_content.lower().find("<!doctype html>")
        else:
            start_idx = newsletter_content.lower().find("<html>")
        
        # Find the ending </html> tag
        end_idx = newsletter_content.lower().find("</html>") + 7
        
        if start_idx >= 0 and end_idx > start_idx:
            html_content = newsletter_content[start_idx:end_idx]
        else:
            html_content = newsletter_content
    else:
        # Extract just the subject line
        subject_line = extract_subject_line(newsletter_content)
        
        # Rest of the content as body
        if "Subject:" in newsletter_content:
            body_start = newsletter_content.find("\n", newsletter_content.find("Subject:"))
            body_content = newsletter_content[body_start:].strip()
        else:
            body_content = newsletter_content
        
        # Create basic HTML structure
        html_content = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{subject_line}</title>\n</head>\n<body>\n{body_content}\n</body>\n</html>"
    
    # If we need to include images and have screenshots available
    if include_images and screenshots and len(screenshots) > 0:
        # Find where to insert the images (before the closing body tag)
        if "</body>" in html_content.lower():
            insert_idx = html_content.lower().rfind("</body>")
        else:
            insert_idx = len(html_content) - 7  # Just before </html>
        
        # Parse stories_info to get account classifications if available
        story_classifications = {}
        if stories_info:
            try:
                # Try to parse the JSON if it's a string
                if isinstance(stories_info, str):
                    import json
                    
                    # Check if JSON is wrapped in code block markers (```json...```)
                    if stories_info.strip().startswith("```") and "```" in stories_info[3:]:
                        # Extract content between the code block markers
                        start_marker = stories_info.find("```") + 3
                        if stories_info[start_marker:].startswith("json\n"):
                            start_marker += 5  # Skip "json\n"
                        elif stories_info[start_marker:].startswith("\n"):
                            start_marker += 1  # Skip newline
                            
                        end_marker = stories_info[start_marker:].find("```") + start_marker
                        json_content = stories_info[start_marker:end_marker].strip()
                        stories_data = json.loads(json_content)
                    else:
                        # Try to parse directly
                        stories_data = json.loads(stories_info)
                else:
                    stories_data = stories_info
                
                # Check if it has a 'stories' key (expected format)
                if 'stories' in stories_data:
                    for story in stories_data['stories']:
                        # Map the filename to its classification
                        if 'filename' in story and 'account_type' in story and 'account_name' in story:
                            story_classifications[story['filename']] = {
                                'account_type': story['account_type'],
                                'account_name': story['account_name']
                            }
            except Exception as e:
                print(f"Warning: Could not parse stories information: {e}")
                print(f"First 100 characters of stories_info: {stories_info[:100]}...")
        
        # Create image gallery section
        image_section = "\n\n<!-- Instagram Story Images -->\n"
        image_section += "<div style='margin-top: 30px; border-top: 1px solid #ccc; padding-top: 20px;'>\n"
        image_section += "<h2 style='text-align: center; color: #ff5722;'>Original Instagram Stories</h2>\n"
        
        # Group stories by account type
        personal_stories = []
        influencer_stories = []
        unknown_stories = []
        
        for i, img_path in enumerate(screenshots):
            img_filename = os.path.basename(img_path)
            
            # Determine account type and name
            account_type = "unknown"
            account_name = "Unknown"
            
            # Try to get from story classifications first
            if img_filename in story_classifications:
                account_type = story_classifications[img_filename]['account_type']
                account_name = story_classifications[img_filename]['account_name']
            # Fallback: try to extract from filename
            elif "_story_" in img_filename:
                account_name = img_filename.split("_story_")[0]
            
            # Categorize the story
            story_item = {
                'path': img_path,
                'filename': img_filename,
                'account_name': account_name
            }
            
            # For sample images that don't have account types, attempt to infer from the content
            if account_type.lower() == "unknown" and img_filename.startswith("story_sample_"):
                if img_filename in ["story_sample_1.png", "story_sample_4.png", "story_sample_5.png", "story_sample_6.png"]:
                    # Assume these are personal friends based on content
                    account_type = "friend"
                    # Set default account names if not already set
                    if account_name == "Unknown":
                        if img_filename == "story_sample_1.png":
                            account_name = "maria.nashef"
                        elif img_filename in ["story_sample_4.png", "story_sample_5.png", "story_sample_6.png"]:
                            account_name = "ladypary_"
                elif img_filename in ["story_sample_2.png"]:
                    account_type = "influencer"
                    if account_name == "Unknown":
                        account_name = "elite.champaign"
                elif img_filename in ["story_sample_3.png"]:
                    account_type = "influencer"
                    if account_name == "Unknown":
                        account_name = "ksi"
            
            if account_type.lower() == "friend" or account_type.lower() == "personal":
                personal_stories.append(story_item)
            elif account_type.lower() == "influencer" or account_type.lower() == "brand":
                influencer_stories.append(story_item)
            else:
                unknown_stories.append(story_item)
        
        # Create friend stories section if we have any
        if personal_stories:
            image_section += "<h3 style='margin-top: 25px; text-align: center; color: #3897f0;'>✨ Friend Stories ✨</h3>\n"
            image_section += "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>\n"
            
            for story in personal_stories:
                image_section += f"<div style='max-width: 300px; text-align: center;'>\n"
                image_section += f"<img src='{story['path']}' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>\n"
                image_section += f"<p style='margin-top: 5px; font-weight: bold;'>{story['account_name']}</p>\n"
                image_section += f"</div>\n"
            
            image_section += "</div>\n"
        
        # Create influencer stories section if we have any
        if influencer_stories:
            image_section += "<h3 style='margin-top: 25px; text-align: center; color: #e1306c;'>🔥 Influencer Content 🔥</h3>\n"
            image_section += "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>\n"
            
            for story in influencer_stories:
                image_section += f"<div style='max-width: 300px; text-align: center;'>\n"
                image_section += f"<img src='{story['path']}' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>\n"
                image_section += f"<p style='margin-top: 5px; font-weight: bold;'>{story['account_name']}</p>\n"
                image_section += f"</div>\n"
            
            image_section += "</div>\n"
        
        # Create unknown type section if we have any
        if unknown_stories:
            image_section += "<h3 style='margin-top: 25px; text-align: center; color: #999;'>Other Stories</h3>\n"
            image_section += "<div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>\n"
            
            for story in unknown_stories:
                image_section += f"<div style='max-width: 300px; text-align: center;'>\n"
                image_section += f"<img src='{story['path']}' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>\n"
                image_section += f"<p style='margin-top: 5px; font-weight: bold;'>{story['account_name']}</p>\n"
                image_section += f"</div>\n"
            
            image_section += "</div>\n"
        
        image_section += "</div>\n"
        
        # Insert the image section
        html_content = html_content[:insert_idx] + image_section + html_content[insert_idx:]
    
    # Write the final HTML to file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Newsletter saved to {filename}")
    return filename

# Enhanced newsletter generation - focusing on top stories
def generate_enhanced_newsletter(analysis, recipient_name="Subscriber"):
    """Generate an enhanced newsletter with friends vs. influencers sections, focusing on top stories."""
    print("\n--- Generating Enhanced Instagram Newsletter ---")
    
    try:
        # Create the prompt for newsletter generation
        messages = [
            {"role": "system", "content": """You are an AI assistant specialized in creating engaging newsletters based on Instagram content.
            Your task is to create a well-formatted, professional newsletter that separates content from friends versus influencers/brands.
            The newsletter should be in HTML format with responsive design and include:
            1. A catchy subject line
            2. Personalized greeting
            3. Separate sections for friends' updates and influencer content
            4. Attribution of content to specific accounts
            5. Well-structured content sections with engaging descriptions
            6. A friendly sign-off
            
            IMPORTANT: Focus only on the top 3 most engaging or relevant stories across both categories.
            You decide which stories are most relevant based on their content, themes, and relevance scores.
            
            Make the newsletter visually appealing with Instagram-inspired styling."""}
        ]
        
        # Add the user prompt with analysis
        user_prompt = f"Based on the following JSON analysis of Instagram stories:\n\n{analysis}\n\nCreate an engaging, well-formatted newsletter email addressed to {recipient_name}. Organize the content into 'Friends Updates' and 'Influencer Highlights' sections as appropriate based on the account classifications. Only include the TOP 3 most interesting/relevant stories in the main content. Include account names with each piece of content. Format the newsletter in HTML with responsive, Instagram-inspired styling."
        messages.append({"role": "user", "content": user_prompt})
        
        print("Generating enhanced newsletter with OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using the current model
            messages=messages,
            max_tokens=2000
        )
        
        newsletter = response.choices[0].message.content
        print("Enhanced newsletter generation complete!")
        return newsletter
        
    except Exception as e:
        print(f"Error during enhanced newsletter generation: {e}")
        return f"Error generating newsletter: {str(e)}"

# Enhanced analysis to include account type classification
def analyze_stories_with_account_info(image_paths):
    """Enhanced analysis that also attempts to classify accounts as friends or influencers."""
    print("\n--- Analyzing Instagram Stories with Enhanced Account Info ---")
    
    if not image_paths or len(image_paths) == 0:
        print("No images provided. Using sample images for testing...")
        sample_images = ["story_sample_1.png", "story_sample_2.png", "story_sample_3.png"]
        existing_samples = [img for img in sample_images if os.path.exists(img)]
        if existing_samples:
            image_paths = existing_samples
        else:
            return "No image content available for analysis."
    
    try:
        # Prepare messages with images
        messages = [
            {"role": "system", "content": """You are an AI assistant specialized in analyzing Instagram stories and creating engaging newsletters. 
            For each Instagram story screenshot:
            1. Describe the content, context, themes, and any text visible in the images.
            2. Try to determine the account type (personal friend or influencer/brand) based on the content.
            3. If possible, identify or suggest the account name.
            4. Categorize the content type (e.g., personal update, promotional, lifestyle, etc.).
            Be detailed but concise."""}
        ]
        
        # Add each image to the messages
        for i, img_path in enumerate(image_paths):
            # Extract username if possible from filename (format: username_story_X.png)
            username = "Unknown"
            img_filename = os.path.basename(img_path)
            if "_story_" in img_filename:
                username = img_filename.split("_story_")[0]
            
            base64_image = encode_image_to_base64(img_path)
            if base64_image:
                messages.append({
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": f"Analyze this Instagram story (image {i+1} of {len(image_paths)}):\n" + 
                                            f"File: {img_filename}\n" + 
                                            (f"Possible username: {username}\n" if username != "Unknown" else "")},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                })
            else:
                print(f"Skipping image {img_path} due to encoding error")
        
        # Ask for a comprehensive analysis with account classification
        messages.append({
            "role": "user",
            "content": """Now provide a comprehensive JSON-formatted analysis of all the Instagram stories, with this structure:
            {
                "stories": [
                    {
                        "index": 0,  // zero-based index of the image
                        "filename": "story_sample_1.png",
                        "account_name": "username or best guess",
                        "account_type": "friend" or "influencer",  // classify based on content
                        "content_type": "personal", "promotional", etc.,
                        "description": "detailed description of the content",
                        "visible_text": "any text visible in the image",
                        "themes": ["theme1", "theme2"],
                        "relevance": "high/medium/low"
                    },
                    // Repeat for each image
                ],
                "overall_themes": ["theme1", "theme2"],
                "newsletter_sections": [
                    {
                        "title": "Section title",
                        "description": "Section content suggestion",
                        "related_stories": [0, 1]  // indices of related stories
                    }
                ]
            }
            
            This will be used to generate a newsletter that differentiates between friend updates and influencer content."""
        })
        
        print("Sending images to OpenAI for enhanced analysis...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using the current vision-capable model
            messages=messages,
            max_tokens=1500,
            response_format={"type": "text"}
        )
        
        analysis = response.choices[0].message.content
        print("Enhanced analysis complete!")
        return analysis
    
    except Exception as e:
        print(f"Error during enhanced OpenAI analysis: {e}")
        return f"Error analyzing Instagram stories: {str(e)}"

# Enhanced newsletter generation
def generate_enhanced_newsletter(analysis, recipient_name="Subscriber"):
    """Generate an enhanced newsletter with friends vs. influencers sections."""
    print("\n--- Generating Enhanced Instagram Newsletter ---")
    
    try:
        # Create the prompt for newsletter generation
        messages = [
            {"role": "system", "content": """You are an AI assistant specialized in creating engaging newsletters based on Instagram content.
            Your task is to create a well-formatted, professional newsletter that separates content from friends versus influencers/brands.
            The newsletter should be in HTML format with responsive design and include:
            1. A catchy subject line
            2. Personalized greeting
            3. Separate sections for friends' updates and influencer content
            4. Attribution of content to specific accounts
            5. Well-structured content sections with engaging descriptions
            6. A friendly sign-off
            
            Make the newsletter visually appealing with Instagram-inspired styling."""}
        ]
        
        # Add the user prompt with analysis
        user_prompt = f"Based on the following JSON analysis of Instagram stories:\n\n{analysis}\n\nCreate an engaging, well-formatted newsletter email addressed to {recipient_name}. Organize the content into 'Friends Updates' and 'Influencer Highlights' sections as appropriate based on the account classifications. Include account names with each piece of content. Format the newsletter in HTML with responsive, Instagram-inspired styling."
        messages.append({"role": "user", "content": user_prompt})
        
        print("Generating enhanced newsletter with OpenAI...")
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using the current model
            messages=messages,
            max_tokens=2000
        )
        
        newsletter = response.choices[0].message.content
        print("Enhanced newsletter generation complete!")
        return newsletter
        
    except Exception as e:
        print(f"Error during enhanced newsletter generation: {e}")
        return f"Error generating newsletter: {str(e)}"

# Main Process Function
def run_instagram_newsletter(usernames=None, use_samples=False):
    """Main function to run the Instagram story newsletter process."""
    print("\n=== Instagram Story Newsletter Generator ===\n")
    
    if use_samples:
        print("Using sample images instead of extracting from Instagram...")
        sample_images = glob.glob("story_sample_*.png")
        
        # Check if sample images exist
        if sample_images:
            print(f"Found {len(sample_images)} sample images")
            screenshots = sample_images
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
    stories_info = analyze_stories_with_account_info(screenshots)
    print(f"\nContent Analysis Summary:\n{stories_info[:300]}..." + ("" if len(stories_info) <= 300 else "\n[content trimmed]"))
    
    # Step 4: Generate a newsletter based on the analysis
    print("\nStep 4: Generating newsletter based on analysis")
    newsletter = generate_enhanced_newsletter(stories_info, "Instagram Subscriber") 
    
    # Step 5: Save the newsletter to a file
    print("\nStep 5: Saving newsletter to file")
    subject_line = extract_subject_line(newsletter)
    print(f"Newsletter Subject: {subject_line}")
    
    # Create a unique filename using timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    newsletter_file = f"instagram_newsletter_{timestamp}.html"
    
    # Pass the stories_info to the save_newsletter function for grouping
    save_newsletter_to_file(newsletter, newsletter_file, screenshots, True, stories_info)
    
    print(f"\nInstagram Newsletter process complete!")
    print(f"Newsletter saved to {newsletter_file}")
    
    return {
        "subject": subject_line,
        "newsletter_file": newsletter_file,
        "analysis": stories_info,
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
