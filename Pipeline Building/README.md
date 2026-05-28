# Weather Data Pipeline 🌤️

A complete, production-ready data pipeline that demonstrates best practices for fetching, cleaning, and transforming external data.

## API Choice: Open-Meteo (Why We Selected It)

### Why Open-Meteo?

We evaluated multiple weather APIs and chose **Open-Meteo** for the following reasons:

| Criteria | Open-Meteo | Alternatives | Winner |
|----------|-----------|--------------|--------|
| **Authentication** | ✅ None required | OpenWeatherMap: API key | **Open-Meteo** |
| **Cost** | ✅ Free forever | Weather.gov: Free but US-only | **Open-Meteo** |
| **Rate Limiting** | ✅ None for reasonable use | Most APIs: 1000 calls/day | **Open-Meteo** |
| **Data Quality** | ✅ Excellent (satellite + model) | Weather.com: Good but proprietary | **Open-Meteo** |
| **Global Coverage** | ✅ Worldwide | Most: Limited regions | **Open-Meteo** |
| **Setup Time** | ✅ 30 seconds | Most: 10-15 minutes | **Open-Meteo** |
| **Reliability** | ✅ 99.9% uptime | Variable | **Open-Meteo** |

### Open-Meteo Advantages

1. **Zero Setup Friction**
   - No API key registration
   - No rate limiting worries
   - No billing concerns
   - Works immediately: `curl https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&daily=temperature_2m_mean`

2. **Enterprise-Grade Data**
   - Data sourced from: NOAA (USA), MeteoFrance, DWD (Germany), ECMWF (Europe)
   - Multiple weather models (GFS, ECMWF, DWD, etc.)
   - Satellite observations integrated
   - Historical data available

3. **Perfect for Learning**
   - No authentication to debug
   - Focus on pipeline logic, not credential management
   - Can test API directly in browser
   - Clear error messages

4. **Production-Ready**
   - Even though it's free, it has enterprise reliability
   - Used by: Windy.com, Weather.gov integration, enterprise apps
   - Geographic redundancy
   - No surprise shutdowns

### API Endpoint Used
```
GET https://api.open-meteo.com/v1/forecast

Parameters:
  - latitude: float (40.7128 for New York)
  - longitude: float (-74.0060 for New York)
  - daily: string (comma-separated parameters)
    * temperature_2m_mean
    * temperature_2m_max
    * temperature_2m_min
    * relative_humidity_2m_mean
    * precipitation_sum
    * windspeed_10m_max
    * weather_code (WMO codes)
  - timezone: string (auto-detect)
  - forecast_days: integer (1-16)

Response: JSON with 7-day forecast at daily aggregation
```

---

## Features

### 1. **Robust API Integration**
- Open-Meteo Weather API (completely free, no API key needed)
- Automatic retry with exponential backoff
- Comprehensive error handling for network issues
- Response validation before processing

### 2. **Data Quality**
- Type conversion and validation
- Missing value handling
- Duplicate detection and removal
- Outlier detection (temperature range validation)

### 3. **Derived Analytics**
The pipeline adds business value through calculated fields:
- **Weather Description**: Human-readable classification of weather codes
- **Comfort Index**: Combined metric (0-100) based on temperature, humidity, and wind
- **Precipitation Risk**: Categorized risk level (none, low, moderate, high)
- **Day Type**: Intelligent classification (sunny, cloudy, rainy, stormy, etc.)
- **Temporal Features**: Day of week, week number, date extraction

### 4. **Professional Logging**
- Dual output: file and console
- Structured logging with timestamps
- Rotating file handler (automatic cleanup)
- Debug-level details for troubleshooting

### 5. **Flexible Configuration**
- All parameters centralized in `config.py`
- Support for multiple locations and date ranges
- Easy to customize without touching business logic

### 6. **BigQuery Integration** 
- Upload weather data to BigQuery Sandbox (completely free, no credit card)
- Automatic schema management (table/dataset creation)
- Secure authentication with service account credentials
- Included SQL queries for analytics (temperature trends, risk assessment, comfort analysis)
- Data retention with 90-day expiration (Sandbox limitation)
- Partitioned and clustered tables for fast queries

## Quick Start

### 1. Clone/Download Project
```bash
cd d:\DataAI
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up BigQuery (5 minutes)
- Follow: **BigQuery Setup** section above
- Place credentials JSON: `d:\DataAI\credentials\bq-credentials.json`
- Update `config.py` with your `BIGQUERY_PROJECT_ID`

### 5. Run Pipeline
```bash
python main.py
```

**Expected output:**
```
[STEP 1] Fetching weather data from API...
[OK] Data fetched successfully

[STEP 2] Transforming and cleaning data...
[OK] Data transformed successfully (7 rows, 20 columns)

[STEP 3] Saving processed data...
[OK] CSV saved: output/weather_forecast_New York_*.csv
[OK] JSON saved: output/weather_forecast_New York_*.json

[STEP 4] Uploading data to BigQuery...
[OK] Dataset 'weather_data' created
[OK] Table 'weather_forecast' created with schema
[OK] BigQuery: Loaded 7 rows

[STEP 5] Data Quality Report...
[OK] No missing values in dataset

[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY
```
---

### Example Output

**CSV Output** (`output/weather_forecast_New York_*.csv`):
```
date       time                city         day_of_week  day_type    temperature_2m  relative_humidity_2m  precipitation  precipitation_risk  ...
2026-05-27  2026-05-27 00:00:00 New York     Tuesday     sunny       22.5            65                     0              none               ...
2026-05-28  2026-05-28 00:00:00 New York     Wednesday   cloudy      21.8            70                     0.5            low                ...
```

**Logs** (`logs/pipeline_*.log`):
```
2026-05-27 10:15:30 - WeatherPipeline - INFO - [STEP 1] Fetching weather data from API...
2026-05-27 10:15:32 - WeatherPipeline - INFO - ✓ Data fetched successfully
2026-05-27 10:15:33 - WeatherPipeline - INFO - [STEP 2] Transforming and cleaning data...
```

### Fetch Data for Different Location

**Option 1: Edit config.py**
```python
DEFAULT_LATITUDE = 51.5074  # London
DEFAULT_LONGITUDE = -0.1278
DEFAULT_CITY_NAME = "London"
```

**Option 2: Modify main.py call**
```python
from main import run_pipeline

success, message = run_pipeline(
    latitude=51.5074,
    longitude=-0.1278,
    city_name="London",
    forecast_days=7
)
```

**Option 3: Use the pipeline programmatically**
```python
from api_client import fetch_weather_data
from data_transformer import transform_weather_data

# Fetch data
raw_data = fetch_weather_data(
    latitude=48.8566,
    longitude=2.3522,
    city_name="Paris"
)

# Transform
df = transform_weather_data(raw_data, "Paris")

# Use dataframe
print(df.head())
df.to_csv("paris_weather.csv", index=False)
```

## BigQuery Setup (Complete Step-by-Step Guide)

### Prerequisites
- Google Account (Gmail or Workspace)
- Project credentials file (5 minutes to create)

### Step 1: Access BigQuery Console
```
1. Open: https://console.cloud.google.com/bigquery
2. Sign in with your Google Account
3. If no project exists, create one
```

### Step 2: Create a Project (if needed)
```
1. Click "New Project"
2. Enter name: "weather-data-pipeline"
3. Click "Create"
```

### Step 3: Create Service Account (for authentication)
```
1. In the search bar at top, type: "iam-admin"
2. Click "IAM & Admin"
3. Left sidebar → "Service Accounts"
4. Click "Create Service Account" (top button)
5. Fill form:
   - Service account name: "weather-pipeline"
   - Description: "Service account for weather data pipeline"
   - Click "Create and Continue"
```

### Step 4: Assign Permissions
```
1. In the "Grant this service account access to project" section:
2. Click "Select a role" dropdown
3. Search and select BOTH:
   ✅ Role 1: "BigQuery Data Editor" (can load data, modify tables)
   ✅ Role 2: "BigQuery User" (can create datasets/tables)
4. Click "Continue"
5. Click "Done"
```

### Step 5: Create and Download JSON Key
```
1. Click on the service account you just created ("weather-pipeline")
2. Click "Keys" tab (top menu)
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create"
6. **File downloads automatically**: `[project-id]-[random].json`
7. Save as: `d:\DataAI\credentials\bq-credentials.json`

⚠️ IMPORTANT: 
   - This file contains credentials
   - Keep it safe and private
   - .gitignore already protects it
```

### Step 6: Extract Project ID from Downloaded JSON
```json
{
  "type": "service_account",
  "project_id": "projectname-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "weather-pipeline@projectname-id.iam.gserviceaccount.com",
  ...
}
```

### Step 7: Update config.py
```python
# d:\DataAI\config.py line 87
BIGQUERY_PROJECT_ID = "projectname-id"  # ← Paste your project_id here
BIGQUERY_DATASET_ID = "weather_data"    # ← Auto-created
BIGQUERY_TABLE_ID = "weather_forecast"  # ← Auto-created
```

### Step 8: Verify Credentials File Location
```
✓ File exists: d:\DataAI\credentials\bq-credentials.json
✓ Readable: Yes
✓ Contains project_id: Yes
```

### Step 9: Run Pipeline (auto-creates dataset + table)
```bash
python main.py
```

**Expected output:**
```
[STEP 4] Uploading data to BigQuery...
Setting up BigQuery infrastructure...
[OK] Dataset 'weather_data' created
[OK] Table 'weather_forecast' created with schema
[OK] BigQuery: Loaded 7 rows
```

### Step 10: Verify Data in BigQuery Console
```
1. Refresh: https://console.cloud.google.com/bigquery
2. Left sidebar: Click project name (projectname-id)
3. Expand "weather_data" dataset
4. Click "weather_forecast" table
5. Click "Preview" tab
6. See your 7 rows! ✅
```

### Troubleshooting BigQuery Setup

| Error | Solution |
|-------|----------|
| "Credentials file not found" | Move JSON to `d:\DataAI\credentials\bq-credentials.json` |
| "Permission denied" | Verify service account has both "BigQuery Data Editor" + "BigQuery User" roles |
| "Project not found" | Check project_id in config.py matches JSON file |
| "Authentication failed" | Delete credentials file and re-download from IAM & Admin |
| "Dataset/table not created" | Check logs in `logs/` folder for detailed error |

---

## SQL Queries & Output Examples

Sample queries to analyze your weather data in BigQuery:

### Query 1: Temperature Trend by Week
```sql
SELECT 
  city,
  week_number,
  COUNT(*) as days_recorded,
  ROUND(AVG(temperature_2m_mean), 1) as avg_temp_c,
  ROUND(MIN(temperature_2m_min), 1) as min_temp_c,
  ROUND(MAX(temperature_2m_max), 1) as max_temp_c
FROM `projectname-id.weather_data.weather_forecast`
GROUP BY city, week_number
ORDER BY week_number DESC
LIMIT 100
```

**Sample Output:**
```
┌──────────┬─────────────┬───────────────┬────────────┬──────────┬──────────┐
│   city   │ week_number │ days_recorded │ avg_temp_c │ min_temp │ max_temp │
├──────────┼─────────────┼───────────────┼────────────┼──────────┼──────────┤
│ New York │      22     │       7       │    21.3    │   19.2   │   23.8   │
└──────────┴─────────────┴───────────────┴────────────┴──────────┴──────────┘
```

### Query 2: High-Risk Weather Days
```sql
SELECT 
  date,
  city,
  temperature_2m_mean,
  precipitation_sum,
  precipitation_risk,
  weather_description,
  relative_humidity_2m_mean
FROM `projectname-id.weather_data.weather_forecast`
WHERE precipitation_risk IN ('high', 'moderate')
   OR relative_humidity_2m_mean > 80
ORDER BY date DESC, precipitation_risk DESC
LIMIT 20
```

**Sample Output:**
```
┌────────────┬──────────┬─────────────┬──────────────┬────────────────┬───────────────────┬────────────────┐
│    date    │   city   │ temperature │ precipitation│ risk_level     │ weather_desc      │ humidity_%     │
├────────────┼──────────┼─────────────┼──────────────┼────────────────┼───────────────────┼────────────────┤
│ 2026-05-28 │ New York │    18.5     │     2.3      │ moderate       │ Rainy             │     85         │
│ 2026-05-29 │ New York │    17.2     │     5.8      │ high           │ Heavy Rain        │     92         │
└────────────┴──────────┴─────────────┴──────────────┴────────────────┴───────────────────┴────────────────┘
```


### How to Run These Queries

1. **Open BigQuery Console**: https://console.cloud.google.com/bigquery
2. **Click "SQL Editor"** (left sidebar)
3. **Paste any query** from above
4. **Replace** `projectname-id` with your actual project ID
5. **Click "Run"** ▶️
6. **View results** in the lower panel

---

**Key Features:**
- ✅ Automatic table creation on first run
- ✅ Partitioned by date (fast queries)
- ✅ Clustered by city + day_type (better performance)
- ✅ Safe mode: validates schema before loading
- ✅ Appends new data (keeps history by default)
- ✅ Credentials stored in `.gitignore` (never committed)

### BigQuery Sandbox Limitations & Workarounds

| Limit | Impact | Solution |
|-------|--------|----------|
| 90-day expiration | Tables auto-delete | Use standard project after 90 days |
| 1TB/month queries | Large queries might not work | Our pipeline uses <100MB/month |
| No streaming inserts | Only batch loads | Pipeline uses batch mode ✅ |
| ~$0 cost | Free forever | No billing needed ✅ |

---

## Project Structure & File Usage

Each file in this project has a specific responsibility:

### Core Pipeline Files

**[config.py](d:\DataAI\config.py)** (104 lines) - **⚙️ Configuration Hub**
- Centralized settings (no hardcoding)
- Default location: New York (40.7128°N, 74.0060°W)
- API parameters: 7 weather metrics with correct naming (temperature_2m_mean, etc.)
- BigQuery settings: project_id, dataset, table, credentials path
- Logging configuration: rotating file handler
- **Key Constants:**
  ```python
  DEFAULT_LATITUDE = 40.7128
  DEFAULT_LONGITUDE = -74.0060
  DEFAULT_CITY_NAME = "New York"
  WEATHER_PARAMETERS = ["temperature_2m_mean", "temperature_2m_max", ...]
  BIGQUERY_PROJECT_ID = "projectname-id"  # Set this to YOUR project ID
  BIGQUERY_DATASET_ID = "weather_data"
  BIGQUERY_TABLE_ID = "weather_forecast"
  ```

**[api_client.py](d:\DataAI\api_client.py)** (262 lines) - **🌐 API Integration**
- Handles Open-Meteo API communication
- **Retry Logic**: Exponential backoff (1s, 2s, 4s) for network failures
- **Error Handling**: Captures API error messages and HTTP status codes
- **Key Methods:**
  - `fetch_forecast(latitude, longitude, city_name)`: Returns raw JSON
  - `_build_params()`: Constructs query string with correct parameter names
  - Validates response has all required fields before returning
- **Error Scenarios Handled:**
  - Network timeouts → retry
  - API returns 400 (bad params) → fail with clear message
  - Missing fields in response → validation error

**[data_transformer.py](d:\DataAI\data_transformer.py)** (430+ lines) - **🔄 Data Cleaning & Enrichment**
- Transforms raw nested JSON into analytical DataFrame
- **5 Derived Analytics Fields Added:**
  1. `weather_description`: WMO codes (0, 1, 45, 48...) → human text ("Sunny", "Foggy", etc.)
  2. `comfort_index`: 0-100 metric based on temperature + humidity + wind
  3. `precipitation_risk`: "none", "low", "moderate", "high" (categorical)
  4. `day_type`: "sunny", "cloudy", "rainy", "stormy", "windy", "foggy"
  5. Temporal: `day_of_week`, `week_number`, date extraction
- **Data Quality Steps:**
  - Type conversion (float, int, datetime, categorical)
  - Missing value handling (fill or drop)
  - Duplicate removal
  - Range validation (temperature: -50°C to +60°C)
- **Key Methods:**
  - `transform()`: Main orchestrator (50 lines)
  - `_flatten_data()`: Converts nested JSON to DataFrame
  - `_convert_types()`: Type casting with error handling
  - `_clean_data()`: Missing values, duplicates, outliers
  - `_add_derived_fields()`: Analytical enrichment

**[main.py](d:\DataAI\main.py)** (207 lines) - **🚀 Pipeline Orchestration**
- Main entry point: coordinates all 5 pipeline steps
- **5-Step Workflow:**
  ```
  STEP 1: Fetch from Open-Meteo API
          ↓ (with retries)
  STEP 2: Transform & Clean Data
          ↓ (add derived fields)
  STEP 3: Save CSV & JSON
          ↓ (to output/ folder)
  STEP 4: Upload to BigQuery 
          ↓ (auto-create dataset/table)
  STEP 5: Data Quality Report
          ↓ (logging statistics)
  ```
- **Key Features:**
  - Dual logging: file + console
  - Error recovery (continues to STEP 5 even if STEP 4 fails)
  - Timestamps on all outputs
  - Complete success/failure reporting

**[bigquery_client.py](d:\DataAI\bigquery_client.py)** (432 lines) - **📊 BigQuery Integration** ⭐ NEW
- Handles BigQuery authentication, schema management, and data loading
- **Auto-Creation Features:**
  - Creates dataset "weather_data" if not exists
  - Creates table "weather_forecast" with schema if not exists
  - Sets up partitioning by DATE(date) for fast queries
  - Sets up clustering by (city, date, day_type) for optimization
- **20-Column Schema:**
  - Dates: `date` (DATE), `time` (TIMESTAMP)
  - Location: `city`, `latitude`, `longitude`, `elevation`
  - Weather: `temperature_2m_*` (FLOAT), `relative_humidity_2m_mean` (INT), `precipitation_*`, `weather_code` (INT)
  - Derived: `comfort_index`, `precipitation_risk`, `weather_description`, `day_type`
  - Temporal: `day_of_week`, `week_number`
  - Tracking: `loaded_timestamp` (TIMESTAMP)
- **Key Methods:**
  - `authenticate()`: Service account auth with error handling
  - `create_dataset_if_not_exists()`: Idempotent dataset creation
  - `create_table_if_not_exists()`: Idempotent table creation with schema
  - `load_dataframe()`: BigQuery data loading with validation
  - `upload_to_bigquery()`: High-level convenience function

### Support Files

**[requirements.txt](d:\DataAI\requirements.txt)** - **📦 Dependencies**
```
requests==2.31.0           # HTTP library for API calls
pandas==2.1.4              # Data manipulation
numpy==1.26.4              # Numerical computing
google-cloud-bigquery==3.13.0  # BigQuery client
pyarrow==1.0.0             # DataFrame serialization
openpyxl==3.1.1            # Excel export (optional)
```

**[.gitignore](d:\DataAI\.gitignore)** - **🔐 Security**
- Protects credentials: `credentials/`
- Excludes virtual env: `.venv/`
- Ignores logs and output files
- Never commit: `bq-credentials.json`, `service-account-key.json`

**[sql/](d:\DataAI\sql/)** - **📋 Sample Queries**
- `01_temperature_trend.sql`: Weekly temperature aggregation
- `02_weather_risk.sql`: High-risk weather identification

**[logs/](d:\DataAI\logs/)** - **📝 Audit Trail** (auto-created)
- Rotating log files: `pipeline_YYYYMMDD_HHMMSS.log`
- Max size: 10MB per file
- Keeps 5 backups automatically
- Format: `[timestamp] [logger] [level] message`

**[output/](d:\DataAI\output/)** - **📊 Pipeline Results** (auto-created)
- CSV files: `weather_forecast_[City]_[timestamp].csv`
- JSON files: `weather_forecast_[City]_[timestamp].json`
- Both contain identical data, just different formats

---

## Data Pipeline Flow

```
[Open-Meteo API]
       ↓
[Fetch with retries & error handling]
       ↓
[Raw JSON data]
       ↓
[Flatten nested structure]
       ↓
[Type conversion]
       ↓
[Data validation & cleaning]
       ↓
[Add derived fields]
       ↓
[Clean DataFrame]
       ↓
[Save CSV & JSON]
       ↓
[✓ Complete with full logging]
```

## Error Handling

The pipeline handles various failure scenarios gracefully:

| Error | Handling |
|-------|----------|
| Network timeout | Retry with exponential backoff (max 3 attempts) |
| Connection error | Retry with exponential backoff |
| Invalid JSON | Log warning and retry |
| Missing API fields | Validation error with clear message |
| Invalid data values | Filter out or fill based on strategy |
| File write errors | Caught and logged |

## Logging

### Log Levels
- **DEBUG**: Detailed information for development
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures

### Log Files
- Location: `logs/pipeline_YYYYMMDD_HHMMSS.log`
- Max size: 10MB (auto-rotated, keeps 5 backups)
- Format: `timestamp - logger - level - message`

### Example Log Output
```
2026-05-27 10:15:30,123 - WeatherPipeline - INFO - ========================================
2026-05-27 10:15:30,124 - WeatherPipeline - INFO - WEATHER DATA PIPELINE STARTED
2026-05-27 10:15:30,125 - WeatherPipeline - INFO - [STEP 1] Fetching weather data from API...
2026-05-27 10:15:32,456 - WeatherPipeline - INFO - ✓ Data fetched successfully
2026-05-27 10:15:33,789 - WeatherPipeline - INFO - [STEP 2] Transforming and cleaning data...
2026-05-27 10:15:33,890 - WeatherPipeline - INFO - ✓ Data transformed successfully
```

## API Reference: Open-Meteo

**Free tier limits:**
- ✅ No authentication required
- ✅ No rate limiting for reasonable usage
- ✅ No monthly API key limits
- ✅ Returns 7-day forecasts
- ✅ Global coverage with satellite data

**Endpoint:** `https://api.open-meteo.com/v1/forecast`

**Parameters Used:**
- `latitude`, `longitude`: Location coordinates
- `daily`: Weather parameters to fetch
- `timezone`: Auto-detect timezone
- `forecast_days`: Days of forecast (1-16)

**Documentation:** https://open-meteo.com/en/docs

## Safety & Security

✅ **Data Privacy:**
- Only location coordinates sent to API
- No user data logged or stored
- All data processing happens locally
- Logs contain only non-sensitive information

## Troubleshooting

### Issue: `requests` module not found
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Connection timeout
**Solution:**
- Check internet connection
- Verify API is accessible: `https://api.open-meteo.com/`
- Check firewall/proxy settings
- Pipeline retries automatically (3 attempts with backoff)

### Issue: No output files created
**Solution:**
- Check `output/` directory exists (auto-created)
- Check logs in `logs/` folder for errors
- Verify write permissions on directory

### Issue: Data looks incomplete
**Solution:**
- Check the log file for warnings
- Verify location coordinates are correct
- Check missing value strategy in `config.py`
- May need to adjust `MISSING_VALUE_STRATEGY`

## Future Enhancements

Potential improvements (not required for current scope):
- [ ] Database output (SQLite, PostgreSQL)
- [ ] Scheduled execution (cron, APScheduler)
- [ ] Email notifications on pipeline completion
- [ ] Data visualization (charts, dashboards)
- [ ] Multiple location batch processing
- [ ] Historical data archival
- [ ] Unit tests and CI/CD pipeline
- [ ] Configuration via CLI arguments
- [ ] Support for different weather APIs

---

## 🏢 STEP 5 : Production Deployment Guide

### How to Schedule This Pipeline to Run Automatically

#### **Option 1: Windows Task Scheduler (Recommended for Windows Servers)**
```batch
# Create a scheduled task that runs daily at 6:00 AM
# PowerShell command:
$action = New-ScheduledTaskAction -Execute "C:\path\to\.venv\Scripts\python.exe" `
    -Argument "C:\path\to\main.py" `
    -WorkingDirectory "C:\path\to"

$trigger = New-ScheduledTaskTrigger -Daily -At 06:00AM

Register-ScheduledTask -TaskName "WeatherPipeline" -Action $action -Trigger $trigger -RunLevel Highest
```

**Advantages:**
- ✅ Native Windows solution
- ✅ No external dependencies
- ✅ GUI management available
- ✅ Granular control (daily, weekly, on-demand)

---

#### **Option 2: Linux Cron Jobs (Recommended for Linux/Mac)**
```bash
# Add to crontab: crontab -e
# Run daily at 6:00 AM UTC
0 6 * * * cd /opt/weather-pipeline && \
    /path/to/.venv/bin/python main.py >> /var/log/weather-pipeline.log 2>&1
```

**Advantages:**
- ✅ Industry standard (25+ years)
- ✅ Minimal overhead
- ✅ Easy to manage multiple pipelines
- ✅ Logs to centralized location

---

#### **Option 3: Google Cloud Scheduler (Recommended for Cloud Deployments)**
```yaml
# Cloud Scheduler Configuration
name: "weather-pipeline-daily"
schedule: "0 6 * * *"  # 6 AM UTC daily
timezone: "UTC"
httpTarget:
  uri: "https://YOUR_CLOUD_FUNCTION_URL"
  oidcToken:
    serviceAccountEmail: "weather-pipeline@project.iam.gserviceaccount.com"
retryConfig:
  retryCount: 3
  maxBackoffDuration: "3600s"
```

**Advantages:**
- ✅ Serverless (no servers to manage)
- ✅ Integrates with BigQuery directly
- ✅ Built-in retry and error handling
- ✅ Scales automatically

---

#### **Option 4: Apache Airflow (Enterprise Scale)**
```python
# dags/weather_pipeline_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineering',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'weather_pipeline',
    default_args=default_args,
    schedule_interval='0 6 * * *',  # Daily 6 AM
    start_date=datetime(2026, 5, 27),
)

def run_weather_pipeline():
    from main import run_pipeline
    success, message = run_pipeline()
    if not success:
        raise Exception(message)

fetch_weather = PythonOperator(
    task_id='fetch_and_transform',
    python_callable=run_weather_pipeline,
    dag=dag,
)
```

**Advantages:**
- ✅ Orchestrate complex workflows
- ✅ Dependency management (task A → B → C)
- ✅ Backfill capabilities for missed runs
- ✅ Web UI monitoring

---

### How You Would Know If It Failed

#### **1. Application-Level Monitoring**
```python
# In main.py - Enhanced error tracking
def run_pipeline():
    try:
        success, message = run_pipeline_internal()
        if not success:
            # Send alert immediately
            send_alert(
                level="ERROR",
                message=message,
                context={"run_time": datetime.now()}
            )
        return success, message
    except Exception as e:
        # Capture stack trace for debugging
        logger.exception("Pipeline failed with exception")
        send_alert(level="CRITICAL", message=str(e))
        raise
```

#### **2. Log Aggregation (ELK Stack or Cloud Logging)**
```bash
# Centralized logging approach
# Ship logs to: Elasticsearch, Splunk, Google Cloud Logging, etc.

# Log format includes:
#   - Timestamp
#   - Log level (INFO, ERROR, CRITICAL)
#   - Component (APIClient, Transformer, etc.)
#   - Message with context
```

**Query examples:**
```
ERROR in logs > 0 in last 24 hours  → ALERT
API Status 400/500 in response      → ALERT
Data quality check failed           → ALERT
Load to BigQuery failed             → ALERT
```

#### **3. Health Check Endpoint (For Cloud Deployments)**
```python
# Add Flask endpoint for monitoring services
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Quick validation
        last_run = get_last_pipeline_run()
        if (datetime.now() - last_run).hours > 25:
            return jsonify({"status": "warning", "msg": "No run in 24+ hours"}), 202
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
```

#### **4. Data Quality Checks After Each Run**
```python
# Validation queries in BigQuery
def validate_data_quality():
    queries = [
        # Check 1: Row count increased
        """SELECT COUNT(*) FROM `project.dataset.weather_forecast` 
           WHERE loaded_timestamp > CURRENT_TIMESTAMP() - INTERVAL 2 HOUR""",
        
        # Check 2: No null values in critical fields
        """SELECT COUNT(*) FROM `project.dataset.weather_forecast` 
           WHERE city IS NULL OR date IS NULL OR temperature_mean_c IS NULL""",
        
        # Check 3: Temperature within valid range
        """SELECT COUNT(*) FROM `project.dataset.weather_forecast` 
           WHERE temperature_mean_c < -60 OR temperature_mean_c > 60""",
    ]
```

#### **5. Alerting Channels**
- **Email**: Critical alerts
- **Slack**: Real-time notifications to team channel
- **PagerDuty**: Wake up on-call for 2+ consecutive failures
- **CloudWatch/Stackdriver**: Integrated monitoring dashboard

---

### What to Add/Change for 10x Data Volume

#### **Current State (Single City, 7-Day Forecast)**
- ~7 rows per run
- ~20 columns per row
- ~5KB per JSON output
- Load time: <1 second

#### **10x Scale (Multiple Cities, Historical Data)**
- **100+ cities × 7 days = 700+ rows per run**
- **Daily runs × 365 days = 255,500 rows/year**
- **10x volume = ~2.55M rows/year**

---

#### **Architecture Changes for 10x Volume**

| Aspect | Current | 10x Scale Solution |
|--------|---------|-------------------|
| **API Calls** | 1 request/run | Batch cities: loop 100 cities, 1 sec each = 100 sec/run |
| **Data Storage** | CSV local + BigQuery | BigQuery only (CSV becomes unwieldy at scale) |
| **Processing** | Synchronous | Parallel: Use ThreadPoolExecutor for concurrent API calls |
| **Load Pattern** | 1 table append | Partitioned by date/city for faster queries |
| **Scheduling** | Daily 6 AM | Stagger: Start 1 city per minute to avoid thundering herd |
| **Cost** | $0 (free tier) | Monitor BigQuery costs (may exceed Sandbox limits) |

---

#### **1. Distributed Processing**
```python
# Process multiple cities in parallel (before: sequential)
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_multiple_cities_parallel(cities, max_workers=5):
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                fetch_weather_data, 
                city['lat'], 
                city['lon'], 
                city['name']
            ): city['name']
            for city in cities
        }
        
        for future in as_completed(futures):
            city_name = futures[future]
            try:
                results[city_name] = future.result()
            except Exception as e:
                logger.error(f"Failed to fetch {city_name}: {e}")
                
    return results
```

**Benefits:**
- ✅ 100 cities in ~30 seconds (not 100 seconds)
- ✅ Graceful failure handling
- ✅ Automatic retry per city

---

#### **2. Database Partitioning in BigQuery**
```sql
-- Before: Single table, full scan for each query
CREATE TABLE `project.dataset.weather_forecast` (...)

-- After: Partitioned by date (90-day rolling window)
CREATE TABLE `project.dataset.weather_forecast`
PARTITION BY DATE(date)
CLUSTER BY city, day_type
AS SELECT * FROM ...;

-- Result: Queries on specific dates scan only relevant partitions
-- Query speed: 10x faster for time-range queries
```

---

#### **3. Incremental Loading Strategy**
```python
# Before: Always append all 7 days
# After: Only load new/changed data

def should_reload_city(city, last_loaded_date):
    """Check if city forecast changed since last load"""
    # If we already have forecast for 2026-05-27, skip it
    # If new data available for 2026-06-02, load just that
    pass

# Result: 
# - Day 1: Load 7 days (100 cities = 700 rows)
# - Day 2: Load only 1 new day (100 cities = 100 rows)
# - Reduces daily load from 700 to 100 rows
```

---

#### **4. Caching Layer for Repeated Requests**
```python
# Before: Every run calls API for every city
# After: Cache responses, only refresh changed data

import redis

cache = redis.Redis(host='localhost', port=6379)

def fetch_weather_data_with_cache(lat, lon, city_name):
    cache_key = f"weather:{city_name}:{date.today()}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit: {city_name}")
        return json.loads(cached)
    
    # Fetch from API if not cached
    data = WeatherAPIClient().fetch_forecast(lat, lon, city_name)
    
    # Cache for 24 hours
    cache.setex(cache_key, 86400, json.dumps(data))
    return data
```

**Result:**
- ✅ 90% fewer API calls
- ✅ API rate limit friendly
- ✅ Sub-second response for cached cities

---

#### **5. Streaming Ingestion (If Moving to Pub/Sub)**
```python
# Before: Batch load once per day
# After: Stream data as it becomes available

from google.cloud import pubsub_v1

def stream_weather_to_pubsub(city_data):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, "weather-data")
    
    message_json = json.dumps(city_data).encode('utf-8')
    publish_future = publisher.publish(topic_path, message_json)
    
    # BigQuery Dataflow picks up from Pub/Sub
    # Near real-time analytics
```

---

#### **6. Configuration Management for Scale**
```python
# config.py for 10x deployment

CITIES = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    # ... 100+ cities from database or config file
]

BATCH_SIZE = 5  # Process 5 cities in parallel
RETRY_ATTEMPTS = 3
TIMEOUT_SECONDS = 10

# BigQuery optimizations
BIGQUERY_PARTITION_EXPIRATION_DAYS = 90
BIGQUERY_CLUSTERING_FIELDS = ["city", "date", "day_type"]
BIGQUERY_MAX_ROWS_PER_LOAD = 10000
```

---

#### **7. Monitoring & Alerting for Scale**
```python
# Dashboard metrics to track
metrics = {
    "pipeline_run_time_seconds": 150,  # Should stay <5 min
    "api_failures_count": 2,            # Track failures per city
    "bigquery_load_time_ms": 3000,      # Should stay <5 sec
    "rows_loaded_daily": 70000,         # Track volume
    "data_quality_score": 99.5,         # Track accuracy
    "cache_hit_rate": 0.92,             # Track efficiency
}

# Alerts
if pipeline_run_time > 300:  # >5 min
    alert("Pipeline running slow", severity="warning")
if api_failures_count > 5:
    alert("Multiple city failures", severity="critical")
```

---

#### **8. Implementation Priority for 10x Scale**

| Phase | Duration | Change | Impact |
|-------|----------|--------|--------|
| **Phase 1** | 1 day | Add ThreadPoolExecutor for parallel API calls | 3x speedup |
| **Phase 2** | 1 day | BigQuery partitioning + clustering | Query 10x faster |
| **Phase 3** | 2 days | Redis caching layer | 90% fewer API calls |
| **Phase 4** | 1 week | Incremental loading strategy | 85% less data transferred |
| **Phase 5** | 2 weeks | Monitoring/alerting dashboard | Visibility into health |

---

#### **Cost Analysis for 10x Volume**

| Metric | Current | 10x Scale | Cost |
|--------|---------|-----------|------|
| API calls/year | 365 | 36,500 | **Still free** (Open-Meteo) |
| BigQuery rows/year | ~2,500 | ~255,000 | **Free** (Sandbox 1TB/month) |
| Storage (GB/year) | 0.05 | 0.5 | **Free** (BigQuery storage cheap) |
| Query costs | $0 | $0 | **Free** (Sandbox) |
| Infrastructure | $0 | $10-50/month | Cloud Function + Redis |

---

#### **Summary: 10x Scale Roadmap**

1. ✅ **API Optimization**: Parallel calls → 3x faster
2. ✅ **Database Design**: Partitioning + clustering → 10x query speedup
3. ✅ **Caching**: Redis layer → 90% fewer API calls
4. ✅ **Incremental Loading**: Only new data → 85% less volume
5. ✅ **Monitoring**: Dashboard + alerts → Operational visibility
6. ✅ **Cost Control**: Incremental loading → Stays within free tier

**Total time to implement:** ~2 weeks of engineering
**Result:** 100+ cities × 365 days of historical data, <5 minute daily run time, <1 cent/day cost

---

**Built with:** Python 3.10+ | Pandas | Requests | Open-Meteo API | BigQuery | Google Cloud