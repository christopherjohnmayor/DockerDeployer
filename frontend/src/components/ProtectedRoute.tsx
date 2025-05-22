import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  // Check if user is authenticated
  if (!isAuthenticated) {
    // Redirect to login page and save the location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if a specific role is required
  if (requiredRole && user?.role !== requiredRole) {
    // User doesn't have the required role, redirect to unauthorized page
    return <Navigate to="/unauthorized" replace />;
  }

  // User is authenticated and has the required role (if any)
  return <>{children}</>;
};

export default ProtectedRoute;
