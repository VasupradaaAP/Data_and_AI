"""
Data Transformer for Weather Data Pipeline
Handles cleaning, normalization, and enrichment of raw API responses
Converts raw nested JSON into clean, analytical data
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from config import VALID_TEMP_RANGE, MISSING_VALUE_STRATEGY

# Setup logger
logger = logging.getLogger(__name__)


class DataTransformationError(Exception):
    """Custom exception for data transformation errors"""
    pass


class WeatherDataTransformer:
    """
    Transform raw weather API responses into clean analytical datasets
    Includes data cleaning, validation, and derived field calculation
    """

    # Weather code to description mapping (WMO Weather interpretation codes)
    WEATHER_CODE_MAP = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def __init__(self, city_name: str = "Unknown"):
        """
        Initialize transformer
        
        Args:
            city_name: Name of the city (for logging)
        """
        self.city_name = city_name
        logger.info(f"WeatherDataTransformer initialized for {city_name}")

    def transform(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Transform raw API response into clean DataFrame
        
        Args:
            raw_data: Raw API response dictionary
            
        Returns:
            Cleaned and enriched DataFrame
            
        Raises:
            DataTransformationError: If transformation fails
        """
        logger.info(f"Starting data transformation for {self.city_name}")
        
        try:
            # Step 1: Flatten nested structure
            logger.debug("Step 1: Flattening nested data structure...")
            df = self._flatten_data(raw_data)
            logger.info(f"  [OK] Flattened to {len(df)} rows")

            # Step 2: Type conversion
            logger.debug("Step 2: Converting data types...")
            df = self._convert_types(df)
            logger.info(f"  [OK] Type conversion completed")

            # Step 3: Data cleaning
            logger.debug("Step 3: Cleaning and validating data...")
            initial_rows = len(df)
            df = self._clean_data(df)
            logger.info(f"  [OK] Cleaned: {initial_rows} rows -> {len(df)} rows (removed {initial_rows - len(df)} invalid rows)")

            # Step 4: Add derived fields
            logger.debug("Step 4: Adding derived analytical fields...")
            df = self._add_derived_fields(df, raw_data)
            logger.info(f"  [OK] Added derived fields")

            # Step 5: Reorder columns for readability
            df = self._reorder_columns(df)

            logger.info(f"[OK] Data transformation completed successfully for {self.city_name}")
            logger.debug(f"Final dataset shape: {df.shape}, columns: {list(df.columns)}")

            return df

        except Exception as e:
            error_msg = f"Data transformation failed: {str(e)}"
            logger.error(f"✗ {error_msg}")
            raise DataTransformationError(error_msg) from e

    def _flatten_data(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Flatten nested JSON structure into DataFrame
        
        Args:
            raw_data: Raw API response
            
        Returns:
            DataFrame with flattened data
        """
        daily_data = raw_data.get("daily", {})
        
        if not daily_data:
            raise DataTransformationError("No daily data found in API response")

        # Create DataFrame from daily data
        # All arrays in daily_data should be same length
        df = pd.DataFrame(daily_data)

        # Add metadata
        df["city"] = self.city_name
        df["timezone"] = raw_data.get("timezone", "Unknown")
        df["elevation"] = raw_data.get("elevation", np.nan)
        df["latitude"] = raw_data.get("latitude", np.nan)
        df["longitude"] = raw_data.get("longitude", np.nan)

        logger.debug(f"Flattened data into {len(df)} rows with {len(df.columns)} columns")

        return df

    def _convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert data types to appropriate formats
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with converted types
        """
        df_copy = df.copy()

        # Convert time strings to datetime
        if "time" in df_copy.columns:
            df_copy["time"] = pd.to_datetime(df_copy["time"])
            logger.debug(f"Converted 'time' to datetime")

        # Convert numeric columns
        numeric_cols = [
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "windspeed_10m_max",
            "elevation",
            "latitude",
            "longitude",
        ]

        for col in numeric_cols:
            if col in df_copy.columns:
                try:
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
                except Exception as e:
                    logger.warning(f"Could not convert '{col}' to numeric: {str(e)}")

        # Convert weather_code to integer
        if "weather_code" in df_copy.columns:
            df_copy["weather_code"] = df_copy["weather_code"].astype("Int64", errors="ignore")

        logger.debug(f"Type conversion completed. DataFrame dtypes:\n{df_copy.dtypes}")

        return df_copy

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate data
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        rows_before = len(df_clean)

        # Handle missing values
        if MISSING_VALUE_STRATEGY == "drop":
            df_clean = df_clean.dropna()
            logger.debug(f"Dropped {rows_before - len(df_clean)} rows with missing values")

        elif MISSING_VALUE_STRATEGY == "fill_zero":
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(0)
            logger.debug(f"Filled {df_clean.isna().sum().sum()} missing values with 0")

        elif MISSING_VALUE_STRATEGY == "fill_mean":
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(df_clean[numeric_cols].mean())
            logger.debug(f"Filled missing numeric values with column means")

        # Validate temperature range
        if "temperature_2m_mean" in df_clean.columns:
            temp_min, temp_max = VALID_TEMP_RANGE
            invalid_temps = (
                (df_clean["temperature_2m_mean"] < temp_min) |
                (df_clean["temperature_2m_mean"] > temp_max)
            )
            if invalid_temps.any():
                logger.warning(f"Found {invalid_temps.sum()} temperatures outside valid range {VALID_TEMP_RANGE}°C")
                df_clean = df_clean[~invalid_temps]

        # Remove complete duplicate rows
        duplicates = df_clean.duplicated().sum()
        if duplicates > 0:
            df_clean = df_clean.drop_duplicates()
            logger.debug(f"Removed {duplicates} duplicate rows")

        logger.debug(f"Data cleaning: {rows_before} rows → {len(df_clean)} rows")

        return df_clean

    def _add_derived_fields(self, df: pd.DataFrame, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Add analytical derived fields
        These add business value beyond raw API data
        
        Args:
            df: Input DataFrame
            raw_data: Raw API response (for reference)
            
        Returns:
            DataFrame with derived fields
        """
        df_enriched = df.copy()

        # Derived Field 1: Weather Description from code
        if "weather_code" in df_enriched.columns:
            df_enriched["weather_description"] = df_enriched["weather_code"].map(
                self.WEATHER_CODE_MAP
            ).fillna("Unknown weather")
            logger.debug("[OK] Added 'weather_description' derived field")
        else:
            logger.debug("[SKIP] Weather code not available in API response")

        # Derived Field 2: Comfort Index
        # Simple comfort index: combines temperature, humidity, and wind
        # Higher is more comfortable (simplified model)
        if all(col in df_enriched.columns for col in ["temperature_2m_mean", "relative_humidity_2m_mean", "windspeed_10m_max"]):
            df_enriched["comfort_index"] = self._calculate_comfort_index(
                df_enriched["temperature_2m_mean"],
                df_enriched["relative_humidity_2m_mean"],
                df_enriched["windspeed_10m_max"]
            )
            logger.debug("[OK] Added 'comfort_index' derived field")

        # Derived Field 3: Precipitation Risk Level
        # Categorizes precipitation probability
        if "precipitation_sum" in df_enriched.columns:
            df_enriched["precipitation_risk"] = pd.cut(
                df_enriched["precipitation_sum"],
                bins=[-np.inf, 0, 2.5, 10, np.inf],
                labels=["none", "low", "moderate", "high"],
                include_lowest=True
            )
            logger.debug("[OK] Added 'precipitation_risk' derived field")

        # Derived Field 4: Day type classification
        # Categorizes the day based on weather conditions
        if "weather_code" in df_enriched.columns and "precipitation_sum" in df_enriched.columns:
            df_enriched["day_type"] = self._classify_day_type(
                df_enriched["weather_code"],
                df_enriched["precipitation_sum"],
                df_enriched["windspeed_10m_max"] if "windspeed_10m_max" in df_enriched.columns else None
            )
            logger.debug("[OK] Added 'day_type' derived field")

        # Derived Field 5: Extract features from datetime
        if "time" in df_enriched.columns:
            df_enriched["date"] = df_enriched["time"].dt.date
            df_enriched["day_of_week"] = df_enriched["time"].dt.day_name()
            df_enriched["week_number"] = df_enriched["time"].dt.isocalendar().week
            logger.debug("[OK] Added temporal derived fields (date, day_of_week, week_number)")

        return df_enriched

    @staticmethod
    def _calculate_comfort_index(
        temperature: pd.Series,
        humidity: pd.Series,
        wind_speed: pd.Series
    ) -> pd.Series:
        """
        Calculate a comfort index (0-100)
        Based on temperature, humidity, and wind
        
        Args:
            temperature: Temperature in Celsius
            humidity: Relative humidity percentage
            wind_speed: Wind speed in km/h
            
        Returns:
            Comfort index series (0-100, higher is better)
        """
        # Optimal temperature range: 18-24°C
        temp_score = 100 - np.abs(temperature - 21) * 3
        temp_score = np.clip(temp_score, 0, 100)

        # Optimal humidity: 40-60%
        humidity_score = 100 - np.abs(humidity - 50) * 2
        humidity_score = np.clip(humidity_score, 0, 100)

        # Optimal wind: 0-10 km/h
        wind_score = 100 - np.clip(wind_speed, 0, 20) * 3
        wind_score = np.clip(wind_score, 0, 100)

        # Weighted average (temperature 50%, humidity 30%, wind 20%)
        comfort_index = (temp_score * 0.5 + humidity_score * 0.3 + wind_score * 0.2)

        return np.round(comfort_index, 2)

    @staticmethod
    def _classify_day_type(
        weather_code: pd.Series,
        precipitation: pd.Series,
        wind_speed: pd.Series = None
    ) -> pd.Series:
        """
        Classify day type based on weather conditions
        
        Args:
            weather_code: WMO weather code
            precipitation: Precipitation amount
            wind_speed: Wind speed (optional)
            
        Returns:
            Day type classification
        """
        day_type = []

        for idx, (code, precip) in enumerate(zip(weather_code, precipitation)):
            wind = wind_speed.iloc[idx] if wind_speed is not None else 0

            if pd.isna(code):
                day_type.append("unknown")
            elif code in [0, 1]:
                day_type.append("sunny")
            elif code in [2, 3]:
                if precip > 0:
                    day_type.append("rainy")
                else:
                    day_type.append("cloudy")
            elif code in [45, 48]:
                day_type.append("foggy")
            elif code in [51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 85, 86]:
                day_type.append("rainy")
            elif code in [95, 96, 99]:
                day_type.append("stormy")
            else:
                day_type.append("variable")

            # Override if very windy (>30 km/h)
            if wind > 30:
                day_type[-1] = "windy"

        return pd.Series(day_type, index=weather_code.index)

    @staticmethod
    def _reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Reorder columns for better readability
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with reordered columns
        """
        # Desired column order
        priority_cols = [
            "date", "time", "city", "day_of_week", "day_type",
            "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
            "relative_humidity_2m_mean",
            "precipitation_sum", "precipitation_risk",
            "weather_code", "weather_description",
            "windspeed_10m_max",
            "comfort_index",
            "timezone", "elevation", "latitude", "longitude"
        ]

        # Get columns that exist in the dataframe
        existing_cols = [col for col in priority_cols if col in df.columns]
        # Add any remaining columns not in priority list
        remaining_cols = [col for col in df.columns if col not in existing_cols]

        return df[existing_cols + remaining_cols]


def transform_weather_data(
    raw_data: Dict[str, Any],
    city_name: str = "Unknown"
) -> pd.DataFrame:
    """
    Convenience function to transform weather data
    
    Args:
        raw_data: Raw API response
        city_name: City name
        
    Returns:
        Cleaned and enriched DataFrame
    """
    transformer = WeatherDataTransformer(city_name)
    return transformer.transform(raw_data)


# Test the transformer on import
