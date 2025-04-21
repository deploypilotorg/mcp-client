# MCP Client

HTTP-based client for connecting to the MCP server and interacting with GitHub repositories.

## Features

- Connect to MCP servers over HTTP
- Streamlit web interface for easy interaction
- Command-line interface for terminal usage
- GitHub repository analysis and exploration

## Installation

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key in the `.env` file:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Streamlit Web Interface

1. Run the Streamlit application:
   ```
   cd streamlit
   streamlit run app.py
   ```

2. Open your browser at `http://localhost:8501`
3. Enter the MCP server URL (e.g., `http://localhost:8000`) and click "Connect to Server"
4. Enter a GitHub repository URL and click "Analyze Repository"
5. Start chatting with the assistant about the repository

### Command-Line Interface

1. Run the client with the server URL:
   ```
   python client.py http://localhost:8000
   ```

2. Type your queries and press Enter
3. Type 'quit' to exit

## Examples

Here are some example queries you can try:

- "List all files in the repository"
- "What does the main file do?"
- "Execute 'git log' to see the commit history"
- "Explain the purpose of this repository" 