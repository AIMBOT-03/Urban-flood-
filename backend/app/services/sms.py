"""
Fast2SMS wrapper. If FAST2SMS_API_KEY is not set, sends are mocked (logged
and recorded) instead of hitting the real API -- lets the whole alert flow be
demoed before a paid/trial API key is wired in.
"""
import os
import requests

FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"
_sent_log = []  # in-process log of mock sends, exposed for the demo/debug endpoint


def _api_key():
    return os.getenv("FAST2SMS_API_KEY", "").strip()


def send_sms(numbers: list[str], message: str) -> dict:
    numbers = [n for n in numbers if n]
    if not numbers:
        return {"sent": False, "reason": "no_recipients"}

    api_key = _api_key()
    if not api_key:
        entry = {"mock": True, "recipients": numbers, "message": message}
        _sent_log.append(entry)
        print(f"[MOCK SMS] To {len(numbers)} recipient(s): {message}")
        return {"sent": True, "mock": True, "recipients": numbers}

    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": ",".join(numbers),
    }
    headers = {"authorization": api_key}
    try:
        resp = requests.post(FAST2SMS_URL, data=payload, headers=headers, timeout=10)
    except requests.RequestException as exc:
        return {"sent": False, "mock": False, "error": str(exc)}

    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}

    if not resp.ok:
        # Fast2SMS puts the real reason in the JSON body even on 4xx/5xx
        # (e.g. "You need to complete one transaction of 100 INR or more
        # before using API route.") -- surface that instead of a generic
        # HTTP error so it's actionable from the app/action log.
        return {
            "sent": False,
            "mock": False,
            "error": body.get("message", f"HTTP {resp.status_code}"),
            "status_code": resp.status_code,
        }

    return {"sent": True, "mock": False, "response": body}


def get_mock_log():
    return list(reversed(_sent_log))
