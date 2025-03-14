import agentops
from agentops import track_agent
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
from playwright.sync_api import sync_playwright
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# Set up logging for agent tracking
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")

# Initialize AgentOps and OpenAI client
agentops.init(AGENTOPS_API_KEY, default_tags=["insta_digest"])
openai_client = OpenAI(api_key=OPENAI_API_KEY)

@track_agent(name="insta_engineer")
class InstaDigestAgent:
    def login_instagram(self):
        """Automates Instagram login and returns session cookies."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://instagram.com/accounts/login")
            page.fill('input[name="username"]', os.getenv('INSTAGRAM_USER'))
            page.fill('input[name="password"]', os.getenv('INSTAGRAM_PASS'))
            page.click("button[type='submit']")
            page.wait_for_selector("xpath=//div[contains(text(),'Home')]")
            cookies = page.context.cookies()
            browser.close()
            return cookies

    def screenshot_stories(self, cookies, num_stories=5):
        """Navigates to Instagram stories, captures screenshots, and returns a list of file paths."""
        screenshots = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto("https://instagram.com")
            # Click the stories button; adjust xpath as needed
            page.click("xpath=//button[contains(@aria-label,'Stories')]")
            for i in range(num_stories):
                page.wait_for_timeout(2000)  # wait 2 seconds for the story to load
                screenshot_path = f"story_{i}.png"
                page.screenshot(path=screenshot_path)
                screenshots.append(screenshot_path)
                page.keyboard.press('ArrowRight')
            browser.close()
        return screenshots

    def create_pdf(self, screenshots):
        """Compiles screenshot images into a PDF digest."""
        pdf = FPDF()
        for image in screenshots:
            pdf.add_page()
            pdf.image(image, x=10, y=10, w=190)  # adjust size as necessary
        pdf_filename = "daily_digest.pdf"
        pdf.output(pdf_filename)
        return pdf_filename

    def send_email(self, pdf_filename, receiver_email):
        """Sends the PDF digest via email using SMTP."""
        email_user = os.getenv('EMAIL_USER')
        email_pass = os.getenv('EMAIL_PASS')
        msg = EmailMessage()
        msg["From"] = email_user
        msg["To"] = receiver_email
        msg["Subject"] = "Instagram Stories Daily Digest"
        msg.set_content("Your daily digest is attached.")
        with open(pdf_filename, "rb") as f:
            msg.add_attachment(
                f.read(), maintype="application", subtype="pdf", filename=pdf_filename
            )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return "Email Sent Successfully"

    def run_pipeline(self, receiver_email):
        """Orchestrates the entire Instagram digest pipeline."""
        cookies = self.login_instagram()
        screenshots = self.screenshot_stories(cookies)
        pdf_file = self.create_pdf(screenshots)
        status = self.send_email(pdf_file, receiver_email)
        return status
