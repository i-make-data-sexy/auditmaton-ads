# services/tasks.py
# Huey task definitions for background processing. Task functions handle
# queue orchestration (status updates, error handling, retries) while
# delegating actual business logic to services/crawl_processor.py.

import logging
import os
from datetime import datetime, timezone, timedelta

from huey import crontab

from services.task_queue import huey, with_app_context

logger = logging.getLogger(__name__)


# ========================================================================
#   Crawl File Processing Task
# ========================================================================

@huey.task(retries=2, retry_delay=30)
@with_app_context
def process_crawl_file(crawl_file_id):
    """
    Processes an uploaded crawl CSV file in the background.

    Loads the CrawlFile record, runs processing logic, and updates
    the record with results or error information. Retries up to 2
    times with a 30-second delay between attempts.

    Args:
        crawl_file_id (str): UUID of the CrawlFile record to process.
    """
    from extensions import db
    from models.audit import CrawlFile
    from services.crawl_processor import process_file

    crawl_file = db.session.get(CrawlFile, crawl_file_id)
    if crawl_file is None:
        logger.error("CrawlFile not found: %s", crawl_file_id)
        return

    # Mark as processing
    crawl_file.processing_status = "processing"
    crawl_file.processing_started_at = datetime.now(timezone.utc)
    db.session.commit()

    try:
        results = process_file(crawl_file.file_path)

        # Update with results
        crawl_file.row_count = results["row_count"]
        crawl_file.column_count = results["column_count"]
        crawl_file.processing_status = "complete"
        crawl_file.processing_completed_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info("Crawl file processed successfully: %s", crawl_file_id)

    except Exception as e:
        db.session.rollback()

        # Update status to failed with error details
        crawl_file.processing_status = "failed"
        crawl_file.processing_error = str(e)
        crawl_file.processing_completed_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.exception("Crawl file processing failed: %s", crawl_file_id)

        # Re-raise so Huey can retry
        raise


# ========================================================================
#   Periodic Cleanup Task
# ========================================================================

@huey.periodic_task(crontab(hour="3", minute="0"))
@with_app_context
def cleanup_stale_uploads():
    """
    Deletes processed crawl files older than 24 hours from disk.

    Runs daily at 3:00 AM. Cleans up completed files after 24 hours
    and failed files after 72 hours. The CrawlFile database record
    is preserved for audit history.
    """
    from flask import current_app
    from extensions import db
    from models.audit import CrawlFile

    cutoff_complete = datetime.now(timezone.utc) - timedelta(hours=24)
    cutoff_failed = datetime.now(timezone.utc) - timedelta(hours=72)

    # Find stale completed files
    stale_files = CrawlFile.query.filter(
        db.or_(
            db.and_(
                CrawlFile.processing_status == "complete",
                CrawlFile.processing_completed_at < cutoff_complete,
            ),
            db.and_(
                CrawlFile.processing_status == "failed",
                CrawlFile.processing_completed_at < cutoff_failed,
            ),
        )
    ).all()

    deleted_count = 0
    for crawl_file in stale_files:
        try:
            if os.path.isfile(crawl_file.file_path):
                os.remove(crawl_file.file_path)
                deleted_count += 1
        except OSError:
            logger.warning("Could not delete file: %s", crawl_file.file_path)

    if deleted_count:
        logger.info("Cleaned up %d stale crawl files", deleted_count)
