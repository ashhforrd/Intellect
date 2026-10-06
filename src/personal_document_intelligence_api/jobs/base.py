from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


class JobQueueError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class QueueMessage:
    body: str
    receipt_handle: str


class JobQueue(Protocol):
    def publish_document_processing(self, document_id: UUID) -> None: ...

    def receive_messages(self) -> list[QueueMessage]: ...

    def delete_message(self, receipt_handle: str) -> None: ...
