import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import Templates from './Templates';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Templates Component', () => {
  const mockTemplates = [
    {
      name: 'lemp',
      description: 'Linux, Nginx, MySQL, and PHP stack',
      version: '1.0.0',
      category: 'web',
      complexity: 'medium',
      tags: ['web', 'nginx', 'mysql', 'php']
    },
    {
      name: 'mean',
      description: 'MongoDB, Express, Angular, and Node.js stack',
      version: '1.0.0',
      category: 'web',
      complexity: 'medium',
      tags: ['web', 'mongodb', 'express', 'angular', 'node']
    },
    {
      name: 'wordpress',
      description: 'WordPress with MySQL',
      version: '1.0.0',
      category: 'cms',
      complexity: 'simple',
      tags: ['cms', 'wordpress', 'mysql']
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock successful templates fetch
    mockedAxios.get.mockResolvedValue({ data: mockTemplates });
    
    // Mock successful template deployment
    mockedAxios.post.mockResolvedValue({
      data: { template: 'lemp', status: 'deployed' }
    });
  });

  test('renders templates list correctly', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Check if all templates are displayed
    expect(screen.getByText('lemp')).toBeInTheDocument();
    expect(screen.getByText('mean')).toBeInTheDocument();
    expect(screen.getByText('wordpress')).toBeInTheDocument();
    
    // Check if template descriptions are displayed
    expect(screen.getByText('Linux, Nginx, MySQL, and PHP stack')).toBeInTheDocument();
    expect(screen.getByText('MongoDB, Express, Angular, and Node.js stack')).toBeInTheDocument();
    expect(screen.getByText('WordPress with MySQL')).toBeInTheDocument();
  });

  test('filters templates by search term', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Get the search input and type in it
    const searchInput = screen.getByPlaceholderText('Search templates...');
    await userEvent.type(searchInput, 'mysql');
    
    // Check if only templates with MySQL are displayed
    expect(screen.getByText('lemp')).toBeInTheDocument();
    expect(screen.getByText('wordpress')).toBeInTheDocument();
    expect(screen.queryByText('mean')).not.toBeInTheDocument();
  });

  test('filters templates by category', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Open the category dropdown
    const categorySelect = screen.getByLabelText('Category');
    fireEvent.mouseDown(categorySelect);
    
    // Select the CMS category
    const cmsOption = screen.getByText('Content Management');
    fireEvent.click(cmsOption);
    
    // Check if only CMS templates are displayed
    expect(screen.queryByText('lemp')).not.toBeInTheDocument();
    expect(screen.queryByText('mean')).not.toBeInTheDocument();
    expect(screen.getByText('wordpress')).toBeInTheDocument();
  });

  test('filters templates by complexity', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Open the complexity dropdown
    const complexitySelect = screen.getByLabelText('Complexity');
    fireEvent.mouseDown(complexitySelect);
    
    // Select the Simple complexity
    const simpleOption = screen.getByText('Simple');
    fireEvent.click(simpleOption);
    
    // Check if only Simple templates are displayed
    expect(screen.queryByText('lemp')).not.toBeInTheDocument();
    expect(screen.queryByText('mean')).not.toBeInTheDocument();
    expect(screen.getByText('wordpress')).toBeInTheDocument();
  });

  test('deploys a template when deploy button is clicked', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Find and click the deploy button for the LEMP stack
    const deployButtons = screen.getAllByText('Deploy');
    const lempDeployButton = deployButtons[0]; // Assuming LEMP is the first template
    fireEvent.click(lempDeployButton);
    
    // Check if the API was called correctly
    expect(mockedAxios.post).toHaveBeenCalledWith('/templates/deploy', {
      template_name: 'lemp'
    });
    
    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText(/Template "lemp" deployed successfully!/)).toBeInTheDocument();
    });
  });

  test('shows template details when details button is clicked', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Find and click the details button for the LEMP stack
    const detailsButtons = screen.getAllByText('Details');
    const lempDetailsButton = detailsButtons[0]; // Assuming LEMP is the first template
    fireEvent.click(lempDetailsButton);
    
    // Check if the details dialog is displayed
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
    
    // Check if template details are displayed
    expect(screen.getByText('Linux, Nginx, MySQL, and PHP stack')).toBeInTheDocument();
    expect(screen.getByText('Tags')).toBeInTheDocument();
    
    // Close the dialog
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    // Check if the dialog is closed
    await waitFor(() => {
      expect(screen.queryByText('Overview')).not.toBeInTheDocument();
    });
  });

  test('customizes template deployment', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Find and click the details button for the LEMP stack
    const detailsButtons = screen.getAllByText('Details');
    const lempDetailsButton = detailsButtons[0]; // Assuming LEMP is the first template
    fireEvent.click(lempDetailsButton);
    
    // Click on the Configuration tab
    const configTab = screen.getByText('Configuration');
    fireEvent.click(configTab);
    
    // Customize the stack name
    const stackNameInput = screen.getByLabelText('Stack Name');
    await userEvent.clear(stackNameInput);
    await userEvent.type(stackNameInput, 'my-custom-lemp');
    
    // Select the environment
    const environmentSelect = screen.getByLabelText('Environment');
    fireEvent.mouseDown(environmentSelect);
    const productionOption = screen.getByText('Production');
    fireEvent.click(productionOption);
    
    // Deploy the customized template
    const deployButton = screen.getByText('Deploy Stack');
    fireEvent.click(deployButton);
    
    // Check if the API was called with customizations
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/templates/deploy', {
        template_name: 'lemp',
        customizations: {
          stackName: 'my-custom-lemp',
          environment: 'production'
        }
      });
    });
  });

  test('displays error message when templates fetch fails', async () => {
    // Mock failed templates fetch
    mockedAxios.get.mockRejectedValueOnce({
      response: { data: { detail: 'Failed to fetch templates' } }
    });
    
    render(<Templates />);
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch templates')).toBeInTheDocument();
    });
  });

  test('displays message when no templates match filters', async () => {
    render(<Templates />);
    
    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Stack Templates')).toBeInTheDocument();
    });
    
    // Search for a non-existent template
    const searchInput = screen.getByPlaceholderText('Search templates...');
    await userEvent.type(searchInput, 'nonexistent');
    
    // Check if no results message is displayed
    expect(screen.getByText('No templates match your search criteria.')).toBeInTheDocument();
  });
});
