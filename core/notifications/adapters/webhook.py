import httpx

from core.notifications.adapters.base import Outbound


class WebhookSender:
    """SMS / push: POST JSON {to, subject, body} to a provider URL."""

    def __init__(self, *, url: str, token: str = "") -> None:
        self.url = url
        self.token = token

    def send(self, *, outbound: Outbound) -> str | None:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                self.url,
                json={"to": outbound.to, "subject": outbound.subject, "body": outbound.body},
                headers=headers,
            )
            response.raise_for_status()
        return None
