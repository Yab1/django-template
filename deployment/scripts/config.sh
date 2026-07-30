#!/bin/bash

export PROJECT_NAME="ehr_backend"
export IMAGE_NAME="ehr_backend:latest"
export COMPOSE_FILE="deployment/docker-compose.yml"

# Jenkins-specific paths
export JENKINS_ENV_FILE="/var/lib/jenkins/api/ehr/ehr_backend.env"
export JENKINS_SECRETS_FILE="/var/lib/jenkins/api/secrets.yml"
export JENKINS_WORKSPACE_PATTERN="ehr-backend"
