#!/bin/bash

# DockerDeployer Production Rollback Script
# This script provides emergency rollback capabilities for production deployments

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
BACKUP_DIR="backups"

# Logging functions
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

# List available backups
list_backups() {
    log "Available backups:"
    echo
    
    if [[ ! -d "$PROJECT_ROOT/$BACKUP_DIR" ]]; then
        error "No backup directory found"
        exit 1
    fi
    
    local backups=($(ls -1t "$PROJECT_ROOT/$BACKUP_DIR" 2>/dev/null || true))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        error "No backups found"
        exit 1
    fi
    
    for i in "${!backups[@]}"; do
        echo "  $((i+1)). ${backups[$i]}"
    done
    
    echo
}

# Select backup
select_backup() {
    list_backups
    
    local backups=($(ls -1t "$PROJECT_ROOT/$BACKUP_DIR" 2>/dev/null))
    
    echo -n "Select backup to restore (1-${#backups[@]}) or 'latest' for most recent: "
    read -r selection
    
    if [[ "$selection" == "latest" ]]; then
        SELECTED_BACKUP="${backups[0]}"
    elif [[ "$selection" =~ ^[0-9]+$ ]] && [[ "$selection" -ge 1 ]] && [[ "$selection" -le ${#backups[@]} ]]; then
        SELECTED_BACKUP="${backups[$((selection-1))]}"
    else
        error "Invalid selection"
        exit 1
    fi
    
    log "Selected backup: $SELECTED_BACKUP"
}

# Confirm rollback
confirm_rollback() {
    warning "This will rollback the production deployment to backup: $SELECTED_BACKUP"
    warning "Current data may be lost if not backed up!"
    echo
    
    read -p "Are you sure you want to proceed? (type 'yes' to confirm): " -r
    if [[ "$REPLY" != "yes" ]]; then
        log "Rollback cancelled"
        exit 0
    fi
}

# Create emergency backup
create_emergency_backup() {
    log "Creating emergency backup before rollback..."
    
    local emergency_backup="backups/emergency_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$emergency_backup"
    
    cd "$PROJECT_ROOT"
    
    # Backup current environment
    if [[ -f ".env.production" ]]; then
        cp ".env.production" "$emergency_backup/"
    fi
    
    # Backup database
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q postgres; then
        log "Backing up current database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U dockerdeployer dockerdeployer > "$emergency_backup/database.sql" 2>/dev/null || true
    fi
    
    success "Emergency backup created: $emergency_backup"
}

# Stop current services
stop_services() {
    log "Stopping current services..."
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down || true
    
    success "Services stopped"
}

# Restore from backup
restore_backup() {
    log "Restoring from backup: $SELECTED_BACKUP"
    
    local backup_path="$PROJECT_ROOT/$BACKUP_DIR/$SELECTED_BACKUP"
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Restore environment file
    if [[ -f "$backup_path/.env.production" ]]; then
        log "Restoring environment configuration..."
        cp "$backup_path/.env.production" .
        success "Environment configuration restored"
    else
        warning "No environment file found in backup"
    fi
    
    # Restore database
    if [[ -f "$backup_path/database.sql" ]]; then
        log "Restoring database..."
        
        # Start database service
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 15
        
        # Drop and recreate database
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U dockerdeployer -c "DROP DATABASE IF EXISTS dockerdeployer;" postgres || true
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U dockerdeployer -c "CREATE DATABASE dockerdeployer;" postgres || true
        
        # Restore database
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U dockerdeployer -d dockerdeployer < "$backup_path/database.sql" || true
        
        success "Database restored"
    else
        warning "No database backup found"
    fi
    
    # Restore volumes
    if [[ -f "$backup_path/volumes.tar.gz" ]]; then
        log "Restoring Docker volumes..."
        
        # Remove existing volume
        docker volume rm dockerdeployer_db_data 2>/dev/null || true
        
        # Create new volume and restore data
        docker volume create dockerdeployer_db_data
        docker run --rm -v dockerdeployer_db_data:/data -v "$PWD/$backup_path":/backup alpine tar xzf /backup/volumes.tar.gz -C /data || true
        
        success "Volumes restored"
    else
        warning "No volume backup found"
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images (in case we're rolling back to a previous image version)
    docker-compose -f "$COMPOSE_FILE" pull || true
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Services started"
}

# Health checks
run_health_checks() {
    log "Running health checks..."
    
    local max_attempts=20
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

# Show rollback status
show_status() {
    log "Rollback Status:"
    echo
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo
    log "Application URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000/api"
    echo "  Health Check: http://localhost:8000/health"
    echo
    
    log "Useful commands:"
    echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo
}

# Emergency stop function
emergency_stop() {
    error "Emergency stop initiated"
    
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down || true
    
    error "All services stopped. Manual intervention required."
    exit 1
}

# Main rollback function
main() {
    log "Starting DockerDeployer Production Rollback"
    echo "============================================="
    
    # Set trap for emergency stop on error
    trap emergency_stop ERR
    
    select_backup
    confirm_rollback
    create_emergency_backup
    stop_services
    restore_backup
    start_services
    run_health_checks
    show_status
    
    echo "============================================="
    success "🔄 DockerDeployer Rollback Completed Successfully!"
    success "📊 System restored to backup: $SELECTED_BACKUP"
    echo
}

# Quick rollback to latest backup
quick_rollback() {
    log "Performing quick rollback to latest backup..."
    
    local backups=($(ls -1t "$PROJECT_ROOT/$BACKUP_DIR" 2>/dev/null || true))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        error "No backups found for quick rollback"
        exit 1
    fi
    
    SELECTED_BACKUP="${backups[0]}"
    
    warning "Quick rollback to: $SELECTED_BACKUP"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Quick rollback cancelled"
        exit 0
    fi
    
    create_emergency_backup
    stop_services
    restore_backup
    start_services
    run_health_checks
    show_status
    
    success "🔄 Quick rollback completed!"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        "quick")
            quick_rollback
            ;;
        "list")
            list_backups
            ;;
        *)
            main "$@"
            ;;
    esac
fi
