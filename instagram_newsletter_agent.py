from __future__ import annotations as _annotations

import asyncio
import os
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from dotenv import load_dotenv

# Import the Agents SDK using the correct structure
from agents import (
    Agent,
    ItemHelpers,
    MessageOutputItem,
    RunContextWrapper,
    Runner,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
    function_tool,
    handoff,
    trace,
)
# If this import is not available, we can modify the implementation as needed
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Import our existing Instagram newsletter code
import agentops
from instagram_story_newsletter import (
    extract_instagram_story, 
    process_instagram_stories,
    analyze_instagram_stories_with_openai,
    generate_instagram_newsletter_with_openai,
    save_newsletter_to_file,
    get_sample_images
)

# Load environment variables
load_dotenv()

# Initialize AgentOps
agentops.init(
    api_key=os.getenv("AGENTOPS_API_KEY"),
)

### CONTEXT

class InstagramNewsletterContext(BaseModel):
    """Context for the Instagram newsletter agent"""
    instagram_user: str | None = None
    instagram_password: str | None = None
    use_sample_images: bool = False
    stories: List[dict] = []
    story_analyses: dict | None = None
    newsletter_content: str | None = None
    newsletter_file: str | None = None
    newsletter_subject: str | None = None
    highlight_top_stories: bool = True
    group_by_account_type: bool = True

### TOOLS

@function_tool
async def get_instagram_stories(context: RunContextWrapper[InstagramNewsletterContext]) -> str:
    """Extract Instagram stories from the user's account or use sample images"""
    if context.context.use_sample_images:
        print("Using sample images for Instagram stories...")
        sample_images = get_sample_images()
        context.context.stories = [{'path': img_path} for img_path in sample_images]
        return f"Found {len(sample_images)} sample images to process"
    else:
        if not context.context.instagram_user or not context.context.instagram_password:
            return "Error: Instagram credentials not provided. Please set username and password or use sample images."
        
        print(f"Extracting Instagram stories for user {context.context.instagram_user}...")
        stories = extract_instagram_story(context.context.instagram_user, context.context.instagram_password)
        context.context.stories = stories
        return f"Extracted {len(stories)} Instagram stories"

@function_tool
async def analyze_stories_content(context: RunContextWrapper[InstagramNewsletterContext]) -> str:
    """Analyze Instagram stories content using OpenAI for enhanced details"""
    if not context.context.stories or len(context.context.stories) == 0:
        return "Error: No stories available to analyze. Please extract stories first."
    
    print("Analyzing Instagram stories with enhanced account info...")
    story_analyses = analyze_instagram_stories_with_openai(context.context.stories)
    context.context.story_analyses = story_analyses
    
    return "Stories analyzed successfully. Found classifications for account types and content."

@function_tool
async def generate_newsletter(context: RunContextWrapper[InstagramNewsletterContext]) -> str:
    """Generate the Instagram newsletter based on the analyzed stories"""
    if not context.context.story_analyses:
        return "Error: No story analyses available. Please analyze stories first."
    
    print("Generating enhanced Instagram newsletter...")
    newsletter_content = generate_instagram_newsletter_with_openai(
        context.context.stories, 
        context.context.story_analyses,
        highlight_top_stories=context.context.highlight_top_stories
    )
    context.context.newsletter_content = newsletter_content
    
    # Extract subject line from newsletter content
    if "Subject:" in newsletter_content:
        subject_line = newsletter_content.split("Subject:")[1].split("\n")[0].strip()
        context.context.newsletter_subject = subject_line
    
    return "Newsletter generated successfully."

@function_tool
async def save_newsletter(context: RunContextWrapper[InstagramNewsletterContext]) -> str:
    """Save the generated newsletter to an HTML file"""
    if not context.context.newsletter_content:
        return "Error: No newsletter content available. Please generate newsletter first."
    
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"instagram_newsletter_{current_date}.html"
    
    print("Saving newsletter to file...")
    saved_file = save_newsletter_to_file(
        context.context.newsletter_content,
        filename=filename,
        screenshots=[story['path'] for story in context.context.stories] if context.context.stories else None,
        include_images=True,
        stories_info=context.context.story_analyses
    )
    
    context.context.newsletter_file = saved_file
    return f"Newsletter saved to {saved_file}"

@function_tool
async def set_newsletter_preferences(
    context: RunContextWrapper[InstagramNewsletterContext], 
    highlight_top_stories: bool = True,
    group_by_account_type: bool = True
) -> str:
    """Set preferences for the newsletter generation"""
    context.context.highlight_top_stories = highlight_top_stories
    context.context.group_by_account_type = group_by_account_type
    
    preferences = []
    if highlight_top_stories:
        preferences.append("Highlighting top stories")
    if group_by_account_type:
        preferences.append("Grouping stories by account type (friends first, then influencers)")
    
    return f"Newsletter preferences set: {', '.join(preferences)}"

### AGENTS

instagram_newsletter_agent = Agent[InstagramNewsletterContext](
    name="Instagram Newsletter Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an Instagram Newsletter Generator Agent that helps users create beautiful,
    organized newsletters from their Instagram stories.
    
    Follow this process to generate newsletters:
    1. First determine if the user wants to use sample images or extract stories from their Instagram account.
    2. If using real Instagram, ask for credentials if not already provided.
    3. Extract Instagram stories using the appropriate tool.
    4. Analyze the stories content with OpenAI to get enhanced details.
    5. Generate the newsletter based on the analysis.
    6. Save the newsletter to an HTML file.
    7. Provide the user with a summary of what was created.
    
    Newsletter features:
    - You can highlight the top 3 most relevant stories in the main newsletter.
    - You organize stories in the gallery section by account type (friends first, then influencers).
    - You provide a full gallery of all stories at the bottom.
    
    You can also adjust newsletter preferences using the set_newsletter_preferences tool.
    Always be helpful and guide the user through the process.
    """,
    tools=[
        get_instagram_stories,
        analyze_stories_content,
        generate_newsletter,
        save_newsletter,
        set_newsletter_preferences
    ],
)

### RUN

async def main():
    print("=== Instagram Newsletter Agent ===\n")
    
    # Set default context
    context = InstagramNewsletterContext(
        instagram_user=os.getenv("INSTAGRAM_USER"),
        instagram_password=os.getenv("INSTAGRAM_PASS"),
        use_sample_images=False,  # Default to real Instagram stories
        highlight_top_stories=True,
        group_by_account_type=True
    )
    
    # Check for command line arguments
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--samples":
        print("Sample images detected - running in sample mode")
        context.use_sample_images = True
    
    current_agent = instagram_newsletter_agent
    input_items: list[TResponseInputItem] = []
    
    # Generate a conversation ID for tracing
    conversation_id = uuid.uuid4().hex[:16]
    
    # First message to start the agent
    if context.use_sample_images:
        start_message = "I'd like to generate a newsletter using the sample Instagram stories."
    else:
        start_message = "I'd like to generate a newsletter from my Instagram stories."
    
    with trace("Instagram Newsletter Generation", group_id=conversation_id):
        input_items.append({"content": start_message, "role": "user"})
        result = await Runner.run(current_agent, input_items, context=context)
        
        # Process and display the first response
        for new_item in result.new_items:
            if isinstance(new_item, MessageOutputItem):
                print(f"Agent: {ItemHelpers.text_message_output(new_item)}\n")
            elif isinstance(new_item, ToolCallItem):
                print(f"Agent is using tool: {new_item.name}")
            elif isinstance(new_item, ToolCallOutputItem):
                print(f"Tool result: {new_item.output}\n")
        
        input_items = result.to_input_list()
        
        # Continue the conversation
        while True:
            user_input = input("Your response (or 'q' to quit): ")
            if user_input.lower() in ['q', 'quit', 'exit']:
                break
                
            with trace("Instagram Newsletter Generation", group_id=conversation_id):
                input_items.append({"content": user_input, "role": "user"})
                result = await Runner.run(current_agent, input_items, context=context)
                
                for new_item in result.new_items:
                    if isinstance(new_item, MessageOutputItem):
                        print(f"Agent: {ItemHelpers.text_message_output(new_item)}\n")
                    elif isinstance(new_item, ToolCallItem):
                        print(f"Agent is using tool: {new_item.name}")
                    elif isinstance(new_item, ToolCallOutputItem):
                        print(f"Tool result: {new_item.output}\n")
                
                input_items = result.to_input_list()
    
    print("\nNewsletter generation session complete.")
    if context.newsletter_file:
        print(f"Your newsletter is available at: {context.newsletter_file}")
        print("You can open it in any web browser to view it.")

if __name__ == "__main__":
    asyncio.run(main())
