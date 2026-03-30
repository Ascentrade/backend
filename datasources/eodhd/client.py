import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from logging_config import get_logger
import pandas as pd

logger = get_logger(__name__)

class EODHDClient:
    """
    Async client for EODHD financial API.
    """
    BASE_URL = "https://eodhd.com/api"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("EODHD_API_TOKEN")
        if not self.api_token:
            logger.warning("EODHD_API_TOKEN not found in environment variables.")

        self.client = httpx.AsyncClient(timeout=30.0)
        
        # User data cache
        self.user_data: Optional[Dict[str, Any]] = None
        self.user_data_last_updated: Optional[datetime] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self.client.aclose()

    async def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """
        Internal method to make a request to EODHD API.
        """
        if not self.api_token:
            raise ValueError("EODHD API token is required but not provided.")

        url = f"{self.BASE_URL}{endpoint}"
        
        # Merge params with api_token and fmt=json
        request_params = {
            "api_token": self.api_token,
            "fmt": "json"
        }
        if params:
            request_params.update(params)

        try:
            response = await self.client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise

    async def async_init(self):
        """
        Async initialization to fetch user data if API token is available.
        Should be called after creating the client instance.
        """
        if self.api_token:
            try:
                await self.fetch_user_data()
                logger.info("Successfully fetched EODHD user data on initialization")
            except Exception as e:
                logger.warning(f"Failed to fetch EODHD user data on initialization: {e}")

    async def fetch_user_data(self) -> Dict[str, Any]:
        """
        Fetches user data for the current API token and caches it.
        Endpoint: /user
        """
        endpoint = "/user"
        data = await self._request(endpoint)
        self.user_data = data
        self.user_data_last_updated = datetime.now()
        return data

    async def fetch_historical_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame | None:
        """
        Fetch end-of-day OHLCV history for a symbol.

        Endpoint: /eod/{symbol} (e.g. MCD.US).

        Optional from_date / to_date are sent as ISO YYYY-MM-DD only when set;
        omitted parameters are not sent to the API.
        Returns date, open, high, low, close, adjusted close, volume columns
        """
        try:
            endpoint = f"/eod/{symbol}"
            params: Dict[str, Any] = {}
            if from_date is not None and to_date is not None:
                params["from"] = from_date.isoformat()
                params["to"] = to_date.isoformat()
            data = await self._request(endpoint, params=params)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
        return None

    async def fetch_split_adjusted_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame | None:
        """
        Split-adjusted series from the Technical Indicators API base endpoint.

        Endpoint: /technical/{symbol} with splitadjusted_only=1 (no `function` or `order`).

        Optional from_date / to_date are sent only when both are set, matching
        fetch_historical_data.
        Returns date, open, high, low, close, volume columns
        """
        try:
            endpoint = f"/technical/{symbol}"
            params: Dict[str, Any] = {"function": "splitadjusted"}
            if from_date is not None and to_date is not None:
                params["from"] = from_date.isoformat()
                params["to"] = to_date.isoformat()
            data = await self._request(endpoint, params=params)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch split-adjusted data for {symbol}: {e}")
        return None
