# DockerDeployer API Documentation

This document provides comprehensive documentation for the DockerDeployer REST API. For interactive documentation, visit `/docs` when running the backend server.

## 📋 Table of Contents

- [Authentication](#authentication)
- [Base URL](#base-url)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
- [Examples](#examples)

## 🔐 Authentication

DockerDeployer uses JWT (JSON Web Token) authentication with role-based access control.

### Login Process

1. **Obtain Token**
   ```http
   POST /auth/login
   Content-Type: application/json

   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

2. **Use Token in Requests**
   ```http
   Authorization: Bearer <your_jwt_token>
   ```

### User Roles

- **User**: Basic container management operations
- **Admin**: Full system access including settings and user management

## 🌐 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## 📊 Response Format

### Success Response
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2023-12-01T10:00:00Z"
}
```

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request |
| 401  | Unauthorized |
| 403  | Forbidden |
| 404  | Not Found |
| 422  | Unprocessable Entity |
| 500  | Internal Server Error |
| 503  | Service Unavailable |

### Common Error Scenarios

- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: Insufficient permissions for the operation
- **422 Unprocessable Entity**: Invalid request data or NLP parsing failure
- **503 Service Unavailable**: Docker service or LLM service unavailable

## 🛠️ Endpoints

### Authentication Endpoints

#### POST /auth/login
Authenticate user and obtain JWT tokens.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "string"
}
```

### Natural Language Processing

#### POST /nlp/parse
Parse natural language command into action plan.

**Request:**
```json
{
  "command": "Deploy a WordPress stack with MySQL 8.0"
}
```

**Response:**
```json
{
  "action_plan": {
    "action": "deploy",
    "template": "wordpress",
    "parameters": {
      "mysql_version": "8.0"
    }
  }
}
```

**Supported Commands:**
- "Deploy a WordPress stack"
- "Stop all running containers"
- "Create a LEMP stack with PHP 8.1"
- "Show container logs for nginx"
- "List all containers"

### Container Management

#### GET /containers
List all Docker containers.

**Response:**
```json
[
  {
    "id": "abc123def456",
    "name": "nginx-web",
    "status": "running",
    "image": ["nginx:latest"],
    "ports": {
      "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]
    },
    "labels": {"app": "web"}
  }
]
```

#### POST /containers/{container_id}/action
Perform action on specific container.

**Path Parameters:**
- `container_id`: Container ID or name

**Request:**
```json
{
  "action": "start|stop|restart"
}
```

**Response:**
```json
{
  "container_id": "abc123def456",
  "action": "start",
  "result": {
    "status": "success",
    "message": "Container started successfully"
  }
}
```

#### GET /logs/{container_id}
Get container logs.

**Path Parameters:**
- `container_id`: Container ID or name

**Response:**
```json
{
  "container_id": "abc123def456",
  "logs": "2023-05-01 12:00:00 Server started\n2023-05-01 12:01:00 Request received"
}
```

### Template Management

#### GET /templates
List available stack templates.

**Response:**
```json
[
  {
    "name": "wordpress",
    "description": "WordPress with MySQL",
    "version": "1.0",
    "services": ["wordpress", "mysql"]
  }
]
```

#### POST /templates/deploy
Deploy a template.

**Request:**
```json
{
  "template_name": "wordpress",
  "variables": {
    "mysql_password": "secure_password"
  }
}
```

**Response:**
```json
{
  "template": "wordpress",
  "status": "deployed",
  "services": ["wordpress", "mysql"]
}
```

### System Information

#### GET /status
Get system status and metrics.

**Response:**
```json
{
  "cpu": "25%",
  "memory": "1024MB",
  "containers": 5,
  "docker_version": "20.10.17"
}
```

#### GET /history
Get deployment history.

**Response:**
```json
[
  {
    "commit": "abc123",
    "author": "John Doe",
    "message": "Deploy WordPress stack",
    "timestamp": "2023-12-01T10:00:00Z"
  }
]
```

## 💡 Examples

### Complete Workflow Example

1. **Login**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
   ```

2. **Parse Natural Language Command**
   ```bash
   curl -X POST http://localhost:8000/nlp/parse \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"command": "Deploy a WordPress stack"}'
   ```

3. **List Containers**
   ```bash
   curl -X GET http://localhost:8000/containers \
     -H "Authorization: Bearer <token>"
   ```

4. **Start Container**
   ```bash
   curl -X POST http://localhost:8000/containers/nginx-web/action \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"action": "start"}'
   ```

### JavaScript/TypeScript Example

```typescript
import axios from 'axios';

// Configure axios with base URL and auth interceptor
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Parse natural language command
async function parseCommand(command: string) {
  try {
    const response = await api.post('/nlp/parse', { command });
    return response.data.action_plan;
  } catch (error) {
    console.error('Failed to parse command:', error);
    throw error;
  }
}

// List containers
async function listContainers() {
  try {
    const response = await api.get('/containers');
    return response.data;
  } catch (error) {
    console.error('Failed to list containers:', error);
    throw error;
  }
}
```

### Python Example

```python
import requests
import json

class DockerDeployerClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.login(username, password)
    
    def login(self, username: str, password: str):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def parse_command(self, command: str):
        response = self.session.post(
            f"{self.base_url}/nlp/parse",
            json={"command": command}
        )
        response.raise_for_status()
        return response.json()["action_plan"]
    
    def list_containers(self):
        response = self.session.get(f"{self.base_url}/containers")
        response.raise_for_status()
        return response.json()

# Usage
client = DockerDeployerClient("http://localhost:8000", "admin", "password")
containers = client.list_containers()
action_plan = client.parse_command("Deploy a WordPress stack")
```

## 🔗 Related Documentation

- [OpenAPI/Swagger Documentation](http://localhost:8000/docs) - Interactive API explorer
- [User Guide](../README.md) - General usage instructions
- [Template System](../TEMPLATES.md) - Template creation and usage
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines
