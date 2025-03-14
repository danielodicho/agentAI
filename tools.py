# tools.py
from typing_extensions import TypedDict, NotRequired, Any
from agents import function_tool, RunContextWrapper
import os

###############################################################################
# 1) Example: Login Tool
###############################################################################
@function_tool
def login_instagram(
    ctx: RunContextWrapper[Any],
    username: str,
    password: str,
    headless: bool = True
) -> list[dict]:
    """
    Logs into Instagram using Playwright and returns cookies.

    Args:
        username: Instagram username.
        password: Instagram password.
        headless: Whether to run the browser in headless mode.

    Returns:
        A list of cookies (dict objects) for the session.
    """
    # -- Replace with your real login code --
    print(f"[login_instagram] Logging in as {username} (headless={headless})...")
    
    # ... Actually launch Playwright, do the login, etc. ...
    cookies = [
        {"name": "sessionid", "value": "FAKE_SESSION", "domain": ".instagram.com"},
        # ... other cookies ...
    ]
    return cookies


###############################################################################
# 2) Example: Extract Stories Tool
###############################################################################
@function_tool
def extract_instagram_story(
    ctx: RunContextWrapper[Any],
    cookies: list[dict],
    username: str,
    num_stories: int = 1
) -> list[str]:
    """
    Extracts a given number of Instagram stories for a specific username.

    Args:
        cookies: A list of cookies from a logged-in session.
        username: The Instagram username to extract stories from.
        num_stories: How many stories to capture.

    Returns:
        A list of file paths (screenshots of stories).
    """
    print(f"[extract_instagram_story] Extracting {num_stories} stories for {username}...")
    # -- Replace with your real story extraction code --
    # For demonstration, just fake it:
    return [f"{username}_story_{i+1}.png" for i in range(num_stories)]


###############################################################################
# 3) Example: Analyze Stories Tool
###############################################################################
@function_tool
def analyze_stories_with_account_info(
    ctx: RunContextWrapper[Any],
    image_paths: list[str]
) -> str:
    """
    Analyzes the given story screenshots and returns a JSON string with details.

    Args:
        image_paths: A list of story screenshot file paths.

    Returns:
        JSON string describing analysis (e.g. classification, text, etc.).
    """
    print(f"[analyze_stories_with_account_info] Analyzing: {image_paths}")
    # ... Real OpenAI analysis code here ...
    # Just returning a mock JSON:
    return (
        '{'
        '"stories":[{"filename":"' + image_paths[0] + '","analysis":"This is a story."}],'
        '"overall_themes":["fun","lifestyle"]'
        '}'
    )


###############################################################################
# 4) Example: Generate Newsletter Tool
###############################################################################
@function_tool
def generate_enhanced_newsletter(
    ctx: RunContextWrapper[Any],
    analysis: str,
    recipient_name: str = "Subscriber"
) -> str:
    """
    Generates an HTML newsletter based on the analysis JSON.

    Args:
        analysis: The JSON string from the story analysis.
        recipient_name: The name used in the greeting of the newsletter.

    Returns:
        A string containing HTML content.
    """
    print(f"[generate_enhanced_newsletter] Generating newsletter for {recipient_name}...")
    # In real life, you'd parse `analysis` JSON and build the HTML
    html = f"<html><body><h1>Hello, {recipient_name}</h1><p>Analysis: {analysis}</p></body></html>"
    return html
