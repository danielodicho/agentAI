import os
import time
import smtplib
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright
from agents import Agent, Runner, tool
import agentops

# Load environment variables
load_dotenv()

# Initialize AgentOps if key is available
agentops_key = os.getenv("AGENTOPS_API_KEY")
if agentops_key:
    agentops.init(agentops_key)
else:
    print("AgentOps API key not found, skipping trace export")

# Ensure the folder for screenshots exists
IMAGE_FOLDER = "instagram_stories"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

#############################
# INSTAGRAM SCRAPING SECTION
#############################

def login_instagram():
    """Automates Instagram login and returns session cookies."""
    print("\n=== Instagram Login ===\n")
    
    instagram_user = os.getenv('INSTAGRAM_USER')
    instagram_pass = os.getenv('INSTAGRAM_PASS')
    if not instagram_user or not instagram_pass:
        print("Error: Instagram credentials not found in .env file")
        return None
    
    print(f"Logging in as {instagram_user}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://instagram.com/accounts/login")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            page.fill('input[name="username"]', instagram_user)
            page.wait_for_timeout(1000)
            page.fill('input[name="password"]', instagram_pass)
            page.wait_for_timeout(1000)
            page.click("button[type='submit']")
            
            print("Waiting for login to complete...")
            page.wait_for_timeout(5000)
            selectors = [
                "xpath=//div[contains(text(),'Home')]",
                "[aria-label='Home']",
                "svg[aria-label='Home']",
                "[role='main']",
            ]
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
                if "instagram.com" in page.url and "accounts/login" not in page.url:
                    print(f"Login appears successful based on URL: {page.url}")
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
        print(f"Error setting up browser: {e}")
        return None

def screenshot_stories(cookies, num_stories=5):
    """Navigates to Instagram stories, captures screenshots, and returns list of file paths."""
    print("\n=== Capturing Instagram Stories ===\n")
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
            page.goto("https://instagram.com")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            page.screenshot(path=os.path.join(IMAGE_FOLDER, "instagram_home.png"))
            
            print("Looking for Instagram stories...")
            story_selectors = [
                "xpath=//div[contains(@role,'button') and contains(@aria-label,'Story')]",
                "xpath=//img[contains(@alt,'Story')]/ancestor::div[contains(@role,'button')]",
                "css=div[role='button'][tabindex='0']:has(canvas)",
                "xpath=//section//div/div/div/div[1]/div/div/div/div/div/div/div[1]"
            ]
            success = False
            for selector in story_selectors:
                try:
                    if page.wait_for_selector(selector, timeout=5000):
                        print(f"Story found with selector: {selector}")
                        page.click(selector)
                        page.wait_for_timeout(2000)
                        success = True
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            if not success:
                print("Could not find any stories using available selectors")
                browser.close()
                return screenshots
            
            print("Capturing screenshots of stories...")
            for i in range(num_stories):
                page.wait_for_timeout(2000)
                screenshot_path = os.path.join(IMAGE_FOLDER, f"story_{i+1}.png")
                page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
                print(f"Screenshot saved as {screenshot_path}")
                page.keyboard.press('ArrowRight')
                page.wait_for_timeout(1000)
            
            browser.close()
            print(f"Captured {len(screenshots)} screenshots")
    except Exception as e:
        print(f"Error capturing stories: {e}")
    
    return screenshots

def create_pdf(screenshots):
    """Compiles screenshot images into a PDF digest."""
    print("\n=== Creating PDF Digest ===\n")
    if not screenshots:
        print("Error: No screenshots provided. Cannot create PDF.")
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 20, "Instagram Stories Digest", 0, 1, "C")
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 1, "C")
        pdf.cell(0, 10, f"Contains {len(screenshots)} stories", 0, 1, "C")
        for image in screenshots:
            pdf.add_page()
            try:
                pdf.image(image, x=10, y=10, w=190)
                print(f"Added {image} to PDF")
            except Exception as e:
                print(f"Error adding {image} to PDF: {e}")
                continue
        pdf_filename = "instagram_digest.pdf"
        pdf.output(pdf_filename)
        print(f"PDF digest created: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

#############################
# NEWSLETTER GENERATION SECTION
#############################

# Define a newsletter agent for AI content analysis and newsletter creation
newsletter_agent = Agent(
    name="InstagramDigestAgent",
    instructions="""You are an AI assistant specialized in creating engaging newsletters based on Instagram content.
Your task is to analyze Instagram story screenshots (represented by their filenames), identify key themes and topics,
and generate an HTML-formatted newsletter email with a catchy subject line, personalized greeting, content summary,
and friendly sign-off."""
)

MOCK_ANALYSIS = """
Based on the screenshots captured, the stories show a mix of personal updates, product highlights, and interactive content.
Overall themes include lifestyle moments, influencer promotions, and community engagement.
"""

MOCK_NEWSLETTER = """
Subject: This Week's Instagram Highlights: Capturing Life's Moments

<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #405DE6;">Instagram Highlights Digest</h1>
    <p>Hello Subscriber,</p>
    <p>We’ve captured some amazing Instagram stories this week featuring personal updates, exciting product showcases, and interactive moments.
    Enjoy the digest below and stay tuned for more!</p>
    <p>Best,<br>Your Instagram Digest Team</p>
</body>
</html>
"""

def analyze_screenshot_content(screenshot_paths):
    """Analyze the content of Instagram story screenshots using AI."""
    print("\n=== Analyzing Instagram Stories Content ===\n")
    screenshot_info = "\n".join([f"- {os.path.basename(path)}" for path in screenshot_paths])
    prompt = f"""Analyze the following Instagram story screenshots captured on {datetime.now().strftime('%Y-%m-%d')}:
{ screenshot_info }

Since you cannot see the images, provide a sample analysis based on common Instagram story themes.
Include potential topics, text elements, and engagement cues."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("No OpenAI API key found. Using mock analysis.")
        return MOCK_ANALYSIS
    
    try:
        result = Runner.run_sync(newsletter_agent, prompt)
        return result.final_output
    except Exception as e:
        print(f"Error during AI analysis: {e}")
        return MOCK_ANALYSIS

def generate_newsletter(analysis, recipient_name="Subscriber"):
    """Generate a newsletter based on analysis using AI."""
    print("\n=== Generating Instagram Newsletter ===\n")
    prompt = f"""Based on the following analysis of Instagram stories:
{analysis}

Generate an engaging HTML newsletter addressed to {recipient_name}. Include a catchy subject line, personalized greeting,
a summary of the highlights, and a friendly sign-off."""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("No OpenAI API key found. Using mock newsletter.")
        return MOCK_NEWSLETTER
    
    try:
        result = Runner.run_sync(newsletter_agent, prompt)
        return result.final_output
    except Exception as e:
        print(f"Error during newsletter generation: {e}")
        return MOCK_NEWSLETTER

#############################
# EMAIL SENDING SECTION
#############################

def send_newsletter_email(pdf_filename, newsletter_content):
    """Sends an email with the newsletter content, inline story images, and the PDF digest attached."""
    print("\n=== Sending Email ===\n")
    
    # Load email credentials from environment variables
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    recipient_email = os.getenv("RECEIVER_EMAIL")
    if not sender_email or not sender_password or not recipient_email:
        print("Error: Email credentials missing in .env file")
        return False

    # Create the root message as 'related' to include inline images
    msg = MIMEMultipart("related")
    # Try to extract subject line from newsletter_content; else use default subject
    subject_line = "Your Instagram Digest for " + datetime.now().strftime("%Y-%m-%d")
    for line in newsletter_content.splitlines():
        if line.startswith("Subject:"):
            subject_line = line.replace("Subject:", "").strip()
            break
    msg["Subject"] = subject_line
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # Create an 'alternative' part for plain text and HTML versions
    alternative = MIMEMultipart("alternative")
    msg.attach(alternative)
    plain_text = "This email contains HTML content with inline images. Please view it in an HTML-capable email client."
    alternative.attach(MIMEText(plain_text, "plain"))

    # Attach the HTML content
    if "<html>" in newsletter_content:
        alternative.attach(MIMEText(newsletter_content, "html"))
    else:
        alternative.attach(MIMEText(newsletter_content, "plain"))
    
    # Attach inline images from the IMAGE_FOLDER
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(".png"):
            filepath = os.path.join(IMAGE_FOLDER, filename)
            try:
                with open(filepath, "rb") as img_file:
                    img_data = img_file.read()
                img = MIMEImage(img_data)
                img.add_header("Content-ID", f"<{filename}>")
                img.add_header("Content-Disposition", "inline", filename=filename)
                msg.attach(img)
                print(f"Attached inline image: {filename}")
            except Exception as e:
                print(f"Error attaching {filename}: {e}")
    
    # Attach the PDF digest
    if pdf_filename and os.path.exists(pdf_filename):
        try:
            with open(pdf_filename, "rb") as f:
                pdf_data = f.read()
            part = EmailMessage()
            part.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=pdf_filename)
            msg.attach(part)
            print(f"Attached PDF digest: {pdf_filename}")
        except Exception as e:
            print(f"Error attaching PDF: {e}")
    
    # Send the email via SMTP_SSL
    try:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        print(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

#############################
# AGENT-TOOL WRAPPERS
#############################

@tool
def scrape_instagram_and_create_pdf(num_stories: int = 5) -> dict:
    """Agent tool to login to Instagram, scrape stories, and create a PDF digest.
       Returns a dictionary with 'screenshots' and 'pdf_filename'."""
    print("=== Starting scraping and PDF creation ===")
    cookies = login_instagram()
    if not cookies:
        print("Falling back to mock cookies.")
        cookies = [{'name': 'mock', 'value': 'mock'}]
    screenshots = screenshot_stories(cookies, num_stories)
    if not screenshots:
        print("No screenshots captured, falling back to mock screenshots.")
        screenshots = [os.path.join(IMAGE_FOLDER, f"mock_story_{i+1}.png") for i in range(num_stories)]
    pdf_filename = create_pdf(screenshots)
    return {"screenshots": screenshots, "pdf_filename": pdf_filename}

@tool
def generate_instagram_newsletter(screenshots: list, recipient_name: str = "Subscriber") -> str:
    """Agent tool to analyze screenshots and generate an HTML newsletter."""
    analysis = analyze_screenshot_content(screenshots)
    newsletter = generate_newsletter(analysis, recipient_name)
    return newsletter

@tool
def send_newsletter(pdf_filename: str, newsletter_content: str) -> bool:
    """Agent tool to send the newsletter email with the PDF digest and inline images."""
    return send_newsletter_email(pdf_filename, newsletter_content)

#############################
# ORCHESTRATION PIPELINE
#############################

def orchestrate_pipeline(num_stories: int = 5, recipient_name: str = "Subscriber"):
    print("\n====== Instagram Newsletter Pipeline ======\n")
    start_time = time.time()
    
    # Step 1: Scrape Instagram and create PDF digest
    scraper_agent = Agent(
        name="InstagramScraper",
        instructions="Execute the scrape_instagram_and_create_pdf tool to capture stories and create a PDF digest."
    )
    scrape_result = Runner.run_sync(scraper_agent, f"Run with num_stories={num_stories}")
    result_data = scrape_result.final_output if isinstance(scrape_result.final_output, dict) else {}
    screenshots = result_data.get("screenshots", [])
    pdf_filename = result_data.get("pdf_filename", None)
    print(f"Scraping and PDF creation completed. PDF: {pdf_filename}")
    
    # Step 2: Generate newsletter content
    newsletter_gen_agent = Agent(
        name="NewsletterGenerator",
        instructions="Use the provided screenshots to analyze and generate an HTML newsletter."
    )
    newsletter_result = Runner.run_sync(newsletter_gen_agent, f"Run with screenshots: {screenshots} and recipient: {recipient_name}")
    newsletter_content = newsletter_result.final_output if newsletter_result.final_output else MOCK_NEWSLETTER
    print("Newsletter generation completed.")
    
    # Step 3: Send the newsletter email
    email_agent = Agent(
        name="EmailSender",
        instructions="Send the newsletter email using the provided PDF and HTML content."
    )
    email_result = Runner.run_sync(email_agent, f"Run with pdf_filename: {pdf_filename} and newsletter_content: {newsletter_content}")
    email_status = email_result.final_output if email_result.final_output is not None else False
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n====== Pipeline Completed in {duration:.2f} seconds ======")
    return email_status

#############################
# MAIN EXECUTION
#############################

if __name__ == "__main__":
    # You can adjust parameters or load them from command line arguments as needed
    num_stories = 5
    recipient = os.getenv("RECEIVER_EMAIL", "Subscriber")
    orchestrate_pipeline(num_stories=num_stories, recipient_name=recipient)
