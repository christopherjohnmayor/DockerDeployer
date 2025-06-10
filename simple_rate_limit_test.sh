#!/bin/bash

# Simple Rate Limiting Test for DockerDeployer
# Tests if rate limiting is working by making rapid requests

BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidXNlcm5hbWUiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc0OTUyNjc2OCwidHlwZSI6ImFjY2VzcyIsImp0aSI6IjliYjQ1NDVkLWM0NDctNDVmMC1hMzM5LTg1ZDUxMTgwMjMwNiJ9.o6KKETaHnQYGkq4foz9Z0BUAXMOW_o1WUY-vY7BUu-8"
CONTAINER_ID="bc56b6ac5b7b"

echo "🚦 Testing Rate Limiting for Container Stats Endpoint"
echo "Expected limit: 60 requests/minute"
echo "Making rapid requests..."

success_count=0
rate_limited_count=0
error_count=0

# Make 70 rapid requests to exceed the 60/minute limit
for i in {1..70}; do
    response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/containers/$CONTAINER_ID/stats" -o /dev/null)
    
    case $response in
        200)
            success_count=$((success_count + 1))
            echo -n "✅"
            ;;
        429)
            rate_limited_count=$((rate_limited_count + 1))
            echo -n "🚫"
            echo ""
            echo "Rate limited after $i requests!"
            break
            ;;
        *)
            error_count=$((error_count + 1))
            echo -n "❌($response)"
            ;;
    esac
    
    # Small delay to avoid overwhelming
    sleep 0.1
done

echo ""
echo "📊 Results:"
echo "  Successful requests: $success_count"
echo "  Rate limited requests: $rate_limited_count"
echo "  Error requests: $error_count"

if [ $rate_limited_count -gt 0 ]; then
    echo "🎉 PASS: Rate limiting is working!"
    exit 0
else
    echo "❌ FAIL: No rate limiting detected"
    exit 1
fi
