#!/bin/bash

export PROJECT_NAME="django_template"
export IMAGE_NAME="django_template:latest"
export COMPOSE_FILE="deploy/docker-compose.yml"

export JENKINS_ENV_FILE="/var/lib/jenkins/api/django-template/django_template.env"
export JENKINS_SECRETS_FILE="/var/lib/jenkins/api/django-template/secrets.yml"
export JENKINS_WORKSPACE_PATTERN="django-template"
