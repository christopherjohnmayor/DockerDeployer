# Version Control Module

## Overview
The version_control module is responsible for tracking all configuration changes made by DockerDeployer, including generated Dockerfiles, docker-compose.yml files, and template modifications. This ensures users can audit, roll back, and review the history of their deployment configurations.

## Approach

- **Git-Based Versioning:**  
  All configuration files are automatically committed to a local Git repository upon creation or modification. Each commit includes a descriptive message referencing the user action or natural language command that triggered the change.

- **Automatic Snapshots:**  
  Snapshots are created before and after major actions (e.g., deployment, template application, manual edits).

- **Rollback Support:**  
  Users can view the history of changes and roll back to any previous state via the web UI or natural language commands.

- **Audit Logging:**  
  All versioning actions are logged for security and traceability.

## Key Features

- Transparent, automatic versioning of all Docker-related configs
- Integration with the web UI for browsing history and restoring versions
- Support for branching and merging in advanced scenarios (future release)
- Designed for local, air-gapped environments (no external Git hosting required)

## Future Enhancements

- Integration with remote Git repositories (GitHub, GitLab, etc.)
- Fine-grained diff and merge tools for resolving configuration conflicts
- Automated tagging of stable/production deployments

---

**Location:** All version-controlled files and the local Git repository are stored within the user's project workspace, isolated from application code.