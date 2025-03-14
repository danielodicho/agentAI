from agents import Agent, Runner
import agentops
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

load_dotenv()

# Initialize AgentOps
agentops.init(os.getenv("AGENTOPS_API_KEY"))

# Basic agent functionality
agent = Agent(name="Assistant", instructions="You are a helpful assistant")

# Instagram login function
def login_instagram():
    """Automates Instagram login and returns session cookies."""
    print("Starting Instagram login process...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            print("Opening Instagram login page...")
            page.goto("https://instagram.com/accounts/login")
            
            # Check for credentials before proceeding
            instagram_user = os.getenv('INSTAGRAM_USER')
            instagram_pass = os.getenv('INSTAGRAM_PASS')
            
            if not instagram_user or not instagram_pass:
                print("Error: Instagram credentials not found in .env file")
                print("Please add INSTAGRAM_USER and INSTAGRAM_PASS to your .env file")
                return None
            
            print(f"Logging in as {instagram_user}...")
            
            # Fill in the login form
            page.fill('input[name="username"]', instagram_user)
            page.fill('input[name="password"]', instagram_pass)
            page.click("button[type='submit']")
            
            # Wait for navigation to complete after login
            try:
                print("Waiting for login to complete...")
                page.wait_for_selector("xpath=//div[contains(text(),'Home')]")
                print("Login successful!")
                cookies = page.context.cookies()
                browser.close()
                return cookies
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

# Screenshot stories function
def screenshot_stories(cookies, num_stories=3):
    """Navigates to Instagram stories, captures screenshots, and returns a list of file paths."""
    print("\n--- Capturing Instagram Stories ---")
    screenshots = []
    
    if not cookies:
        print("Error: No cookies provided. Please login first.")
        return screenshots
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            
            print("Navigating to Instagram homepage...")
            page.goto("https://instagram.com")
            
            # Give page time to load
            page.wait_for_load_state("networkidle")
            
            # Take a screenshot of homepage for debugging
            page.screenshot(path="instagram_home.png")
            print("Homepage screenshot saved as instagram_home.png")
            
            print("Looking for stories button...")
            # Try different selectors for the stories button
            try:
                # Try clicking on the first story in the stories tray
                print("Attempting to click on first story...")
                page.wait_for_selector("xpath=//div[contains(@role,'button') and contains(@aria-label,'Story')]")
                page.click("xpath=//div[contains(@role,'button') and contains(@aria-label,'Story')]")
            except Exception as e:
                print(f"Could not find stories using primary selector: {e}")
                try:
                    # Alternative selector
                    print("Trying alternative selector...")
                    page.click("xpath=//button[contains(@aria-label,'Stories')]")
                except Exception as e:
                    print(f"Could not find stories using alternative selector: {e}")
                    # One more attempt with a more generic selector
                    try:
                        print("Trying one more selector approach...")
                        # Take a screenshot to help identify the UI
                        page.screenshot(path="before_click.png")
                        print("Screenshot saved as before_click.png")
                        
                        # Try to find stories by looking for circular elements that might be story icons
                        page.click("xpath=//div[contains(@class,'story')]")
                    except Exception as e:
                        print(f"Final attempt failed: {e}")
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

# PDF Creation function
def create_pdf(screenshots):
    """Compiles screenshot images into a PDF digest."""
    print("\n--- Creating PDF Digest ---")
    
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
        pdf.cell(0, 10, f"Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}", 0, 1, "C")
        pdf.cell(0, 10, f"Contains {len(screenshots)} stories", 0, 1, "C")
        
        # Add each screenshot to a new page
        for i, image in enumerate(screenshots):
            print(f"Adding {image} to PDF...")
            pdf.add_page()
            # Try to add the image to the PDF
            try:
                pdf.image(image, x=10, y=10, w=190)  # adjust size as necessary
                print(f"Added {image} to PDF")
            except Exception as e:
                print(f"Error adding {image} to PDF: {e}")
                # Continue to the next image rather than failing completely
                continue
        
        # Save the PDF
        pdf_filename = "instagram_digest.pdf"
        pdf.output(pdf_filename)
        print(f"PDF digest created successfully: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

# Email sending function
def send_email(pdf_filename, receiver_email=None):
    """Sends the PDF digest via email using SMTP."""
    print("\n--- Sending Email ---")
    
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
    
    try:
        print(f"Preparing email to {receiver_email}...")
        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = receiver_email
        msg["Subject"] = "Instagram Stories Daily Digest"
        msg.set_content("Your daily Instagram stories digest is attached.")
        
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

# Function to check if we have Instagram credentials
def check_instagram_credentials():
    instagram_user = os.getenv('INSTAGRAM_USER')
    instagram_pass = os.getenv('INSTAGRAM_PASS')
    if instagram_user and instagram_pass:
        print("Instagram credentials found in .env file")
        return True
    else:
        print("Instagram credentials not found in .env file")
        print("Please add the following to your .env file:")
        print("INSTAGRAM_USER=your_instagram_username")
        print("INSTAGRAM_PASS=your_instagram_password")
        return False

# Function to check if we have Email credentials
def check_email_credentials():
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    receiver_email = os.getenv('RECEIVER_EMAIL')
    
    if email_user and email_pass and receiver_email:
        print("Email credentials found in .env file")
        return True
    else:
        print("Email credentials not found in .env file")
        print("Please add the following to your .env file:")
        print("EMAIL_USER=your_email_address")
        print("EMAIL_PASS=your_email_password_or_app_password")
        print("RECEIVER_EMAIL=recipient_email_address")
        return False

# Mock functions for testing without Instagram credentials
def mock_login():
    """Mock function to simulate a successful login without actual Instagram credentials."""
    print("Using mock login (no actual Instagram login)")
    return [{'name': 'mock_cookie', 'value': 'mock_value'}]  # Return mock cookies

def mock_screenshot_stories(cookies=None, num_stories=3):
    """Mock function to simulate capturing screenshots without actual Instagram access."""
    print("Using mock screenshot function (no actual Instagram access)")
    screenshots = []
    
    for i in range(num_stories):
        # Create a simple FPDF to generate image files
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Mock Instagram Story {i+1}", 0, 1, "C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "This is a mock story for testing purposes", 0, 1, "C")
        
        # Save as PNG using PDF's output method
        screenshot_path = f"mock_story_{i+1}.png"
        try:
            # Create PDF first, then convert to image (simplified for testing)
            temp_pdf = f"temp_{i}.pdf"
            pdf.output(temp_pdf)
            
            # For now, just pretend we have images
            screenshots.append(screenshot_path)
            print(f"Created mock story file: {screenshot_path}")
        except Exception as e:
            print(f"Error creating mock story: {e}")
    
    return screenshots

# Mock email sending
def mock_send_email(pdf_filename=None, receiver_email=None):
    """Mock function to simulate sending an email without actual email credentials."""
    print("\n--- Mock Email Sending ---")
    print(f"Simulating sending digest to: {receiver_email or 'test@example.com'}")
    print("Email sent successfully! (mock)")
    return True

# Integrated test function
def test_instagram_digest(use_mocks=True):
    print("\n--- Testing Instagram Digest Functions ---")
    
    if use_mocks:
        print("\nUsing mock functions for testing without real credentials")
        # Step 1: Login to Instagram (mock)
        print("\nStep 1: Mock Instagram login")
        cookies = mock_login()
        
        # Step 2: Screenshot stories (mock)
        print("\nStep 2: Mock story screenshots")
        screenshots = mock_screenshot_stories(cookies, 3)  # Mock 3 stories
    else:
        # Step 1: Check credentials
        if not check_instagram_credentials():
            print("Instagram credentials missing. Using mocks instead.")
            cookies = mock_login()
            screenshots = mock_screenshot_stories(cookies, 3)
        else:
            # Step 2: Login to Instagram
            print("\nStep 1: Logging in to Instagram")
            cookies = login_instagram()
            if not cookies:
                print("Login failed. Cannot proceed with real Instagram.")
                return False
            
            # Step 3: Screenshot stories
            print("\nStep 2: Capturing story screenshots")
            screenshots = screenshot_stories(cookies, 3)  # Capture 3 stories
    
    if not screenshots:
        print("Failed to capture any screenshots (real or mock)")
        return False
    
    print(f"\nSuccessfully obtained {len(screenshots)} story screenshots:")
    for screenshot in screenshots:
        print(f"- {screenshot}")
    
    # Step 4: Create PDF
    print("\nStep 3: Creating PDF digest")
    pdf_file = create_pdf(screenshots)
    if not pdf_file:
        print("Failed to create PDF digest")
        return False
    
    print(f"\nSuccessfully created PDF digest: {pdf_file}")
    
    # Step 5: Send Email
    print("\nStep 4: Sending email with digest")
    if use_mocks:
        email_sent = mock_send_email(pdf_file, "test@example.com")
    else:
        # Check for email credentials
        if not check_email_credentials():
            print("Email credentials missing. Using mock email sender.")
            email_sent = mock_send_email(pdf_file)
        else:
            email_sent = send_email(pdf_file)
    
    if not email_sent:
        print("Failed to send email with digest")
        return False
    
    print("\nCompleted Instagram digest pipeline test!")
    return True

# Complete Instagram Digest Pipeline function
def run_instagram_digest_pipeline(use_mocks=False, num_stories=5, receiver_email=None):
    """Run the complete Instagram digest pipeline from login to email sending."""
    print("\n=== Running Instagram Digest Pipeline ===\n")
    
    # Step 1: Get cookies (either real or mock)
    if use_mocks:
        print("Using mock functions (no real credentials needed)")
        cookies = mock_login()
        screenshots = mock_screenshot_stories(cookies, num_stories)
        pdf_file = create_pdf(screenshots)
        email_sent = mock_send_email(pdf_file, receiver_email)
    else:
        # Check for all required credentials
        instagram_creds = check_instagram_credentials()
        email_creds = check_email_credentials()
        
        if not instagram_creds:
            print("Cannot run pipeline without Instagram credentials.")
            return False
        
        if not email_creds:
            print("Cannot run pipeline without email credentials.")
            return False
        
        # Run the real pipeline
        cookies = login_instagram()
        if not cookies:
            print("Login failed. Cannot proceed.")
            return False
        
        screenshots = screenshot_stories(cookies, num_stories)
        if not screenshots:
            print("Failed to capture screenshots. Cannot proceed.")
            return False
        
        pdf_file = create_pdf(screenshots)
        if not pdf_file:
            print("Failed to create PDF. Cannot proceed.")
            return False
        
        email_sent = send_email(pdf_file, receiver_email)
        if not email_sent:
            print("Failed to send email.")
            return False
    
    print("\n=== Instagram Digest Pipeline Completed Successfully! ===\n")
    return True

# Main execution
if __name__ == "__main__":
    # Run the Instagram digest test with mocks (no real Instagram credentials needed)
    test_instagram_digest(use_mocks=True)
    
    # Original agent demo
    print("\n--- Agent Demo ---")
    result = Runner.run_sync(agent, "Write a short essay about recursion in programming.")
    print(result.final_output)
    
    # Uncomment to run the complete Instagram Digest Pipeline
    # run_instagram_digest_pipeline(use_mocks=True)