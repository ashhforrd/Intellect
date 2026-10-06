import boto3

from personal_document_intelligence_api.core.config import Settings, get_settings

from .base import JobQueue
from .sqs import SqsJobQueue


class JobQueueConfigurationError(Exception):
    pass


def create_job_queue(settings: Settings | None = None) -> JobQueue:
    settings = settings or get_settings()

    if not settings.sqs_queue_url:
        raise JobQueueConfigurationError("SQS_QUEUE_URL is required")

    client = boto3.client(
        "sqs",
        region_name=settings.aws_region,
    )

    return SqsJobQueue(
        queue_url=settings.sqs_queue_url,
        client=client,
    )
