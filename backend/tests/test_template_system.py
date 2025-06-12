"""
Tests for the template system (loader and validator).
"""

import os
from unittest.mock import mock_open, patch

import pytest
import yaml

from backend.templates.loader import list_templates, load_template
from backend.templates.validator import (
    validate_files,
    validate_services,
    validate_template,
    validate_template_file,
    validate_template_structure,
    validate_variable_values,
    validate_variables,
)


class TestTemplateLoader:
    """Test suite for template loader functions."""

    @patch("os.listdir")
    @patch("os.path.isdir")
    def test_list_templates_empty(self, mock_isdir, mock_listdir):
        """Test listing templates when none exist."""
        mock_listdir.return_value = []
        mock_isdir.return_value = True

        templates = list_templates()

        assert templates == []
        mock_listdir.assert_called_once()

    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.exists")
    @patch("backend.templates.loader.load_template_metadata")
    def test_list_templates(
        self, mock_load_metadata, mock_exists, mock_isdir, mock_listdir
    ):
        """Test listing templates."""
        mock_listdir.return_value = ["lemp", "mean", "wordpress"]
        mock_isdir.return_value = True
        mock_exists.return_value = True  # template.yaml exists

        # Mock template metadata
        mock_load_metadata.side_effect = [
            {"name": "lemp", "description": "LEMP Stack", "version": "1.0.0"},
            {"name": "mean", "description": "MEAN Stack", "version": "1.0.0"},
            {"name": "wordpress", "description": "WordPress", "version": "1.0.0"},
        ]

        templates = list_templates()

        assert len(templates) == 3
        assert templates[0]["name"] == "lemp"
        assert templates[1]["name"] == "mean"
        assert templates[2]["name"] == "wordpress"

        assert mock_load_metadata.call_count == 3

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_template_success(self, mock_yaml_load, mock_file_open, mock_exists):
        """Test loading a template successfully."""
        mock_exists.return_value = True

        # Mock YAML data
        mock_yaml_data = {
            "description": "LEMP Stack",
            "version": "1.0.0",
            "services": {
                "nginx": {"image": "nginx:latest"},
                "php": {"image": "php:8.0-fpm"},
                "mysql": {"image": "mysql:8.0"},
            },
        }
        mock_yaml_load.return_value = mock_yaml_data

        template = load_template("lemp")

        # The function adds name and path to the template
        expected_template = {**mock_yaml_data, "name": "lemp"}
        expected_template[
            "path"
        ] = "/Volumes/2TB/Projects/DockerDeployer/templates/lemp"

        assert template["name"] == "lemp"
        assert template["description"] == "LEMP Stack"
        assert template["version"] == "1.0.0"
        assert "path" in template

        # exists is called twice: once for directory, once for template.yaml
        assert mock_exists.call_count == 2
        mock_file_open.assert_called_once()
        mock_yaml_load.assert_called_once()

    @patch("os.path.exists")
    def test_load_template_not_found(self, mock_exists):
        """Test loading a non-existent template."""
        mock_exists.return_value = False

        template = load_template("nonexistent")

        assert template is None
        mock_exists.assert_called_once()

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_template_invalid_yaml(
        self, mock_yaml_load, mock_file_open, mock_exists
    ):
        """Test loading a template with invalid YAML."""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        template = load_template("invalid")

        assert template is None
        # exists is called twice: once for directory, once for template.yaml
        assert mock_exists.call_count == 2
        mock_file_open.assert_called_once()
        mock_yaml_load.assert_called_once()


class TestTemplateValidator:
    """Test suite for template validator functions."""

    def test_validate_template_structure_valid(self):
        """Test validating a template with valid structure."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {"web": {"image": "nginx"}},
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_template_structure_missing_required(self):
        """Test validating a template with missing required fields."""
        template_data = {
            "name": "test",
            "description": "Test template"
            # Missing version and services
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is False
        assert "Missing required field" in error

    def test_validate_template_structure_empty_services(self):
        """Test validating a template with empty services."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {},
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is False
        assert "Services must be a non-empty dictionary" in error

    def test_validate_variables_valid(self):
        """Test validating valid variables."""
        template_data = {
            "variables": {
                "PROJECT_NAME": {
                    "description": "Project name",
                    "default": "test-project",
                },
                "PHP_VERSION": {
                    "description": "PHP version",
                    "default": "8.0",
                    "options": ["7.4", "8.0", "8.1"],
                },
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_variables_invalid_name(self):
        """Test validating variables with invalid name format."""
        template_data = {
            "variables": {
                "project_name": {  # Should be uppercase
                    "description": "Project name",
                    "default": "test-project",
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "Invalid variable name format" in error

    def test_validate_variables_missing_description(self):
        """Test validating variables with missing description."""
        template_data = {
            "variables": {
                "PROJECT_NAME": {
                    "default": "test-project"
                    # Missing description
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "Missing description" in error

    def test_validate_variables_invalid_default(self):
        """Test validating variables with invalid default value."""
        template_data = {
            "variables": {
                "PHP_VERSION": {
                    "description": "PHP version",
                    "default": "8.2",  # Not in options
                    "options": ["7.4", "8.0", "8.1"],
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "Default value" in error
        assert "must be one of the options" in error

    def test_validate_services_valid(self):
        """Test validating valid services."""
        template_data = {
            "services": {
                "web": {"image": "nginx:latest", "ports": ["80:80"]},
                "db": {
                    "image": "mysql:8.0",
                    "environment": {"MYSQL_ROOT_PASSWORD": "${MYSQL_PASSWORD}"},
                },
            },
            "variables": {
                "MYSQL_PASSWORD": {
                    "description": "MySQL password",
                    "default": "password",
                }
            },
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_services_invalid_name(self):
        """Test validating services with invalid name."""
        template_data = {
            "services": {
                "Web-Server": {  # Invalid name (uppercase and hyphen)
                    "image": "nginx:latest"
                }
            }
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is False
        assert "Invalid service name" in error

    def test_validate_services_missing_image(self):
        """Test validating services with missing image or build."""
        template_data = {
            "services": {
                "web": {
                    "ports": ["80:80"]
                    # Missing image or build
                }
            }
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is False
        assert "must have either 'image' or 'build'" in error

    def test_validate_services_undefined_variable(self):
        """Test validating services with undefined variable reference."""
        template_data = {
            "services": {
                "db": {
                    "image": "mysql:8.0",
                    "environment": {"MYSQL_ROOT_PASSWORD": "${MYSQL_PASSWORD}"},
                }
            }
            # Missing variables section
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is False
        assert "references undefined variable" in error

    def test_validate_files_valid(self):
        """Test validating valid files section."""
        template_data = {
            "files": [
                {"path": "nginx/default.conf", "content": "server { listen 80; }"},
                {
                    "path": "php/custom.ini",
                    "content": "memory_limit = ${PHP_MEMORY_LIMIT}",
                },
            ],
            "variables": {
                "PHP_MEMORY_LIMIT": {
                    "description": "PHP memory limit",
                    "default": "128M",
                }
            },
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_files_missing_path(self):
        """Test validating files with missing path."""
        template_data = {
            "files": [
                {
                    # Missing path
                    "content": "server { listen 80; }"
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "missing required field: path" in error.lower()

    def test_validate_files_invalid_path(self):
        """Test validating files with invalid path."""
        template_data = {
            "files": [
                {
                    "path": "../etc/passwd",  # Path traversal attempt
                    "content": "malicious content",
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "Invalid file path" in error

    def test_validate_files_undefined_variable(self):
        """Test validating files with undefined variable reference."""
        template_data = {
            "files": [
                {"path": "config.ini", "content": "value = ${UNDEFINED_VARIABLE}"}
            ]
            # Missing variables section
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "references undefined variable" in error

    def test_validate_template_valid(self):
        """Test validating a complete valid template."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {
                "web": {"image": "nginx:${NGINX_VERSION}", "ports": ["${WEB_PORT}:80"]}
            },
            "variables": {
                "NGINX_VERSION": {"description": "Nginx version", "default": "latest"},
                "WEB_PORT": {"description": "Web port", "default": "80"},
            },
        }

        is_valid, error = validate_template(template_data)

        assert is_valid is True
        assert error is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_validate_template_file(self, mock_yaml_load, mock_file_open):
        """Test validating a template file."""
        # Mock YAML data
        mock_yaml_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {"web": {"image": "nginx"}},
        }
        mock_yaml_load.return_value = mock_yaml_data

        is_valid, error = validate_template_file("test_template.yaml")

        assert is_valid is True
        assert error is None
        mock_file_open.assert_called_once_with("test_template.yaml", "r")
        mock_yaml_load.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_validate_template_file_invalid_yaml(self, mock_yaml_load, mock_file_open):
        """Test validating a template file with invalid YAML."""
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        is_valid, error = validate_template_file("invalid.yaml")

        assert is_valid is False
        assert "Invalid YAML" in error
        mock_file_open.assert_called_once_with("invalid.yaml", "r")
        mock_yaml_load.assert_called_once()

    def test_validate_variable_values_valid(self):
        """Test validating valid variable values."""
        template_data = {
            "variables": {
                "PROJECT_NAME": {
                    "description": "Project name",
                    "default": "test-project",
                },
                "PHP_VERSION": {
                    "description": "PHP version",
                    "default": "8.0",
                    "options": ["7.4", "8.0", "8.1"],
                },
            }
        }

        variable_values = {"PROJECT_NAME": "my-project", "PHP_VERSION": "8.1"}

        is_valid, error, processed = validate_variable_values(
            template_data, variable_values
        )

        assert is_valid is True
        assert error is None
        assert processed["PROJECT_NAME"] == "my-project"
        assert processed["PHP_VERSION"] == "8.1"

    def test_validate_variable_values_missing_required(self):
        """Test validating variable values with missing required value."""
        template_data = {
            "variables": {
                "API_KEY": {
                    "description": "API Key",
                    "required": True
                    # No default value
                }
            }
        }

        variable_values = {}  # Missing API_KEY

        is_valid, error, processed = validate_variable_values(
            template_data, variable_values
        )

        assert is_valid is False
        assert "Missing required variable" in error
        assert processed == {}

    def test_validate_variable_values_invalid_option(self):
        """Test validating variable values with invalid option."""
        template_data = {
            "variables": {
                "PHP_VERSION": {
                    "description": "PHP version",
                    "default": "8.0",
                    "options": ["7.4", "8.0", "8.1"],
                }
            }
        }

        variable_values = {"PHP_VERSION": "8.2"}  # Not in options

        is_valid, error, processed = validate_variable_values(
            template_data, variable_values
        )

        assert is_valid is False
        assert "must be one of" in error
        assert processed == {}

    def test_validate_variable_values_with_defaults(self):
        """Test validating variable values using defaults."""
        template_data = {
            "variables": {
                "PROJECT_NAME": {
                    "description": "Project name",
                    "default": "default-project",
                },
                "DEBUG_MODE": {
                    "description": "Debug mode",
                    "default": "false",
                },
            }
        }

        variable_values = {"PROJECT_NAME": "my-project"}  # DEBUG_MODE not provided

        is_valid, error, processed = validate_variable_values(
            template_data, variable_values
        )

        assert is_valid is True
        assert error is None
        assert processed["PROJECT_NAME"] == "my-project"
        assert processed["DEBUG_MODE"] == "false"  # Default value used

    def test_validate_template_structure_invalid_services_type(self):
        """Test validating template structure with invalid services type."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": "invalid",  # Should be dict
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is False
        assert "Services must be a non-empty dictionary" in error

    def test_validate_template_structure_invalid_variables_type(self):
        """Test validating template structure with invalid variables type."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {"web": {"image": "nginx"}},
            "variables": "invalid",  # Should be dict
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is False
        assert "Variables must be a dictionary" in error

    def test_validate_template_structure_invalid_files_type(self):
        """Test validating template structure with invalid files type."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {"web": {"image": "nginx"}},
            "files": "invalid",  # Should be list
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is False
        assert "Files must be a list" in error

    def test_validate_variables_no_variables(self):
        """Test validating template with no variables section."""
        template_data = {}  # No variables

        is_valid, error = validate_variables(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_variables_invalid_config_type(self):
        """Test validating variables with invalid configuration type."""
        template_data = {
            "variables": {
                "PROJECT_NAME": "invalid"  # Should be dict
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "must be a dictionary" in error

    def test_validate_variables_required_without_default(self):
        """Test validating required variable without default value."""
        template_data = {
            "variables": {
                "API_KEY": {
                    "description": "API Key",
                    "required": True
                    # No default value
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "Required variable" in error
        assert "must have a default value" in error

    def test_validate_variables_empty_options(self):
        """Test validating variables with empty options list."""
        template_data = {
            "variables": {
                "VERSION": {
                    "description": "Version",
                    "default": "1.0",
                    "options": []  # Empty options - this is actually valid (ignored)
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        # Empty options list is valid (ignored by validation logic)
        assert is_valid is True
        assert error is None

    def test_validate_variables_invalid_options_with_content(self):
        """Test validating variables with invalid options that have content."""
        template_data = {
            "variables": {
                "VERSION": {
                    "description": "Version",
                    "default": "2.0",  # Default not in options
                    "options": ["1.0", "1.5"]  # Valid options but default not included
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        # This should fail since default is not in options
        assert is_valid is False
        assert "not in options" in error

    def test_validate_variables_invalid_options_type(self):
        """Test validating variables with invalid options type."""
        template_data = {
            "variables": {
                "VERSION": {
                    "description": "Version",
                    "default": "1.0",
                    "options": "invalid"  # Should be list
                }
            }
        }

        is_valid, error = validate_variables(template_data)

        assert is_valid is False
        assert "must be a non-empty list" in error

    def test_validate_services_no_services(self):
        """Test validating template with no services."""
        template_data = {}  # No services

        is_valid, error = validate_services(template_data)

        assert is_valid is False
        assert "No services defined" in error

    def test_validate_services_invalid_config_type(self):
        """Test validating services with invalid configuration type."""
        template_data = {
            "services": {
                "web": "invalid"  # Should be dict
            }
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is False
        assert "must be a dictionary" in error

    def test_validate_services_with_build(self):
        """Test validating services with build instead of image."""
        template_data = {
            "services": {
                "web": {
                    "build": "./docker/web",
                    "ports": ["80:80"]
                }
            }
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_services_nested_variable_references(self):
        """Test validating services with nested variable references."""
        template_data = {
            "services": {
                "web": {
                    "image": "nginx:${NGINX_VERSION}",
                    "environment": {
                        "API_URL": "https://${DOMAIN}:${PORT}/api",
                        "CONFIG": {
                            "database": {
                                "host": "${DB_HOST}",
                                "port": "${DB_PORT}"
                            }
                        }
                    },
                    "volumes": ["${DATA_DIR}:/data"]
                }
            },
            "variables": {
                "NGINX_VERSION": {"description": "Nginx version", "default": "latest"},
                "DOMAIN": {"description": "Domain", "default": "localhost"},
                "PORT": {"description": "Port", "default": "443"},
                "DB_HOST": {"description": "DB host", "default": "localhost"},
                "DB_PORT": {"description": "DB port", "default": "5432"},
                "DATA_DIR": {"description": "Data directory", "default": "./data"}
            }
        }

        is_valid, error = validate_services(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_files_no_files(self):
        """Test validating template with no files section."""
        template_data = {}  # No files

        is_valid, error = validate_files(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_files_invalid_entry_type(self):
        """Test validating files with invalid entry type."""
        template_data = {
            "files": [
                "invalid"  # Should be dict
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "File entry must be a dictionary" in error

    def test_validate_files_missing_content(self):
        """Test validating files with missing content."""
        template_data = {
            "files": [
                {
                    "path": "config.txt"
                    # Missing content
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "missing required field: content" in error.lower()

    def test_validate_files_empty_path(self):
        """Test validating files with empty path."""
        template_data = {
            "files": [
                {
                    "path": "",  # Empty path
                    "content": "test content"
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "must be a non-empty string" in error

    def test_validate_files_invalid_path_type(self):
        """Test validating files with invalid path type."""
        template_data = {
            "files": [
                {
                    "path": 123,  # Should be string
                    "content": "test content"
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "must be a non-empty string" in error

    def test_validate_files_invalid_content_type(self):
        """Test validating files with invalid content type."""
        template_data = {
            "files": [
                {
                    "path": "config.txt",
                    "content": 123  # Should be string
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "must be a string" in error

    def test_validate_files_absolute_path(self):
        """Test validating files with absolute path."""
        template_data = {
            "files": [
                {
                    "path": "/etc/passwd",  # Absolute path
                    "content": "malicious content"
                }
            ]
        }

        is_valid, error = validate_files(template_data)

        assert is_valid is False
        assert "Invalid file path" in error
        assert "cannot contain '..' or start with '/'" in error

    def test_validate_template_file_read_error(self):
        """Test validating template file with read error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            is_valid, error = validate_template_file("unreadable.yaml")

            assert is_valid is False
            assert "Error validating template" in error

    def test_validate_template_comprehensive_valid(self):
        """Test validating a comprehensive valid template."""
        template_data = {
            "name": "comprehensive-test",
            "description": "Comprehensive test template",
            "version": "2.0.0",
            "services": {
                "web": {
                    "image": "nginx:${NGINX_VERSION}",
                    "ports": ["${WEB_PORT}:80"],
                    "environment": {
                        "API_URL": "https://${DOMAIN}/api"
                    },
                    "volumes": ["${CONFIG_DIR}/nginx.conf:/etc/nginx/nginx.conf"]
                },
                "api": {
                    "build": "./api",
                    "environment": {
                        "DATABASE_URL": "postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}"
                    },
                    "depends_on": ["db"]
                },
                "db": {
                    "image": "postgres:${POSTGRES_VERSION}",
                    "environment": {
                        "POSTGRES_DB": "${DB_NAME}",
                        "POSTGRES_USER": "${DB_USER}",
                        "POSTGRES_PASSWORD": "${DB_PASSWORD}"
                    },
                    "volumes": ["${DATA_DIR}:/var/lib/postgresql/data"]
                }
            },
            "variables": {
                "NGINX_VERSION": {
                    "description": "Nginx version",
                    "default": "latest",
                    "options": ["latest", "1.20", "1.21"]
                },
                "POSTGRES_VERSION": {
                    "description": "PostgreSQL version",
                    "default": "13",
                    "options": ["11", "12", "13", "14"]
                },
                "WEB_PORT": {
                    "description": "Web server port",
                    "default": "80"
                },
                "DOMAIN": {
                    "description": "Domain name",
                    "default": "localhost"
                },
                "DB_NAME": {
                    "description": "Database name",
                    "default": "myapp"
                },
                "DB_USER": {
                    "description": "Database user",
                    "default": "postgres"
                },
                "DB_PASSWORD": {
                    "description": "Database password",
                    "default": "password"
                },
                "CONFIG_DIR": {
                    "description": "Configuration directory",
                    "default": "./config"
                },
                "DATA_DIR": {
                    "description": "Data directory",
                    "default": "./data"
                }
            },
            "files": [
                {
                    "path": "config/nginx.conf",
                    "content": "server {\n    listen 80;\n    server_name ${DOMAIN};\n}"
                },
                {
                    "path": "config/app.env",
                    "content": "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}\nDOMAIN=${DOMAIN}"
                }
            ]
        }

        is_valid, error = validate_template(template_data)

        assert is_valid is True
        assert error is None

    def test_validate_template_comprehensive_invalid(self):
        """Test validating a comprehensive invalid template."""
        template_data = {
            "name": "invalid-test",
            "description": "Invalid test template",
            "version": "1.0.0",
            "services": {
                "web": {
                    "image": "nginx:${UNDEFINED_VERSION}",  # Undefined variable
                    "ports": ["80:80"]
                }
            },
            "variables": {
                "NGINX_VERSION": {
                    "description": "Nginx version",
                    "default": "latest"
                }
            }
        }

        is_valid, error = validate_template(template_data)

        assert is_valid is False
        assert "references undefined variable" in error

    def test_validate_variable_values_edge_cases(self):
        """Test validating variable values with edge cases."""
        template_data = {
            "variables": {
                "STRING_VAR": {
                    "description": "String variable",
                    "default": "default"
                },
                "NUMERIC_VAR": {
                    "description": "Numeric variable",
                    "default": "123",
                    "options": ["123", "456", "789"]
                },
                "BOOLEAN_VAR": {
                    "description": "Boolean variable",
                    "default": "true",
                    "options": ["true", "false"]
                }
            }
        }

        # Test with numeric values converted to strings
        variable_values = {
            "STRING_VAR": "custom",
            "NUMERIC_VAR": "456",  # String input matching options
            "BOOLEAN_VAR": "true"   # String input matching options
        }

        is_valid, error, processed = validate_variable_values(
            template_data, variable_values
        )

        assert is_valid is True
        assert error is None
        assert processed["STRING_VAR"] == "custom"
        assert processed["NUMERIC_VAR"] == "456"
        assert processed["BOOLEAN_VAR"] == "true"

    def test_validate_template_structure_with_optional_fields(self):
        """Test validating template structure with optional fields."""
        template_data = {
            "name": "test",
            "description": "Test template",
            "version": "1.0.0",
            "services": {"web": {"image": "nginx"}},
            "variables": {
                "TEST_VAR": {
                    "description": "Test variable",
                    "default": "test"
                }
            },
            "files": [
                {
                    "path": "test.txt",
                    "content": "test content"
                }
            ]
        }

        is_valid, error = validate_template_structure(template_data)

        assert is_valid is True
        assert error is None
