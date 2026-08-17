"""
Jarvis Social Media Tools — Phase 6
=====================================
Exposes Social Media integration capabilities to Gemini.
Calls the skyra-social-service (port 8005).

Available tools:
  - post_to_linkedin    → Create post on your LinkedIn company page
  - post_to_twitter     → Create tweet on your Twitter/X account
  - post_to_instagram   → Upload photo + caption to Instagram
  - post_to_facebook    → Create post on your Facebook page
"""

from loguru import logger
from utils.network import call_local_api
from config import config

SOCIAL_SERVICE_URL = config.SOCIAL_SERVICE_URL


async def post_to_linkedin(content: str, title: str = "") -> str:
    """
    Publish a post to your LinkedIn professional / company page.
    Use this to share company updates, technical blogs, or announcements.

    Args:
        content: The text content of the post
        title: Optional title for the share event
    """
    logger.info("📢 Tool Call: Posting to LinkedIn...")
    payload = {"content": content}
    if title:
        payload["title"] = title

    success, data, err = await call_local_api("POST", f"{SOCIAL_SERVICE_URL}/linkedin/post", payload)

    if success:
        if data.get("mock"):
            return "Dry-run: LinkedIn post created successfully (mock mode)."
        return f"Success! Posted to LinkedIn. Share ID: {data.get('postId')}"
    return f"Failed to post to LinkedIn: {err}"


async def post_to_twitter(content: str) -> str:
    """
    Publish a tweet to your Twitter/X account.
    Use this to broadcast updates, share technical tips, or threads.

    Args:
        content: The text content of the tweet (must be under 280 characters unless Premium)
    """
    logger.info("📢 Tool Call: Posting to Twitter/X...")
    payload = {"content": content}
    success, data, err = await call_local_api("POST", f"{SOCIAL_SERVICE_URL}/twitter/post", payload)

    if success:
        if data.get("mock"):
            return "Dry-run: Tweet posted successfully (mock mode)."
        return f"Success! Tweet posted. Tweet ID: {data.get('tweetId')}"
    return f"Failed to tweet: {err}"


async def post_to_instagram(image_url: str, caption: str) -> str:
    """
    Publish an image with a caption to your Instagram business account.

    Args:
        image_url: Publicly accessible URL of the image to publish (e.g. from Google Drive or Cloud Storage)
        caption: Caption text (hashtags are allowed)
    """
    logger.info("📢 Tool Call: Posting to Instagram...")
    payload = {"imageUrl": image_url, "caption": caption}
    success, data, err = await call_local_api("POST", f"{SOCIAL_SERVICE_URL}/instagram/post", payload)

    if success:
        if data.get("mock"):
            return "Dry-run: Instagram post published successfully (mock mode)."
        return f"Success! Posted to Instagram. Media ID: {data.get('mediaId')}"
    return f"Failed to post to Instagram: {err}"


async def post_to_facebook(content: str, page_id: str) -> str:
    """
    Publish a post to a Facebook Page you manage.

    Args:
        content: Text content of the post
        page_id: The Facebook Page ID
    """
    logger.info(f"📢 Tool Call: Posting to Facebook Page '{page_id}'...")
    payload = {"content": content, "pageId": page_id}
    success, data, err = await call_local_api("POST", f"{SOCIAL_SERVICE_URL}/facebook/post", payload)

    if success:
        if data.get("mock"):
            return "Dry-run: Facebook Page post created successfully (mock mode)."
        return f"Success! Posted to Facebook Page. Post ID: {data.get('postId')}"
    return f"Failed to post to Facebook: {err}"
