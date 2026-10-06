from functools import lru_cache

from personal_document_intelligence_api.jobs.base import JobQueue
from personal_document_intelligence_api.jobs.factory import create_job_queue


@lru_cache
def get_job_queue() -> JobQueue:
    return create_job_queue()
