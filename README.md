# Agent Implementation

A simple agent implementation using OpenAI, AgentOps, and python-dotenv.

## Setup

1. Clone the repository
2. Set up the virtual environment:
   ```
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # On Windows
   source venv/bin/activate     # On macOS/Linux
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys (see `.env.example` for reference)
5. Run the agent:
   ```
   python main.py
   ```

## Project Structure

- `main.py`: Main agent implementation using OpenAI, AgentOps, and python-dotenv
- `requirements.txt`: Project dependencies
- `.env.example`: Template for environment variables
- `.gitignore`: Specifies files that Git should ignore

## Features

- Uses OpenAI API for generating responses
- Integrates AgentOps for monitoring and tracing agent behavior
- Loads environment variables from a .env file using python-dotenv
