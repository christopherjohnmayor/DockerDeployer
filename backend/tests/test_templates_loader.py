"""
Tests for Templates Loader.
"""

import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from templates.loader import (
    TEMPLATES_DIR,
    list_templates,
    load_template,
    load_template_metadata,
)


class TestTemplatesLoader:
    """Test suite for Templates Loader."""

    def test_templates_dir_constant(self):
        """Test that TEMPLATES_DIR is correctly defined."""
        assert TEMPLATES_DIR is not None
        assert isinstance(TEMPLATES_DIR, str)
        assert "templates" in TEMPLATES_DIR

    @patch("templates.loader.os.path.exists")
    def test_list_templates_directory_not_found(self, mock_exists):
        """Test list_templates when templates directory doesn't exist."""
        # Setup mock
        mock_exists.return_value = False

        # Test
        with patch("builtins.print") as mock_print:
            result = list_templates()

        # Assertions
        assert len(result) == 3
        assert result[0]["name"] == "lemp"
        assert result[0]["title"] == "LEMP Stack"
        assert result[0]["category"] == "web"
        assert result[1]["name"] == "mean"
        assert result[2]["name"] == "wordpress"
        mock_print.assert_called_once()
        assert "Templates directory not found" in mock_print.call_args[0][0]

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.os.listdir")
    @patch("templates.loader.load_template_metadata")
    def test_list_templates_success(self, mock_load_metadata, mock_listdir, mock_exists):
        """Test successful template listing."""
        # Setup mocks
        mock_exists.side_effect = lambda path: True
        mock_listdir.return_value = ["lemp", "mean", "invalid_dir"]
        
        # Mock metadata loading
        def mock_metadata(name):
            if name == "lemp":
                return {
                    "name": "lemp",
                    "title": "LEMP Stack",
                    "description": "Linux, Nginx, MySQL, PHP",
                    "category": "web",
                    "complexity": "medium",
                    "tags": ["nginx", "mysql", "php"],
                    "version": "1.0"
                }
            elif name == "mean":
                return {
                    "name": "mean",
                    "title": "MEAN Stack",
                    "description": "MongoDB, Express, Angular, Node.js",
                    "category": "web",
                    "complexity": "medium",
                    "tags": ["mongodb", "express", "angular"],
                    "version": "1.0"
                }
            return None
        
        mock_load_metadata.side_effect = mock_metadata

        # Test
        result = list_templates()

        # Assertions
        assert len(result) == 2
        assert result[0]["name"] == "lemp"
        assert result[1]["name"] == "mean"
        mock_listdir.assert_called_once_with(TEMPLATES_DIR)

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.os.listdir")
    def test_list_templates_listdir_exception(self, mock_listdir, mock_exists):
        """Test list_templates when os.listdir raises exception."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.side_effect = PermissionError("Permission denied")

        # Test
        with patch("builtins.print") as mock_print:
            result = list_templates()

        # Assertions
        assert result == []
        mock_print.assert_called_once()
        assert "Error reading templates directory" in mock_print.call_args[0][0]

    @patch("templates.loader.os.path.exists")
    def test_load_template_metadata_file_not_found(self, mock_exists):
        """Test load_template_metadata when template.yaml doesn't exist."""
        # Setup mock
        mock_exists.return_value = False

        # Test
        result = load_template_metadata("nonexistent")

        # Assertions
        assert result is None
        mock_exists.assert_called_once()

    @patch("templates.loader.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("templates.loader.yaml.safe_load")
    def test_load_template_metadata_success(self, mock_yaml_load, mock_file, mock_exists):
        """Test successful template metadata loading."""
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_data = {
            "title": "LEMP Stack",
            "description": "Linux, Nginx, MySQL, PHP",
            "category": "web",
            "complexity": "medium",
            "tags": ["nginx", "mysql", "php"],
            "version": "1.0"
        }
        mock_yaml_load.return_value = mock_yaml_data

        # Test
        result = load_template_metadata("lemp")

        # Assertions
        assert result is not None
        assert result["name"] == "lemp"
        assert result["title"] == "LEMP Stack"
        assert result["category"] == "web"
        mock_file.assert_called_once()
        mock_yaml_load.assert_called_once()

    @patch("templates.loader.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("templates.loader.yaml.safe_load")
    def test_load_template_metadata_yaml_error(self, mock_yaml_load, mock_file, mock_exists):
        """Test load_template_metadata when YAML parsing fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")

        # Test
        result = load_template_metadata("invalid")

        # Assertions
        assert result is None
        mock_file.assert_called_once()
        mock_yaml_load.assert_called_once()

    @patch("templates.loader.os.path.exists")
    def test_load_template_path_not_found(self, mock_exists):
        """Test load_template when template path doesn't exist."""
        # Setup mock
        mock_exists.return_value = False

        # Test
        result = load_template("nonexistent")

        # Assertions
        assert result is None

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.load_template_metadata")
    def test_load_template_metadata_not_found(self, mock_load_metadata, mock_exists):
        """Test load_template when metadata loading fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_load_metadata.return_value = None

        # Test
        result = load_template("invalid")

        # Assertions
        assert result is None
        mock_load_metadata.assert_called_once_with("invalid")

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.load_template_metadata")
    def test_load_template_success(self, mock_load_metadata, mock_exists):
        """Test successful template loading."""
        # Setup mocks
        mock_exists.return_value = True
        mock_metadata = {
            "name": "lemp",
            "title": "LEMP Stack",
            "description": "Linux, Nginx, MySQL, PHP",
            "category": "web",
            "complexity": "medium",
            "tags": ["nginx", "mysql", "php"],
            "version": "1.0"
        }
        mock_load_metadata.return_value = mock_metadata

        # Test
        result = load_template("lemp")

        # Assertions
        assert result is not None
        assert result["name"] == "lemp"
        assert result["title"] == "LEMP Stack"
        assert "path" in result
        assert result["path"] == os.path.join(TEMPLATES_DIR, "lemp")
        mock_load_metadata.assert_called_once_with("lemp")

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.os.listdir")
    @patch("templates.loader.os.path.isdir")
    @patch("templates.loader.load_template_metadata")
    def test_list_templates_mixed_entries(self, mock_load_metadata, mock_isdir, mock_listdir, mock_exists):
        """Test list_templates with mixed directory entries."""
        # Setup mocks
        def mock_exists_func(path):
            if "template.yaml" in path:
                return "lemp" in path or "mean" in path
            return True
        
        mock_exists.side_effect = mock_exists_func
        mock_listdir.return_value = ["lemp", "mean", "file.txt", "empty_dir"]
        
        def mock_isdir_func(path):
            return not path.endswith("file.txt")
        
        mock_isdir.side_effect = mock_isdir_func
        
        def mock_metadata(name):
            if name == "lemp":
                return {"name": "lemp", "title": "LEMP Stack"}
            elif name == "mean":
                return {"name": "mean", "title": "MEAN Stack"}
            return None
        
        mock_load_metadata.side_effect = mock_metadata

        # Test
        result = list_templates()

        # Assertions
        assert len(result) == 2
        assert result[0]["name"] == "lemp"
        assert result[1]["name"] == "mean"

    def test_default_templates_structure(self):
        """Test the structure of default templates."""
        with patch("templates.loader.os.path.exists", return_value=False):
            with patch("builtins.print"):
                result = list_templates()

        # Verify all default templates have required fields
        required_fields = ["name", "title", "description", "category", "complexity", "tags", "version"]
        
        for template in result:
            for field in required_fields:
                assert field in template, f"Missing field '{field}' in template {template.get('name', 'unknown')}"
            
            # Verify data types
            assert isinstance(template["name"], str)
            assert isinstance(template["title"], str)
            assert isinstance(template["description"], str)
            assert isinstance(template["category"], str)
            assert isinstance(template["complexity"], str)
            assert isinstance(template["tags"], list)
            assert isinstance(template["version"], str)

    @patch("templates.loader.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_template_metadata_file_read_error(self, mock_file, mock_exists):
        """Test load_template_metadata when file reading fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file.side_effect = IOError("File read error")

        # Test - should raise exception since templates/loader.py doesn't handle IOError
        with pytest.raises(IOError):
            load_template_metadata("error_template")

    @patch("templates.loader.os.path.exists")
    @patch("templates.loader.os.listdir")
    @patch("templates.loader.load_template_metadata")
    def test_list_templates_empty_directory(self, mock_load_metadata, mock_listdir, mock_exists):
        """Test list_templates with empty templates directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = []

        # Test
        result = list_templates()

        # Assertions
        assert result == []
        mock_listdir.assert_called_once_with(TEMPLATES_DIR)
        mock_load_metadata.assert_not_called()

    @patch("templates.loader.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("templates.loader.yaml.safe_load")
    def test_load_template_metadata_empty_yaml(self, mock_yaml_load, mock_file, mock_exists):
        """Test load_template_metadata with empty YAML file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = {}

        # Test
        result = load_template_metadata("empty")

        # Assertions
        assert result is not None
        assert result["name"] == "empty"
        # Should only have the name field added
        assert len(result) == 1
