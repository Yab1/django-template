#!/bin/bash

export PROJECT_NAME="vendor_management"
export IMAGE_NAME="vendor_management:latest"
export COMPOSE_FILE="deployment/docker-compose.yml"

# Jenkins — prefer Credentials Plugin secret-file IDs (set in job/folder env or Jenkinsfile params).
# When unset, prepare-env.sh falls back to legacy host paths below.
# export JENKINS_ENV_CREDENTIAL_ID="vendor-management-env"
# export JENKINS_SECRETS_CREDENTIAL_ID="vendor-management-secrets"

# Legacy host paths (used when credential IDs not provided)
export JENKINS_ENV_FILE="/var/lib/jenkins/api/ehr/vendor_management.env"
export JENKINS_SECRETS_FILE="/var/lib/jenkins/api/secrets.yml"
export JENKINS_WORKSPACE_PATTERN="vendor-management-core"
