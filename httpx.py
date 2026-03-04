from __future__ import annotations

import json
import urllib.parse
import urllib.request


class HTTPStatusError(Exception):
    pass


class Response:
    def __init__(self, status_code: int, content: bytes, url: str):
        self.status_code = status_code
        self.content = content
        self.url = url

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="ignore")

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPStatusError(f"HTTP {self.status_code} for {self.url}")


class Client:
    def __init__(self, timeout: float = 30.0, follow_redirects: bool = True):
        self.timeout = timeout

    def get(self, url: str, params: dict | None = None, headers: dict | None = None, timeout: float | None = None):
        return get(url, params=params, headers=headers, timeout=timeout or self.timeout)


def get(url: str, params: dict | None = None, headers: dict | None = None, timeout: float = 30.0, follow_redirects: bool = True):
    if params:
        qs = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{qs}"
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        content = res.read()
        status = getattr(res, "status", 200)
    return Response(status, content, url)
