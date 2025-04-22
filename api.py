import asyncio
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from mcp_agent.core.fastagent import FastAgent

# Load API key from .env file
dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path)

app = FastAPI()

# Create a dedicated workspace directory for the agent
WORKSPACE_DIR = Path(__file__).parent / "agent_workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# Define FastAgent configuration
AGENT_INSTRUCTIONS = """You are a Deployment Pilot and GitHub operations assistant that uses the GitHub CLI (gh) to manage repositories.

You have access to a wide range of docker tools and all command line tools, you will be expected to take repositories from github and deploy them to a docker container, while also using docker compose if needed.

IMPORTANT: You have a dedicated workspace directory at {workspace_dir}. Always use this directory for:
- Cloning repositories
- Storing configuration files
- Building Docker images
- Running applications

For GitHub operations, use the `gh` command-line tool instead of direct API calls.
The GitHub CLI should already be authenticated.

The target repository is: https://github.com/deploypilotorg/example-repo

Examples of useful commands:

1. To create a branch:
   ```
   # Clone the repository into your workspace
   cd {workspace_dir}
   gh repo clone deploypilotorg/example-repo
   cd example-repo
   
   # Create a branch
   git checkout -b feature/new-feature
   
   # Push to GitHub
   git push -u origin feature/new-feature
   ```

2. To create a pull request:
   ```
   cd {workspace_dir}/example-repo
   gh pr create --title "Your PR title" --body "Description of changes"
   ```

3. To check repository details:
   ```
   cd {workspace_dir}
   gh repo view deploypilotorg/example-repo
   ```

4. To build and run with Docker:
   ```
   cd {workspace_dir}/example-repo
   docker build -t example-app .
   docker run -p 8080:8080 example-app
   ```

5. To deploy with Docker Compose:
   ```
   cd {workspace_dir}/example-repo
   docker-compose up -d
   ```

Always check the current status and provide clear explanations of what commands you're using.
"""

class Query(BaseModel):
    text: str

# Store active tasks
active_tasks = {}

# Function to run agent
async def run_agent(query_id: str, query_text: str):
    # Verify API key is loaded from .env
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        active_tasks[query_id] = {"status": "error", "result": "Error: ANTHROPIC_API_KEY not found in .env file"}
        return
    
    # Set it as environment variable for fast-agent
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    try:
        # Create a new agent
        fast = FastAgent("GitHub CLI Agent")
        
        # Format the instructions with the workspace directory
        formatted_instructions = AGENT_INSTRUCTIONS.format(workspace_dir=WORKSPACE_DIR)
        
        @fast.agent(
            instruction=formatted_instructions,
            servers=["cli"],
            model="sonnet"
        )
        async def agent_query():
            async with fast.run() as agent:
                result = await agent(query_text)
                return result
        
        result = await agent_query()
        active_tasks[query_id] = {"status": "completed", "result": result}
    except Exception as e:
        active_tasks[query_id] = {"status": "error", "result": f"Error: {str(e)}"}

@app.post("/query")
async def create_query(query: Query, background_tasks: BackgroundTasks):
    query_id = f"query_{len(active_tasks) + 1}"
    active_tasks[query_id] = {"status": "processing", "result": None}
    
    # Run the agent in a background task
    background_tasks.add_task(run_agent, query_id, query.text)
    
    return {"query_id": query_id, "status": "processing"}

@app.get("/result/{query_id}")
async def get_result(query_id: str):
    if query_id not in active_tasks:
        return {"status": "not_found"}
    
    return active_tasks[query_id]

@app.get("/workspace_info")
async def workspace_info():
    """Return information about the agent workspace"""
    workspace_exists = os.path.exists(WORKSPACE_DIR)
    
    # Generate a nested file tree instead of a flat list
    def get_directory_tree(path, rel_path=""):
        result = []
        items = sorted(os.listdir(path))
        
        for item in items:
            item_path = os.path.join(path, item)
            if rel_path:
                item_rel_path = os.path.join(rel_path, item)
            else:
                item_rel_path = item
                
            if os.path.isdir(item_path):
                children = get_directory_tree(item_path, item_rel_path)
                result.append({
                    "name": item,
                    "path": item_rel_path,
                    "type": "directory",
                    "children": children
                })
            else:
                result.append({
                    "name": item,
                    "path": item_rel_path,
                    "type": "file"
                })
        
        return result
    
    # Get file tree if workspace exists
    file_tree = []
    if workspace_exists:
        file_tree = get_directory_tree(WORKSPACE_DIR)
    
    return {
        "workspace_path": str(WORKSPACE_DIR),
        "workspace_exists": workspace_exists,
        "files": file_tree
    }

@app.post("/reset_workspace")
async def reset_workspace():
    """Reset the agent workspace by deleting and recreating it"""
    try:
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        return {"status": "success", "message": f"Workspace at {WORKSPACE_DIR} has been reset"}
    except Exception as e:
        return {"status": "error", "message": f"Error resetting workspace: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 