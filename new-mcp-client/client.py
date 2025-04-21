"""
HTTP-based MCP client that connects to the MCP server.
"""
import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class MCPHttpClient:
    """HTTP-based MCP client that connects to the MCP server"""
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.anthropic = Anthropic()
        self.session = None
        self.tools = []
    
    async def connect(self):
        """Connect to the MCP server"""
        self.session = aiohttp.ClientSession()
        
        try:
            # Initialize connection
            async with self.session.get(f"{self.server_url}/initialize") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to initialize connection: {error_text}")
                
                data = await response.json()
                if data.get('type') != 'initialize_result':
                    raise Exception(f"Unexpected response type: {data.get('type')}")
            
            # List available tools
            async with self.session.get(f"{self.server_url}/list_tools") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to list tools: {error_text}")
                
                data = await response.json()
                if data.get('type') != 'list_tools_result':
                    raise Exception(f"Unexpected response type: {data.get('type')}")
                
                self.tools = data.get('tools', [])
                return self.tools
                
        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            raise e
    
    async def close(self):
        """Close the connection to the MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        try:
            # Prepare the request
            request_data = {
                "name": tool_name,
                "arguments": arguments
            }
            
            # Execute the tool
            async with self.session.post(
                f"{self.server_url}/execute_tool", 
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to execute tool: {error_text}")
                
                data = await response.json()
                if data.get('type') == 'error':
                    raise Exception(data.get('message', 'Unknown error'))
                
                return data
                
        except Exception as e:
            raise e
    
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        available_tools = [
            {
                "name": tool.get("name"),
                "description": tool.get("description"),
                "input_schema": tool.get("inputSchema")
            } for tool in self.tools
        ]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=messages,
            tools=available_tools
        )

        tool_results = []
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self.call_tool(tool_name, tool_args)
                tool_result = result.get('content', 'No content in response')
                tool_results.append({"call": tool_name, "result": tool_result})
                
                final_text.append(f"[Called tool {tool_name}]")

                # Add tool result as a user message
                messages.append({
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": content.id,
                            "name": tool_name,
                            "input": tool_args
                        }
                    ]
                })
                
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": tool_result
                        }
                    ]
                })

                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=messages,
                )
                
                for content_item in response.content:
                    if content_item.type == 'text':
                        final_text.append(content_item.text)

        return "\n\n".join(final_text)

async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        server_url = "http://localhost:8000"
    else:
        server_url = sys.argv[1]
    
    client = MCPHttpClient(server_url=server_url)
    
    try:
        await client.connect()
        print(f"Connected to MCP server at {server_url}")
        print(f"Available tools: {[tool.get('name') for tool in client.tools]}")
        
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
                
            response = await client.process_query(query)
            print("\n" + response)
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main()) 