import json
from typing import Any
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError

from .base import JobQueueError, QueueMessage


class SqsJobQueue:
    def __init__(self, queue_url: str, client: Any) -> None:
        self.queue_url = queue_url
        self.client = client

    def publish_document_processing(self, document_id: UUID) -> None:
        message = {
            "type": "document.processing.requested",
            "document_id": str(document_id),
        }

        try:
            self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
            )
        except (BotoCoreError, ClientError) as error:
            raise JobQueueError("Could not publish document processing job") from error

    def receive_messages(self) -> list[QueueMessage]:
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
            )
        except (BotoCoreError, ClientError) as error:
            raise JobQueueError("Could not receive queue messages") from error

        return [
            QueueMessage(
                body=message["Body"],
                receipt_handle=message["ReceiptHandle"],
            )
            for message in response.get("Messages", [])
        ]

    def delete_message(self, receipt_handle: str) -> None:
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
        except (BotoCoreError, ClientError) as error:
            raise JobQueueError("Could not delete queue message") from error
