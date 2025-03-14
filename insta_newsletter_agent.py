import os
from dotenv import load_dotenv
from agents import Agent, Runner  # OpenAI Agent libraries
import agentops
from datetime import datetime
import sys

# Load environment variables
load_dotenv()

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY is not set in your .env file")
    print("Please add your OpenAI API key to your .env file:")
    print("OPENAI_API_KEY=your_openai_api_key")
    # For testing, we'll continue with mock responses
    print("\nContinuing with mock AI responses for demonstration purposes...\n")

# Initialize AgentOps for tracking (only if key exists)
agentops_key = os.getenv("AGENTOPS_API_KEY")
if agentops_key:
    agentops.init(agentops_key)
else:
    print("AgentOps API key not found, skipping trace export")

# Create our newsletter agent with specific instructions
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
    """Use the AI agent to analyze the content of Instagram story screenshots.
    
    In a real implementation, we would use image analysis or OCR here to extract
    text from the screenshots and provide it to the agent.
    """
    print("\n--- Analyzing Instagram Stories Content ---")
    
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
    print("\n--- Generating Instagram Newsletter ---")
    
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

# Example usage in the Instagram newsletter pipeline:
def process_stories_with_ai(screenshot_paths, recipient_email):
    """Process Instagram stories with AI to create and send a newsletter."""
    print("\n=== Processing Instagram Stories with AI ===\n")
    
    # Step 1: Analyze the content of the screenshots
    analysis = analyze_screenshot_content(screenshot_paths)
    print(f"\nContent Analysis:\n{analysis}\n")
    
    # Step 2: Generate a newsletter based on the analysis
    newsletter = generate_newsletter(analysis, recipient_email.split('@')[0])
    print(f"\nGenerated Newsletter:\n{newsletter}\n")
    
    # Step 3: Extract the subject line for the email
    subject_line = extract_subject_line(newsletter)
    print(f"\nEmail Subject: {subject_line}")
    
    # The newsletter content and subject line can now be used in the email sending function
    return {
        "subject": subject_line,
        "content": newsletter,
        "analysis": analysis
    }

# Integration with the full Instagram digest pipeline
def integrate_with_digest_pipeline(screenshots_paths, pdf_file, recipient_email):
    """Integrate the AI newsletter generation with the Instagram digest pipeline."""
    print("\n=== Running Full Instagram Newsletter Pipeline ===\n")
    
    # Step 1: Process stories with AI to get newsletter content
    newsletter_data = process_stories_with_ai(screenshots_paths, recipient_email)
    
    # Step 2: In a real implementation, you would modify your email sending function
    # to include the AI-generated newsletter content along with the PDF attachment
    print(f"\nReady to send email to {recipient_email}:")
    print(f"- Subject: {newsletter_data['subject']}")
    print(f"- Content: AI-generated newsletter")
    print(f"- Attachment: {pdf_file}")
    
    return newsletter_data

# Example usage to test the functionality:
if __name__ == "__main__":
    # For testing purposes, we'll use mock screenshot paths
    mock_screenshots = [
        "story_1.png",
        "story_2.png",
        "story_3.png"
    ]
    
    # Process with AI
    newsletter_data = process_stories_with_ai(mock_screenshots, "test@example.com")
    
    # Print the result
    print("\n=== Newsletter Ready to Send ===\n")
    print(f"Subject: {newsletter_data['subject']}")
    print(f"Content Sample: {newsletter_data['content'][:300]}...")
    
    # Show how this would integrate with the full pipeline
    print("\n--- To integrate with your full pipeline ---")
    print("Add this code to your main Instagram digest pipeline:")
    print("""
    # After capturing screenshots and creating PDF:
    from insta_newsletter_agent import integrate_with_digest_pipeline
    
    # This adds the AI newsletter generation to your pipeline
    newsletter_data = integrate_with_digest_pipeline(screenshots, pdf_file, receiver_email)
    
    # Now you can use newsletter_data in your email sending function
    """)
