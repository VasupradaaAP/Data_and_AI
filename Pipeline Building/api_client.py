"""
API Client for Open-Meteo Weather API
Handles all interactions with the external API including error handling,
retries, validation, and logging
"""

import requests
import logging
import time
from typing import Dict, Any, Optional
from config import (
    API_BASE_URL,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    WEATHER_PARAMETERS,
)

# Setup logger
logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Custom exception for API client errors"""
    pass


class WeatherAPIClient:
    """
    Client for fetching weather data from Open-Meteo API
    Includes error handling, retries, and comprehensive logging
    """

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the API endpoint
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        logger.info(f"WeatherAPIClient initialized with base_url={base_url}, timeout={timeout}s")

    def fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        city_name: str = "Unknown",
        forecast_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Fetch weather forecast from Open-Meteo API with retry logic
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            city_name: City name (for logging purposes)
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary containing API response data
            
        Raises:
            APIClientError: If all retry attempts fail
        """
        params = self._build_params(latitude, longitude, forecast_days)

        logger.info(
            f"Fetching weather forecast for {city_name} "
            f"(lat={latitude}, lon={longitude}), forecast_days={forecast_days}"
        )
        logger.debug(f"API Parameters: {params}")

        # Retry loop with exponential backoff
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"API Request Attempt {attempt}/{MAX_RETRIES}")
                
                # Add headers that might be required
                headers = {
                    "User-Agent": "WeatherDataPipeline/1.0",
                    "Accept": "application/json"
                }
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

                # Check for HTTP errors
                response.raise_for_status()

                # Parse JSON response
                data = response.json()

                # Validate response structure
                self._validate_response(data)

                logger.info(
                    f"[OK] Successfully fetched data for {city_name} "
                    f"(Response size: {len(str(data))} bytes)"
                )
                logger.debug(f"Response keys: {data.keys()}")

                return data

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Attempt {attempt}: Request timeout after {self.timeout}s"
                )
                self._handle_retry(attempt)

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Attempt {attempt}: Connection error - {str(e)}")
                self._handle_retry(attempt)

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_detail = ""
                try:
                    error_json = e.response.json()
                    error_detail = f" - API says: {error_json}"
                except:
                    error_detail = f" - Response: {e.response.text[:200]}"
                
                logger.warning(
                    f"Attempt {attempt}: HTTP Error {status_code}{error_detail}"
                )
                # Don't retry on 4xx errors (except 429)
                if 400 <= status_code < 500 and status_code != 429:
                    raise APIClientError(
                        f"Client error ({status_code}): {str(e)}{error_detail}"
                    ) from e
                self._handle_retry(attempt)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt}: Request exception - {str(e)}")
                self._handle_retry(attempt)

            except ValueError as e:
                logger.error(f"Attempt {attempt}: Invalid JSON response - {str(e)}")
                self._handle_retry(attempt)

            except APIClientError as e:
                logger.error(f"Attempt {attempt}: API validation error - {str(e)}")
                raise

        # All retries exhausted
        error_msg = (
            f"Failed to fetch weather data for {city_name} "
            f"after {MAX_RETRIES} attempts"
        )
        logger.error(f"[FAILED] {error_msg}")
        raise APIClientError(error_msg)

    def _build_params(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int,
    ) -> Dict[str, Any]:
        """
        Build query parameters for the API request
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            forecast_days: Number of forecast days
            
        Returns:
            Dictionary of query parameters
        """
        # Build params dict
        # Open-Meteo expects daily parameters as a SINGLE comma-separated string
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(WEATHER_PARAMETERS),  # Comma-separated string (correct format)
            "forecast_days": forecast_days,
        }
        return params

    def _validate_response(self, data: Dict[str, Any]) -> None:
        """
        Validate API response structure
        
        Args:
            data: Response data from API
            
        Raises:
            APIClientError: If response structure is invalid
        """
        # Check for required top-level keys
        required_keys = ["daily", "elevation", "timezone"]
        missing_keys = [key for key in required_keys if key not in data]

        if missing_keys:
            raise APIClientError(f"Response missing required keys: {missing_keys}")

        # Check for daily data
        if not isinstance(data.get("daily"), dict):
            raise APIClientError("Response 'daily' field is not a dictionary")

        daily_data = data["daily"]
        if not daily_data:
            raise APIClientError("Response 'daily' data is empty")

        # Check for at least one temperature reading (using new parameter name with _mean suffix)
        if "temperature_2m_mean" not in daily_data:
            raise APIClientError("Response missing 'temperature_2m_mean' field")

        logger.debug("[OK] Response structure validated successfully")

    def _handle_retry(self, attempt: int) -> None:
        """
        Handle retry logic with exponential backoff
        
        Args:
            attempt: Current attempt number
            
        Raises:
            APIClientError: If max retries exceeded
        """
        if attempt >= MAX_RETRIES:
            return  # Don't sleep after the last failed attempt

        wait_time = RETRY_BACKOFF_FACTOR ** (attempt - 1)
        logger.info(f"Retrying in {wait_time}s...")
        time.sleep(wait_time)


def fetch_weather_data(
    latitude: float,
    longitude: float,
    city_name: str = "Unknown",
    forecast_days: int = 7,
) -> Dict[str, Any]:
    """
    Convenience function to fetch weather data
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        city_name: City name (for logging)
        forecast_days: Number of forecast days
        
    Returns:
        Weather data dictionary
        
    Raises:
        APIClientError: If fetch fails
    """
    client = WeatherAPIClient()
    return client.fetch_forecast(latitude, longitude, city_name, forecast_days)
