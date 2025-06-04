# WebSocket CSP Configuration Fix

## Overview

This document describes the fix for WebSocket connection failures due to Content Security Policy (CSP) restrictions in the DockerDeployer frontend.

## Problem Description

The DockerDeployer frontend was experiencing WebSocket connection failures when trying to establish real-time connections for:
- Container status updates and notifications (`/ws/notifications/{user_id}`)
- Real-time metrics visualization (`/ws/metrics/multiple`)

The issue was caused by restrictive CSP headers that only allowed HTTP connections but not WebSocket (`ws://` or `wss://`) protocols.

## Root Cause

The original CSP configuration in `frontend/nginx/nginx.conf` was:
```
Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' http://backend:8000"
```

The `connect-src` directive only allowed:
- `'self'` (same origin HTTP/HTTPS)
- `http://backend:8000` (HTTP only)

This blocked WebSocket connections which use `ws://` or `wss://` protocols.

## Solution Implemented

### 1. Updated Development CSP Configuration

**File:** `frontend/nginx/nginx.conf`

Updated the CSP to include WebSocket protocol support:
```nginx
# CSP with WebSocket support for real-time features (container metrics, notifications)
# connect-src allows both HTTP API calls and WebSocket connections to backend
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' http://backend:8000 ws://backend:8000 http://localhost:8000 ws://localhost:8000";
```

### 2. Added WebSocket Proxy Configuration

**File:** `frontend/nginx/nginx.conf`

Added dedicated WebSocket proxy configuration:
```nginx
# WebSocket proxy for real-time features (notifications, metrics)
location /ws/ {
    proxy_pass http://backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
```

### 3. Updated Production CSP Configuration

**File:** `nginx/nginx.prod.conf`

Updated production CSP to support WebSocket over HTTPS:
```nginx
# CSP with WebSocket support for real-time features (container metrics, notifications)
# connect-src allows both HTTP API calls and WebSocket connections to backend
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://${DOMAIN} wss://${DOMAIN}" always;
```

Added WebSocket proxy configuration for production:
```nginx
# WebSocket proxy for real-time features (notifications, metrics)
location /ws/ {
    proxy_pass http://backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_buffering off;
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
```

### 4. Created Environment-Aware WebSocket Utility

**File:** `frontend/src/utils/websocket.ts`

Created utility functions for environment-aware WebSocket URL construction:
- `getWebSocketUrl()` - Generic WebSocket URL builder
- `getNotificationWebSocketUrl()` - Specific for notifications
- `getMetricsWebSocketUrl()` - Specific for metrics

### 5. Updated Frontend Components

**Files Updated:**
- `frontend/src/components/AlertNotifications.tsx`
- `frontend/src/pages/MetricsVisualization.tsx`

Changed from hardcoded URLs to environment-aware utility functions.

## Security Considerations

### CSP Directives Explained

- `connect-src 'self'` - Allows connections to same origin
- `http://backend:8000` / `https://${DOMAIN}` - Allows HTTP API calls
- `ws://backend:8000` / `wss://${DOMAIN}` - Allows WebSocket connections
- `http://localhost:8000 ws://localhost:8000` - Development environment support

### Why These Changes Are Secure

1. **Restricted Domains**: Only allows connections to known backend endpoints
2. **Protocol Specific**: Explicitly allows only necessary protocols
3. **Environment Separation**: Different configurations for dev/prod
4. **Proxy Protection**: WebSocket connections go through Nginx proxy

## Testing

### Manual Testing Steps

1. **Start the development environment:**
   ```bash
   docker-compose up -d
   ```

2. **Open browser and navigate to:**
   ```
   http://localhost:3000
   ```

3. **Test WebSocket connections:**
   - Login to the application
   - Navigate to Metrics Visualization page
   - Enable "Real-time Updates" toggle
   - Check browser console for WebSocket connection messages

4. **Test notifications:**
   - Trigger an alert condition
   - Verify notification appears in real-time

### Automated Testing

Use the provided test file:
```bash
# Serve the test file and open in browser
open test-websocket-csp.html
```

## Troubleshooting

### Common Issues

1. **WebSocket still failing:**
   - Check browser console for CSP violation errors
   - Verify Nginx configuration is loaded (restart containers)
   - Check Network tab in DevTools for failed WebSocket requests

2. **CSP violations in console:**
   - Verify the CSP header includes the correct WebSocket URLs
   - Check if the frontend is using the correct WebSocket URLs

3. **Connection timeouts:**
   - Verify backend WebSocket endpoints are running
   - Check Docker network connectivity between containers

### Debug Commands

```bash
# Check Nginx configuration
docker exec dockerdeployer-frontend nginx -t

# View Nginx logs
docker logs dockerdeployer-frontend

# Check backend WebSocket endpoints
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost:8000/ws/test
```

## Deployment Notes

### Development Environment
- Uses `ws://` protocol
- Allows both `backend:8000` and `localhost:8000` for flexibility
- Includes comprehensive logging for debugging

### Production Environment
- Uses `wss://` protocol (WebSocket over HTTPS)
- Restricts connections to the domain specified in `${DOMAIN}`
- Includes security headers with `always` directive

## Future Considerations

1. **WebSocket Authentication**: Consider implementing WebSocket-specific authentication
2. **Rate Limiting**: Add rate limiting for WebSocket connections
3. **Monitoring**: Add WebSocket connection monitoring and alerting
4. **Fallback**: Implement fallback mechanisms for when WebSocket connections fail
