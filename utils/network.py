"""
Network Utility Manager
=======================
Checks internet connectivity status quickly and efficiently.
Provides standardized httpx calls to local satellite APIs with 15.0-second timeouts.
"""

import socket
import json
import httpx
from loguru import logger
from typing import Tuple, Optional, Any


def is_online() -> bool:
    """
    Check if the laptop has active internet connectivity.
    Performs a quick socket connection check to a reliable DNS server.
    """
    try:
        # Connect to Cloudflare DNS with a localized 1.5s timeout (no global default timeout side-effect)
        s = socket.create_connection(("1.1.1.1", 53), timeout=1.5)
        s.close()
        return True
    except socket.error:
        return False


async def call_local_api(method: str, url: str, json_data: Optional[dict] = None) -> Tuple[bool, Any, Optional[str]]:
    """
    Reusable local HTTP API caller with centralized logging and connection recovery.
    Uses httpx.AsyncClient with a strict 15.0-second timeout.
    
    Args:
        method: "GET" or "POST"
        url: Destination API URL (e.g. http://localhost:8001/repos)
        json_data: Optional JSON payload dictionary
        
    Returns:
        Tuple: (success: bool, response_data: Any, error_message: str | None)
    """
    try:
        logger.debug(f"API Request: {method} {url}")
        timeout = httpx.Timeout(15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "POST":
                resp = await client.post(url, json=json_data)
            else:
                resp = await client.get(url)
                
            status = resp.status_code
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
                
            if status == 200:
                return True, data, None
                
            error_msg = data.get("error") if isinstance(data, dict) else f"HTTP Status {status}"
            return False, None, error_msg

    except (httpx.ConnectError, httpx.ConnectTimeout) as ce:
        # Extract port to give a friendly service name hint
        try:
            port = url.split(":")[2].split("/")[0]
        except Exception:
            port = "unknown"
            
        service_names = {
            "8001": "skyra-github-service",
            "8002": "skyra-google-service",
            "8004": "skyra-browser-service",
            "8005": "skyra-social-service",
            "8006": "skyra-vision-service"
        }
        name_hint = service_names.get(port, "local service")
        err_msg = json.dumps({
            "success": False,
            "error": f"Connection refused to {name_hint}. Please ensure it is running on port {port}."
        })
        logger.warning(f"Connection failed to {url}: {err_msg}")
        return False, None, err_msg
        
    except httpx.TimeoutException as te:
        err_msg = json.dumps({
            "success": False,
            "error": f"Request to {url} timed out after 15.0 seconds."
        })
        logger.warning(f"Timeout connecting to {url}: {err_msg}")
        return False, None, err_msg
        
    except Exception as e:
        logger.error(f"API Error ({url}): {e}")
        err_msg = json.dumps({
            "success": False,
            "error": f"Internal API request error: {str(e)}"
        })
        return False, None, err_msg
