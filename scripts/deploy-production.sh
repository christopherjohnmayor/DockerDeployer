#!/bin/bash

# DockerDeployer Production Deployment Script
# This script automates the production deployment process with proper checks and validations

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if production environment file exists
    if [[ ! -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        error "Production environment file $ENV_FILE not found"
        error "Please copy .env.production.example to .env.production and configure it"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Validate environment configuration
validate_environment() {
    log "Validating environment configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Source the environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check critical environment variables
    local required_vars=(
        "ENVIRONMENT"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "DATABASE_URL"
        "DOMAIN"
        "EMAIL_PROVIDER"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check if using default/insecure values
    if [[ "$SECRET_KEY" == *"CHANGE_THIS"* ]] || [[ ${#SECRET_KEY} -lt 32 ]]; then
        error "SECRET_KEY must be changed from default and be at least 32 characters"
        exit 1
    fi
    
    if [[ "$JWT_SECRET_KEY" == *"CHANGE_THIS"* ]] || [[ ${#JWT_SECRET_KEY} -lt 32 ]]; then
        error "JWT_SECRET_KEY must be changed from default and be at least 32 characters"
        exit 1
    fi
    
    if [[ "$ENVIRONMENT" != "production" ]]; then
        error "ENVIRONMENT must be set to 'production'"
        exit 1
    fi
    
    success "Environment configuration validated"
}

# Run tests
run_tests() {
    log "Running test suite..."
    
    cd "$PROJECT_ROOT"
    
    # Backend tests
    log "Running backend tests..."
    cd backend
    if ! python -m pytest --cov=. --cov-fail-under=80 --quiet; then
        error "Backend tests failed"
        exit 1
    fi
    success "Backend tests passed (80%+ coverage)"
    
    # Frontend tests
    log "Running frontend tests..."
    cd ../frontend
    if ! npm test -- --coverage --watchAll=false --passWithNoTests; then
        warning "Frontend tests have failures - proceeding with caution"
        read -p "Continue with deployment despite test failures? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Deployment cancelled due to test failures"
            exit 1
        fi
    else
        success "Frontend tests passed"
    fi
    
    cd "$PROJECT_ROOT"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current environment
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/"
    fi
    
    # Backup database if it exists
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q postgres; then
        log "Backing up database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U dockerdeployer dockerdeployer > "$BACKUP_DIR/database.sql" || true
    fi
    
    # Backup volumes
    if docker volume ls | grep -q dockerdeployer; then
        log "Backing up Docker volumes..."
        docker run --rm -v dockerdeployer_db_data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar czf /backup/volumes.tar.gz -C /data . || true
    fi
    
    success "Backup created in $BACKUP_DIR"
}

# Build production images
build_images() {
    log "Building production images..."
    
    cd "$PROJECT_ROOT"
    
    # Build images with no cache for production
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    success "Production images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down || true
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Services deployed"
}

# Health checks
run_health_checks() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost:8000/health > /dev/null; then
            success "Backend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Backend health check failed after $max_attempts attempts"
            return 1
        fi
        
        log "Backend health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    # Check frontend
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost:3000/ > /dev/null; then
            success "Frontend health check passed"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Frontend health check failed after $max_attempts attempts"
            return 1
        fi
        
        log "Frontend health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    success "All health checks passed"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo
    log "Application URLs:"
    echo "  Frontend: https://${DOMAIN:-localhost}"
    echo "  Backend API: https://${DOMAIN:-localhost}/api"
    echo "  Health Check: https://${DOMAIN:-localhost}/health"
    echo
    
    log "Useful commands:"
    echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo
}

# Rollback function
rollback() {
    error "Deployment failed, initiating rollback..."
    
    cd "$PROJECT_ROOT"
    
    # Stop current deployment
    docker-compose -f "$COMPOSE_FILE" down || true
    
    # Restore from backup if available
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup..."
        
        # Restore environment file
        if [[ -f "$BACKUP_DIR/$ENV_FILE" ]]; then
            cp "$BACKUP_DIR/$ENV_FILE" .
        fi
        
        # Restore database
        if [[ -f "$BACKUP_DIR/database.sql" ]]; then
            log "Restoring database..."
            docker-compose -f "$COMPOSE_FILE" up -d postgres
            sleep 10
            docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U dockerdeployer -d dockerdeployer < "$BACKUP_DIR/database.sql" || true
        fi
    fi
    
    error "Rollback completed. Please check the system manually."
    exit 1
}

# Main deployment function
main() {
    log "Starting DockerDeployer Production Deployment"
    echo "=================================================="
    
    # Set trap for cleanup on error
    trap rollback ERR
    
    check_root
    check_prerequisites
    validate_environment
    run_tests
    create_backup
    build_images
    deploy_services
    run_health_checks
    show_status
    
    echo "=================================================="
    success "🚀 DockerDeployer Production Deployment Completed Successfully!"
    success "🌐 Application is now available at: https://${DOMAIN:-localhost}"
    echo
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
