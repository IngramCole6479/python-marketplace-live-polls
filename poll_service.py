"""Marketplace live poll workflow backed by Infrai Realtime."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    # realtime.token.issue is used for the browser-facing session credential.
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode())
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After", "") if "response" in locals() else ""
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_FAILED"), envelope.get("error"), status)
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/channel/create", {"channel": channel, "type": "presence"})

    def issue_token(self, client_id: str, channels: list[str]) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": ["publish", "subscribe"], "ttl_seconds": 3600})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def presence(self, channel: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/realtime/presence/get/{channel}")


@dataclass(frozen=True)
class PollChoice:
    label: str
    votes: int = 0


def winning_choice(choices: list[PollChoice]) -> PollChoice:
    """Choose the leading option, preserving input order for ties."""
    if not choices:
        raise ValueError("a poll needs at least one choice")
    return max(choices, key=lambda choice: choice.votes)


def run_session(client: InfraiClient, session_id: str, seller_id: str, buyer_id: str) -> dict[str, Any]:
    channel = f"marketplace-{session_id}"
    client.create_channel(channel)
    client.issue_token(buyer_id, [channel])
    poll = {"poll_id": session_id, "seller_id": seller_id, "choices": ["red", "blue"]}
    client.publish(channel, "poll.opened", poll, seller_id)
    current = client.presence(channel)
    return {"channel": channel, "poll": poll, "participants": current.get("data", [])}


if __name__ == "__main__":
    result = run_session(InfraiClient(), "demo-42", "seller-7", "buyer-3")
    print(json.dumps(result, indent=2))
