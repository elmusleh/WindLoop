#!/usr/bin/env python3
"""Test webhook functionality with mocked urllib."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_webhook_success():
    print("[1/3] Testing send_webhook success path...")
    with patch("urllib.request.urlopen") as mock_urlopen:
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        cl.send_webhook("https://example.com/hook")
        assert mock_urlopen.called
    print("  PASS")


def test_webhook_payload_structure():
    print("[2/3] Testing webhook payload structure...")
    captured = {}
    with patch("urllib.request.urlopen") as mock_urlopen:
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        def capture(req, **kwargs):
            captured["body"] = json.loads(req.data)
            return resp
        mock_urlopen.side_effect = capture

        cl.send_webhook("https://example.com/hook")
        body = captured.get("body", {})
        assert "source" in body
        assert body["source"] == "cascade-loop"
        assert "version" in body
        assert "total_iterations" in body
        assert "success_rate" in body
        assert "avg_duration_sec" in body
        assert "timestamp" in body
    print("  PASS")


def test_webhook_http_error():
    print("[3/3] Testing webhook HTTP error handling...")
    from urllib.error import HTTPError
    with patch("urllib.request.urlopen", side_effect=HTTPError("url", 500, "Internal Server Error", {}, None)):
        # Should not raise; just log error
        cl.send_webhook("https://example.com/hook")
    print("  PASS")


if __name__ == "__main__":
    test_webhook_success()
    test_webhook_payload_structure()
    test_webhook_http_error()
    print("\nAll webhook tests passed.")
