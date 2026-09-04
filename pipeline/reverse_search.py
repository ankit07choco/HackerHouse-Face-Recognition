"""
Stage 2: Multi-Engine Reverse Image Search Pipeline
Performs genuine reverse-image searches using Google Lens (via SerpApi).
Extracts real, accessible candidate web pages, social media posts, and profile URLs.
Strictly adheres to Zero False-Positive Policy (PRD Section 4.4 & 7).
"""

import os
import re
import io
import json
import requests
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, unquote, quote
from dotenv import load_dotenv

load_dotenv()

SOCIAL_DOMAINS = {
    "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "facebook.com", "reddit.com", "github.com", "youtube.com",
    "tiktok.com", "pinterest.com", "medium.com", "threads.net",
    "substack.com", "wikipedia.org", "wikimedia.org"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class SearchCandidate:
    title: str
    source_url: str
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    domain: str = ""
    is_social: bool = False
    source_engine: str = "Google Lens"
    raw_metadata: Optional[Dict[str, Any]] = None


def upload_temp_image(image_path: str) -> Optional[str]:
    """Upload a local image to a temporary public host so Google Lens can access it."""
    if not os.path.exists(image_path):
        return None

    # 1. Try catbox.moe
    try:
        with open(image_path, "rb") as f:
            resp = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=10)
            if resp.status_code == 200 and resp.text.startswith("http"):
                return resp.text.strip()
    except Exception:
        pass

    # 2. Try tmpfiles.org
    try:
        with open(image_path, "rb") as f:
            resp = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and "url" in data["data"]:
                    return data["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception:
        pass

    # 3. Try file.io
    try:
        with open(image_path, "rb") as f:
            resp = requests.post("https://file.io", files={"file": f}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and "link" in data:
                    return data["link"]
    except Exception:
        pass

    return None


def extract_domain(url: str) -> str:
    """Extract registered domain from a URL."""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def is_social_domain(domain: str) -> bool:
    """Check if domain matches any known social platform."""
    domain = domain.lower()
    return any(social in domain for social in SOCIAL_DOMAINS)


class ReverseImageSearcher:
    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY")

    def search(
        self,
        image_path_or_url: str,
        embedding: Optional[np.ndarray] = None,
        limit: int = 15
    ) -> List[SearchCandidate]:
        """
        Execute genuine reverse image search using Google Lens via SerpApi.
        Returns real visual matches containing actual candidate pages and image thumbnails.
        """
        candidates: List[SearchCandidate] = []
        is_url = image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://")
        public_url = image_path_or_url if is_url else None

        # 1. Query SerpApi Google Lens (if API key is present)
        if self.serpapi_key and self.serpapi_key != "your_serpapi_api_key_here" and len(self.serpapi_key.strip()) > 8:
            try:
                candidates = self._search_serpapi_google_lens(
                    public_url or image_path_or_url,
                    local_path=image_path_or_url if not is_url else None,
                    limit=limit
                )
                if candidates:
                    return candidates
            except Exception as e:
                print(f"[Notice] SerpApi Google Lens query error: {e}")

        # If no SerpApi key is provided or no visual matches exist, return empty list
        # Never invent false candidates from unrelated footer links!
        return candidates

    def _search_serpapi_google_lens(
        self,
        image_url: str,
        local_path: Optional[str] = None,
        limit: int = 15
    ) -> List[SearchCandidate]:
        """Query SerpApi Google Lens engine."""
        from serpapi import GoogleSearch

        params = {
            "engine": "google_lens",
            "api_key": self.serpapi_key,
        }

        if image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
            params["url"] = image_url
        elif local_path and os.path.exists(local_path):
            uploaded = upload_temp_image(local_path)
            if not uploaded:
                raise ValueError("Could not upload local image to public host for SerpApi")
            params["url"] = uploaded

        search = GoogleSearch(params)
        results = search.get_dict()

        candidates: List[SearchCandidate] = []
        visual_matches = results.get("visual_matches", [])

        for item in visual_matches:
            title = item.get("title", "Visual Match")
            source_url = item.get("link", "")
            img_url = item.get("original") or item.get("thumbnail") or item.get("image")
            thumb = item.get("thumbnail")
            source = item.get("source", "")

            if not source_url:
                continue

            domain = extract_domain(source_url) or extract_domain(source)
            is_social = is_social_domain(domain)

            candidates.append(
                SearchCandidate(
                    title=title,
                    source_url=source_url,
                    image_url=img_url,
                    thumbnail_url=thumb,
                    domain=domain,
                    is_social=is_social,
                    source_engine="Google Lens (SerpApi)",
                    raw_metadata=item
                )
            )
            if len(candidates) >= limit:
                break

        return candidates
