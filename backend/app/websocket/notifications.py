"""
WebSocket endpoints for real-time notifications.
"""

import json
import logging
from typing import Dict, Any

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_websocket
from app.db.database import get_db
from app.db.models import User as UserModel
from app.services.alert_notification_service import connection_manager

logger = logging.getLogger(__name__)


async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for the connection
        db: Database session
    """
    try:
        # Verify user exists and is active
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect to the connection manager
        await connection_manager.connect(websocket, user_id)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "user_id": user_id,
            "message": "Connected to DockerDeployer notifications"
        }))

        # Initialize Redis client for notification history
        redis_client = None
        try:
            redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
            await redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available: {e}")

        # Send any pending notifications from Redis
        if redis_client:
            await send_pending_notifications(websocket, user_id, redis_client)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(websocket, user_id, message, db)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await connection_manager.disconnect(websocket)
        if redis_client:
            await redis_client.close()


async def handle_websocket_message(
    websocket: WebSocket,
    user_id: int,
    message: Dict[str, Any],
    db: Session
):
    """
    Handle incoming WebSocket messages from clients.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID
        message: Parsed message from client
        db: Database session
    """
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }))
    
    elif message_type == "acknowledge_alert":
        # Handle alert acknowledgment
        alert_id = message.get("alert_id")
        if alert_id:
            from app.services.alert_notification_service import AlertNotificationService
            notification_service = AlertNotificationService(db)
            success = await notification_service.acknowledge_alert(alert_id, user_id)
            
            await websocket.send_text(json.dumps({
                "type": "alert_acknowledgment_response",
                "alert_id": alert_id,
                "success": success,
                "timestamp": "2024-01-01T00:00:00Z"
            }))
    
    elif message_type == "get_notification_history":
        # Send notification history
        limit = message.get("limit", 50)
        await send_notification_history(websocket, user_id, limit)
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


async def send_pending_notifications(
    websocket: WebSocket,
    user_id: int,
    redis_client: redis.Redis
):
    """
    Send any pending notifications from Redis to the newly connected client.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID
        redis_client: Redis client
    """
    try:
        key = f"notifications:user:{user_id}"
        notifications = await redis_client.lrange(key, 0, 9)  # Get last 10 notifications
        
        if notifications:
            for notification_str in reversed(notifications):  # Send oldest first
                try:
                    notification = json.loads(notification_str)
                    notification["type"] = "pending_notification"
                    await websocket.send_text(json.dumps(notification))
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        logger.error(f"Error sending pending notifications: {e}")


async def send_notification_history(
    websocket: WebSocket,
    user_id: int,
    limit: int = 50
):
    """
    Send notification history to the client.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID
        limit: Maximum number of notifications to send
    """
    try:
        redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
        await redis_client.ping()
        
        key = f"notifications:user:{user_id}"
        notifications = await redis_client.lrange(key, 0, limit - 1)
        
        history = []
        for notification_str in notifications:
            try:
                notification = json.loads(notification_str)
                history.append(notification)
            except json.JSONDecodeError:
                continue
        
        await websocket.send_text(json.dumps({
            "type": "notification_history",
            "notifications": history,
            "count": len(history),
            "timestamp": "2024-01-01T00:00:00Z"
        }))
        
        await redis_client.close()
        
    except Exception as e:
        logger.error(f"Error sending notification history: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to retrieve notification history"
        }))


async def broadcast_system_notification(message: str, notification_type: str = "info"):
    """
    Broadcast a system-wide notification to all connected users.
    
    Args:
        message: Notification message
        notification_type: Type of notification (info, warning, error)
    """
    notification = {
        "type": "system_notification",
        "notification_type": notification_type,
        "message": message,
        "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
    }
    
    await connection_manager.broadcast_message(notification)


async def send_user_notification(user_id: int, message: str, notification_type: str = "info"):
    """
    Send a notification to a specific user.
    
    Args:
        user_id: Target user ID
        message: Notification message
        notification_type: Type of notification (info, warning, error)
    """
    notification = {
        "type": "user_notification",
        "notification_type": notification_type,
        "message": message,
        "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
    }
    
    await connection_manager.send_personal_message(notification, user_id)
