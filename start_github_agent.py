import subprocess
import sys
import time
import webbrowser
import os
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger('start_script')

def setup_workspace():
    """Create and set up the agent workspace directory"""
    workspace_dir = Path(__file__).parent / "agent_workspace"
    
    # Create if it doesn't exist
    if not os.path.exists(workspace_dir):
        logger.info(f"Creating agent workspace directory at {workspace_dir}")
        os.makedirs(workspace_dir, exist_ok=True)
    else:
        logger.info(f"Agent workspace already exists at {workspace_dir}")
    
    # Set appropriate permissions
    try:
        # Make sure directories are writable by the agent
        os.chmod(workspace_dir, 0o755)
        logger.info(f"Set permissions on workspace directory")
    except Exception as e:
        logger.warning(f"Could not set permissions on workspace: {str(e)}")
    
    return workspace_dir

def main():
    logger.info("Starting GitHub CLI Assistant...")
    
    # Setup workspace for the agent
    workspace_dir = setup_workspace()
    logger.info(f"Agent workspace ready at: {workspace_dir}")
    
    # Start the FastAPI server in a separate process
    logger.info("Starting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "github_agent_server.py"],
        # Don't capture output to see logs in console
        stdout=None,
        stderr=None
    )
    
    time.sleep(3)  # Give the server time to start
    
    # Check if server started successfully
    if api_process.poll() is not None:
        logger.error("API server failed to start")
        return
    
    logger.info("API server started successfully")
    
    # Start the Flask app
    logger.info("Starting Flask app...")
    flask_process = subprocess.Popen(
        [sys.executable, "flask_github_agent.py"],
        # Don't capture output to see logs in console
        stdout=None,
        stderr=None
    )
    
    # Wait a moment
    time.sleep(2)
    
    # Open browser with the correct port
    webbrowser.open("http://127.0.0.1:8080")
    
    try:
        # Keep both processes running
        while True:
            # Check if processes are still running
            if api_process.poll() is not None:
                logger.error("API server stopped unexpectedly")
                flask_process.terminate()
                break
                
            if flask_process.poll() is not None:
                logger.error("Flask app stopped unexpectedly")
                api_process.terminate()
                break
                
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # Terminate the processes
        api_process.terminate()
        flask_process.terminate()
        
        # Wait for the processes to terminate
        api_process.wait()
        flask_process.wait()
        
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main() 