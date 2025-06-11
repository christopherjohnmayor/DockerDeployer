/**
 * Enhanced WebSocket utilities for Container Metrics Visualization
 * 
 * Provides specialized WebSocket functions for enhanced metrics streaming
 * including health scores, predictions, and real-time analytics.
 */

import { getWebSocketUrl } from './websocket';
import { EnhancedMetricsWebSocketMessage } from '../types/enhancedMetrics';

/**
 * Get WebSocket URL for enhanced metrics streaming
 * @param containerId - Container ID for metrics streaming
 * @param token - Authentication token
 * @returns WebSocket URL for enhanced metrics
 */
export const getEnhancedMetricsWebSocketUrl = (
  containerId: string,
  token: string
): string => {
  return getWebSocketUrl(`/ws/metrics/enhanced/${containerId}`, token);
};

/**
 * Get WebSocket URL for multiple enhanced metrics streaming
 * @param token - Authentication token
 * @returns WebSocket URL for multiple enhanced metrics
 */
export const getMultipleEnhancedMetricsWebSocketUrl = (token: string): string => {
  return getWebSocketUrl('/ws/metrics/enhanced/multiple', token);
};

/**
 * Enhanced WebSocket message handler
 * Provides type-safe message parsing and error handling
 */
export class EnhancedMetricsWebSocketHandler {
  private onMetricsUpdate?: (data: any) => void;
  private onHealthScoreUpdate?: (data: any) => void;
  private onPredictionUpdate?: (data: any) => void;
  private onAlertTriggered?: (data: any) => void;
  private onConnectionStatus?: (status: string) => void;
  private onError?: (error: string) => void;

  constructor(callbacks: {
    onMetricsUpdate?: (data: any) => void;
    onHealthScoreUpdate?: (data: any) => void;
    onPredictionUpdate?: (data: any) => void;
    onAlertTriggered?: (data: any) => void;
    onConnectionStatus?: (status: string) => void;
    onError?: (error: string) => void;
  }) {
    this.onMetricsUpdate = callbacks.onMetricsUpdate;
    this.onHealthScoreUpdate = callbacks.onHealthScoreUpdate;
    this.onPredictionUpdate = callbacks.onPredictionUpdate;
    this.onAlertTriggered = callbacks.onAlertTriggered;
    this.onConnectionStatus = callbacks.onConnectionStatus;
    this.onError = callbacks.onError;
  }

  /**
   * Handle incoming WebSocket message
   * @param event - WebSocket message event
   */
  handleMessage = (event: MessageEvent): void => {
    try {
      const message: EnhancedMetricsWebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'enhanced_metrics_update':
          this.onMetricsUpdate?.(message.data);
          break;

        case 'health_score_update':
          this.onHealthScoreUpdate?.(message.data);
          break;

        case 'prediction_update':
          this.onPredictionUpdate?.(message.data);
          break;

        case 'alert_triggered':
          this.onAlertTriggered?.(message.data);
          break;

        case 'connection_status':
          this.onConnectionStatus?.(message.message || 'Unknown status');
          break;

        default:
          console.warn('Unknown enhanced metrics message type:', message.type);
      }
    } catch (error) {
      const errorMessage = `Error parsing enhanced metrics WebSocket message: ${error}`;
      console.error(errorMessage);
      this.onError?.(errorMessage);
    }
  };

  /**
   * Create subscription message for container metrics
   * @param containerIds - Array of container IDs to subscribe to
   * @param options - Subscription options
   * @returns Subscription message object
   */
  createSubscriptionMessage = (
    containerIds: string[],
    options: {
      includeHealthScores?: boolean;
      includePredictions?: boolean;
      includeAlerts?: boolean;
      updateInterval?: number;
    } = {}
  ) => {
    return {
      type: 'subscribe',
      container_ids: containerIds,
      options: {
        include_health_scores: options.includeHealthScores ?? true,
        include_predictions: options.includePredictions ?? true,
        include_alerts: options.includeAlerts ?? true,
        update_interval: options.updateInterval ?? 3000, // 3 seconds default
      },
      timestamp: new Date().toISOString(),
    };
  };

  /**
   * Create unsubscription message
   * @param containerIds - Array of container IDs to unsubscribe from
   * @returns Unsubscription message object
   */
  createUnsubscriptionMessage = (containerIds: string[]) => {
    return {
      type: 'unsubscribe',
      container_ids: containerIds,
      timestamp: new Date().toISOString(),
    };
  };
}

/**
 * Enhanced WebSocket connection manager
 * Provides connection lifecycle management with enhanced features
 */
export class EnhancedMetricsWebSocketManager {
  private websocket: WebSocket | null = null;
  private url: string;
  private messageHandler: EnhancedMetricsWebSocketHandler;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private isConnecting = false;
  private shouldReconnect = true;

  constructor(
    url: string,
    messageHandler: EnhancedMetricsWebSocketHandler
  ) {
    this.url = url;
    this.messageHandler = messageHandler;
  }

  /**
   * Connect to the WebSocket
   */
  connect = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || this.websocket?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.isConnecting = true;

      try {
        this.websocket = new WebSocket(this.url);

        this.websocket.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          console.log('Enhanced metrics WebSocket connected');
          resolve();
        };

        this.websocket.onmessage = this.messageHandler.handleMessage;

        this.websocket.onclose = () => {
          this.isConnecting = false;
          console.log('Enhanced metrics WebSocket disconnected');
          
          if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
              this.connect().catch(console.error);
            }, this.reconnectInterval);
          }
        };

        this.websocket.onerror = (error) => {
          this.isConnecting = false;
          console.error('Enhanced metrics WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  };

  /**
   * Send message to WebSocket
   * @param message - Message object to send
   */
  sendMessage = (message: any): void => {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };

  /**
   * Disconnect from WebSocket
   */
  disconnect = (): void => {
    this.shouldReconnect = false;
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  };

  /**
   * Get connection state
   */
  getConnectionState = (): string => {
    if (!this.websocket) return 'disconnected';
    
    switch (this.websocket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  };

  /**
   * Check if WebSocket is connected
   */
  isConnected = (): boolean => {
    return this.websocket?.readyState === WebSocket.OPEN;
  };
}

/**
 * Utility function to format WebSocket connection status for UI display
 * @param state - Connection state
 * @returns Formatted status object
 */
export const formatConnectionStatus = (state: string) => {
  const statusMap = {
    connecting: { text: 'Connecting...', color: 'warning', icon: 'sync' },
    connected: { text: 'Connected', color: 'success', icon: 'check_circle' },
    closing: { text: 'Disconnecting...', color: 'warning', icon: 'sync' },
    disconnected: { text: 'Disconnected', color: 'error', icon: 'error' },
    unknown: { text: 'Unknown', color: 'default', icon: 'help' },
  };

  return statusMap[state as keyof typeof statusMap] || statusMap.unknown;
};
