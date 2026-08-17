"""
Network Utility Manager
=======================
Checks internet connectivity status quickly and efficiently.
"""

import socket
from loguru import logger


def is_online() -> bool:
    """
    Check if the laptop has active internet connectivity.
    Performs a quick socket connection check to a reliable DNS server.
    """
    try:
        # Try to connect to Cloudflare DNS (1.1.1.1) on port 53 (DNS) with a short timeout
        socket.setdefaulttimeout(1.5)
        # Using socket.create_connection is robust on Windows
        s = socket.create_connection(("1.1.1.1", 53))
        s.close()
        return True
    except socket.error:
        return False


import aiohttp
from typing import Tuple, Optional, Any

# Reusable client session
_session: Optional[aiohttp.ClientSession] = None

async def get_session() -> aiohttp.ClientSession:
    """Get or create the global persistent ClientSession."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session

async def close_session() -> None:
    """Close the global ClientSession on shutdown."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None

async def call_local_api(method: str, url: str, json_data: Optional[dict] = None) -> Tuple[bool, Any, Optional[str]]:
    """
    Reusable local HTTP API caller with centralized logging and connection recovery.
    
    Args:
        method: "GET" or "POST"
        url: Destination API URL (e.g. http://localhost:8001/repos)
        json_data: Optional JSON payload dictionary
        
    Returns:
        Tuple: (success: bool, response_data: Any, error_message: str | None)
    """
    try:
        session = await get_session()
        logger.debug(f"API Request: {method} {url}")
        
        # Select method
        if method.upper() == "POST":
            async with session.post(url, json=json_data, timeout=10) as resp:
                status = resp.status
                data = await resp.json()
        else:
            async with session.get(url, timeout=10) as resp:
                status = resp.status
                data = await resp.json()
                
        if status == 200:
            return True, data, None
            
        error_msg = data.get("error") if isinstance(data, dict) else f"HTTP Status {status}"
        return False, None, error_msg

    except aiohttp.ClientConnectorError:
        # Extract port to give a friendly service name hint
        try:
            port = url.split(":")[2].split("/")[0]
        except Exception:
            port = "unknown"
            
        name_hint = "skyra-github-service" if port == "8001" else "local service"
        err_msg = f"Cannot connect to {name_hint}. Please ensure it is running on port {port}."
        logger.warning(f"Connection failed to {url}: {err_msg}")
        return False, None, err_msg
        
    except Exception as e:
        logger.error(f"API Error ({url}): {e}")
        return False, None, str(e)
