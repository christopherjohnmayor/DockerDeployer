# DockerDeployer Backend

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI (REST API)
- **Docker Management:** Docker SDK for Python
- **Async Tasks:** Celery (for background jobs, optional in Phase 1)
- **Database:** SQLite (for minimal state/config tracking, can be swapped later)
- **Version Control:** GitPython (for config versioning)
- **LLM Integration:** HTTP clients for local LLMs and LiteLLM API

## Directory Structure

- `app/` — FastAPI application code
- `docker/` — Docker management logic (compose, build, deploy, logs)
- `nlp/` — NLP-to-action translation logic
- `llm/` — LLM integration clients
- `templates/` — Built-in stack templates (YAML/JSON)
- `version_control/` — Git integration for config files

## Initial API Endpoints

| Method | Endpoint                  | Description                                      |
|--------|---------------------------|--------------------------------------------------|
| POST   | /nlp/parse                | Parse NL command, return action plan             |
| POST   | /deploy                   | Deploy containers from action/config              |
| GET    | /containers               | List running containers and status               |
| POST   | /containers/{id}/action   | Perform action (restart, stop, logs, etc.)       |
| GET    | /templates                | List available stack templates                   |
| POST   | /templates/deploy         | Deploy from a template                           |
| GET    | /logs/{container_id}      | Get logs for a container                         |
| GET    | /status                   | System and resource status                       |
| GET    | /history                  | Deployment/config change history                 |

## Development

- Install dependencies: `pip install -r requirements.txt`
- Run API server: `uvicorn app.main:app --reload`
- Docker Compose for local development (planned)

## Notes

- All configuration files are version-controlled.
- LLM and NLP modules are decoupled for future extensibility.
- API-first design for easy frontend and CLI integration.