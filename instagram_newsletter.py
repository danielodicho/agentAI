import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
from datetime import datetime
from agents import Agent, Runner
import agentops
import time

# Load environment variables
load_dotenv()

# Initialize AgentOps if key is available
agentops_key = os.getenv("AGENTOPS_API_KEY")
if agentops_key:
    agentops.init(agentops_key)
else:
    print("AgentOps API key not found, skipping trace export")

# Print startup message
print("*** Instagram Newsletter Automation ***")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

#################################
# Instagram Login Function
#################################
def login_instagram():
    """Automates Instagram login and returns session cookies."""
    print("\n=== Instagram Login ===\n")
    
    # Check for credentials
    instagram_user = os.getenv('INSTAGRAM_USER')
    instagram_pass = os.getenv('INSTAGRAM_PASS')
    
    if not instagram_user or not instagram_pass:
        print("Error: Instagram credentials not found in .env file")
        print("Please add INSTAGRAM_USER and INSTAGRAM_PASS to your .env file")
        return None
    
    print(f"Logging in as {instagram_user}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Set to True for production
            page = browser.new_page()
            print("Opening Instagram login page...")
            page.goto("https://instagram.com/accounts/login")
            
            # Wait for page to fully load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Extra wait to ensure login form is ready
            
            # Fill in the login form with explicit waits
            print("Filling username field...")
            page.fill('input[name="username"]', instagram_user)
            page.wait_for_timeout(1000)  # Wait 1 second
            
            print("Filling password field...")
            page.fill('input[name="password"]', instagram_pass)
            page.wait_for_timeout(1000)  # Wait 1 second
            
            print("Submitting login form...")
            page.click("button[type='submit']")
            
            # Wait for navigation to complete after login
            try:
                print("Waiting for login to complete...")
                
                # Wait for any security checkpoint to appear
                page.wait_for_timeout(5000)  # 5 seconds to load any security page
                
                # Wait for any of these selectors that might indicate a successful login
                selectors = [
                    "xpath=//div[contains(text(),'Home')]",  # Text-based Home button
                    "[aria-label='Home']",                 # Aria-label Home button
                    "svg[aria-label='Home']",              # SVG Home icon
                    "[role='main']",                       # Main content area
                ]
                
                print("Checking for successful login...")
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
                    # Check based on URL
                    current_url = page.url
                    if "instagram.com" in current_url and "accounts/login" not in current_url:
                        print(f"Login appears successful based on URL: {current_url}")
                        success = True
                
                if success:
                    print("Login successful!")
                    cookies = page.context.cookies()
                    browser.close()
                    return cookies
                else:
                    print("Could not confirm successful login.")
                    browser.close()
                    return None
            except Exception as e:
                print(f"Error during login: {e}")
                print("Login failed. Check credentials or try again.")
                browser.close()
                return None
    except Exception as e:
        print(f"Error setting up browser: {e}")
        return None

#################################
# Screenshot Stories Function
#################################
def screenshot_stories(cookies, num_stories=5):
    """Navigates to Instagram stories, captures screenshots, and returns a list of file paths."""
    print("\n=== Capturing Instagram Stories ===\n")
    screenshots = []
    
    if not cookies:
        print("Error: No cookies provided. Please login first.")
        return screenshots
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Set to True for production
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            
            print("Navigating to Instagram homepage...")
            page.goto("https://instagram.com")
            
            # Give page time to load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)  # Additional time to ensure full load
            
            # Save a screenshot for debugging
            page.screenshot(path="instagram_home.png")
            
            print("Looking for Instagram stories...")
            # Try different selectors for the stories button
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
                        page.click(selector)
                        page.wait_for_timeout(2000)  # Wait for story to open
                        success = True
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not success:
                print("Could not find or click any stories using available selectors")
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
            
            browser.close()
            print(f"Successfully captured {len(screenshots)} screenshots")
    except Exception as e:
        print(f"Error capturing stories: {e}")
    
    return screenshots

#################################
# PDF Creation Function
#################################
def create_pdf(screenshots):
    """Compiles screenshot images into a PDF digest."""
    print("\n=== Creating PDF Digest ===\n")
    
    if not screenshots:
        print("Error: No screenshots provided. Cannot create PDF.")
        return None
    
    try:
        pdf = FPDF()
        
        # Add a cover page
        pdf.add_page()
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 20, "Instagram Stories Digest", 0, 1, "C")
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 1, "C")
        pdf.cell(0, 10, f"Contains {len(screenshots)} stories", 0, 1, "C")
        
        # Add each screenshot to a new page
        for i, image in enumerate(screenshots):
            print(f"Adding {image} to PDF...")
            pdf.add_page()
            try:
                pdf.image(image, x=10, y=10, w=190)  # adjust size as necessary
                print(f"Added {image} to PDF")
            except Exception as e:
                print(f"Error adding {image} to PDF: {e}")
                continue
        
        # Save the PDF
        pdf_filename = "instagram_digest.pdf"
        pdf.output(pdf_filename)
        print(f"PDF digest created successfully: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

#################################
# AI Content Analysis & Newsletter Generation
#################################

# Newsletter generation agent
newsletter_agent = Agent(
    name="InstagramDigestAgent",
    instructions="""You are an AI assistant specialized in creating engaging newsletters based on Instagram content.
    Your task is to analyze Instagram story screenshots, understand the content, extract key information,
    and create a well-formatted, engaging newsletter. Focus on:
    1. Identifying main themes and topics from the stories
    2. Extracting any visible text from the screenshots
    3. Creating a cohesive narrative that connects the stories
    4. Writing in an engaging, conversational style
    5. Adding helpful commentary and context to the content
    6. Organizing content in a logical and appealing structure
    """
)

# Mock responses for testing without API key
MOCK_ANALYSIS = """
Based on the Instagram stories captured, here's my analysis:

1. Story 1 appears to be a personal update, possibly showing a daily activity or highlight moment.
   It likely contains a casual setting with some visual elements that engage followers.

2. Story 2 seems to showcase a product or experience, potentially with some descriptive text overlay.
   This type of content is common for sharing recommendations or promotions.

3. Story 3 might be a more interactive element, perhaps a poll, question box, or behind-the-scenes glimpse.
   These types of stories typically drive engagement and create a sense of connection.

Overall themes:
- Personal sharing and lifestyle content
- Product or experience highlights
- Interactive engagement with followers

This content represents a typical mix of Instagram story elements that balance personal connection with follower engagement.
"""

MOCK_NEWSLETTER = """
Subject: This Week's Instagram Highlights: Personal Updates & Must-See Moments

<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #405DE6;">Instagram Highlights Digest</h1>
    
    <p>Hey Subscriber,</p>
    
    <p>We've captured some amazing moments from Instagram stories that you might have missed!</p>
    
    <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h2 style="color: #833AB4;">Personal Moments</h2>
        <p>The latest stories featured some delightful personal updates, giving us a glimpse into daily life and special moments that create authentic connections.</p>
    </div>
    
    <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h2 style="color: #833AB4;">Featured Highlights</h2>
        <p>We noticed some exciting product features and experiences being shared! These highlights showcase some must-see recommendations that you'll definitely want to check out.</p>
    </div>
    
    <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h2 style="color: #833AB4;">Community Engagement</h2>
        <p>The stories included some interactive elements designed to connect with followers. This kind of engagement creates a vibrant community experience that we all appreciate.</p>
    </div>
    
    <p>Don't miss out on future updates! We'll keep bringing you the best Instagram content in your next digest.</p>
    
    <p>Until next time,<br>
    Your Instagram Digest Team</p>
</body>
</html>
"""

def analyze_screenshot_content(screenshot_paths):
    """Use the AI agent to analyze the content of Instagram story screenshots."""
    print("\n=== Analyzing Instagram Stories Content ===\n")
    
    # For demo purposes, we're just passing the filenames
    # In a real implementation, you'd extract text/content from the images first
    screenshot_info = "\n".join([f"- {path}" for path in screenshot_paths])
    
    prompt = f"""Analyze the following Instagram story screenshots that were captured on {datetime.now().strftime('%Y-%m-%d')}:
    {screenshot_info}
    
    Since you can't see the actual images, create a sample analysis based on what these might contain.
    Include possible themes, topics, and content types that might be present in Instagram stories.
    Structure your analysis to later be used for newsletter generation.
    """
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("No OpenAI API key found. Using mock analysis response.")
        return MOCK_ANALYSIS
    
    try:
        print("Asking AI agent to analyze the stories...")
        result = Runner.run_sync(newsletter_agent, prompt)
        print("\nAI Analysis Complete!")
        return result.final_output
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        print("Falling back to mock analysis...")
        return MOCK_ANALYSIS

def generate_newsletter(analysis, recipient_name="Subscriber"):
    """Use the AI agent to generate a newsletter based on the content analysis."""
    print("\n=== Generating Instagram Newsletter ===\n")
    
    prompt = f"""Based on the following analysis of Instagram stories:
    
    {analysis}
    
    Create an engaging, well-formatted newsletter email addressed to {recipient_name}.
    Include a catchy subject line, personalized greeting, summary of the Instagram highlights,
    and a friendly sign-off. Format the newsletter in HTML with appropriate styling.
    """
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("No OpenAI API key found. Using mock newsletter response.")
        return MOCK_NEWSLETTER
    
    try:
        print("Asking AI agent to create the newsletter...")
        result = Runner.run_sync(newsletter_agent, prompt)
        print("\nNewsletter Generation Complete!")
        return result.final_output
    except Exception as e:
        print(f"Error during newsletter generation: {e}")
        print("Falling back to mock newsletter...")
        return MOCK_NEWSLETTER

def extract_subject_line(newsletter_content):
    """Extract the subject line from the generated newsletter."""
    if "Subject:" in newsletter_content:
        lines = newsletter_content.split("\n")
        for line in lines:
            if line.startswith("Subject:"):
                return line.replace("Subject:", "").strip()
    
    # Default subject if none found
    return "Your Instagram Digest for " + datetime.now().strftime("%Y-%m-%d")

#################################
# Email Sending Function
#################################
def send_email(pdf_filename, newsletter_content, receiver_email=None):
    """Sends the PDF digest and newsletter content via email using SMTP."""
    print("\n=== Sending Email ===\n")
    
    if not pdf_filename or not os.path.exists(pdf_filename):
        print(f"Error: PDF file {pdf_filename} does not exist")
        return False
    
    # Check for email credentials
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    receiver_email = receiver_email or os.getenv('RECEIVER_EMAIL')
    
    if not email_user or not email_pass or not receiver_email:
        print("Error: Email credentials not found in .env file")
        print("Please add EMAIL_USER, EMAIL_PASS, and RECEIVER_EMAIL to your .env file")
        return False
    
    # Extract subject line from newsletter content
    subject_line = extract_subject_line(newsletter_content)
    
    try:
        print(f"Preparing email to {receiver_email}...")
        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = receiver_email
        msg["Subject"] = subject_line
        
        # Add the newsletter content as HTML
        if "<html>" in newsletter_content:
            # Extract just the HTML part if there's a subject line or other text before it
            html_start = newsletter_content.find("<html>")
            html_end = newsletter_content.find("</html>", html_start) + 7
            html_content = newsletter_content[html_start:html_end]
            
            msg.add_alternative(html_content, subtype="html")
        else:
            # Just use the content as is
            msg.set_content(newsletter_content)
        
        # Attach the PDF
        with open(pdf_filename, "rb") as f:
            file_data = f.read()
            msg.add_attachment(
                file_data, 
                maintype="application", 
                subtype="pdf", 
                filename=pdf_filename
            )
        
        # Send the email
        print("Connecting to email server...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

#################################
# Mock Functions for Testing
#################################
def mock_login():
    """Mock function for testing without Instagram credentials."""
    print("Using mock login (no actual Instagram login)")
    return [{'name': 'mock_cookie', 'value': 'mock_value'}]  # Return mock cookies

def mock_screenshot_stories(cookies=None, num_stories=3):
    """Mock function for testing without actual Instagram access."""
    print("Using mock screenshot function (no actual Instagram access)")
    screenshots = []
    
    for i in range(num_stories):
        # Create mock screenshot filename
        screenshot_path = f"mock_story_{i+1}.png"
        screenshots.append(screenshot_path)
        print(f"Created mock story reference: {screenshot_path}")
    
    return screenshots

def mock_send_email(pdf_filename=None, newsletter_content=None, receiver_email=None):
    """Mock function for testing without email credentials."""
    print("\n=== Mock Email Sending ===\n")
    receiver = receiver_email or "test@example.com"
    subject = extract_subject_line(newsletter_content)
    
    print(f"Simulating sending email to: {receiver}")
    print(f"Subject: {subject}")
    print(f"Attachments: {pdf_filename}")
    print("Email content: HTML Newsletter")
    print("Email sent successfully! (mock)")
    return True

#################################
# Main Pipeline Function
#################################
def run_instagram_newsletter_pipeline(use_mocks=False, num_stories=5, receiver_email=None):
    """Run the complete Instagram newsletter pipeline from login to email sending."""
    print("\n====== Instagram Newsletter Pipeline ======\n")
    start_time = time.time()
    
    # Step 1: Login (or use mock)
    if use_mocks:
        print("Using mock functions (no real credentials needed)")
        cookies = mock_login()
        screenshots = mock_screenshot_stories(cookies, num_stories)
    else:
        # Check for Instagram credentials
        if not os.getenv('INSTAGRAM_USER') or not os.getenv('INSTAGRAM_PASS'):
            print("Instagram credentials missing. Using mock functions.")
            cookies = mock_login()
            screenshots = mock_screenshot_stories(None, num_stories)
        else:
            # Real Instagram login and screenshots
            cookies = login_instagram()
            if not cookies:
                print("Login failed. Falling back to mock functions.")
                cookies = mock_login()
                screenshots = mock_screenshot_stories(cookies, num_stories)
            else:
                screenshots = screenshot_stories(cookies, num_stories)
    
    # Step 2: Create PDF from screenshots
    if not screenshots:
        print("Failed to capture screenshots. Cannot proceed.")
        return False
    
    pdf_file = create_pdf(screenshots)
    if not pdf_file:
        print("Failed to create PDF. Cannot proceed.")
        return False
    
    # Step 3: Analyze content with AI
    analysis = analyze_screenshot_content(screenshots)
    
    # Step 4: Generate newsletter
    recipient = receiver_email or os.getenv('RECEIVER_EMAIL') or "Subscriber"
    recipient_name = recipient.split('@')[0] if '@' in recipient else recipient
    newsletter = generate_newsletter(analysis, recipient_name)
    
    # Step 5: Send email
    if use_mocks or not os.getenv('EMAIL_USER') or not os.getenv('EMAIL_PASS'):
        print("Email credentials missing or using mocks. Using mock email sender.")
        email_sent = mock_send_email(pdf_file, newsletter, receiver_email)
    else:
        email_sent = send_email(pdf_file, newsletter, receiver_email)
    
    if not email_sent:
        print("Failed to send email.")
        return False
    
    # Calculate and print execution time
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n====== Pipeline Completed Successfully! ======")
    print(f"Total execution time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    return True

#################################
# Main Execution
#################################
if __name__ == "__main__":
    # By default, we'll use mocks unless command line arguments are provided
    use_mocks = True
    num_stories = 5
    recipient = None
    
    # Check for command line arguments
    import sys
    if len(sys.argv) > 1:
        if "--real" in sys.argv:
            use_mocks = False
            print("Running with real credentials (no mocks)")
        
        for arg in sys.argv:
            if arg.startswith("--stories="):
                try:
                    num_stories = int(arg.split("=")[1])
                    print(f"Set to capture {num_stories} stories")
                except:
                    pass
            
            if arg.startswith("--email="):
                recipient = arg.split("=")[1]
                print(f"Set recipient to: {recipient}")
    
    # Run the pipeline
    run_instagram_newsletter_pipeline(use_mocks, num_stories, recipient)
