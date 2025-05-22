# DockerDeployer

<p align="center">
  <img src="docs/images/logo.png" alt="DockerDeployer Logo" width="200" height="200">
</p>

DockerDeployer is an AI-powered tool that simplifies Docker deployment and management through natural language interaction. It enables users to create, manage, deploy, and maintain containerized web services using plain English commands. The system generates configuration files, handles deployment, and provides monitoring capabilities, supporting both self-hosting and multiple LLM providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![API Docs](https://img.shields.io/badge/API-Documentation-green)](https://github.com/yourusername/DockerDeployer/wiki/API-Documentation)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-80%25-brightgreen)](https://github.com/yourusername/DockerDeployer/actions)

---

## 🚀 Features

- **Natural Language Interface:** Accepts plain English commands for Docker tasks (create, deploy, manage containers)
- **Configuration Generation:** Auto-generates `docker-compose.yml` and `Dockerfile` with best practices and security
- **Deployment & Management:** Local deployment with proper networking, volumes, and security settings
- **Web Dashboard:** Modern UI for monitoring containers, logs, and resource usage
- **Template Library:** Deploy common stacks from a built-in template library
- **Version Control:** Tracks configuration changes and enables rollbacks
- **LLM Support:** Works with local LLMs and LiteLLM for natural language understanding
- **Authentication:** Secure JWT-based authentication with role-based access control

---

## 🛠️ Tech Stack

### Backend

- **Language:** Python 3.10+
- **Framework:** FastAPI (REST API)
- **Docker Management:** Docker SDK for Python
- **Database:** SQLite (for minimal state/config tracking)
- **Version Control:** GitPython (for config versioning)
- **LLM Integration:** HTTP clients for local LLMs and LiteLLM API
- **Authentication:** JWT with role-based access control

### Frontend

- **Framework:** React with TypeScript
- **UI Library:** Material-UI (MUI)
- **State Management:** React Context API
- **Networking:** Axios
- **Build Tool:** Vite
- **Testing:** Jest + React Testing Library

---

## 📂 Project Structure

```
DockerDeployer/
├── backend/           # API server and Docker management logic
│   ├── app/           # FastAPI application code
│   ├── docker/        # Docker management logic
│   ├── nlp/           # NLP-to-action translation logic
│   ├── llm/           # LLM integration clients
│   ├── templates/     # Built-in stack templates
│   └── version_control/ # Git integration for config files
├── frontend/          # Web UI dashboard (React)
│   ├── src/           # Source code
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/     # Page components
│   │   ├── contexts/  # React contexts
│   │   ├── hooks/     # Custom React hooks
│   │   └── api/       # API client code
├── templates/         # Built-in stack templates (YAML)
├── docs/              # Documentation
├── .github/           # GitHub Actions workflows
└── README.md          # Project overview (this file)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/DockerDeployer.git
   cd DockerDeployer
   ```

2. Set up the backend:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend server:

   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Start the frontend development server:

   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at http://localhost:5173

### Using Docker Compose (Alternative)

```bash
docker-compose up -d
```

---

## 📚 Documentation

### API Documentation

- **OpenAPI/Swagger**: Comprehensive API documentation available at `/docs` when running the backend
- **Interactive API Explorer**: Test endpoints directly from the browser interface
- **Authentication Guide**: JWT token-based authentication with role-based access control
- **Endpoint Reference**: Detailed documentation for all REST API endpoints

### Frontend Documentation

- **Component Library**: JSDoc-documented React components with usage examples
- **TypeScript Interfaces**: Fully typed components and API interactions
- **Testing Guide**: Unit and integration testing with Jest and React Testing Library
- **Styling Guide**: Material-UI theming and responsive design patterns

### Additional Resources

- [User Guide](https://github.com/yourusername/DockerDeployer/wiki/User-Guide)
- [Developer Guide](https://github.com/yourusername/DockerDeployer/wiki/Developer-Guide)
- [Template System](TEMPLATES.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## 🧪 Testing

### Running Tests Locally

**Backend Tests:**

```bash
cd backend
pytest --cov=. --cov-report=term --cov-report=html
```

**Frontend Tests:**

```bash
cd frontend
npm test
npm run test:coverage
```

### Test Coverage Requirements

- **Minimum Coverage**: 80% for both backend and frontend
- **Coverage Reports**: Generated automatically in CI/CD pipeline
- **Quality Gates**: Tests must pass before merging to main branch

### Continuous Integration

The project uses GitHub Actions for automated testing and deployment:

- **Test Workflow** (`.github/workflows/test.yml`):

  - Runs on every PR and push to main/develop
  - Backend: Python tests with pytest and coverage reporting
  - Frontend: Jest tests with coverage validation
  - Linting: Code quality checks with flake8, black, and ESLint

- **Build Workflow** (`.github/workflows/build.yml`):

  - Multi-architecture Docker builds (amd64, arm64)
  - Automated semantic versioning and releases
  - Docker image security scanning with Trivy
  - Artifact attestation and SBOM generation

- **Deploy Workflow** (`.github/workflows/deploy.yml`):
  - Automated deployment to staging/production environments
  - Health checks and rollback capabilities
  - Environment-specific configuration management

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

For questions or feedback, please open an issue or contact the maintainers.
