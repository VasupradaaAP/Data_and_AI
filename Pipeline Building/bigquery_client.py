"""
BigQuery Client Module
Handles all BigQuery operations: authentication, schema definition, and data loading
Designed for safe operation in BigQuery Sandbox environment
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.oauth2 import service_account


logger = logging.getLogger(__name__)


class BigQueryClient:
    """
    Safe BigQuery client for weather data pipeline
    Handles authentication, schema management, and data loading
    """
    
    def __init__(
        self,
        project_id: str,
        dataset_id: str = "weather_data",
        table_id: str = "weather_forecast",
        credentials_path: Optional[str] = None
    ):
        """
        Initialize BigQuery client with safe authentication
        
        Args:
            project_id: GCP project ID from BigQuery Sandbox
            dataset_id: BigQuery dataset name
            table_id: BigQuery table name
            credentials_path: Path to service account JSON (optional, uses default otherwise)
        
        Raises:
            ValueError: If credentials cannot be found or loaded
            GoogleCloudError: If BigQuery connection fails
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.credentials_path = credentials_path or self._get_default_credentials_path()
        
        # Initialize client
        self.client = self._authenticate()
        logger.info(f"[OK] BigQuery client initialized for project: {project_id}")
    
    @staticmethod
    def _get_default_credentials_path() -> str:
        """
        Get default service account credentials path
        Checks: environment variable, then ./credentials/bq-credentials.json
        
        Returns:
            Path to credentials file
            
        Raises:
            ValueError: If no credentials found
        """
        # Check environment variable first
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            if os.path.exists(path):
                logger.debug(f"Using credentials from env: {path}")
                return path
        
        # Check local credentials directory
        local_path = Path(__file__).parent / "credentials" / "bq-credentials.json"
        if local_path.exists():
            logger.debug(f"Using local credentials: {local_path}")
            return str(local_path)
        
        # Check home directory
        home_creds = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        if home_creds.exists():
            logger.debug(f"Using gcloud credentials: {home_creds}")
            return str(home_creds)
        
        raise ValueError(
            "BigQuery credentials not found. Please:\n"
            "1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable, OR\n"
            "2. Place service account JSON in ./credentials/bq-credentials.json, OR\n"
            "3. Run: gcloud auth application-default login"
        )
    
    def _authenticate(self) -> bigquery.Client:
        """
        Authenticate with BigQuery using service account
        Safe authentication with error handling
        
        Returns:
            Authenticated BigQuery client
            
        Raises:
            ValueError: If credentials invalid
            GoogleCloudError: If connection fails
        """
        try:
            # Verify credentials file exists
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
            
            # Load and validate credentials
            with open(self.credentials_path, 'r') as f:
                creds_data = json.load(f)
            
            # Validate required fields
            required_fields = ["type", "project_id", "private_key_id", "private_key"]
            missing = [f for f in required_fields if f not in creds_data]
            if missing:
                raise ValueError(f"Invalid credentials. Missing fields: {missing}")
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            
            # Create BigQuery client
            client = bigquery.Client(
                project=self.project_id,
                credentials=credentials
            )
            
            # Test connection
            _ = client.project  # Access project property to verify client is valid
            logger.info(f"[OK] Successfully authenticated with BigQuery")
            return client
            
        except FileNotFoundError as e:
            raise ValueError(f"Credentials file not found: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials: {e}")
        except Exception as e:
            raise GoogleCloudError(f"BigQuery authentication failed: {e}")
    
    def create_dataset_if_not_exists(self) -> bool:
        """
        Create dataset if it doesn't exist (safe operation)
        
        Returns:
            True if dataset exists or was created
            
        Raises:
            GoogleCloudError: If dataset creation fails
        """
        try:
            dataset_id_full = f"{self.project_id}.{self.dataset_id}"
            
            try:
                self.client.get_dataset(dataset_id_full)
                logger.info(f"[OK] Dataset '{self.dataset_id}' already exists")
                return True
            except NotFound:
                logger.info(f"Creating dataset: {self.dataset_id}")
                
                # Create dataset with Sandbox defaults
                dataset = bigquery.Dataset(dataset_id_full)
                dataset.location = "US"
                dataset.description = "Weather forecast data pipeline"
                
                # Note: Sandbox doesn't require expiration settings - they're optional
                # No billing required for Sandbox
                dataset = self.client.create_dataset(dataset, exists_ok=True)
                logger.info(f"[OK] Dataset created: {dataset.project}.{dataset.dataset_id}")
                return True
                
        except GoogleCloudError as e:
            logger.error(f"[FAILED] Dataset creation error: {e}")
            raise
    
    def get_table_schema(self) -> List[bigquery.SchemaField]:
        """
        Define the BigQuery table schema for weather data
        
        Returns:
            List of SchemaField objects defining the table structure
        """
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED", description="Forecast date"),
            bigquery.SchemaField("time", "TIMESTAMP", mode="REQUIRED", description="Forecast timestamp"),
            bigquery.SchemaField("city", "STRING", mode="REQUIRED", description="City name"),
            bigquery.SchemaField("day_of_week", "STRING", mode="NULLABLE", description="Day of week"),
            bigquery.SchemaField("day_type", "STRING", mode="NULLABLE", description="Weather classification"),
            
            # Temperature fields
            bigquery.SchemaField("temperature_2m_mean", "FLOAT64", mode="NULLABLE", description="Mean temperature (C)"),
            bigquery.SchemaField("temperature_2m_max", "FLOAT64", mode="NULLABLE", description="Max temperature (C)"),
            bigquery.SchemaField("temperature_2m_min", "FLOAT64", mode="NULLABLE", description="Min temperature (C)"),
            
            # Humidity and precipitation
            bigquery.SchemaField("relative_humidity_2m_mean", "INT64", mode="NULLABLE", description="Mean humidity (%)"),
            bigquery.SchemaField("precipitation_sum", "FLOAT64", mode="NULLABLE", description="Total precipitation (mm)"),
            bigquery.SchemaField("precipitation_risk", "STRING", mode="NULLABLE", description="Precipitation risk level"),
            
            # Wind and weather
            bigquery.SchemaField("windspeed_10m_max", "FLOAT64", mode="NULLABLE", description="Max wind speed (km/h)"),
            bigquery.SchemaField("weather_code", "INT64", mode="NULLABLE", description="WMO weather code"),
            bigquery.SchemaField("weather_description", "STRING", mode="NULLABLE", description="Human-readable weather"),
            
            # Comfort metric
            bigquery.SchemaField("comfort_index", "FLOAT64", mode="NULLABLE", description="Comfort metric (0-100)"),
            
            # Location metadata
            bigquery.SchemaField("timezone", "STRING", mode="NULLABLE", description="Timezone"),
            bigquery.SchemaField("elevation", "FLOAT64", mode="NULLABLE", description="Elevation (meters)"),
            bigquery.SchemaField("latitude", "FLOAT64", mode="NULLABLE", description="Latitude"),
            bigquery.SchemaField("longitude", "FLOAT64", mode="NULLABLE", description="Longitude"),
            
            # Temporal features
            bigquery.SchemaField("week_number", "INT64", mode="NULLABLE", description="ISO week number"),
            
            # Tracking
            bigquery.SchemaField("loaded_timestamp", "TIMESTAMP", mode="REQUIRED", description="Data load time"),
        ]
        return schema
    
    def create_table_if_not_exists(self) -> bool:
        """
        Create table with defined schema if it doesn't exist
        
        Returns:
            True if table exists or was created
            
        Raises:
            GoogleCloudError: If table creation fails
        """
        try:
            table_id_full = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            
            try:
                self.client.get_table(table_id_full)
                logger.info(f"[OK] Table '{self.table_id}' already exists")
                return True
            except NotFound:
                logger.info(f"Creating table: {self.table_id}")
                
                # Create table with schema
                table = bigquery.Table(table_id_full, schema=self.get_table_schema())
                
                # Set partitioning for better query performance
                # Sandbox doesn't require custom expiration - removed for compatibility
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="date"
                )
                
                # Set clustering for better query performance
                table.clustering_fields = ["city", "date", "day_type"]
                
                # Set description
                table.description = "Weather forecast data from Open-Meteo API"
                
                table = self.client.create_table(table)
                logger.info(f"[OK] Table created: {table.project}.{table.dataset_id}.{table.table_id}")
                return True
                
        except GoogleCloudError as e:
            logger.error(f"[FAILED] Table creation error: {e}")
            raise
    
    def load_dataframe(self, df: pd.DataFrame, write_mode: str = "APPEND") -> Tuple[bool, str]:
        """
        Load DataFrame to BigQuery table
        Safe loading with validation and error handling
        
        Args:
            df: DataFrame with weather data
            write_mode: "APPEND" (add new rows) or "WRITE_TRUNCATE" (replace all)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if df.empty:
                logger.warning("DataFrame is empty, skipping BigQuery load")
                return True, "No data to load (empty DataFrame)"
            
            # Add loaded timestamp (as pandas Timestamp for BigQuery compatibility)
            df["loaded_timestamp"] = pd.Timestamp(datetime.utcnow())
            
            # Configure load job
            table_id_full = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            job_config = bigquery.LoadJobConfig(
                schema=self.get_table_schema(),
                write_disposition=f"WRITE_{write_mode}",
                autodetect=False,  # Use explicit schema
                max_bad_records=0,  # Fail if any records are bad (safe mode)
            )
            
            logger.info(f"Loading {len(df)} rows to {table_id_full}")
            
            # Execute load job
            load_job = self.client.load_table_from_dataframe(
                df,
                table_id_full,
                job_config=job_config
            )
            
            # Wait for job completion with timeout
            load_job.result(timeout=300)  # 5 minute timeout
            
            # Check for errors
            if load_job.errors:
                error_msg = f"BigQuery load errors: {load_job.errors}"
                logger.error(f"[FAILED] {error_msg}")
                return False, error_msg
            
            logger.info(
                f"[OK] Successfully loaded {load_job.output_rows} rows to BigQuery"
            )
            return True, f"Loaded {load_job.output_rows} rows"
            
        except Exception as e:
            error_msg = f"BigQuery load failed: {str(e)}"
            logger.error(f"[FAILED] {error_msg}")
            return False, error_msg
    
    def get_row_count(self) -> Optional[int]:
        """
        Get current row count in table
        
        Returns:
            Number of rows in table, or None if query fails
        """
        try:
            table_id_full = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            query = f"SELECT COUNT(*) as count FROM `{table_id_full}`"
            
            result = self.client.query(query).result()
            count = list(result)[0]['count']
            logger.info(f"Table row count: {count}")
            return count
            
        except Exception as e:
            logger.warning(f"Could not get row count: {e}")
            return None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test BigQuery connection and permissions
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Test 1: List datasets
            self.client.list_datasets(max_results=1)
            
            # Test 2: Create dataset if needed
            self.create_dataset_if_not_exists()
            
            # Test 3: Create table if needed
            self.create_table_if_not_exists()
            
            logger.info("[OK] BigQuery connection test successful")
            return True, "BigQuery connection successful"
            
        except Exception as e:
            error_msg = f"BigQuery connection test failed: {str(e)}"
            logger.error(f"[FAILED] {error_msg}")
            return False, error_msg


def upload_to_bigquery(
    df: pd.DataFrame,
    project_id: str,
    dataset_id: str = "weather_data",
    table_id: str = "weather_forecast",
    credentials_path: Optional[str] = None,
    write_mode: str = "APPEND"
) -> Tuple[bool, str]:
    """
    Convenience function to upload DataFrame to BigQuery
    
    Args:
        df: DataFrame to upload
        project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        credentials_path: Path to service account JSON (optional)
        write_mode: "APPEND" or "WRITE_TRUNCATE"
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create client
        client = BigQueryClient(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials_path
        )
        
        # Auto-create dataset and table on first run
        logger.info("Setting up BigQuery infrastructure...")
        client.create_dataset_if_not_exists()
        client.create_table_if_not_exists()
        
        # Load data
        return client.load_dataframe(df, write_mode=write_mode)
        
    except Exception as e:
        logger.error(f"[FAILED] BigQuery upload error: {str(e)}")
        return False, str(e)
