import strawberry


@strawberry.type
class HealthCheckMutation:
    ping_patient_service: str = strawberry.field(default="pong")
