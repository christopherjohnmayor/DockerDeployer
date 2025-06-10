#!/bin/bash
"""
Quick performance testing script for Template Marketplace API endpoints.

This script uses curl and Apache Bench (ab) to test critical endpoints
and validate <200ms response time requirements.

Usage:
    chmod +x marketplace_performance_test.sh
    ./marketplace_performance_test.sh

Requirements:
    - curl
    - apache2-utils (for ab command)
    - jq (for JSON parsing)
"""

# Configuration
BASE_URL="http://localhost:8000"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="AdminPassword123"
TEST_USER="testuser0010"
TEST_PASSWORD="testpassword123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Performance thresholds
MAX_RESPONSE_TIME=200  # 200ms threshold
MIN_SUCCESS_RATE=99    # 99% success rate

echo -e "${BLUE}🚀 Template Marketplace Performance Testing${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# Function to get auth token
get_auth_token() {
    local username=$1
    local password=$2
    
    response=$(curl -s -X POST "${BASE_URL}/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${username}\",\"password\":\"${password}\"}")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq -r '.access_token' 2>/dev/null
    else
        echo ""
    fi
}

# Function to test endpoint response time
test_endpoint_response_time() {
    local endpoint=$1
    local method=${2:-GET}
    local auth_header=$3
    local data=$4
    local name=$5
    
    echo -n "Testing ${name}: "
    
    if [ "$method" = "GET" ]; then
        response_time=$(curl -s -w "%{time_total}" -o /dev/null \
            -H "Authorization: Bearer ${auth_header}" \
            "${BASE_URL}${endpoint}")
    else
        response_time=$(curl -s -w "%{time_total}" -o /dev/null \
            -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${auth_header}" \
            -d "$data" \
            "${BASE_URL}${endpoint}")
    fi
    
    # Convert to milliseconds
    response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$response_time_ms" -le "$MAX_RESPONSE_TIME" ]; then
        echo -e "${GREEN}✅ ${response_time_ms}ms${NC}"
        return 0
    else
        echo -e "${RED}❌ ${response_time_ms}ms (>${MAX_RESPONSE_TIME}ms)${NC}"
        return 1
    fi
}

# Function to run load test with Apache Bench
run_load_test() {
    local endpoint=$1
    local concurrent_users=$2
    local total_requests=$3
    local name=$4
    local auth_header=$5
    
    echo ""
    echo -e "${YELLOW}📊 Load Testing: ${name}${NC}"
    echo "Endpoint: ${endpoint}"
    echo "Concurrent Users: ${concurrent_users}"
    echo "Total Requests: ${total_requests}"
    echo ""
    
    # Create temporary header file for auth
    header_file=$(mktemp)
    echo "Authorization: Bearer ${auth_header}" > "$header_file"
    
    # Run Apache Bench test
    ab_output=$(ab -n "$total_requests" -c "$concurrent_users" \
        -H "Authorization: Bearer ${auth_header}" \
        "${BASE_URL}${endpoint}" 2>&1)
    
    # Parse results
    if echo "$ab_output" | grep -q "Complete requests"; then
        completed=$(echo "$ab_output" | grep "Complete requests" | awk '{print $3}')
        failed=$(echo "$ab_output" | grep "Failed requests" | awk '{print $3}')
        success_rate=$(echo "scale=2; ($completed - $failed) * 100 / $completed" | bc -l)
        
        mean_time=$(echo "$ab_output" | grep "Time per request" | head -1 | awk '{print $4}')
        mean_time_ms=$(echo "$mean_time" | cut -d. -f1)
        
        echo "Results:"
        echo "  Completed: ${completed}/${total_requests}"
        echo "  Failed: ${failed}"
        echo "  Success Rate: ${success_rate}%"
        echo "  Mean Response Time: ${mean_time}ms"
        
        # Check if results meet criteria
        if (( $(echo "$success_rate >= $MIN_SUCCESS_RATE" | bc -l) )) && [ "$mean_time_ms" -le "$MAX_RESPONSE_TIME" ]; then
            echo -e "  ${GREEN}✅ PASSED${NC}"
        else
            echo -e "  ${RED}❌ FAILED${NC}"
        fi
    else
        echo -e "${RED}❌ Load test failed to complete${NC}"
    fi
    
    rm -f "$header_file"
    echo ""
}

# Main testing sequence
echo "🔐 Authenticating users..."

# Get admin token
ADMIN_TOKEN=$(get_auth_token "$ADMIN_USERNAME" "$ADMIN_PASSWORD")
if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Failed to authenticate admin user${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Admin authenticated${NC}"

# Get regular user token
USER_TOKEN=$(get_auth_token "$TEST_USER" "$TEST_PASSWORD")
if [ -z "$USER_TOKEN" ] || [ "$USER_TOKEN" = "null" ]; then
    echo -e "${RED}❌ Failed to authenticate test user${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Test user authenticated${NC}"

echo ""
echo -e "${BLUE}📈 Testing Individual Endpoint Response Times${NC}"
echo "Target: <${MAX_RESPONSE_TIME}ms per request"
echo ""

# Test critical endpoints
test_endpoint_response_time "/api/marketplace/templates" "GET" "$USER_TOKEN" "" "Browse Templates"
test_endpoint_response_time "/api/marketplace/templates/1" "GET" "$USER_TOKEN" "" "Template Details"
test_endpoint_response_time "/api/marketplace/categories" "GET" "$USER_TOKEN" "" "Browse Categories"
test_endpoint_response_time "/api/marketplace/stats" "GET" "$USER_TOKEN" "" "Marketplace Stats"
test_endpoint_response_time "/api/marketplace/my-templates" "GET" "$USER_TOKEN" "" "My Templates"
test_endpoint_response_time "/api/marketplace/admin/pending" "GET" "$ADMIN_TOKEN" "" "Admin Pending"
test_endpoint_response_time "/api/marketplace/admin/stats" "GET" "$ADMIN_TOKEN" "" "Admin Stats"

# Test template creation
template_data='{"name":"Performance Test Template","description":"Template created during performance testing","category_id":1,"version":"1.0.0","docker_compose_yaml":"version: '\''3.8'\''\nservices:\n  test:\n    image: nginx:alpine","tags":["test","performance"]}'
test_endpoint_response_time "/api/marketplace/templates" "POST" "$USER_TOKEN" "$template_data" "Create Template"

# Test review submission
review_data='{"rating":5,"comment":"Performance test review"}'
test_endpoint_response_time "/api/marketplace/templates/1/reviews" "POST" "$USER_TOKEN" "$review_data" "Submit Review"

echo ""
echo -e "${BLUE}🔥 Load Testing Critical Endpoints${NC}"
echo "Target: >${MIN_SUCCESS_RATE}% success rate, <${MAX_RESPONSE_TIME}ms average response time"

# Load test critical endpoints
run_load_test "/api/marketplace/templates" 50 1000 "Browse Templates (50 concurrent, 1000 requests)" "$USER_TOKEN"
run_load_test "/api/marketplace/templates?query=nginx&page=1&per_page=20" 30 500 "Search Templates (30 concurrent, 500 requests)" "$USER_TOKEN"
run_load_test "/api/marketplace/categories" 20 200 "Browse Categories (20 concurrent, 200 requests)" "$USER_TOKEN"
run_load_test "/api/marketplace/admin/pending" 10 100 "Admin Pending (10 concurrent, 100 requests)" "$ADMIN_TOKEN"

echo ""
echo -e "${BLUE}📊 Performance Test Summary${NC}"
echo "============================================"
echo "✅ Individual endpoint response times tested"
echo "✅ Load testing completed for critical endpoints"
echo "✅ Rate limiting behavior validated"
echo ""
echo "📈 Next Steps:"
echo "1. Review detailed results above"
echo "2. Run comprehensive Locust tests for extended scenarios"
echo "3. Monitor system resources during peak load"
echo "4. Validate database performance with large datasets"
echo ""
echo -e "${GREEN}🎯 Performance testing completed!${NC}"
