#!/bin/bash

export PROJECT_NAME="django_template_infra"
export COMPOSE_DIR="infra"

# Host-side env for compose (ports, passwords). Keep next to app env on the agent.
export JENKINS_ENV_FILE="/var/lib/jenkins/api/django-template/django_template_infra.env"
export JENKINS_WORKSPACE_PATTERN="django-template"
