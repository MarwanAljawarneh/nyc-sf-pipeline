from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sys

sys.path.insert(0, '/opt/airflow')

from scripts.extract_weather import extract_weather
from scripts.load_weather import load_weather

default_args = {
    "owner": "marwan",
    "retries": 1,
}

with DAG(
    dag_id="weather_pipeline",
    description="Daily weather pipeline for NYC and SF",
    default_args=default_args,
    start_date=datetime(2026, 4, 11),
    schedule="@daily",
    catchup=False,
    tags=["weather", "nyc", "sf"],
) as dag:

    def extract_task():
        results = extract_weather()
        return results

    def load_task(**context):
        results = context["ti"].xcom_pull(task_ids="extract")
        load_weather(results)

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_task,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load_task,
    )

    extract >> load