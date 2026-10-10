import json
from unittest.mock import Mock
from uuid import uuid4

from personal_document_intelligence_api.jobs.redis import RedisJobQueue


def make_queue(client: Mock) -> RedisJobQueue:
    return RedisJobQueue(client=client, consumer_name="test-worker")


def test_publish_document_processing_job() -> None:
    client = Mock()
    queue = make_queue(client)
    document_id = uuid4()

    queue.publish_document_processing(document_id)

    stream, fields = client.xadd.call_args.args
    assert stream == "intellect:document-processing"
    assert json.loads(fields["body"]) == {
        "type": "document.processing.requested",
        "document_id": str(document_id),
    }


def test_receive_new_message() -> None:
    client = Mock()
    client.xautoclaim.return_value = ("0-0", [])
    client.xreadgroup.return_value = [
        (
            "intellect:document-processing",
            [("123-0", {"body": '{"document_id": "123"}'})],
        )
    ]
    queue = make_queue(client)

    messages = queue.receive_messages()

    assert messages[0].body == '{"document_id": "123"}'
    assert messages[0].receipt_handle == "123-0"


def test_receive_reclaims_timed_out_message() -> None:
    client = Mock()
    client.xautoclaim.return_value = (
        "0-0",
        [("123-0", {"body": '{"document_id": "123"}'})],
    )
    queue = make_queue(client)

    messages = queue.receive_messages()

    assert messages[0].receipt_handle == "123-0"
    client.xreadgroup.assert_not_called()


def test_delete_acknowledges_and_removes_message() -> None:
    client = Mock()
    queue = make_queue(client)

    queue.delete_message("123-0")

    client.xack.assert_called_once_with(
        "intellect:document-processing", "document-workers", "123-0"
    )
    client.xdel.assert_called_once_with("intellect:document-processing", "123-0")
