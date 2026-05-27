"""
Main Weather Data Pipeline
Orchestrates the entire workflow: fetch -> transform -> save
This is the entry point for the data pipeline
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

import config
from api_client import fetch_weather_data, APIClientError
from data_transformer import transform_weather_data, DataTransformationError


def setup_logging() -> logging.Logger:
    """
    Configure logging to both file and console
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("WeatherPipeline")
    logger.setLevel(logging.DEBUG)

    # Create formatters
    file_formatter = logging.Formatter(config.LOG_FORMAT)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def run_pipeline(
    latitude: float = config.DEFAULT_LATITUDE,
    longitude: float = config.DEFAULT_LONGITUDE,
    city_name: str = config.DEFAULT_CITY_NAME,
    forecast_days: int = config.FORECAST_DAYS,
) -> Tuple[bool, str]:
    """
    Execute the complete weather data pipeline
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        city_name: City name (for logging and file naming)
        forecast_days: Number of forecast days
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info(f"WEATHER DATA PIPELINE STARTED")
    logger.info(f"Configuration: {city_name} (lat={latitude}, lon={longitude})")
    logger.info(f"Forecast Days: {forecast_days}")
    logger.info("=" * 80)

    try:
        # ===== STEP 1: FETCH DATA =====
        logger.info("\n[STEP 1] Fetching weather data from API...")
        logger.info(f"URL: {config.API_BASE_URL}")

        raw_data = fetch_weather_data(
            latitude=latitude,
            longitude=longitude,
            city_name=city_name,
            forecast_days=forecast_days,
        )

        logger.info(f"[OK] Data fetched successfully")
        logger.debug(f"Raw data keys: {raw_data.keys()}")
        logger.debug(f"Raw data size: {len(str(raw_data))} bytes")

        # ===== STEP 2: TRANSFORM DATA =====
        logger.info("\n[STEP 2] Transforming and cleaning data...")

        df = transform_weather_data(raw_data, city_name)

        logger.info(f"[OK] Data transformed successfully")
        logger.info(f"Dataset shape: {df.shape} (rows, columns)")
        logger.debug(f"Columns: {list(df.columns)}")

        # ===== STEP 3: SAVE DATA =====
        logger.info("\n[STEP 3] Saving processed data...")

        # Save to CSV
        csv_path = config.get_output_path(config.OUTPUT_CSV_FILENAME, city_name)
        df.to_csv(csv_path, index=False)
        logger.info(f"[OK] CSV saved: {csv_path}")
        logger.debug(f"CSV file size: {csv_path.stat().st_size} bytes")

        # Save to JSON
        json_path = config.get_output_path(config.OUTPUT_JSON_FILENAME, city_name)
        df.to_json(json_path, orient="records", indent=2, date_format="iso")
        logger.info(f"[OK] JSON saved: {json_path}")
        logger.debug(f"JSON file size: {json_path.stat().st_size} bytes")

        # ===== STEP 4: DATA QUALITY SUMMARY =====
        logger.info("\n[STEP 4] Data Quality Report...")
        _log_data_quality_summary(logger, df)

        # ===== SUCCESS =====
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        success_msg = (
            f"Pipeline completed successfully!\n"
            f"  • CSV: {csv_path}\n"
            f"  • JSON: {json_path}\n"
            f"  • Rows: {len(df)}\n"
            f"  • Columns: {len(df.columns)}"
        )
        logger.info(success_msg)

        return True, success_msg

    except APIClientError as e:
        error_msg = f"API Error: {str(e)}"
        logger.error(f"[FAILED] {error_msg}")
        logger.error("The external API is unavailable or returned invalid data.")
        logger.error("Please check your internet connection and try again.")
        return False, error_msg

    except DataTransformationError as e:
        error_msg = f"Data Transformation Error: {str(e)}"
        logger.error(f"[FAILED] {error_msg}")
        logger.error("Failed to process the fetched data.")
        return False, error_msg

    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        logger.error(f"[FAILED] {error_msg}")
        logger.exception("Full traceback:")
        return False, error_msg


def _log_data_quality_summary(logger: logging.Logger, df) -> None:
    """
    Log a summary of data quality metrics
    
    Args:
        logger: Logger instance
        df: DataFrame to analyze
    """
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Total columns: {len(df.columns)}")

    # Missing values summary
    missing = df.isna().sum()
    if missing.any():
        logger.info(f"Columns with missing values:")
        for col, count in missing[missing > 0].items():
            logger.info(f"  • {col}: {count} missing ({count/len(df)*100:.1f}%)")
    else:
        logger.info(f"[OK] No missing values in dataset")

    # Data type summary
    logger.info(f"Data types:")
    for col, dtype in df.dtypes.items():
        logger.debug(f"  • {col}: {dtype}")

    # Sample derived fields
    if "comfort_index" in df.columns:
        logger.info(
            f"Comfort Index range: {df['comfort_index'].min():.1f} - "
            f"{df['comfort_index'].max():.1f}"
        )
    if "day_type" in df.columns:
        logger.info(f"Day type distribution: {dict(df['day_type'].value_counts())}")


def main():
    """Main entry point"""
    # Run with default configuration
    success, message = run_pipeline()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
