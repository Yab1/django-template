import strawberry


@strawberry.type
class HealthCheckQuery:
    ping_patient_service: str = strawberry.field(default="pong")
