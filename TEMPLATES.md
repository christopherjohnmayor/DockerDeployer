# DockerDeployer Template System

## Overview

The DockerDeployer template system provides pre-configured Docker Compose stacks for common application deployments. Templates are designed to be easy to use while following Docker best practices and security standards.

## Template Format

Templates are defined in YAML format with the following structure:

```yaml
# Template metadata
name: "Template Name"
description: "Template description"
version: "1.0.0"
category: "web|database|utility|custom"
tags: ["tag1", "tag2"]

# Template variables with descriptions, defaults, and validation
variables:
  VARIABLE_NAME:
    description: "Variable description"
    default: "default value"
    required: true|false
    pattern: "regex pattern for validation" # Optional
    options: ["option1", "option2"] # Optional list of allowed values

# Docker Compose services definition
services:
  service1:
    image: "image:${VARIABLE_NAME}"
    # ... other Docker Compose service configuration
```

## Variable Substitution

Templates use variable substitution to customize deployments. Variables are referenced using the `${VARIABLE_NAME}` syntax in the template and are replaced with actual values during deployment.

### Variable Properties

- **description**: Human-readable description of the variable
- **default**: Default value if not provided by the user
- **required**: Whether the variable must be provided (if no default)
- **pattern**: Optional regex pattern for validation
- **options**: Optional list of allowed values

## Built-in Templates

DockerDeployer includes several built-in templates for common application stacks:

### LEMP Stack (Linux, Nginx, MySQL, PHP)

A popular web stack for PHP applications.

**Variables:**
- `PHP_VERSION`: PHP version (e.g., "8.1-fpm")
- `MYSQL_VERSION`: MySQL version (e.g., "8.0")
- `MYSQL_ROOT_PASSWORD`: Root password for MySQL
- `MYSQL_DATABASE`: Database name
- `MYSQL_USER`: Database user
- `MYSQL_PASSWORD`: Database password
- `WEB_PORT`: Web server port (default: "80")
- `PHPMYADMIN_PORT`: phpMyAdmin port (default: "8080")

### MEAN Stack (MongoDB, Express, Angular, Node.js)

A JavaScript stack for building dynamic web applications.

**Variables:**
- `MONGODB_VERSION`: MongoDB version (e.g., "6.0")
- `NODE_VERSION`: Node.js version (e.g., "18")
- `MONGODB_ROOT_USERNAME`: MongoDB root username
- `MONGODB_ROOT_PASSWORD`: MongoDB root password
- `MONGODB_DATABASE`: MongoDB database name
- `API_PORT`: API server port (default: "3000")
- `FRONTEND_PORT`: Frontend server port (default: "4200")

### WordPress

A ready-to-use WordPress installation with MySQL.

**Variables:**
- `WORDPRESS_VERSION`: WordPress version (e.g., "latest")
- `MYSQL_VERSION`: MySQL version (e.g., "8.0")
- `WORDPRESS_PORT`: WordPress port (default: "80")
- `MYSQL_ROOT_PASSWORD`: Root password for MySQL
- `MYSQL_DATABASE`: Database name (default: "wordpress")
- `MYSQL_USER`: Database user (default: "wordpress")
- `MYSQL_PASSWORD`: Database password
- `WORDPRESS_DEBUG`: Enable debug mode (default: "false")
- `ENABLE_REDIS_CACHE`: Enable Redis caching (default: "false")

## Using Templates

Templates can be deployed through:

1. **Web UI**: Navigate to the Templates section and select a template to deploy
2. **Natural Language**: Use commands like "Deploy a WordPress stack with MySQL 8.0"
3. **API**: Use the `/templates/deploy` endpoint with template name and variables

## Example: Deploying a Template

### Via Natural Language

```
Deploy a LEMP stack with PHP 8.1 and MySQL 8.0
```

### Via API

```json
POST /templates/deploy
{
  "template_name": "lemp",
  "overrides": {
    "PHP_VERSION": "8.1-fpm",
    "MYSQL_VERSION": "8.0",
    "MYSQL_ROOT_PASSWORD": "secure_password",
    "MYSQL_DATABASE": "myapp",
    "MYSQL_USER": "myuser",
    "MYSQL_PASSWORD": "mypassword",
    "WEB_PORT": "8080"
  }
}
```

## Creating Custom Templates

You can create custom templates by:

1. Creating a new YAML file in the `templates/` directory
2. Following the template format described above
3. Ensuring all required variables have descriptions and defaults where appropriate
4. Testing the template with various configurations

## Best Practices

- Use specific version tags for images instead of `latest`
- Set reasonable defaults for non-sensitive variables
- Never set defaults for passwords or sensitive information
- Use environment variables for configuration
- Mount volumes for persistent data
- Configure proper restart policies
- Use health checks for critical services
- Implement proper networking between services

## Template Validation

DockerDeployer validates templates before deployment to ensure:

- All required variables are provided
- Variable values match their patterns or options
- The template structure is valid
- The Docker Compose configuration is valid

## Troubleshooting

If a template deployment fails:

1. Check the logs for specific error messages
2. Verify all required variables are provided
3. Ensure port conflicts are resolved
4. Check that the Docker daemon is running
5. Verify network connectivity for image pulling

## Contributing Templates

To contribute a new template:

1. Create a new template following the format above
2. Test the template thoroughly
3. Submit a pull request with the template and documentation
4. Include example usage and variable descriptions
