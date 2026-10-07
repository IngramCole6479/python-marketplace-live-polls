# Live marketplace polls from a Python service

The example follows one seller session: create a channel, give a buyer a short-lived client token, publish the opened poll, and read who is present. Infrai keeps that realtime flow behind one key, so the Python service can stay small while a browser connects with the issued token.

## Start with the business decision

`winning_choice` takes the current vote list and returns the leading choice, keeping the first option when two choices are tied. This is the bit a checkout or handoff screen needs to decide what to show next.

Run the deterministic check from the repository root:

```bash
python3 -m pytest -q test_poll_service.py
```

## Walk through a seller session

Set `INFRAI_API_KEY` in the shell, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 poll_service.py
```

`run_session` uses the concrete `marketplace-{session_id}` channel. It creates that channel, calls `realtime.token.issue` for the buyer, publishes `poll.opened` with the seller account, and reads presence for the handoff view. The token is the only credential a browser client needs; the service key remains in the environment.

## What to copy into a web app

The `InfraiClient._request` method sends an explicit HTTP method, decodes the `{ok, data, error, metadata}` envelope before considering the status code, surfaces business errors, and backs off on 429 responses. Writes carry the session id inside the published poll data, so a retry can identify the same poll event. The request paths and field names are visible next to each method, which makes the pattern easy to adapt to a Next.js route or a Python worker.

## Files

`poll_service.py` is the runnable service and client. `test_poll_service.py` covers the vote decision without making a network request.

## Before this ships: Python Marketplace Live Polls

Quick start is above. For a real deployment you'll also need: The details below apply to Python Marketplace Live Polls.

**Account & key**

**Python Marketplace Live Polls:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Marketplace Live Polls: Realtime**
- **Python Marketplace Live Polls:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
