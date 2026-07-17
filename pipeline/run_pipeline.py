import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_setup import init_db
from etl.logging_config import logger
from services.etl_service import ETLService


def run_pipeline():
    """Execute the full ETL pipeline.

    Initializes the database, then runs the extract-transform-load cycle
    with retry logic and pipeline metadata tracking.
    """
    start_time = datetime.now()
    logger.info("=" * 50)
    logger.info(f"Pipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nPipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        print("\n[1/2] Initializing database...")
        init_db()

        print("\n[2/2] Running ETL pipeline...")
        service = ETLService()
        metrics = service.run_pipeline()

        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        logger.info(f"Pipeline completed successfully in {duration} seconds.")
        print(f"\nPipeline completed successfully in {duration} seconds.")
        print(f"  Rows extracted:   {metrics['rows_extracted']}")
        print(f"  Rows transformed: {metrics['rows_transformed']}")
        print(f"  Rows loaded:      {metrics['rows_loaded']}")
        print(f"  Duplicates removed: {metrics['duplicates_removed']}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"\nPipeline failed: {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
