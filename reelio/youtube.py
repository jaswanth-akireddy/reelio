"""Uploads a finished video to YouTube as a Short (resumable upload, OAuth refresh token)."""
import json

import requests

from .core import env


def configured():
    return all(env(k, required=False) for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"))


def upload(path, title, description, privacy="public", tags=None):
    tok = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": env("YOUTUBE_CLIENT_ID"), "client_secret": env("YOUTUBE_CLIENT_SECRET"),
        "refresh_token": env("YOUTUBE_REFRESH_TOKEN"), "grant_type": "refresh_token"}, timeout=60)
    tok.raise_for_status()
    auth = {"Authorization": "Bearer " + tok.json()["access_token"]}
    meta = {"snippet": {"title": title[:100], "description": description, "tags": tags or [], "categoryId": "2"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                         headers={**auth, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4"},
                         data=json.dumps(meta), timeout=60)
    init.raise_for_status()
    with open(path, "rb") as f:
        up = requests.put(init.headers["Location"], headers={**auth, "Content-Type": "video/mp4"}, data=f, timeout=900)
    up.raise_for_status()
    return "https://youtube.com/shorts/" + up.json()["id"]
