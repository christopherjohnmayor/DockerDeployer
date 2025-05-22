# CI/CD Pipeline Setup Guide

This guide explains how to fix the CI/CD pipeline failure and set up the required secrets for DockerDeployer.

## Issue Description

The GitHub Actions workflow is failing with "Username and password required" error during the "Login to DockerHub" step. This happens because the required DockerHub authentication secrets are not configured in the repository.

## Required GitHub Secrets

To fix the CI/CD pipeline, you need to configure the following secrets in your GitHub repository:

### 1. DockerHub Authentication (Required)

- **`DOCKERHUB_USERNAME`**: Your DockerHub username
- **`DOCKERHUB_TOKEN`**: DockerHub access token (not your password)

### 2. Deployment Secrets (Optional - for staging/production deployment)

- **`SSH_PRIVATE_KEY`**: SSH private key for deployment servers
- **`SSH_USER`**: SSH username for deployment
- **`STAGING_HOST`**: Staging server hostname/IP
- **`STAGING_DOMAIN`**: Staging domain name
- **`PRODUCTION_HOST`**: Production server hostname/IP
- **`PRODUCTION_DOMAIN`**: Production domain name
- **`SECRET_KEY`**: Application secret key for production

## Step-by-Step Setup

### Step 1: Create DockerHub Access Token

1. Go to [DockerHub](https://hub.docker.com/)
2. Sign in to your account
3. Click on your username → Account Settings
4. Go to Security → New Access Token
5. Create a new token with name "GitHub Actions" and Read/Write permissions
6. **Copy the token immediately** (you won't be able to see it again)

### Step 2: Configure GitHub Repository Secrets

1. Go to your GitHub repository: `https://github.com/christopherjohnmayor/DockerDeployer`
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the following secrets:

#### Required Secrets:
```
Name: DOCKERHUB_USERNAME
Value: christopherjohnmayor (or your actual DockerHub username)

Name: DOCKERHUB_TOKEN
Value: [paste the access token you created in Step 1]
```

#### Optional Deployment Secrets (add if you plan to use automated deployment):
```
Name: SECRET_KEY
Value: [generate a secure random string, e.g., using: openssl rand -hex 32]

Name: SSH_PRIVATE_KEY
Value: [your SSH private key content for deployment servers]

Name: SSH_USER
Value: [your SSH username for deployment]

Name: STAGING_HOST
Value: [your staging server IP/hostname]

Name: STAGING_DOMAIN
Value: [your staging domain]

Name: PRODUCTION_HOST
Value: [your production server IP/hostname]

Name: PRODUCTION_DOMAIN
Value: [your production domain]
```

### Step 3: Verify the Setup

1. After adding the secrets, go to the **Actions** tab in your repository
2. Find the failed workflow run
3. Click **Re-run all jobs** to retry the workflow
4. The workflow should now complete successfully

## What Was Fixed

The following changes were made to resolve the CI/CD issues:

1. **Updated Docker image references**: Changed from `yourusername/dockerdeployer` to `christopherjohnmayor/dockerdeployer`
2. **Updated production docker-compose**: Modified to use pre-built images from DockerHub instead of building locally
3. **Maintained consistency**: Ensured all workflow files use the correct image naming

## Workflow Overview

The CI/CD pipeline now works as follows:

1. **Build and Push** (`.github/workflows/build.yml`):
   - Triggers on pushes to main branch and version tags
   - Builds Docker images for backend and frontend
   - Pushes images to DockerHub with appropriate tags
   - Creates GitHub releases for version tags

2. **Test** (`.github/workflows/test.yml`):
   - Runs on pull requests and pushes
   - Executes backend and frontend tests
   - Reports test coverage

3. **Deploy** (`.github/workflows/deploy.yml`):
   - Triggers after successful builds
   - Deploys to staging (on main branch pushes)
   - Deploys to production (on releases)

## Troubleshooting

### Common Issues:

1. **"Username and password required"**: DockerHub secrets not configured
2. **"Repository does not exist"**: Wrong DockerHub username in workflow
3. **"Permission denied"**: DockerHub token doesn't have write permissions
4. **"SSH connection failed"**: SSH secrets not configured for deployment

### Verification Commands:

```bash
# Test DockerHub login locally
echo $DOCKERHUB_TOKEN | docker login --username $DOCKERHUB_USERNAME --password-stdin

# Check if images exist on DockerHub
docker pull christopherjohnmayor/dockerdeployer:latest-backend
docker pull christopherjohnmayor/dockerdeployer:latest-frontend
```

## Next Steps

After fixing the CI/CD pipeline:

1. **Test the workflow**: Push a commit to main branch and verify it builds successfully
2. **Create a release**: Tag a version (e.g., `v1.0.0`) to test the release workflow
3. **Set up deployment**: Configure deployment secrets if you want automated deployment
4. **Monitor builds**: Check the Actions tab regularly for any issues

## Security Notes

- Never commit secrets to the repository
- Use GitHub repository secrets for sensitive information
- Rotate DockerHub tokens periodically
- Use least-privilege access for deployment keys
- Consider using environment-specific secrets for staging vs production
