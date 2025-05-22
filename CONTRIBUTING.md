# Contributing to DockerDeployer

Thank you for your interest in contributing to DockerDeployer! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## 🤝 Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/DockerDeployer.git
   cd DockerDeployer
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🔄 Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Workflow Steps

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code standards
   - Add tests for new functionality
   - Update documentation

3. **Test Locally**
   ```bash
   # Backend tests
   cd backend && pytest --cov=. --cov-report=term

   # Frontend tests
   cd frontend && npm test

   # Linting
   cd backend && black . && flake8 .
   cd frontend && npm run lint
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Code Standards

### Backend (Python)

- **Style**: Follow PEP 8, enforced by `black` and `flake8`
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Error Handling**: Use appropriate exception handling with meaningful error messages

**Example:**
```python
def create_container(
    name: str, 
    image: str, 
    ports: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Create a new Docker container.
    
    Args:
        name: Container name
        image: Docker image to use
        ports: Port mappings (optional)
        
    Returns:
        Container creation result with status and details
        
    Raises:
        DockerException: If container creation fails
    """
    # Implementation here
```

### Frontend (TypeScript/React)

- **Style**: Use Prettier and ESLint configurations
- **Components**: Use functional components with TypeScript
- **Documentation**: Use JSDoc for all components and complex functions
- **Testing**: Write unit tests for all components

**Example:**
```typescript
/**
 * ContainerCard component displays container information in a card format.
 * 
 * @param props - Component props
 * @param props.container - Container data object
 * @param props.onAction - Callback for container actions
 * @returns JSX element representing the container card
 */
interface ContainerCardProps {
  container: Container;
  onAction: (action: string, containerId: string) => void;
}

const ContainerCard: React.FC<ContainerCardProps> = ({ container, onAction }) => {
  // Component implementation
};
```

## 🧪 Testing Requirements

### Coverage Requirements
- **Minimum**: 80% code coverage for both backend and frontend
- **New Features**: Must include comprehensive tests
- **Bug Fixes**: Must include regression tests

### Backend Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_docker_manager.py
```

### Frontend Testing
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- ContainerDetail.test.tsx
```

## 📚 Documentation Guidelines

### API Documentation
- Use comprehensive OpenAPI/Swagger documentation
- Include request/response examples
- Document all error codes and responses
- Provide clear parameter descriptions

### Component Documentation
- Use JSDoc for all React components
- Include usage examples
- Document all props and their types
- Explain component behavior and state

### Code Comments
- Write clear, concise comments for complex logic
- Avoid obvious comments
- Use TODO comments for future improvements
- Include references to related issues or PRs

## 🔍 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Add changelog entry** if applicable
4. **Rebase on latest main** to avoid merge conflicts

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
```

### Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: Verify tests cover new functionality
4. **Documentation**: Ensure documentation is updated

## 🐛 Issue Reporting

### Bug Reports

Use the bug report template and include:
- **Environment details** (OS, Docker version, etc.)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Screenshots or logs** if applicable
- **Minimal reproduction case**

### Feature Requests

Use the feature request template and include:
- **Problem description** you're trying to solve
- **Proposed solution** with implementation details
- **Alternative solutions** considered
- **Additional context** or examples

## 🏷️ Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add container metrics endpoint
fix(frontend): resolve container status display issue
docs(readme): update installation instructions
```

## 🎯 Development Tips

### Debugging
- Use Docker logs for container debugging
- Enable debug mode in FastAPI for detailed error messages
- Use React DevTools for frontend debugging

### Performance
- Profile API endpoints for performance bottlenecks
- Optimize Docker builds with multi-stage builds
- Use React.memo for expensive component renders

### Security
- Never commit secrets or API keys
- Use environment variables for configuration
- Follow security best practices for Docker containers

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Discord/Slack**: For real-time communication (if available)

Thank you for contributing to DockerDeployer! 🚀
