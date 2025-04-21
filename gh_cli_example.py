import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from mcp_agent.core.fastagent import FastAgent

# Load API key from .env file in the current directory
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path)

# Create the application
fast = FastAgent("GitHub CLI Agent")

@fast.agent(
    instruction="""You are a GitHub operations assistant that uses the GitHub CLI (gh) to manage repositories.
    
    For GitHub operations, use the `gh` command-line tool instead of direct API calls.
    The GitHub CLI should already be authenticated.
    
    The target repository is: https://github.com/deploypilotorg/example-repo
    
    Examples of useful gh commands:
    
    1. To create a branch:
       ```
       # Clone the repository first
       gh repo clone deploypilotorg/example-repo
       cd example-repo
       
       # Create a branch
       git checkout -b feature/new-feature
       
       # Push to GitHub
       git push -u origin feature/new-feature
       ```
    
    2. To create a pull request:
       ```
       gh pr create --title "Your PR title" --body "Description of changes"
       ```
    
    3. To check repository details:
       ```
       gh repo view deploypilotorg/example-repo
       ```
    
    Always check the current status and provide clear explanations of what commands you're using.
    """,
    servers=["cli"],
    model="sonnet"
)
async def main():
    # Verify API key is loaded from .env
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in .env file")
        return
    
    print(f"API key loaded successfully: {api_key[:8]}...{api_key[-4:]}")
    
    # Also set it as environment variable for fast-agent
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    async with fast.run() as agent:
        # For interactive mode
        print("GitHub CLI Agent - Interactive Mode")
        print("You can ask about:")
        print("- Creating branches using the GitHub CLI")
        print("- Creating and managing pull requests")
        print("- Checking repository information")
        print("\nType 'exit' to end the session")
        await agent.interactive()
        
        # For specific tasks (uncomment to use)
        # result = await agent("Create a new branch called 'feature/improved-ui' in the deploypilotorg/example-repo repository")
        # print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 