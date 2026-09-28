from celery import Celery
import time

# Configure Celery to use Redis
celery_app = Celery(
    "etl",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


@celery_app.task
def run_etl(param):
    print(f"Starting ETL with param: {param}")

    time.sleep(5)  # Simulate ETL work

    print("ETL complete")

    return f"Processed with param: {param}"
