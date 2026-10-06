import json
from unittest.mock import Mock
from uuid import uuid4

from personal_document_intelligence_api.jobs.sqs import SqsJobQueue

QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/123/document-processing"


def test_publish_document_processing_job() -> None:
    client = Mock()
    queue = SqsJobQueue(
        queue_url=QUEUE_URL,
        client=client,
    )
    document_id = uuid4()

    queue.publish_document_processing(document_id)

    call = client.send_message.call_args.kwargs
    body = json.loads(call["MessageBody"])

    assert call["QueueUrl"] == QUEUE_URL
    assert body == {
        "type": "document.processing.requested",
        "document_id": str(document_id),
    }


def test_receive_messages() -> None:
    client = Mock()
    client.receive_message.return_value = {
        "Messages": [
            {
                "Body": '{"document_id": "123"}',
                "ReceiptHandle": "receipt-123",
            }
        ]
    }
    queue = SqsJobQueue(
        queue_url=QUEUE_URL,
        client=client,
    )

    messages = queue.receive_messages()

    assert len(messages) == 1
    assert messages[0].body == '{"document_id": "123"}'
    assert messages[0].receipt_handle == "receipt-123"


def test_delete_message() -> None:
    client = Mock()
    queue = SqsJobQueue(
        queue_url=QUEUE_URL,
        client=client,
    )

    queue.delete_message("receipt-123")

    client.delete_message.assert_called_once_with(
        QueueUrl=QUEUE_URL,
        ReceiptHandle="receipt-123",
    )
