import streamlit as st
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import nest_asyncio
from mcp_agent.core.fastagent import FastAgent

# Apply nest_asyncio to allow asyncio to work with Streamlit
nest_asyncio.apply()

# Load API key from .env file in the current directory
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path)

# Page configuration
st.set_page_config(
    page_title="GitHub CLI Assistant",
    page_icon="🐙",
    layout="wide"
)

st.title("GitHub CLI Assistant")
st.markdown("""
This app allows you to interact with GitHub via the GitHub CLI (gh) tool.
Ask questions about creating branches, managing pull requests, or checking repository information.
""")

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
async def run_github_agent(query):
    # Verify API key is loaded from .env
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not found in .env file"
    
    # Set it as environment variable for fast-agent
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    async with fast.run() as agent:
        result = await agent(query)
        return result

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about GitHub operations..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        # Run the agent
        response = asyncio.run(run_github_agent(prompt))
        
        # Update the placeholder with the response
        message_placeholder.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This application uses the GitHub CLI to perform operations on GitHub repositories.
    
    ### Examples you can ask:
    - "Create a new branch called 'feature/improved-ui'"
    - "Create a pull request for my current branch"
    - "Show me the details of the repository"
    
    ### Target Repository:
    https://github.com/deploypilotorg/example-repo
    """) 