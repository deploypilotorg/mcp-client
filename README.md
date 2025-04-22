# Containerized Agent API

This project provides a containerized API for running an AI agent that interacts with GitHub repositories through the GitHub CLI.

## Prerequisites

- Docker and Docker Compose installed on your system
- An Anthropic API key

## Setup

1. Create a `.env` file in the project root with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

2. Build and start the container:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at http://localhost:8000

## API Endpoints

- `POST /query`: Submit a query to the agent
- `GET /result/{query_id}`: Get the result of a query
- `GET /workspace_info`: Get information about the agent workspace
- `POST /reset_workspace`: Reset the agent workspace

## Security Benefits

- The agent workspace is fully containerized, isolating it from your host system
- All GitHub operations happen within the container
- Docker volume ensures data persistence while maintaining isolation

## Stopping the Service

```bash
docker-compose down
```

To completely remove the persistent workspace data:
```bash
docker-compose down -v
``` 