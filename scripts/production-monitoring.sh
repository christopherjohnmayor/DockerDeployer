#!/bin/bash

# DockerDeployer Production Monitoring Script
# Automated health checks and performance monitoring

set -euo pipefail

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
ALERT_EMAIL="admin@localhost"
LOG_FILE="/var/log/dockerdeployer-monitoring.log"
RESPONSE_TIME_THRESHOLD=200  # milliseconds
CPU_THRESHOLD=80            # percentage
MEMORY_THRESHOLD=80         # percentage

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Health check function
check_backend_health() {
    log "🏥 Checking backend health..."
    
    local start_time=$(date +%s%3N)
    if curl -f -s "$BACKEND_URL/health" > /dev/null; then
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))
        
        if [[ $response_time -le $RESPONSE_TIME_THRESHOLD ]]; then
            success "Backend healthy (${response_time}ms)"
            return 0
        else
            warning "Backend slow response: ${response_time}ms (threshold: ${RESPONSE_TIME_THRESHOLD}ms)"
            return 1
        fi
    else
        error "Backend health check failed"
        return 1
    fi
}

# Frontend health check
check_frontend_health() {
    log "🌐 Checking frontend health..."
    
    if curl -f -s "$FRONTEND_URL" > /dev/null; then
        success "Frontend accessible"
        return 0
    else
        error "Frontend health check failed"
        return 1
    fi
}

# Container resource monitoring
check_container_resources() {
    log "💻 Checking container resources..."
    
    # Get container stats
    local stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemPerc}}" | grep dockerdeployer)
    
    while IFS=$'\t' read -r container cpu_perc mem_perc; do
        # Remove % symbol and convert to integer
        local cpu=$(echo "$cpu_perc" | sed 's/%//' | cut -d. -f1)
        local mem=$(echo "$mem_perc" | sed 's/%//' | cut -d. -f1)
        
        log "Container: $container - CPU: ${cpu}%, Memory: ${mem}%"
        
        if [[ $cpu -gt $CPU_THRESHOLD ]]; then
            warning "High CPU usage: $container (${cpu}%)"
        fi
        
        if [[ $mem -gt $MEMORY_THRESHOLD ]]; then
            warning "High memory usage: $container (${mem}%)"
        fi
        
        if [[ $cpu -le $CPU_THRESHOLD && $mem -le $MEMORY_THRESHOLD ]]; then
            success "Resource usage normal: $container"
        fi
    done <<< "$stats"
}

# Database backup verification
verify_backup() {
    log "💾 Verifying database backup..."
    
    local backup_dir="backups/$(date +%Y%m%d)"
    if [[ -d "$backup_dir" && -f "$backup_dir/dockerdeployer.db" ]]; then
        local backup_size=$(du -h "$backup_dir/dockerdeployer.db" | cut -f1)
        success "Database backup verified: $backup_size"
        return 0
    else
        warning "Database backup not found or outdated"
        return 1
    fi
}

# API endpoint testing
test_api_endpoints() {
    log "🔌 Testing critical API endpoints..."
    
    # Test health endpoint
    if curl -f -s "$BACKEND_URL/health" > /dev/null; then
        success "Health endpoint: OK"
    else
        error "Health endpoint: FAILED"
    fi
    
    # Test docs endpoint
    if curl -f -s "$BACKEND_URL/docs" > /dev/null; then
        success "Documentation endpoint: OK"
    else
        error "Documentation endpoint: FAILED"
    fi
    
    # Test auth endpoint (should require authentication)
    local auth_response=$(curl -s "$BACKEND_URL/auth/me")
    if echo "$auth_response" | grep -q "Not authenticated"; then
        success "Authentication endpoint: OK (requires auth)"
    else
        warning "Authentication endpoint: Unexpected response"
    fi
}

# Performance benchmark
run_performance_test() {
    log "⚡ Running performance benchmark..."
    
    local total_time=0
    local test_count=5
    
    for i in $(seq 1 $test_count); do
        local response_time=$(curl -w "%{time_total}" -s -o /dev/null "$BACKEND_URL/health")
        local response_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
        total_time=$((total_time + response_ms))
        log "Test $i: ${response_ms}ms"
    done
    
    local avg_time=$((total_time / test_count))
    
    if [[ $avg_time -le $RESPONSE_TIME_THRESHOLD ]]; then
        success "Average response time: ${avg_time}ms (within threshold)"
    else
        warning "Average response time: ${avg_time}ms (above ${RESPONSE_TIME_THRESHOLD}ms threshold)"
    fi
}

# Main monitoring function
main() {
    log "🚀 Starting DockerDeployer Production Monitoring"
    log "================================================"
    
    local health_status=0
    
    # Run all checks
    check_backend_health || health_status=1
    check_frontend_health || health_status=1
    check_container_resources
    verify_backup
    test_api_endpoints
    run_performance_test
    
    log "================================================"
    
    if [[ $health_status -eq 0 ]]; then
        success "🎉 All health checks passed"
    else
        error "❌ Some health checks failed - review logs"
    fi
    
    log "Monitoring completed at $(date)"
    return $health_status
}

# Run monitoring if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
