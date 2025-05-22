#!/bin/bash

# Generate Secrets Script for DockerDeployer
# This script helps generate secure secrets for the application

set -e

echo "🔐 DockerDeployer Secrets Generator"
echo "=================================="
echo

# Function to generate a secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -hex $length 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex($length))" 2>/dev/null || head -c $length /dev/urandom | xxd -p -c $length
}

# Generate SECRET_KEY
echo "📝 Generating APPLICATION SECRET_KEY..."
SECRET_KEY=$(generate_secret 32)
echo "SECRET_KEY: $SECRET_KEY"
echo

# Generate JWT secret if needed
echo "📝 Generating JWT SECRET (optional)..."
JWT_SECRET=$(generate_secret 32)
echo "JWT_SECRET: $JWT_SECRET"
echo

# Instructions for DockerHub
echo "🐳 DockerHub Setup Instructions:"
echo "1. Go to https://hub.docker.com/"
echo "2. Sign in to your account"
echo "3. Go to Account Settings → Security"
echo "4. Create a new Access Token with Read/Write permissions"
echo "5. Copy the token for DOCKERHUB_TOKEN secret"
echo

# Instructions for SSH key
echo "🔑 SSH Key Generation (for deployment):"
echo "If you need to generate SSH keys for deployment:"
echo "ssh-keygen -t ed25519 -C 'dockerdeployer-deployment' -f ~/.ssh/dockerdeployer_deploy"
echo "Then add the public key to your deployment servers"
echo

# Summary
echo "📋 GitHub Secrets Summary:"
echo "========================="
echo "Required secrets to add to GitHub repository:"
echo
echo "DOCKERHUB_USERNAME: christopherjohnmayor"
echo "DOCKERHUB_TOKEN: [get from DockerHub as described above]"
echo "SECRET_KEY: $SECRET_KEY"
echo
echo "Optional deployment secrets:"
echo "SSH_PRIVATE_KEY: [content of private key file]"
echo "SSH_USER: [your deployment server username]"
echo "STAGING_HOST: [staging server IP/hostname]"
echo "STAGING_DOMAIN: [staging domain]"
echo "PRODUCTION_HOST: [production server IP/hostname]"
echo "PRODUCTION_DOMAIN: [production domain]"
echo
echo "✅ Copy these values to GitHub repository secrets!"
echo "   Go to: https://github.com/christopherjohnmayor/DockerDeployer/settings/secrets/actions"
