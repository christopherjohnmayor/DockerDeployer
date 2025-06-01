# DockerDeployer Production Deployment Guide

## Overview

This guide provides a comprehensive approach to deploying DockerDeployer to production with proper security, monitoring, and performance optimization.

## Current Status

### ✅ Backend Ready
- **Test Coverage**: 84.38% (exceeds 80% threshold)
- **Tests**: 307 passing, 1 skipped
- **Key Features**: JWT auth, rate limiting, metrics, alerts

### ⚠️ Frontend Needs Fixes
- **Tests**: 496 passing, 32 failing
- **Issues**: Material-UI testing patterns, timeouts, dialog state

### ✅ Infrastructure Ready
- Docker configurations for dev/prod
- GitHub Actions CI/CD pipeline
- Environment configurations

## Phase 1: Pre-deployment Fixes

### 1.1 Frontend Test Fixes (HIGH PRIORITY)

```bash
# Fix Material-UI testing patterns
cd frontend

# Update tests to use getAllByText for multiple elements
# Fix timeout issues in MetricsHistory tests
# Resolve dialog state management in AlertsManagement

npm test -- --coverage
```

**Required Changes:**
- Use `getAllByText()` for multiple elements instead of `getByText()`
- Increase test timeouts for async operations
- Fix dialog state management with proper cleanup
- Wrap disabled buttons in span elements for Tooltips

### 1.2 CI/CD Pipeline Verification

```bash
# Check GitHub Actions status
git push origin main

# Verify all workflows pass:
# - test.yml (backend + frontend tests)
# - build.yml (Docker image builds)
```

## Phase 2: Production Configuration

### 2.1 Environment Setup

Create production environment file:

```bash
# .env.production
ENVIRONMENT=production
SECRET_KEY=<GENERATE_SECURE_KEY>
DATABASE_URL=postgresql://user:pass@host:5432/dockerdeployer
DOMAIN=your-domain.com
CORS_ORIGINS=https://your-domain.com

# Email Configuration
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<YOUR_SENDGRID_KEY>
EMAIL_FROM=noreply@your-domain.com

# LLM Configuration
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=<YOUR_API_KEY>
LLM_MODEL=meta-llama/llama-3.2-3b-instruct:free

# Redis Configuration
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET_KEY=<GENERATE_SECURE_JWT_KEY>
```

### 2.2 Database Migration

```bash
# For production, migrate from SQLite to PostgreSQL
# Update DATABASE_URL in production environment
# Run database migrations
```

### 2.3 SSL/TLS Configuration

```bash
# Configure reverse proxy (nginx/traefik)
# Set up SSL certificates (Let's Encrypt)
# Update CORS_ORIGINS for HTTPS
```

## Phase 3: Production Deployment

### 3.1 Docker Production Deployment

```bash
# Build and deploy production images
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### 3.2 Health Checks

```bash
# Backend health check
curl https://your-domain.com/health

# Frontend health check
curl https://your-domain.com/

# Database connectivity
curl https://your-domain.com/api/containers
```

### 3.3 Monitoring Setup

```bash
# Configure monitoring endpoints
# Set up log aggregation
# Configure alerting for critical metrics
```

## Phase 4: Security Hardening

### 4.1 Authentication & Authorization
- ✅ JWT authentication implemented
- ✅ Role-based access control (admin/user)
- ✅ Rate limiting configured (87% coverage)
- ✅ Password reset functionality

### 4.2 API Security
- ✅ CORS properly configured
- ✅ Input validation on all endpoints
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (React built-in)

### 4.3 Infrastructure Security
- ✅ Docker socket access controlled
- ✅ Environment variables for secrets
- ✅ Network isolation with Docker networks
- ✅ Health checks configured

## Phase 5: Performance Optimization

### 5.1 API Performance
- **Target**: <200ms response times
- **Current**: Optimized with async/await patterns
- **Caching**: Redis implementation ready
- **Database**: Connection pooling configured

### 5.2 Frontend Performance
- **Build**: Vite production builds optimized
- **Assets**: Static asset optimization
- **Lazy Loading**: Component-based code splitting
- **Caching**: Browser caching headers

### 5.3 Container Performance
- **Images**: Multi-stage builds for smaller images
- **Resources**: CPU/memory limits configured
- **Networking**: Optimized container networking
- **Storage**: Volume mounts for persistence

## Phase 6: Monitoring & Logging

### 6.1 Application Monitoring
- ✅ Real-time metrics collection
- ✅ Container health monitoring
- ✅ Alert system with WebSocket notifications
- ✅ Performance metrics tracking

### 6.2 Infrastructure Monitoring
- Docker container metrics
- System resource utilization
- Network performance
- Storage usage

### 6.3 Logging Strategy
- Centralized log collection
- Log rotation and retention
- Error tracking and alerting
- Audit trail for admin actions

## Deployment Commands

### Single-Click Production Deployment

```bash
#!/bin/bash
# deploy-production.sh

set -e

echo "🚀 Starting DockerDeployer Production Deployment..."

# 1. Verify environment
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found"
    exit 1
fi

# 2. Run tests
echo "🧪 Running tests..."
cd backend && python -m pytest --cov=. --cov-fail-under=80
cd ../frontend && npm test -- --coverage --watchAll=false

# 3. Build production images
echo "🏗️ Building production images..."
docker-compose -f docker-compose.prod.yml build

# 4. Deploy services
echo "🚀 Deploying services..."
docker-compose -f docker-compose.prod.yml up -d

# 5. Health checks
echo "🏥 Running health checks..."
sleep 30
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000/ || exit 1

echo "✅ Production deployment completed successfully!"
echo "🌐 Application available at: https://your-domain.com"
```

## Rollback Procedure

```bash
#!/bin/bash
# rollback.sh

echo "🔄 Rolling back to previous version..."

# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore previous images
docker-compose -f docker-compose.prod.yml pull

# Start previous version
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Rollback completed"
```

## Post-Deployment Checklist

- [ ] All services running and healthy
- [ ] SSL certificates configured and valid
- [ ] Database migrations completed
- [ ] Monitoring and alerting active
- [ ] Backup procedures in place
- [ ] Documentation updated
- [ ] Team notified of deployment

## Support and Maintenance

### Regular Maintenance Tasks
- Monitor system metrics and alerts
- Review and rotate security keys
- Update dependencies and security patches
- Backup database and configuration
- Review and optimize performance metrics

### Emergency Procedures
- Incident response plan
- Rollback procedures
- Contact information for critical issues
- Escalation procedures

---

**Next Steps**: Fix frontend test failures, then proceed with production deployment following this guide.
