# DockerDeployer - Docker-based Local Development Environment

This guide provides complete instructions for deploying DockerDeployer locally using Docker containers with hot reloading support for development.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Git
- At least 4GB of available RAM
- Ports 3000, 6379, and 8000 available on your machine

### One-Click Deployment

```bash
# Clone the repository (if not already done)
git clone https://github.com/christopherjohnmayor/DockerDeployer.git
cd DockerDeployer

# Run the deployment script
./scripts/deploy-dev.sh
```

That's it! The script will:
- Check Docker prerequisites
- Build optimized development containers
- Start all services with hot reloading
- Wait for services to be ready
- Display service URLs and status

## 📋 Manual Deployment

If you prefer to run commands manually:

### 1. Environment Setup

```bash
# Ensure .env.dev exists (it should be included in the repository)
ls -la .env.dev

# Create necessary directories
mkdir -p backend/data config_repo
```

### 2. Build and Start Services

```bash
# Build containers (first time or after Dockerfile changes)
docker-compose build

# Start all services
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### 3. Verify Services

```bash
# Check service status
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

## 🏗️ Architecture

The containerized development environment includes:

### Services

1. **Frontend Container** (`dockerdeployer-frontend`)
   - React/TypeScript application with Vite
   - Hot reloading enabled
   - Port: 3000

2. **Backend Container** (`dockerdeployer-backend`)
   - FastAPI application with auto-reload
   - Docker socket access for container management
   - Port: 8000

3. **Redis Container** (`dockerdeployer-redis`)
   - Caching and session storage
   - Persistent data volume
   - Port: 6379

### Volumes

- `db_data`: SQLite database persistence
- `redis_data`: Redis data persistence
- `config_data`: Application configuration
- Source code volumes for hot reloading

### Networks

- `dockerdeployer-network`: Internal bridge network for service communication

## 🔧 Development Features

### Hot Reloading

Both frontend and backend support hot reloading:

- **Frontend**: Vite dev server with file watching
- **Backend**: Uvicorn with `--reload` flag
- **File Changes**: Automatically detected via volume mounts

### Service Communication

Services communicate using Docker network names:
- Frontend → Backend: `http://backend:8000`
- Backend → Redis: `redis://redis:6379`
- External access via localhost ports

### Environment Variables

Development-specific settings in `.env.dev`:
- Debug mode enabled
- CORS configured for container communication
- Development database settings
- Test email provider

## 📱 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | FastAPI endpoints |
| API Docs | http://localhost:8000/redoc | Interactive API documentation |
| Redis | localhost:6379 | Redis cache (internal) |

## 🛠️ Common Commands

### Container Management

```bash
# View running containers
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Development Workflow

```bash
# Rebuild after dependency changes
docker-compose build --no-cache
docker-compose up -d

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Run tests in containers
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Install new dependencies
docker-compose exec backend pip install package_name
docker-compose exec frontend npm install package_name
```

### Database Management

```bash
# Access SQLite database
docker-compose exec backend sqlite3 /app/data/dockerdeployer.db

# Backup database
docker cp dockerdeployer-backend:/app/data/dockerdeployer.db ./backup.db

# View database files
docker-compose exec backend ls -la /app/data/
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :3000
   lsof -i :8000
   lsof -i :6379
   ```

2. **Docker Socket Permission Issues**
   ```bash
   # Ensure Docker socket is accessible
   ls -la /var/run/docker.sock
   ```

3. **Container Build Failures**
   ```bash
   # Clean build with no cache
   docker-compose build --no-cache --pull
   ```

4. **Volume Mount Issues**
   ```bash
   # Check volume mounts
   docker-compose exec backend ls -la /app
   docker-compose exec frontend ls -la /app
   ```

### Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:3000
docker-compose exec redis redis-cli ping
```

### Performance Optimization

For better performance on macOS/Windows:

1. **Allocate more resources to Docker Desktop**
   - Memory: 4GB minimum, 8GB recommended
   - CPU: 2+ cores

2. **Use Docker Desktop's file sharing optimization**
   - Enable "Use gRPC FUSE for file sharing"
   - Add project directory to file sharing

## 🔒 Security Notes

- Development containers run with elevated privileges for Docker socket access
- This is intentional for Docker management functionality
- Do not use these configurations in production
- Production deployment uses different security models

## 📚 Next Steps

After successful deployment:

1. **Configure LLM Integration**: Update settings via the web interface
2. **Set up Email Provider**: Configure SendGrid or Gmail in settings
3. **Explore Templates**: Try deploying LEMP, MEAN, or WordPress stacks
4. **Run Tests**: Execute the comprehensive test suite
5. **Development**: Start building new features with hot reloading

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs -f`
3. Ensure all prerequisites are met
4. Try a clean rebuild: `docker-compose down -v && docker-compose build --no-cache && docker-compose up -d`

For additional help, refer to the main project documentation or create an issue in the repository.
