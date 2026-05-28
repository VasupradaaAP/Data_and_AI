"""
Configuration module for Weather Data Pipeline
All parameters are centralized here to avoid hardcoding values in business logic
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# ===========================
# PROJECT STRUCTURE
# ===========================
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ===========================
# API CONFIGURATION
# ===========================
API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
API_TIMEOUT = 10  # seconds

# Default location (New York City)
# Can be overridden by passing different coordinates to the pipeline
DEFAULT_LATITUDE = 40.7128
DEFAULT_LONGITUDE = -74.0060
DEFAULT_CITY_NAME = "New York"

# Weather parameters to fetch
# Note: Open-Meteo daily parameters use suffixes like _mean, _max, _min, _sum
WEATHER_PARAMETERS = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "windspeed_10m_max",
    "weather_code",
]

# ===========================
# TRANSFORMATION CONFIGURATION
# ===========================
# How to handle missing values: 'drop', 'fill_zero', 'fill_mean'
MISSING_VALUE_STRATEGY = "fill_zero"

# Temperature range validation (in Celsius)
VALID_TEMP_RANGE = (-50, 60)

# ===========================
# OUTPUT CONFIGURATION
# ===========================
# Output file formats
OUTPUT_CSV_FILENAME = "weather_forecast_{city}_{date}.csv"
OUTPUT_JSON_FILENAME = "weather_forecast_{city}_{date}.json"

# Date format for filenames
DATE_FORMAT_FILENAME = "%Y%m%d_%H%M%S"

# ===========================
# LOGGING CONFIGURATION
# ===========================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / f"pipeline_{datetime.now().strftime(DATE_FORMAT_FILENAME)}.log"

# ===========================
# RETRY CONFIGURATION
# ===========================
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # exponential backoff: 1s, 2s, 4s

# ===========================
# DATA FORECAST DAYS
# ===========================
FORECAST_DAYS = 7  # Fetch 7-day forecast

# ===========================
# BIGQUERY CONFIGURATION
# ===========================
# BigQuery Sandbox settings (free tier, no billing required)
BIGQUERY_ENABLED = True  # Set to False to disable BigQuery upload
BIGQUERY_PROJECT_ID = "storage-497612"  # Will be read from credentials if not set
BIGQUERY_DATASET_ID = "weather_data"  # Dataset name
BIGQUERY_TABLE_ID = "weather_forecast"  # Table name
BIGQUERY_WRITE_MODE = "APPEND"  # "APPEND" (add rows) or "WRITE_TRUNCATE" (replace all)

# Credentials path (leave empty to use default locations)
# Priority: env var GOOGLE_APPLICATION_CREDENTIALS → ./credentials/bq-credentials.json → gcloud defaults
BIGQUERY_CREDENTIALS_PATH = ""

def get_output_path(filename_template: str, city_name: str = DEFAULT_CITY_NAME) -> Path:
    """
    Generate output file path with timestamp and city name
    
    Args:
        filename_template: Template string with {city} and {date} placeholders
        city_name: Name of the city (used in filename)
    
    Returns:
        Path object pointing to output file
    """
    timestamp = datetime.now().strftime(DATE_FORMAT_FILENAME)
    filename = filename_template.format(city=city_name, date=timestamp)
    return OUTPUT_DIR / filename

