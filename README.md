# NYC vs SF Cost & Quality of Life Pipeline

A daily ELT pipeline that compares New York City and San Francisco across weather, housing, and cost of living — orchestrated with Apache Airflow, warehoused in PostgreSQL (Supabase), transformed with dbt, and visualized in a live Streamlit dashboard.

---

## Architecture

```
Open-Meteo API  ──┐
Zillow ZORI CSV ──┼──▶ Airflow (Docker) ──▶ Supabase (Postgres) ──▶ dbt ──▶ Streamlit
BLS CPI API     ──┘
```

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow (Docker) |
| Extraction | Python, Requests, Polars |
| Warehouse | Supabase (PostgreSQL) |
| Transformation | dbt Core |
| Dashboard | Streamlit |
| Dependency Management | uv |
| Logging | Loguru |

## Data Sources

| Source | Data | Frequency |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Daily temperature & precipitation | Daily |
| [Zillow ZORI](https://www.zillow.com/research/data/) | Median observed rent | Monthly |
| [BLS CPI API](https://www.bls.gov/developers/) | Consumer Price Index | Monthly |

## Project Structure

```
nyc-sf-pipeline/
├── dags/
│   ├── weather_dag.py       # Daily weather pipeline
│   ├── housing_dag.py       # Monthly housing pipeline
│   └── cpi_dag.py           # Monthly CPI pipeline
├── scripts/
│   ├── extract_weather.py
│   ├── load_weather.py
│   ├── extract_housing.py
│   ├── load_housing.py
│   ├── extract_cpi.py
│   └── load_cpi.py
└── pyproject.toml
```

## Setup

### Prerequisites
- Docker Desktop
- Python 3.12+
- uv

### Installation

1. Clone the repo
```bash
git clone git@github.com:MarwanAljawarneh/nyc-sf-pipeline.git
cd nyc-sf-pipeline
```

2. Install dependencies
```bash
uv sync
```

3. Create a `.env` file in the root directory with the following variables:
```
SUPABASE_DB_URL=postgresql://...
BLS_API_KEY=your_bls_api_key
```

4. Start Airflow
```bash
cd airflow-practice
docker-compose up -d
```

5. Open Airflow UI at `http://localhost:8080`

## DAGs

| DAG | Schedule | Description |
|---|---|---|
| `weather_pipeline` | `@daily` | Pulls temperature and precipitation for NYC and SF |
| `housing_pipeline` | `@monthly` | Pulls median observed rent from Zillow ZORI |
| `cpi_pipeline` | `@monthly` | Pulls Consumer Price Index from BLS API |

## Dashboard

A live interactive dashboard is available here:

👉 https://nyc-sf-pipeline.streamlit.app/

The dashboard visualizes key comparisons between New York City and San Francisco across:

- 🌤️ Daily weather (temperature & precipitation)
- 🏠 Median rent trends over time
- 📈 Cost of living (CPI) trends

Built with Streamlit and connected directly to a PostgreSQL warehouse (Supabase), the dashboard reflects data processed through the full ELT pipeline.

### Features
- Real-time data updates from scheduled Airflow pipelines
- Clean side-by-side city comparison
- Interactive time-series visualizations
- Cached queries for fast performance

### Tech Highlights
- Streamlit for frontend visualization
- Polars for fast in-memory data processing
- PostgreSQL (Supabase) as the serving layer

## Author

Marwan Aljawarneh — [LinkedIn](https://www.linkedin.com/in/marwan-aljawarneh/)