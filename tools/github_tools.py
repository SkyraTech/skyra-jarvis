"""
Jarvis Tools — GitHub Automation Endpoints
===========================================
Defines the tool interfaces exposed to Gemini and executes HTTP calls 
to the local Node.js `skyra-github-service` running on port 8001.
Uses the unified call_local_api utility for robust and reusable networking.
"""

from loguru import logger
from utils.network import call_local_api
from config import config

GITHUB_SERVICE_URL = config.GITHUB_SERVICE_URL


async def create_github_repository(name: str, description: str = "", is_private: bool = False) -> str:
    """
    Create a new repository on your GitHub account.

    Args:
        name: The name of the repository to create (e.g., "my-new-app").
        description: A short description of the repository.
        is_private: True to make it private, False to make it public.
    """
    logger.info(f"🔧 Tool Call: Creating GitHub repository '{name}' (private={is_private})...")
    url = f"{GITHUB_SERVICE_URL}/repos/create"
    payload = {
        "name": name,
        "description": description,
        "isPrivate": is_private
    }
    
    success, data, err = await call_local_api("POST", url, payload)
    if success:
        return f"Success! Created repository {name}. URL: {data.get('repoUrl')}"
    return f"Failed to create repository: {err}"


async def list_github_repositories() -> str:
    """
    List all repositories owned by your GitHub account.
    """
    logger.info("🔧 Tool Call: Listing GitHub repositories...")
    url = f"{GITHUB_SERVICE_URL}/repos"
    
    success, data, err = await call_local_api("GET", url)
    if success:
        repos = data.get("repos", [])
        if not repos:
            return "You don't have any repositories yet on this account."
        
        lines = [f"Found {len(repos)} repositories:"]
        for r in repos:
            vis = "Private" if r.get("private") else "Public"
            lines.append(f"• {r.get('name')} ({vis}) - {r.get('url')}")
        return "\n".join(lines)
        
    return f"Failed to list repositories: {err}"


async def clone_github_repository(repo_name: str, destination_dir: str) -> str:
    """
    Clone a remote GitHub repository from your account onto your local laptop folder.

    Args:
        repo_name: The name of the repository to clone.
        destination_dir: The absolute local directory path on your laptop where the repo should be cloned.
    """
    logger.info(f"🔧 Tool Call: Cloning repository '{repo_name}' to '{destination_dir}'...")
    url = f"{GITHUB_SERVICE_URL}/repos/clone"
    payload = {
        "repoName": repo_name,
        "destinationDir": destination_dir
    }
    
    success, data, err = await call_local_api("POST", url, payload)
    if success:
        return f"Success! Repository '{repo_name}' successfully cloned to local path: {data.get('localPath')}"
    return f"Failed to clone repository: {err}"

