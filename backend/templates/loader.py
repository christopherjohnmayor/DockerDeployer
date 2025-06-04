import os
from typing import Dict, List, Optional

import yaml

TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../templates")
)


def list_templates() -> List[Dict]:
    """
    List all available stack templates in the templates directory.
    Returns a list of dicts with template name and description.
    """
    templates = []

    # Check if templates directory exists
    if not os.path.exists(TEMPLATES_DIR):
        print(f"⚠️  Templates directory not found: {TEMPLATES_DIR}")
        # Return default templates for development/testing
        return [
            {
                "name": "lemp",
                "title": "LEMP Stack",
                "description": "Linux, Nginx, MySQL, PHP stack for web applications",
                "category": "web",
                "complexity": "medium",
                "tags": ["nginx", "mysql", "php", "web"],
                "version": "1.0"
            },
            {
                "name": "mean",
                "title": "MEAN Stack",
                "description": "MongoDB, Express.js, Angular, Node.js stack",
                "category": "web",
                "complexity": "medium",
                "tags": ["mongodb", "express", "angular", "nodejs"],
                "version": "1.0"
            },
            {
                "name": "wordpress",
                "title": "WordPress",
                "description": "WordPress CMS with MySQL database",
                "category": "cms",
                "complexity": "easy",
                "tags": ["wordpress", "mysql", "cms"],
                "version": "1.0"
            }
        ]

    try:
        for entry in os.listdir(TEMPLATES_DIR):
            entry_path = os.path.join(TEMPLATES_DIR, entry)
            if os.path.isdir(entry_path) and os.path.exists(
                os.path.join(entry_path, "template.yaml")
            ):
                meta = load_template_metadata(entry)
                if meta:
                    templates.append(meta)
    except Exception as e:
        print(f"⚠️  Error reading templates directory: {e}")

    return templates


def load_template_metadata(template_name: str) -> Optional[Dict]:
    """
    Load metadata for a given template (from template.yaml).
    """
    meta_path = os.path.join(TEMPLATES_DIR, template_name, "template.yaml")
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r") as f:
            meta = yaml.safe_load(f)
        meta["name"] = template_name
        return meta
    except yaml.YAMLError:
        return None


def load_template(template_name: str) -> Optional[Dict]:
    """
    Load the full template definition (docker-compose, Dockerfiles, etc.).
    """
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    if not os.path.exists(template_path):
        return None
    # For now, just return metadata and path; can be extended to load files
    meta = load_template_metadata(template_name)
    if not meta:
        return None
    meta["path"] = template_path
    return meta
