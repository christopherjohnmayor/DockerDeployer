import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';
import { MemoryRouter } from 'react-router-dom';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ToastProvider } from '../components/Toast';
import { AuthContext } from '../contexts/AuthContext';

// Create a default theme for testing
const theme = createTheme();

// Default mock auth context
export const mockAuthContext = {
  isAuthenticated: false,
  user: null,
  login: jest.fn(),
  logout: jest.fn(),
  refreshAuth: jest.fn(),
  loading: false,
  error: null,
};

// Mock admin auth context
export const mockAdminAuthContext = {
  isAuthenticated: true,
  user: { id: 1, username: 'admin', role: 'admin' },
  login: jest.fn(),
  logout: jest.fn(),
  refreshAuth: jest.fn(),
  loading: false,
  error: null,
};

// Mock regular user auth context
export const mockUserAuthContext = {
  isAuthenticated: true,
  user: { id: 2, username: 'user', role: 'user' },
  login: jest.fn(),
  logout: jest.fn(),
  refreshAuth: jest.fn(),
  loading: false,
  error: null,
};

interface AllTheProvidersProps {
  children: React.ReactNode;
  authContext?: typeof mockAuthContext;
  initialRoute?: string;
}

// Comprehensive provider wrapper for tests
const AllTheProviders: React.FC<AllTheProvidersProps> = ({ 
  children, 
  authContext = mockAuthContext,
  initialRoute = '/'
}) => {
  return (
    <MemoryRouter initialEntries={[initialRoute]}>
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <AuthContext.Provider value={authContext}>
            <ToastProvider>
              {children}
            </ToastProvider>
          </AuthContext.Provider>
        </LocalizationProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
};

// Custom render function with all providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    authContext?: typeof mockAuthContext;
    initialRoute?: string;
  }
) => {
  const { authContext, initialRoute, ...renderOptions } = options || {};
  
  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders authContext={authContext} initialRoute={initialRoute}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  });
};

// Render with theme only (for simpler components)
export const renderWithTheme = (component: ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

// Render with providers (comprehensive)
export const renderWithProviders = customRender;

// Render with auth context
export const renderWithAuth = (
  component: ReactElement,
  authContext = mockAuthContext
) => {
  return render(
    <ThemeProvider theme={theme}>
      <AuthContext.Provider value={authContext}>
        <ToastProvider>
          {component}
        </ToastProvider>
      </AuthContext.Provider>
    </ThemeProvider>
  );
};

// Render with router
export const renderWithRouter = (
  component: ReactElement,
  initialRoute = '/'
) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <ThemeProvider theme={theme}>
        {component}
      </ThemeProvider>
    </MemoryRouter>
  );
};

// Render with date picker provider
export const renderWithDatePicker = (component: ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        {component}
      </LocalizationProvider>
    </ThemeProvider>
  );
};

// Export everything needed for tests
export * from '@testing-library/react';
export { theme, mockAuthContext, mockAdminAuthContext, mockUserAuthContext };

// Re-export render as the default
export { customRender as render };
