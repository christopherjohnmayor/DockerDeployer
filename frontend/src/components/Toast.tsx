import React, { createContext, useContext, useState, ReactNode } from 'react';
import {
  Snackbar,
  Alert,
  AlertColor,
  Slide,
  SlideProps,
} from '@mui/material';

interface Toast {
  id: string;
  message: string;
  severity: AlertColor;
  duration?: number;
}

interface ToastContextType {
  showToast: (message: string, severity?: AlertColor, duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="up" />;
}

/**
 * Toast Provider component for global toast notifications
 * 
 * Features:
 * - Multiple toast types (success, error, warning, info)
 * - Auto-dismiss with configurable duration
 * - Queue management for multiple toasts
 * - Smooth slide animations
 * - Accessible notifications
 */
export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (
    message: string, 
    severity: AlertColor = 'info', 
    duration: number = 6000
  ) => {
    const id = Date.now().toString();
    const newToast: Toast = { id, message, severity, duration };
    
    setToasts(prev => [...prev, newToast]);
  };

  const showSuccess = (message: string, duration?: number) => {
    showToast(message, 'success', duration);
  };

  const showError = (message: string, duration?: number) => {
    showToast(message, 'error', duration || 8000); // Longer duration for errors
  };

  const showWarning = (message: string, duration?: number) => {
    showToast(message, 'warning', duration);
  };

  const showInfo = (message: string, duration?: number) => {
    showToast(message, 'info', duration);
  };

  const handleClose = (toastId: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== toastId));
  };

  const contextValue: ToastContextType = {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      
      {/* Render all toasts */}
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          autoHideDuration={toast.duration}
          onClose={() => handleClose(toast.id)}
          TransitionComponent={SlideTransition}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{
            // Stack multiple toasts
            bottom: `${(index * 70) + 24}px !important`,
          }}
        >
          <Alert
            onClose={() => handleClose(toast.id)}
            severity={toast.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {toast.message}
          </Alert>
        </Snackbar>
      ))}
    </ToastContext.Provider>
  );
};

/**
 * Hook to use toast notifications
 * 
 * @returns Toast context with notification methods
 * @throws Error if used outside ToastProvider
 */
export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export default ToastProvider;
