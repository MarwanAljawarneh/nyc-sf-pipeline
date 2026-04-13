from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sys

sys.path.insert(0, '/opt/airflow')

from scripts.extract_housing import extract_housing
from scripts.load_housing import load_housing

default_args = {
    "owner": "marwan",
    "retries": 1,
}

with DAG(
    dag_id="housing_pipeline",
    description="Monthly housing rental data pipeline for NYC and SF",
    default_args=default_args,
    start_date=datetime(2026, 4, 12),
    schedule="@monthly",
    catchup=False,
    tags=["housing", "nyc", "sf", "zillow"],
) as dag:

    def extract_task():
        return extract_housing()

    def load_task(**context):
        results = context["ti"].xcom_pull(task_ids="extract")
        load_housing(results)

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_task,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load_task,
    )

    extract >> load