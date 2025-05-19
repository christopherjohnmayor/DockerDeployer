"""
Prompt templates for Docker operations using LLMs.
These templates are used to generate prompts for the LLM to understand and process
natural language commands related to Docker operations.
"""

from typing import Dict, List, Optional, Any

# Base system prompt that defines the LLM's role and capabilities
SYSTEM_PROMPT = """
You are DockerGPT, an AI assistant specialized in Docker container management.
Your task is to interpret natural language commands and convert them into structured
Docker operations. You should:

1. Understand the user's intent related to Docker operations
2. Extract relevant parameters and options
3. Determine the appropriate Docker command or API call
4. Return a structured JSON response with the parsed command

Focus only on Docker-related operations such as:
- Creating, starting, stopping, or removing containers
- Building or pulling images
- Managing networks and volumes
- Deploying stacks with docker-compose
- Inspecting container logs and status

If the user's request is ambiguous or lacks necessary information, identify what's missing
and include it in the 'missing_info' field of your response.

If the request is not related to Docker, indicate this in the 'is_docker_command' field.
"""

# Template for parsing a natural language command into a structured Docker operation
PARSE_COMMAND_TEMPLATE = """
{system_prompt}

Current Docker Context:
- Running Containers: {running_containers}
- Available Images: {available_images}
- Networks: {networks}
- Volumes: {volumes}

User Command: "{user_command}"

Analyze this command and respond with a JSON object containing:
1. "is_docker_command": boolean indicating if this is a Docker-related command
2. "command_type": one of ["container", "image", "network", "volume", "compose", "system", "unknown"]
3. "operation": the specific operation (e.g., "create", "start", "stop", "remove", "build", "pull")
4. "parameters": an object with all relevant parameters
5. "missing_info": any information needed but not provided in the command
6. "docker_command": the equivalent Docker CLI command (if applicable)
7. "explanation": a brief explanation of what this command will do

JSON Response:
"""

# Template for generating docker-compose.yml content
GENERATE_COMPOSE_TEMPLATE = """
{system_prompt}

The user wants to deploy a {stack_type} stack with the following requirements:
{requirements}

Additional context:
- Environment: {environment}
- Host OS: {host_os}
- Available ports: {available_ports}
- Data persistence needed: {persistence_needed}

Generate a valid docker-compose.yml file that meets these requirements.
Include appropriate environment variables, volumes, networks, and port mappings.
Add comments to explain key configuration choices.

docker-compose.yml:
"""

# Template for troubleshooting Docker issues
TROUBLESHOOT_TEMPLATE = """
{system_prompt}

The user is experiencing the following issue with Docker:
{issue_description}

Relevant context:
- Docker version: {docker_version}
- Host OS: {host_os}
- Container logs: {container_logs}
- Error message: {error_message}

Analyze this issue and provide:
1. A diagnosis of the likely cause
2. Step-by-step troubleshooting instructions
3. A potential solution
4. Preventative measures for the future

Troubleshooting Analysis:
"""

# Template for explaining Docker concepts
EXPLAIN_CONCEPT_TEMPLATE = """
{system_prompt}

The user wants to understand the following Docker concept:
{concept}

Provide a clear explanation that includes:
1. What it is
2. How it works
3. When and why to use it
4. Common pitfalls or best practices
5. A simple example demonstrating the concept

Explanation:
"""

def get_parse_command_prompt(
    user_command: str,
    running_containers: Optional[List[Dict[str, Any]]] = None,
    available_images: Optional[List[str]] = None,
    networks: Optional[List[str]] = None,
    volumes: Optional[List[str]] = None
) -> str:
    """
    Generate a prompt for parsing a natural language Docker command.
    
    Args:
        user_command: The natural language command from the user
        running_containers: List of currently running containers
        available_images: List of available Docker images
        networks: List of Docker networks
        volumes: List of Docker volumes
        
    Returns:
        A formatted prompt string
    """
    context = {
        "system_prompt": SYSTEM_PROMPT,
        "user_command": user_command,
        "running_containers": "None" if not running_containers else 
                             ", ".join([f"{c.get('name', 'unnamed')} ({c.get('id', 'unknown')[:12]})" 
                                       for c in (running_containers or [])]),
        "available_images": "None" if not available_images else ", ".join(available_images or []),
        "networks": "None" if not networks else ", ".join(networks or []),
        "volumes": "None" if not volumes else ", ".join(volumes or [])
    }
    
    return PARSE_COMMAND_TEMPLATE.format(**context)

def get_generate_compose_prompt(
    stack_type: str,
    requirements: str,
    environment: str = "development",
    host_os: str = "Linux",
    available_ports: List[int] = None,
    persistence_needed: bool = True
) -> str:
    """
    Generate a prompt for creating a docker-compose.yml file.
    
    Args:
        stack_type: Type of stack (e.g., "LEMP", "MEAN", "WordPress")
        requirements: Specific requirements for the stack
        environment: Deployment environment
        host_os: Host operating system
        available_ports: List of available ports
        persistence_needed: Whether data persistence is needed
        
    Returns:
        A formatted prompt string
    """
    if available_ports is None:
        available_ports = [80, 443, 3306, 5432, 27017, 6379, 8080]
        
    context = {
        "system_prompt": SYSTEM_PROMPT,
        "stack_type": stack_type,
        "requirements": requirements,
        "environment": environment,
        "host_os": host_os,
        "available_ports": ", ".join(map(str, available_ports)),
        "persistence_needed": "Yes" if persistence_needed else "No"
    }
    
    return GENERATE_COMPOSE_TEMPLATE.format(**context)

def get_troubleshoot_prompt(
    issue_description: str,
    docker_version: str = "latest",
    host_os: str = "Linux",
    container_logs: str = "",
    error_message: str = ""
) -> str:
    """
    Generate a prompt for troubleshooting Docker issues.
    
    Args:
        issue_description: Description of the issue
        docker_version: Docker version
        host_os: Host operating system
        container_logs: Relevant container logs
        error_message: Error message if any
        
    Returns:
        A formatted prompt string
    """
    context = {
        "system_prompt": SYSTEM_PROMPT,
        "issue_description": issue_description,
        "docker_version": docker_version,
        "host_os": host_os,
        "container_logs": container_logs or "Not provided",
        "error_message": error_message or "Not provided"
    }
    
    return TROUBLESHOOT_TEMPLATE.format(**context)

def get_explain_concept_prompt(concept: str) -> str:
    """
    Generate a prompt for explaining Docker concepts.
    
    Args:
        concept: The Docker concept to explain
        
    Returns:
        A formatted prompt string
    """
    context = {
        "system_prompt": SYSTEM_PROMPT,
        "concept": concept
    }
    
    return EXPLAIN_CONCEPT_TEMPLATE.format(**context)
