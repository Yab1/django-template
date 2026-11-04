import httpx

from core.notifications.adapters.base import Outbound


class TelegramSender:
    def __init__(self, *, bot_token: str) -> None:
        self.bot_token = bot_token

    def send(self, *, outbound: Outbound) -> str | None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                url,
                json={"chat_id": outbound.to, "text": outbound.body or outbound.subject},
            )
            response.raise_for_status()
        return None
