#!/bin/bash

# DockerDeployer Development Deployment Script
# This script sets up the complete containerized development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p backend/data
    mkdir -p config_repo
    print_success "Directories created"
}

# Function to copy environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    if [ ! -f .env.dev ]; then
        print_error ".env.dev file not found. Please ensure it exists."
        exit 1
    fi
    print_success "Environment configuration ready"
}

# Function to build and start containers
start_containers() {
    print_status "Building and starting Docker containers..."
    print_status "This may take a few minutes on first run..."
    
    # Build containers
    docker-compose build --no-cache
    
    # Start containers
    docker-compose up -d
    
    print_success "Containers started successfully"
}

# Function to wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout 60 bash -c 'until docker-compose exec redis redis-cli ping; do sleep 2; done'
    print_success "Redis is ready"
    
    # Wait for Backend
    print_status "Waiting for Backend API..."
    timeout 120 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 5; done'
    print_success "Backend API is ready"
    
    # Wait for Frontend
    print_status "Waiting for Frontend..."
    timeout 120 bash -c 'until curl -f http://localhost:3000 > /dev/null 2>&1; do sleep 5; done'
    print_success "Frontend is ready"
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_status "Service URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/redoc"
    echo "  Redis: localhost:6379"
    
    echo ""
    print_status "Useful Commands:"
    echo "  View logs: docker-compose logs -f [service_name]"
    echo "  Stop services: docker-compose down"
    echo "  Restart services: docker-compose restart"
    echo "  Rebuild services: docker-compose build --no-cache && docker-compose up -d"
}

# Main execution
main() {
    echo "=================================================="
    echo "  DockerDeployer Development Environment Setup  "
    echo "=================================================="
    echo ""
    
    check_docker
    check_docker_compose
    create_directories
    setup_environment
    start_containers
    wait_for_services
    show_status
    
    echo ""
    print_success "Development environment is ready!"
    print_status "You can now access the application at http://localhost:3000"
}

# Run main function
main "$@"
