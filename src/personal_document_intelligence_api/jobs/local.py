import json
import os
from pathlib import Path
from time import monotonic, time_ns
from uuid import UUID, uuid4

from .base import JobQueueError, QueueMessage


class LocalFileJobQueue:
    """Durable single-machine queue shared by the API and worker processes."""

    def __init__(self, queue_path: Path, visibility_timeout_seconds: int = 30) -> None:
        self.queue_path = queue_path
        self.visibility_timeout_seconds = visibility_timeout_seconds
        self._visible_after: dict[str, float] = {}

    def publish_document_processing(self, document_id: UUID) -> None:
        message = {
            "type": "document.processing.requested",
            "document_id": str(document_id),
        }
        try:
            self.queue_path.mkdir(parents=True, exist_ok=True)
            message_id = uuid4()
            destination = self.queue_path / f"{time_ns()}-{message_id}.json"
            temporary = self.queue_path / f".{message_id}.tmp"
            temporary.write_text(json.dumps(message), encoding="utf-8")
            os.replace(temporary, destination)
        except OSError as error:
            raise JobQueueError("Could not publish local processing job") from error

    def receive_messages(self) -> list[QueueMessage]:
        try:
            self.queue_path.mkdir(parents=True, exist_ok=True)
            jobs = sorted(self.queue_path.glob("*.json"))
            now = monotonic()
            job = next(
                (path for path in jobs if self._visible_after.get(path.name, 0) <= now),
                None,
            )
            if job is None:
                return []
            self._visible_after[job.name] = now + self.visibility_timeout_seconds
            return [
                QueueMessage(
                    body=job.read_text(encoding="utf-8"),
                    receipt_handle=job.name,
                )
            ]
        except OSError as error:
            raise JobQueueError("Could not receive local processing jobs") from error

    def delete_message(self, receipt_handle: str) -> None:
        try:
            message_name = Path(receipt_handle).name
            (self.queue_path / message_name).unlink(missing_ok=True)
            self._visible_after.pop(message_name, None)
        except OSError as error:
            raise JobQueueError("Could not delete local processing job") from error
