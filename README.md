# GitHub Operations Agent

A simple agent that helps you perform GitHub operations using natural language.

## Prerequisites

- Python 3.8+
- An Anthropic API key
- `mcp-agent` Python package

## Setup

1. Clone this repository:
```
git clone <repository-url>
cd <repository-directory>
```

2. Install dependencies:
```
pip install mcp-agent python-dotenv
```

3. Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage

Run the GitHub operations agent:
```
python github_api_example.py
```

When running, you can:
- Create branches
- Create/edit files
- Create pull requests
- Check repository information

Example commands:
- "Create a new branch called feature/improved-ui"
- "Create a file called README.md with basic project information"
- "Create a pull request from feature/improved-ui to main"

## Troubleshooting

If the agent gets stuck during initialization:
- Verify your Anthropic API key is correct
- Check your internet connection
- Ensure the MCP server is accessible from your network

## License

MIT 