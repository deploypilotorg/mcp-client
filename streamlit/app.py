"""
Streamlit app for the MCP client that connects to the HTTP server.
"""

import os
import json
import asyncio
import re
import streamlit as st
import aiohttp
from anthropic import Anthropic

# Get environment variables
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEFAULT_MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# Initialize session state if needed
if "server_url" not in st.session_state:
    st.session_state.server_url = ""
if "is_connected" not in st.session_state:
    st.session_state.is_connected = False
if "tools" not in st.session_state:
    st.session_state.tools = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "repo_path" not in st.session_state:
    st.session_state.repo_path = None

# Set up anthropic client
if ANTHROPIC_API_KEY:
    st.session_state.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    st.session_state.anthropic_client = None


# Create the async session
@st.cache_resource
def get_aiohttp_session():
    """Get or create an aiohttp client session"""
    return aiohttp.ClientSession()


async def connect_to_server(server_url):
    """Connect to the MCP server and get the list of tools"""
    try:
        async with get_aiohttp_session() as session:
            async with session.get(f"{server_url}/list_tools") as response:
                if response.status == 200:
                    data = await response.json()
                    st.session_state.tools = data.get("tools", [])
                    st.session_state.is_connected = True
                    st.session_state.server_url = server_url
                    return True, "Connected successfully"
                else:
                    error_text = await response.text()
                    return False, f"Failed to connect: {error_text}"
    except (aiohttp.ClientError, ValueError) as e:
        return False, f"Error connecting to server: {str(e)}"


async def execute_tool(tool_name, arguments):
    """Execute a tool on the MCP server"""
    if not st.session_state.is_connected:
        return False, "Not connected to any server"

    try:
        async with get_aiohttp_session() as session:
            payload = {"name": tool_name, "arguments": arguments}

            async with session.post(
                f"{st.session_state.server_url}/execute_tool", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("type") == "error":
                        return False, data.get("message", "Unknown error")
                    return True, data.get("content", "")
                else:
                    error_text = await response.text()
                    return False, f"Failed to execute tool: {error_text}"
    except (aiohttp.ClientError, ValueError) as e:
        return False, f"Error executing tool: {str(e)}"


async def process_query(query):
    """Process a user query using Claude to determine which tool to use"""
    if not st.session_state.anthropic_client:
        return "Please set your Anthropic API key in the .env file."

    # Format the chat history and tools for Claude
    formatted_history = []
    for msg in st.session_state.chat_history:
        role = "user" if msg["is_user"] else "assistant"
        formatted_history.append({"role": role, "content": msg["content"]})

    # Format available tools
    tool_descriptions = []
    for tool in st.session_state.tools:
        tool_descriptions.append(
            f"Tool: {tool['name']}\nDescription: {tool['description']}\nSchema: {json.dumps(tool['inputSchema'])}"
        )

    tools_text = "\n\n".join(tool_descriptions)

    # Create the system prompt
    system_prompt = f"""You are an AI assistant that helps users interact with a server that has tools.
Available tools:
{tools_text}

When the user asks a question or makes a request, determine which tool would be appropriate to use.
Then, construct the arguments to pass to that tool based on the user's request.
Your response should be formatted as JSON with 'tool_name' and 'arguments' fields.

If the user's request doesn't clearly map to a tool, provide a helpful response directly.
If the user is asking about the repository, use the github_repo tool with appropriate action.
"""

    try:
        # Send the query to Claude
        message = await st.session_state.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            system=system_prompt,
            messages=[*formatted_history, {"role": "user", "content": query}],
            max_tokens=1024,
            temperature=0,
        )

        claude_response = message.content[0].text

        # Try to parse the response as JSON
        try:
            # Check if the response is wrapped in ```json and ``` markers
            if "```json" in claude_response:
                json_part = claude_response.split("```json")[1].split("```")[0].strip()
                tool_request = json.loads(json_part)
            else:
                # Try to find a JSON object in the response
                json_match = re.search(r"\{[^}]+\}", claude_response)
                if json_match:
                    tool_request = json.loads(json_match.group(0))
                else:
                    # No JSON found, just return the response
                    return claude_response

            tool_name = tool_request.get("tool_name")
            arguments = tool_request.get("arguments", {})

            if tool_name:
                # Execute the tool
                success, tool_result = await execute_tool(tool_name, arguments)

                if success:
                    # Save repository path if it was set during tool execution
                    if (
                        tool_name == "github_repo"
                        and arguments.get("action") == "clone"
                    ):
                        result_lines = tool_result.split("\n")
                        for line in result_lines:
                            if "to " in line and "repo_path" not in st.session_state:
                                path = line.split("to ")[-1].strip()
                                st.session_state.repo_path = path

                    return tool_result
                else:
                    return f"Error executing tool: {tool_result}"
            else:
                return claude_response
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, just return the original response
            return f"{claude_response}\n\nNote: I tried to execute a tool but encountered an error: {str(e)}"
    except Exception as e:
        return f"Error processing query: {str(e)}"


# Set up the Streamlit interface
st.title("MCP Client")

# Sidebar for connection settings
with st.sidebar:
    st.header("Server Connection")

    server_url_input = st.text_input(
        "Server URL",
        value=(
            DEFAULT_MCP_SERVER_URL
            if not st.session_state.server_url
            else st.session_state.server_url
        ),
        placeholder="http://localhost:8000",
    )

    connect_button = st.button("Connect to Server")

    if connect_button:
        with st.spinner("Connecting to server..."):
            success, message = asyncio.run(connect_to_server(server_url_input))
            st.write(message)

    if st.session_state.is_connected:
        st.success(f"Connected to {st.session_state.server_url}")

        # Display available tools
        st.subheader("Available Tools")
        for tool in st.session_state.tools:
            st.write(f"- {tool['name']}")

    # GitHub repository section
    st.header("GitHub Repository")
    repo_url = st.text_input(
        "Repository URL", placeholder="https://github.com/user/repo"
    )

    if st.button("Clone Repository"):
        if st.session_state.is_connected:
            with st.spinner("Cloning repository..."):
                success, result = asyncio.run(
                    execute_tool(
                        "github_repo", {"action": "clone", "repo_url": repo_url}
                    )
                )
                st.write(result)

                # Extract repository path from the result
                if success:
                    result_lines = result.split("\n")
                    for line in result_lines:
                        if "to " in line:
                            path = line.split("to ")[-1].strip()
                            st.session_state.repo_path = path
        else:
            st.error("Please connect to a server first")

    # Code Analysis section (new!)
    if st.session_state.repo_path:
        st.header("Code Analysis")
        analysis_action = st.selectbox(
            "Analysis Type",
            options=[
                "analyze_languages",
                "find_todos",
                "get_dependencies",
                "search_code",
                "analyze_complexity",
            ],
        )

        # Search code input
        search_query = ""
        if analysis_action == "search_code":
            search_query = st.text_input(
                "Search Query", placeholder="Enter search pattern"
            )

        # File complexity analysis input
        file_path = ""
        if analysis_action == "analyze_complexity":
            file_path = st.text_input("File Path", placeholder="path/to/file.py")

        if st.button("Analyze Code"):
            if st.session_state.is_connected:
                with st.spinner("Analyzing code..."):
                    args = {
                        "action": analysis_action,
                        "repo_path": st.session_state.repo_path,
                    }

                    if analysis_action == "search_code" and search_query:
                        args["query"] = search_query

                    if analysis_action == "analyze_complexity" and file_path:
                        args["file_path"] = file_path

                    success, result = asyncio.run(execute_tool("analyze_code", args))
                    st.code(result)
            else:
                st.error("Please connect to a server first")

        # Auto-deployment section (new!)
        st.header("Auto-Deployment")
        deploy_action = st.selectbox(
            "Deployment Action",
            options=[
                "detect_deployment_type",
                "prepare_deployment",
                "start_deployment",
                "get_status",
                "abort_deployment",
            ],
        )

        # Deployment configuration (if needed)
        if deploy_action == "prepare_deployment":
            deploy_type = st.selectbox(
                "Deployment Type", options=["static", "docker", "heroku", "custom"]
            )

            # Configuration fields based on type
            deploy_config = {"type": deploy_type}

            if deploy_type == "static":
                deploy_config["build_dir"] = st.text_input(
                    "Build Directory", value="build"
                )
                deploy_config["build_command"] = st.text_input(
                    "Build Command", value="npm run build"
                )
                deploy_config["deploy_target"] = st.text_input(
                    "Deploy Target", value="/var/www/html"
                )
                deploy_config["create_if_missing"] = st.checkbox(
                    "Create if missing", value=True
                )

            elif deploy_type == "docker":
                deploy_config["dockerfile_path"] = st.text_input(
                    "Dockerfile Path", value="Dockerfile"
                )
                deploy_config["image_name"] = st.text_input("Image Name", value="myapp")
                deploy_config["container_name"] = st.text_input(
                    "Container Name", value="myapp-container"
                )
                ports = st.text_input("Ports (comma separated)", value="8080:80")
                deploy_config["ports"] = [p.strip() for p in ports.split(",")]

            elif deploy_type == "heroku":
                deploy_config["app_name"] = st.text_input("App Name")
                deploy_config["create_if_missing"] = st.checkbox(
                    "Create if missing", value=True
                )

            elif deploy_type == "custom":
                deploy_config["script_path"] = st.text_input(
                    "Script Path", value="deploy.sh"
                )
                args = st.text_input("Arguments (comma separated)")
                if args:
                    deploy_config["args"] = [a.strip() for a in args.split(",")]

        if st.button("Execute Deployment Action"):
            if st.session_state.is_connected:
                with st.spinner(f"Executing {deploy_action}..."):
                    args = {
                        "action": deploy_action,
                        "repo_path": st.session_state.repo_path,
                    }

                    if deploy_action == "prepare_deployment":
                        args["deploy_config"] = deploy_config

                    success, result = asyncio.run(execute_tool("autodeploy", args))
                    st.code(result)
            else:
                st.error("Please connect to a server first")

# Main content area
st.header("Chat")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message("user" if message["is_user"] else "assistant"):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Enter your message"):
    # Add user message to chat history
    st.session_state.chat_history.append({"is_user": True, "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.write(prompt)

    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if st.session_state.is_connected:
                response = asyncio.run(process_query(prompt))
                st.write(response)

                # Add assistant message to chat history
                st.session_state.chat_history.append(
                    {"is_user": False, "content": response}
                )
            else:
                st.error("Please connect to a server first")
