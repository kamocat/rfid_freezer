from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    type: str
    id: str
    text: str


class Source(BaseModel):
    type: str
    userId: str


class DeliveryContext(BaseModel):
    isRedelivery: bool


class Event(BaseModel):
    type: str
    message: Optional[Message] = None
    timestamp: int
    source: Source
    replyToken: Optional[str] = None
    mode: str
    webhookEventId: str
    deliveryContext: DeliveryContext


class Webhook(BaseModel):
    destination: str
    events: List[Event]

