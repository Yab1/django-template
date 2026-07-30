# pyright: reportArgumentType=false

from config.env import env

# Temporal server gRPC address (not the UI port).
TEMPORAL_ADDRESS = env.str("TEMPORAL_ADDRESS", default="localhost:7233")

# Task queue used by workflow starters and workers.
TEMPORAL_TASK_QUEUE = env.str("TEMPORAL_TASK_QUEUE", default="workflow-engine")

# Workflow type name registered by Temporal worker.
TEMPORAL_WORKFLOW_TYPE = env.str("TEMPORAL_WORKFLOW_TYPE", default="PlanExecutionWorkflow")
