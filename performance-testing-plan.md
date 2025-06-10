# Template Marketplace Performance Testing Plan

## Overview
Comprehensive performance testing for the Template Marketplace to ensure <200ms API response times, efficient rate limiting, and system stability under load.

## Testing Scope

### 1. API Endpoint Performance Testing

#### Critical Endpoints to Test:
- `GET /api/marketplace/templates` (search/browse)
- `POST /api/marketplace/templates` (template submission)
- `GET /api/marketplace/templates/{id}` (template details)
- `POST /api/marketplace/templates/{id}/reviews` (review submission)
- `GET /api/marketplace/admin/pending` (admin queue)
- `POST /api/marketplace/admin/templates/{id}/approve` (approval)

#### Performance Targets:
- **Response Time**: <200ms for all endpoints
- **Throughput**: Handle 100+ concurrent users
- **Rate Limiting**: Validate 10-200 requests/minute limits
- **Database Performance**: Efficient queries with large datasets

### 2. Load Testing Scenarios

#### Scenario A: Normal User Browsing
```bash
# Simulate 50 concurrent users browsing templates
- Search templates with various filters
- View template details
- Submit reviews
- Download templates
```

#### Scenario B: Template Submission Load
```bash
# Simulate 20 concurrent users submitting templates
- Create new templates
- Upload Docker Compose YAML
- Submit for approval
```

#### Scenario C: Admin Approval Workflow
```bash
# Simulate 5 concurrent admins processing queue
- Fetch pending templates
- Approve/reject templates
- Bulk operations
- View statistics
```

#### Scenario D: Peak Load Simulation
```bash
# Simulate 100+ concurrent users
- Mixed browsing and submission activities
- Stress test rate limiting
- Database connection pooling
- Memory usage monitoring
```

### 3. Database Performance Testing

#### Large Dataset Testing:
- **1000+ templates** in marketplace
- **5000+ reviews** across templates
- **100+ categories** with templates
- **Complex search queries** with multiple filters

#### Query Optimization:
- Template search with pagination
- Category filtering performance
- Rating aggregation queries
- Recent activity tracking

### 4. Rate Limiting Validation

#### Test Rate Limits:
- **Template Creation**: 10/minute per user
- **Template Search**: 100/minute per user
- **Review Submission**: 30/minute per user
- **Admin Operations**: 200/minute per admin

#### Rate Limiting Scenarios:
- Single user hitting limits
- Multiple users approaching limits
- Rate limit recovery testing
- Redis performance under load

### 5. Frontend Performance Testing

#### Client-Side Performance:
- **Component Rendering**: Large template lists
- **Search Performance**: Real-time filtering
- **Memory Usage**: Long browsing sessions
- **Network Efficiency**: API call optimization

#### User Experience Metrics:
- **First Contentful Paint**: <1.5s
- **Largest Contentful Paint**: <2.5s
- **Time to Interactive**: <3s
- **Cumulative Layout Shift**: <0.1

## Testing Tools and Implementation

### 1. Backend Load Testing
```bash
# Using Apache Bench (ab)
ab -n 1000 -c 50 http://localhost:8000/api/marketplace/templates

# Using wrk for advanced scenarios
wrk -t12 -c400 -d30s --script=marketplace-load.lua http://localhost:8000/

# Using Locust for complex user scenarios
locust -f marketplace_locust.py --host=http://localhost:8000
```

### 2. Database Performance Monitoring
```sql
-- Monitor slow queries
EXPLAIN ANALYZE SELECT * FROM marketplace_templates 
WHERE status = 'approved' 
ORDER BY rating_avg DESC 
LIMIT 20 OFFSET 100;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';
```

### 3. Application Monitoring
```python
# Performance monitoring middleware
import time
import psutil
from fastapi import Request, Response

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log slow requests
    if process_time > 0.2:  # 200ms threshold
        logger.warning(f"Slow request: {request.url} took {process_time:.3f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 4. Memory and Resource Monitoring
```bash
# Monitor system resources during testing
htop
iostat -x 1
vmstat 1
docker stats

# Monitor database connections
SELECT count(*) FROM pg_stat_activity;
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
```

## Performance Test Scripts

### 1. Marketplace Load Test Script
```python
# marketplace_locust.py
from locust import HttpUser, task, between
import random

class MarketplaceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login user
        self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    
    @task(3)
    def browse_templates(self):
        # Search templates with random filters
        params = {
            "page": random.randint(1, 5),
            "per_page": 20,
            "sort_by": random.choice(["created_at", "rating_avg", "downloads"]),
            "category_id": random.choice([None, 1, 2, 3])
        }
        self.client.get("/api/marketplace/templates", params=params)
    
    @task(2)
    def view_template_details(self):
        template_id = random.randint(1, 100)
        self.client.get(f"/api/marketplace/templates/{template_id}")
    
    @task(1)
    def submit_review(self):
        template_id = random.randint(1, 100)
        self.client.post(f"/api/marketplace/templates/{template_id}/reviews", json={
            "rating": random.randint(1, 5),
            "comment": "Test review comment"
        })
```

### 2. Database Seeding Script
```python
# seed_marketplace_data.py
import asyncio
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import MarketplaceTemplate, TemplateCategory, TemplateReview

async def seed_large_dataset():
    """Seed database with large dataset for performance testing"""
    db = next(get_db())
    
    # Create 1000 templates
    for i in range(1000):
        template = MarketplaceTemplate(
            name=f"Performance Test Template {i}",
            description=f"Template {i} for performance testing",
            author_id=random.randint(1, 10),
            category_id=random.randint(1, 5),
            version="1.0.0",
            docker_compose_yaml="version: '3.8'\nservices:\n  app:\n    image: nginx",
            tags=[f"tag{j}" for j in range(3)],
            status="approved",
            downloads=random.randint(0, 1000),
            rating_avg=random.uniform(1, 5),
            rating_count=random.randint(0, 100)
        )
        db.add(template)
    
    # Create 5000 reviews
    for i in range(5000):
        review = TemplateReview(
            template_id=random.randint(1, 1000),
            user_id=random.randint(1, 100),
            rating=random.randint(1, 5),
            comment=f"Performance test review {i}"
        )
        db.add(review)
    
    db.commit()
```

## Success Criteria

### Performance Benchmarks:
- ✅ **API Response Times**: All endpoints <200ms under normal load
- ✅ **Concurrent Users**: Support 100+ concurrent users
- ✅ **Rate Limiting**: Effective protection without false positives
- ✅ **Database Queries**: Optimized for large datasets
- ✅ **Memory Usage**: Stable under extended load
- ✅ **Error Rate**: <1% under normal conditions

### Scalability Targets:
- ✅ **Template Capacity**: Handle 10,000+ templates efficiently
- ✅ **Review Volume**: Process 50,000+ reviews without degradation
- ✅ **Search Performance**: Sub-second search with complex filters
- ✅ **Admin Operations**: Bulk operations complete within 5 seconds

## Next Steps

1. **Implement Load Testing Scripts**: Create comprehensive test scenarios
2. **Set Up Monitoring**: Deploy performance monitoring tools
3. **Execute Test Scenarios**: Run all performance test cases
4. **Analyze Results**: Identify bottlenecks and optimization opportunities
5. **Optimize Performance**: Implement database indexing and query optimization
6. **Validate Improvements**: Re-run tests to confirm performance gains
7. **Document Results**: Create performance benchmark documentation

## Monitoring and Alerting

### Key Metrics to Monitor:
- API response times (95th percentile)
- Database query performance
- Memory and CPU usage
- Rate limiting effectiveness
- Error rates and types
- User experience metrics

### Alert Thresholds:
- Response time >200ms for 5+ minutes
- Error rate >5% for 2+ minutes
- Memory usage >80% for 10+ minutes
- Database connections >80% of pool
- Rate limiting triggered >100 times/hour
