import os
from dotenv import load_dotenv
import openai
import agentops

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize AgentOps
agentops.init(api_key=os.getenv("AGENTOPS_API_KEY"))

# Create a new trace for tracking the agent session
trace = agentops.trace()

def get_completion(prompt):
    """Get a completion from OpenAI API with agentops tracking"""
    with trace.span("openai_completion") as span:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            completion = response.choices[0].message.content
            span.add_attribute("success", True)
            return completion
        except Exception as e:
            span.add_attribute("success", False)
            span.add_attribute("error", str(e))
            raise e

def main():
    print("Simple Agent Demo using OpenAI, AgentOps, and python-dotenv")
    
    user_input = input("Ask a question: ")
    with trace.span("user_query") as span:
        span.add_attribute("query", user_input)
        response = get_completion(user_input)
        print("Agent response:", response)

if __name__ == "__main__":
    main()