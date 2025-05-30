#!/bin/bash

# DockerDeployer Development Environment Stop Script
# This script stops and cleans up the development environment

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

# Function to stop containers
stop_containers() {
    print_status "Stopping Docker containers..."
    docker-compose down
    print_success "Containers stopped"
}

# Function to clean up (optional)
cleanup_volumes() {
    if [ "$1" = "--clean" ]; then
        print_warning "Cleaning up volumes (this will delete all data)..."
        read -p "Are you sure? This will delete the database and Redis data. (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            print_success "Volumes cleaned up"
        else
            print_status "Volume cleanup cancelled"
        fi
    fi
}

# Function to show cleanup options
show_cleanup_options() {
    echo ""
    print_status "Cleanup Options:"
    echo "  To remove all data (database, Redis, etc.):"
    echo "    ./scripts/stop-dev.sh --clean"
    echo ""
    echo "  To remove Docker images:"
    echo "    docker-compose down --rmi all"
    echo ""
    echo "  To remove everything (containers, volumes, images):"
    echo "    docker-compose down -v --rmi all --remove-orphans"
}

# Main execution
main() {
    echo "=================================================="
    echo "  DockerDeployer Development Environment Stop   "
    echo "=================================================="
    echo ""
    
    stop_containers
    cleanup_volumes "$1"
    show_cleanup_options
    
    echo ""
    print_success "Development environment stopped!"
    print_status "To start again, run: ./scripts/deploy-dev.sh"
}

# Run main function
main "$@"
