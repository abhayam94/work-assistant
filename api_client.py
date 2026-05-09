"""
api_client.py — Resilient HTTP client with retry + backoff.
All Jira and Google API calls go through this.
"""

import time
import requests
from requests.auth import HTTPBasicAuth
from logger import log_step


def _should_retry(status_code: int) -> bool:
    """Retry on server errors and rate limits, not on auth/client errors."""
    return status_code in (429, 500, 502, 503, 504)


def get(url: str, auth=None, headers: dict = None, params: dict = None,
        retries: int = 3, backoff: float = 2.0, label: str = ""):
    """
    GET with retry + exponential backoff.
    Raises on final failure.
    """
    headers = headers or {"Accept": "application/json"}
    last_exc = None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, auth=auth, headers=headers,
                                params=params, timeout=15)
            if resp.status_code == 200:
                return resp
            if _should_retry(resp.status_code) and attempt < retries:
                wait = backoff ** attempt
                log_step(label or url, "WARN",
                         f"HTTP {resp.status_code} — retrying in {wait:.0f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            last_exc = TimeoutError(f"Request timed out: {url}")
            if attempt < retries:
                wait = backoff ** attempt
                log_step(label or url, "WARN",
                         f"Timeout — retrying in {wait:.0f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
        except requests.exceptions.ConnectionError as e:
            last_exc = e
            if attempt < retries:
                wait = backoff ** attempt
                log_step(label or url, "WARN",
                         f"Connection error — retrying in {wait:.0f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
        except Exception as e:
            raise

    raise last_exc or RuntimeError(f"Failed after {retries} attempts: {url}")


def post(url: str, headers: dict = None, json_body: dict = None,
         retries: int = 3, backoff: float = 2.0, label: str = ""):
    """
    POST with retry + exponential backoff.
    """
    headers = headers or {"Content-Type": "application/json"}
    last_exc = None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=json_body, timeout=30)
            if resp.status_code in (200, 201):
                return resp
            if _should_retry(resp.status_code) and attempt < retries:
                wait = backoff ** attempt
                log_step(label or url, "WARN",
                         f"HTTP {resp.status_code} — retrying in {wait:.0f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            last_exc = TimeoutError(f"Request timed out: {url}")
            if attempt < retries:
                wait = backoff ** attempt
                time.sleep(wait)
        except requests.exceptions.ConnectionError as e:
            last_exc = e
            if attempt < retries:
                wait = backoff ** attempt
                time.sleep(wait)
        except Exception as e:
            raise

    raise last_exc or RuntimeError(f"Failed after {retries} attempts: {url}")
