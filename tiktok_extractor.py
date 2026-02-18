from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests

LOG = logging.getLogger(__name__)

BASE_URL = "https://open.tiktokapis.com"
MAX_PER_REQUEST = 100
DAILY_LIMIT = 1000


@dataclass(frozen=True)
class TikTokCredentials:
    client_key: str
    client_secret: str


def load_credentials() -> TikTokCredentials:
    """Load credentials from environment variables.

    Required:
      - TIKTOK_CLIENT_KEY
      - TIKTOK_CLIENT_SECRET
    """
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

    missing = [
        name
        for name, value in [
            ("TIKTOK_CLIENT_KEY", client_key),
            ("TIKTOK_CLIENT_SECRET", client_secret),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return TikTokCredentials(client_key=client_key, client_secret=client_secret)


class TikTokMaxDataExtractor:
    def __init__(self, credentials: TikTokCredentials, *, timeout: int = 30) -> None:
        self.client_key = credentials.client_key
        self.client_secret = credentials.client_secret
        self.token: Optional[str] = None
        self.request_count = 0
        self._session = requests.Session()
        self._timeout = timeout

    def get_token(self) -> bool:
        """Get an access token via client credentials."""
        url = f"{BASE_URL}/v2/oauth/token/"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        response = self._session.post(url, headers=headers, data=data, timeout=self._timeout)
        self.request_count += 1

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            LOG.info("Token obtained")
            return True

        LOG.error("Token error: %s - %s", response.status_code, response.text)
        return False

    def _auth_headers(self) -> Dict[str, str]:
        if not self.token:
            raise RuntimeError("Token not set. Call get_token() first.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, *, params: Optional[Dict[str, Any]] = None, body: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{BASE_URL}{endpoint}"
        response = self._session.post(url, headers=self._auth_headers(), params=params, json=body, timeout=self._timeout)
        self.request_count += 1

        if response.status_code == 200:
            return response.json()

        LOG.warning("Request failed: %s - %s", response.status_code, response.text)
        return None

    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        params = {
            "fields": "display_name,bio_description,avatar_url,is_verified,follower_count,following_count,likes_count,video_count,bio_url",
        }
        body = {"username": username}
        return self._post("/v2/research/user/info/", params=params, body=body)

    def get_user_videos(self, username: str, *, days_back: int = 30, max_videos: int = 100) -> Optional[Dict[str, Any]]:
        """Get user videos with a single 30-day chunk.

        TikTok limits searches to 30 days per request. If you want longer periods,
        call this multiple times or implement chunking in the notebook.
        """
        params = {
            "fields": "id,video_description,create_time,username,region_code,like_count,comment_count,share_count,view_count,music_id,hashtag_names,effect_ids,playlist_id,voice_to_text,video_duration,favorites_count,is_stem_verified",
        }

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        body = {
            "query": {
                "and": [
                    {
                        "operation": "EQ",
                        "field_name": "username",
                        "field_values": [username],
                    }
                ]
            },
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "max_count": min(max_videos, MAX_PER_REQUEST),
        }
        return self._post("/v2/research/video/query/", params=params, body=body)

    def get_video_comments(self, video_id: str, *, max_count: int = 100) -> Optional[Dict[str, Any]]:
        params = {
            "fields": "id,video_id,text,like_count,reply_count,parent_comment_id,create_time",
        }
        body = {"video_id": video_id, "max_count": min(max_count, MAX_PER_REQUEST)}
        return self._post("/v2/research/video/comment/list/", params=params, body=body)

    def get_followers(self, username: str, *, max_count: int = 100) -> Optional[Dict[str, Any]]:
        params = {"fields": "display_name,username"}
        body = {"username": username, "max_count": min(max_count, MAX_PER_REQUEST)}
        return self._post("/v2/research/user/followers/", params=params, body=body)

    def get_following(self, username: str, *, max_count: int = 100) -> Optional[Dict[str, Any]]:
        params = {"fields": "display_name,username"}
        body = {"username": username, "max_count": min(max_count, MAX_PER_REQUEST)}
        return self._post("/v2/research/user/following/", params=params, body=body)

    def get_liked_videos(self, username: str, *, max_count: int = 100) -> Optional[Dict[str, Any]]:
        params = {
            "fields": "id,video_description,create_time,username,like_count,comment_count,share_count,view_count",
        }
        body = {"username": username, "max_count": min(max_count, MAX_PER_REQUEST)}
        return self._post("/v2/research/user/liked_videos/", params=params, body=body)

    def get_pinned_videos(self, username: str) -> Optional[Dict[str, Any]]:
        params = {
            "fields": "id,video_description,create_time,username,like_count,comment_count,share_count,view_count",
        }
        body = {"username": username}
        return self._post("/v2/research/user/pinned_videos/", params=params, body=body)

    def get_reposted_videos(self, username: str, *, max_count: int = 100) -> Optional[Dict[str, Any]]:
        params = {
            "fields": "id,video_description,create_time,username,like_count,comment_count,share_count,view_count",
        }
        body = {"username": username, "max_count": min(max_count, MAX_PER_REQUEST)}
        return self._post("/v2/research/user/reposted_videos/", params=params, body=body)

    def extract_all_data(
        self,
        *,
        username: str,
        include_comments: bool = False,
        max_videos: int = 50,
        max_videos_for_comments: Optional[int] = None,
        max_comments_per_video: int = 100,
        days_back: int = 30,
        include_followers: bool = True,
        include_following: bool = True,
        include_liked_videos: bool = True,
        include_pinned_videos: bool = True,
        include_reposted_videos: bool = True,
    ) -> Dict[str, Any]:
        LOG.info("Extracting data for @%s", username)

        all_data: Dict[str, Any] = {
            "username": username,
            "extracted_at": datetime.now().isoformat(),
            "profile": None,
            "videos": None,
            "comments": {},
            "followers": None,
            "following": None,
            "liked_videos": None,
            "pinned_videos": None,
            "reposted_videos": None,
        }

        all_data["profile"] = self.get_user_profile(username)
        time.sleep(0.3)

        all_data["videos"] = self.get_user_videos(
            username,
            days_back=days_back,
            max_videos=max_videos,
        )
        time.sleep(0.3)

        if include_comments and all_data["videos"]:
            videos = all_data["videos"].get("data", {}).get("videos", [])
            videos_to_process = (
                videos if max_videos_for_comments is None else videos[:max_videos_for_comments]
            )
            comments_dict: Dict[str, Any] = {}
            for video in videos_to_process:
                video_id = video.get("id")
                if not video_id:
                    continue
                comments = self.get_video_comments(
                    str(video_id), max_count=max_comments_per_video
                )
                if comments:
                    comments_dict[str(video_id)] = comments
                time.sleep(0.3)
            all_data["comments"] = comments_dict

        if include_followers:
            all_data["followers"] = self.get_followers(username)
            time.sleep(0.3)

        if include_following:
            all_data["following"] = self.get_following(username)
            time.sleep(0.3)

        if include_liked_videos:
            all_data["liked_videos"] = self.get_liked_videos(username)
            time.sleep(0.3)

        if include_pinned_videos:
            all_data["pinned_videos"] = self.get_pinned_videos(username)
            time.sleep(0.3)

        if include_reposted_videos:
            all_data["reposted_videos"] = self.get_reposted_videos(username)

        LOG.info("Extraction complete. Requests used: %s", self.request_count)
        return all_data

    def save_json(self, data: Dict[str, Any], filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        LOG.info("Data saved to %s", filename)

    def log_daily_usage(self, log_file: str = "tiktok_api_usage_log.json") -> Dict[str, int]:
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with open(log_file, "r", encoding="utf-8") as handle:
                log = json.load(handle)
        except FileNotFoundError:
            log = {}

        log[today] = log.get(today, 0) + self.request_count
        with open(log_file, "w", encoding="utf-8") as handle:
            json.dump(log, handle, indent=2)

        remaining = DAILY_LIMIT - log[today]
        LOG.info("Daily usage: %s/%s. Remaining: %s", log[today], DAILY_LIMIT, remaining)
        return log
