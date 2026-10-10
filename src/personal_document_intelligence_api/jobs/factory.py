import boto3
from redis import Redis

from personal_document_intelligence_api.core.config import Settings, get_settings

from .base import JobQueue
from .local import LocalFileJobQueue
from .redis import RedisJobQueue
from .sqs import SqsJobQueue


class JobQueueConfigurationError(Exception):
    pass


def create_job_queue(settings: Settings | None = None) -> JobQueue:
    settings = settings or get_settings()

    if settings.job_queue_backend == "local":
        return LocalFileJobQueue(settings.local_queue_path)

    if settings.job_queue_backend == "redis":
        if not settings.redis_url:
            raise JobQueueConfigurationError("REDIS_URL is required when JOB_QUEUE_BACKEND=redis")
        client = Redis.from_url(
            settings.redis_url.get_secret_value(),
            decode_responses=True,
        )
        return RedisJobQueue(client)

    if not settings.sqs_queue_url:
        raise JobQueueConfigurationError("SQS_QUEUE_URL is required when JOB_QUEUE_BACKEND=sqs")

    client = boto3.client(
        "sqs",
        region_name=settings.aws_region,
    )

    return SqsJobQueue(
        queue_url=settings.sqs_queue_url,
        client=client,
    )
