from agents import Agent, Runner
from dotenv import load_dotenv
import os
from insta_digest import InstaDigestAgent

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Example 1: Basic Agent Usage
print("\n--- Example 1: Basic Agent Usage ---")
agent = Agent(name="Assistant", instructions="You are a helpful assistant")
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Example 2: Instagram Digest Pipeline
print("\n--- Example 2: Instagram Digest Pipeline ---")
print("To run the Instagram Digest Pipeline, you would need to:")
print("1. Install additional dependencies: playwright, pillow, fpdf")
print("2. Set up required environment variables in .env file:")
print("   - INSTAGRAM_USER: Your Instagram username")
print("   - INSTAGRAM_PASS: Your Instagram password")
print("   - EMAIL_USER: Your email address")
print("   - EMAIL_PASS: Your email password or app password")
print("   - RECEIVER_EMAIL: Email address to send the digest to")
print("\nExample code to run the pipeline:")
print("""
# Uncomment to run the Instagram Digest Pipeline
# Ensure you have set all required environment variables first

# insta_agent = InstaDigestAgent()
# result = insta_agent.run_pipeline(os.getenv("RECEIVER_EMAIL"))
# print(f"Pipeline Result: {result}")
""")