import asyncio
import json
import logging
from uuid import UUID

from personal_document_intelligence_api.database.repositories.document import (
    DocumentRepository,
)
from personal_document_intelligence_api.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from personal_document_intelligence_api.database.repositories.document_section import (
    DocumentSectionRepository,
)
from personal_document_intelligence_api.database.session import async_session_factory
from personal_document_intelligence_api.documents.ocr import TesseractOcrEngine
from personal_document_intelligence_api.documents.service import (
    DocumentExtractionService,
)
from personal_document_intelligence_api.jobs.factory import create_job_queue
from personal_document_intelligence_api.retrieval.embeddings.factory import (
    create_embedding_provider,
)
from personal_document_intelligence_api.storage.factory import create_file_storage
from personal_document_intelligence_api.workers.document_processor import (
    DocumentProcessingError,
    DocumentProcessor,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker() -> None:
    queue = create_job_queue()
    storage = create_file_storage()
    extraction_service = DocumentExtractionService(
        ocr_engine=TesseractOcrEngine(),
    )

    logger.info("Document worker started")

    while True:
        messages = await asyncio.to_thread(queue.receive_messages)
        if not messages:
            await asyncio.sleep(0.5)
            continue
        embedding_provider = create_embedding_provider()

        for message in messages:
            try:
                payload = json.loads(message.body)
                document_id = UUID(payload["document_id"])

                async with async_session_factory() as session:
                    processor = DocumentProcessor(
                        session=session,
                        repository=DocumentRepository(session),
                        section_repository=DocumentSectionRepository(session),
                        chunk_repository=DocumentChunkRepository(session),
                        storage=storage,
                        extraction_service=extraction_service,
                        embedding_provider=embedding_provider,
                    )

                    processed = await processor.process(document_id)

                await asyncio.to_thread(
                    queue.delete_message,
                    message.receipt_handle,
                )

                if processed:
                    logger.info("Processed document %s", document_id)
                else:
                    logger.info(
                        "Skipped job for deleted document %s",
                        document_id,
                    )

            except (KeyError, ValueError, json.JSONDecodeError):
                logger.exception("Invalid queue message")
                await asyncio.to_thread(
                    queue.delete_message,
                    message.receipt_handle,
                )
            except DocumentProcessingError:
                logger.exception("Document processing failed")


if __name__ == "__main__":
    asyncio.run(run_worker())
