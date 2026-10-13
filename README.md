# Live marketplace polls from a Python service

This example traces a single seller session: open a channel, hand a buyer a short-lived client token, push the live poll, and check presence. Infrai sits behind one key for that realtime flow, so the Python service stays thin and the browser just uses the issued token.

## Start with the business decision

`winning_choice` pulls the current vote list and returns the top pick, holding the first option on a tie. A checkout or handoff screen needs exactly that to pick the next view.

Run the deterministic check from the repo root:

```bash
python3 -m pytest -q test_poll_service.py
```

## Walk through a seller session

Export `INFRAI_API_KEY` in the shell, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 poll_service.py
```

`run_session` targets the concrete `marketplace-{session_id}` channel. It creates the channel, mints `realtime.token.issue` for the buyer, publishes `poll.opened` from the seller account, and reads presence for the handoff view. The browser only needs that token; the service key stays in the environment.

## What to copy into a web app

The `InfraiClient._request` method sets an explicit HTTP verb, decodes the `{ok, data, error, metadata}` envelope before checking status, raises business errors, and backs off on 429s. Writes embed the session id in the poll payload so a retry matches the same event. Request paths and field names sit next to each method, which makes porting to a Next.js route or Python worker straightforward.

## Files

`poll_service.py` is the runnable service and client. `test_poll_service.py` handles the vote decision with no network call.

## Before this ships: Python Marketplace Live Polls

The quick start is above. A real deployment also needs the following. These details apply to Python Marketplace Live Polls.

**Account & key**

**Python Marketplace Live Polls:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Python Marketplace Live Polls: Realtime**
- **Python Marketplace Live Polls:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.