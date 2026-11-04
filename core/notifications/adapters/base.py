from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Outbound:
    to: str
    subject: str
    body: str
    format: str


class Sender(Protocol):
    def send(self, *, outbound: Outbound) -> str | None:
        """Deliver one message. Return provider reference if any."""
