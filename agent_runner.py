# agent_runner.py
import asyncio
import json
from agents import Agent, Runner, FunctionTool
from tools import (
    login_instagram, 
    extract_instagram_story, 
    analyze_stories_with_account_info, 
    generate_enhanced_newsletter
)

# Create the Agent
newsletter_agent = Agent(
    name="Instagram Newsletter Agent",
    instructions=(
        "You can call the provided tools to log in to Instagram, extract stories, "
        "analyze them, and generate an HTML newsletter. "
        "Return the final HTML or any relevant output to the user."
    ),
    tools=[
        login_instagram,                # function_tool-wrapped
        extract_instagram_story,        # function_tool-wrapped
        analyze_stories_with_account_info,
        generate_enhanced_newsletter
    ],
)

async def main():
    # Example user instruction
    user_input = (
        "Please log in to Instagram with username='test_user' and password='secret', "
        "extract 2 stories from user='friend123', analyze them, and create a newsletter for 'John Doe'."
    )

    # Run the agent
    result = await Runner.run(newsletter_agent, input=user_input)
    
    print("\n=== Agent’s Final Output ===")
    print(result.final_output)
    
    # (Optional) Inspect how the agent sees each tool
    print("\n=== Tools Info ===")
    for tool in newsletter_agent.tools:
        if isinstance(tool, FunctionTool):
            print(f"Tool Name: {tool.name}")
            print(f"Tool Description: {tool.description}")
            print("Tool JSON Schema:", json.dumps(tool.params_json_schema, indent=2))
            print()

if __name__ == "__main__":
    asyncio.run(main())
