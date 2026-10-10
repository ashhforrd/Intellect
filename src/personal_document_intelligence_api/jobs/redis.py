import json
import socket
from typing import Any
from uuid import UUID, uuid4

from redis import Redis
from redis.exceptions import RedisError, ResponseError

from .base import JobQueueError, QueueMessage


class RedisJobQueue:
    def __init__(
        self,
        client: Redis,
        stream_name: str = "intellect:document-processing",
        consumer_group: str = "document-workers",
        consumer_name: str | None = None,
        visibility_timeout_seconds: int = 30,
    ) -> None:
        self.client = client
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"{socket.gethostname()}-{uuid4()}"
        self.visibility_timeout_seconds = visibility_timeout_seconds
        self._ensure_consumer_group()

    def publish_document_processing(self, document_id: UUID) -> None:
        message = json.dumps(
            {
                "type": "document.processing.requested",
                "document_id": str(document_id),
            }
        )
        try:
            self.client.xadd(self.stream_name, {"body": message})
        except RedisError as error:
            raise JobQueueError("Could not publish Redis processing job") from error

    def receive_messages(self) -> list[QueueMessage]:
        try:
            reclaimed = self.client.xautoclaim(
                self.stream_name,
                self.consumer_group,
                self.consumer_name,
                min_idle_time=self.visibility_timeout_seconds * 1000,
                start_id="0-0",
                count=1,
            )
            reclaimed_messages = reclaimed[1] if len(reclaimed) > 1 else []
            if reclaimed_messages:
                return [self._to_queue_message(reclaimed_messages[0])]

            response = self.client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {self.stream_name: ">"},
                count=1,
                block=1000,
            )
            if not response:
                return []
            return [self._to_queue_message(response[0][1][0])]
        except RedisError as error:
            raise JobQueueError("Could not receive Redis processing jobs") from error

    def delete_message(self, receipt_handle: str) -> None:
        try:
            self.client.xack(self.stream_name, self.consumer_group, receipt_handle)
            self.client.xdel(self.stream_name, receipt_handle)
        except RedisError as error:
            raise JobQueueError("Could not delete Redis processing job") from error

    def _ensure_consumer_group(self) -> None:
        try:
            self.client.xgroup_create(
                self.stream_name,
                self.consumer_group,
                id="0",
                mkstream=True,
            )
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise JobQueueError("Could not initialize Redis job queue") from error
        except RedisError as error:
            raise JobQueueError("Could not initialize Redis job queue") from error

    @staticmethod
    def _to_queue_message(message: tuple[str, dict[str, Any]]) -> QueueMessage:
        message_id, fields = message
        body = fields.get("body")
        if not isinstance(body, str):
            raise JobQueueError("Redis processing job has no body")
        return QueueMessage(body=body, receipt_handle=message_id)
