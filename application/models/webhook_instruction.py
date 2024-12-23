from dataclasses import dataclass


@dataclass
class WebhookInstruction:
    webhook_id: str
    actor: str
    type: str
