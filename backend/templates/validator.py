"""
Template validation module for DockerDeployer.
This module provides functions to validate stack templates and their variables.
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


class TemplateValidationError(Exception):
    """Exception raised when a template validation fails."""

    pass


def validate_template_structure(
    template_data: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate the basic structure of a template.

    Args:
        template_data: The template data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["name", "description", "version", "services"]
    for field in required_fields:
        if field not in template_data:
            return False, f"Missing required field: {field}"

    # Check services
    services = template_data.get("services", {})
    if not isinstance(services, dict) or not services:
        return False, "Services must be a non-empty dictionary"

    # Check variables if present
    variables = template_data.get("variables", {})
    if variables and not isinstance(variables, dict):
        return False, "Variables must be a dictionary"

    # Check files if present
    files = template_data.get("files", [])
    if files and not isinstance(files, list):
        return False, "Files must be a list"

    return True, None


def validate_variables(template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the variables section of a template.

    Args:
        template_data: The template data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    variables = template_data.get("variables", {})
    if not variables:
        return True, None  # No variables to validate

    for var_name, var_config in variables.items():
        # Check variable name format
        if not re.match(r"^[A-Z][A-Z0-9_]*$", var_name):
            return (
                False,
                f"Invalid variable name format: {var_name}. Must be uppercase with underscores.",
            )

        # Check variable configuration
        if not isinstance(var_config, dict):
            return False, f"Variable configuration for {var_name} must be a dictionary"

        # Check required fields for each variable
        if "description" not in var_config:
            return False, f"Missing description for variable: {var_name}"

        # Check default value
        if "default" not in var_config and var_config.get("required", False):
            return False, f"Required variable {var_name} must have a default value"

        # Check options if present
        options = var_config.get("options", [])
        if options:
            if not isinstance(options, list) or not options:
                return (
                    False,
                    f"Options for variable {var_name} must be a non-empty list",
                )

            default = var_config.get("default")
            if default is not None and str(default) not in [
                str(opt) for opt in options
            ]:
                return False, f"Default value for {var_name} must be one of the options"

    return True, None


def validate_services(template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the services section of a template.

    Args:
        template_data: The template data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    services = template_data.get("services", {})
    if not services:
        return False, "No services defined in template"

    for service_name, service_config in services.items():
        # Check service name format
        if not re.match(r"^[a-z][a-z0-9_\-]*$", service_name):
            return (
                False,
                f"Invalid service name: {service_name}. Use lowercase letters, numbers, hyphens, and underscores.",
            )

        # Check service configuration
        if not isinstance(service_config, dict):
            return (
                False,
                f"Service configuration for {service_name} must be a dictionary",
            )

        # Check if service has image or build
        if "image" not in service_config and "build" not in service_config:
            return (
                False,
                f"Service {service_name} must have either 'image' or 'build' defined",
            )

        # Check variable references in service configuration
        for key, value in service_config.items():
            if isinstance(value, str):
                var_refs = re.findall(r"\${([A-Z][A-Z0-9_]*)}", value)
                for var_ref in var_refs:
                    if var_ref not in template_data.get("variables", {}):
                        return (
                            False,
                            f"Service {service_name} references undefined variable: {var_ref}",
                        )

    return True, None


def validate_files(template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate the files section of a template.

    Args:
        template_data: The template data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    files = template_data.get("files", [])
    if not files:
        return True, None  # No files to validate

    for file_entry in files:
        # Check file entry structure
        if not isinstance(file_entry, dict):
            return False, "File entry must be a dictionary"

        # Check required fields
        if "path" not in file_entry:
            return False, "File entry missing required field: path"
        if "content" not in file_entry:
            return False, "File entry missing required field: content"

        # Check path format
        path = file_entry["path"]
        if not isinstance(path, str) or not path:
            return False, "File path must be a non-empty string"

        # Check for path traversal vulnerabilities
        if ".." in path or path.startswith("/"):
            return (
                False,
                f"Invalid file path: {path}. Path cannot contain '..' or start with '/'",
            )

        # Check content
        content = file_entry["content"]
        if not isinstance(content, str):
            return False, f"File content for {path} must be a string"

        # Check variable references in content
        var_refs = re.findall(r"\${([A-Z][A-Z0-9_]*)}", content)
        for var_ref in var_refs:
            if var_ref not in template_data.get("variables", {}):
                return False, f"File {path} references undefined variable: {var_ref}"

    return True, None


def validate_template(template_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a complete template.

    Args:
        template_data: The template data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate basic structure
    is_valid, error = validate_template_structure(template_data)
    if not is_valid:
        return False, error

    # Validate variables
    is_valid, error = validate_variables(template_data)
    if not is_valid:
        return False, error

    # Validate services
    is_valid, error = validate_services(template_data)
    if not is_valid:
        return False, error

    # Validate files
    is_valid, error = validate_files(template_data)
    if not is_valid:
        return False, error

    return True, None


def validate_template_file(template_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a template file.

    Args:
        template_path: Path to the template file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        return validate_template(template_data)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {str(e)}"
    except Exception as e:
        return False, f"Error validating template: {str(e)}"


def validate_variable_values(
    template_data: Dict[str, Any], variable_values: Dict[str, Any]
) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate user-provided values for template variables.

    Args:
        template_data: The template data
        variable_values: User-provided values for variables

    Returns:
        Tuple of (is_valid, error_message, processed_values)
    """
    variables = template_data.get("variables", {})
    processed_values = {}

    # Check all required variables
    for var_name, var_config in variables.items():
        if var_name not in variable_values:
            # If variable is not provided, use default if available
            if "default" in var_config:
                processed_values[var_name] = var_config["default"]
            elif var_config.get("required", False):
                return False, f"Missing required variable: {var_name}", {}
        else:
            value = variable_values[var_name]

            # Check against options if defined
            options = var_config.get("options", [])
            if options and str(value) not in [str(opt) for opt in options]:
                return (
                    False,
                    f"Value for {var_name} must be one of: {', '.join(map(str, options))}",
                    {},
                )

            processed_values[var_name] = value

    # Add any missing variables with default values
    for var_name, var_config in variables.items():
        if var_name not in processed_values and "default" in var_config:
            processed_values[var_name] = var_config["default"]

    return True, None, processed_values
