from functools import lru_cache

from personal_document_intelligence_api.storage import FileStorage
from personal_document_intelligence_api.storage.factory import (
    create_file_storage,
)


@lru_cache
def get_file_storage() -> FileStorage:
    return create_file_storage()
