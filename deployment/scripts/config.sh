#!/bin/bash

export PROJECT_NAME="vendor_management"
export IMAGE_NAME="vendor_management:latest"
export COMPOSE_FILE="deployment/docker-compose.yml"

# Jenkins-specific paths
export JENKINS_ENV_FILE="/var/lib/jenkins/api/ehr/vendor_management.env"
export JENKINS_SECRETS_FILE="/var/lib/jenkins/api/secrets.yml"
export JENKINS_WORKSPACE_PATTERN="vendor-management-core"
