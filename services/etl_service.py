"""Service layer for ETL operations.

Encapsulates business logic for the ETL pipeline, coordinating between
extract, transform, load modules and the repository layer.
"""

import time
import uuid
from datetime import datetime, timezone

from database.repositories import PipelineRunRepository, SalesRepository
from etl.extract import extract_data
from etl.load import load_data
from etl.logging_config import logger
from etl.transform import transform_data


class ETLService:
    """Service for orchestrating ETL pipeline execution.

    Handles the full extract-transform-load cycle with metadata tracking,
    retry logic, and structured error handling.
    """

    def __init__(
        self,
        sales_repo: SalesRepository | None = None,
        run_repo: PipelineRunRepository | None = None,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        """Initialize the ETL service.

        Args:
            sales_repo: Sales repository instance. Created if None.
            run_repo: Pipeline run repository. Created if None.
            max_retries: Maximum number of retry attempts on failure.
            retry_delay: Delay between retries in seconds.
        """
        self.sales_repo = sales_repo or SalesRepository()
        self.run_repo = run_repo or PipelineRunRepository()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def run_pipeline(self) -> dict:
        """Execute the full ETL pipeline with retry and metadata tracking.

        Returns:
            Dict containing pipeline execution metrics:
            - run_id, status, rows_extracted, rows_transformed,
              rows_loaded, duplicates_removed, duration_seconds
        """
        run_id = f"run_{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info(
            f"Pipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} (run_id={run_id})"
        )
        print(f"\nPipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        metrics = {
            "run_id": run_id,
            "status": "running",
            "rows_extracted": 0,
            "rows_transformed": 0,
            "rows_loaded": 0,
            "duplicates_removed": 0,
            "duration_seconds": 0,
        }

        try:
            self.run_repo.create_run(run_id)

            raw_data = self._execute_with_retry(extract_data, "Extract")
            metrics["rows_extracted"] = len(raw_data)

            clean_data = self._execute_with_retry(lambda: transform_data(raw_data), "Transform")
            before_count = len(raw_data)
            after_count = len(clean_data)
            metrics["rows_transformed"] = after_count
            metrics["duplicates_removed"] = before_count - after_count

            loaded_count = self._execute_with_retry(lambda: load_data(clean_data), "Load")
            metrics["rows_loaded"] = loaded_count

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            metrics["duration_seconds"] = round(duration, 2)
            metrics["status"] = "completed"

            self.run_repo.complete_run(
                run_id=run_id,
                rows_extracted=metrics["rows_extracted"],
                rows_transformed=metrics["rows_transformed"],
                rows_loaded=metrics["rows_loaded"],
                duplicates_removed=metrics["duplicates_removed"],
            )

            logger.info(f"Pipeline completed successfully in {duration:.1f} seconds.")
            print(f"\nPipeline completed successfully in {duration:.1f} seconds.")

        except Exception as e:
            metrics["status"] = "failed"
            error_msg = str(e)
            self.run_repo.fail_run(run_id, error_msg)
            logger.error(f"Pipeline failed: {error_msg}")
            print(f"\nPipeline failed: {error_msg}")
            raise

        return metrics

    def _execute_with_retry(self, func, step_name: str):
        """Execute a function with retry logic.

        Args:
            func: Callable to execute.
            step_name: Name of the ETL step for logging.

        Returns:
            Result of the function call.

        Raises:
            The last exception if all retries are exhausted.
        """
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"\n[{step_name}] Attempt {attempt}/{self.max_retries}...")
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(f"{step_name} attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

        logger.error(f"{step_name} failed after {self.max_retries} attempts.")
        raise last_exception
