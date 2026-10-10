import json
from uuid import uuid4

from personal_document_intelligence_api.jobs.local import LocalFileJobQueue


def test_local_queue_publishes_receives_and_deletes(tmp_path) -> None:
    queue = LocalFileJobQueue(tmp_path / "jobs")
    document_id = uuid4()

    queue.publish_document_processing(document_id)

    messages = queue.receive_messages()
    assert len(messages) == 1
    assert json.loads(messages[0].body) == {
        "type": "document.processing.requested",
        "document_id": str(document_id),
    }
    assert queue.receive_messages() == []

    queue.delete_message(messages[0].receipt_handle)
    assert queue.receive_messages() == []


def test_local_queue_returns_oldest_job_first(tmp_path) -> None:
    queue = LocalFileJobQueue(tmp_path / "jobs")
    first_document_id = uuid4()
    second_document_id = uuid4()

    queue.publish_document_processing(first_document_id)
    queue.publish_document_processing(second_document_id)

    first_message = queue.receive_messages()[0]
    assert json.loads(first_message.body)["document_id"] == str(first_document_id)
