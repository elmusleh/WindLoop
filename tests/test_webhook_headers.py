#!/usr/bin/env python3
"""Test webhook custom headers functionality."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import cascade_loop as cl


def test_webhook_custom_headers():
    print("[1/3] Testing send_webhook with custom headers...")
    captured = {}
    with patch("urllib.request.urlopen") as mock_urlopen:
        resp = MagicMock()
        resp.status = 200

        def capture(req, **kwargs):
            captured["headers"] = dict(req.headers)
            return resp
        mock_urlopen.side_effect = capture

        cl.send_webhook("https://example.com/hook", headers_json='{"Authorization": "Bearer token123", "X-Custom": "test"}')
        assert "Authorization" in captured["headers"]
        assert captured["headers"]["Authorization"] == "Bearer token123"
        assert captured["headers"]["X-custom"] == "test"
    print("  PASS")


def test_webhook_invalid_json_headers():
    print("[2/3] Testing send_webhook with invalid JSON headers...")
    with patch("urllib.request.urlopen") as mock_urlopen:
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        # Should not raise; just log warning and proceed with default headers
        cl.send_webhook("https://example.com/hook", headers_json="not json")
        assert mock_urlopen.called
    print("  PASS")


def test_webhook_non_dict_headers():
    print("[3/3] Testing send_webhook with non-dict JSON headers...")
    with patch("urllib.request.urlopen") as mock_urlopen:
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        # Should warn and proceed with default headers
        cl.send_webhook("https://example.com/hook", headers_json='["array", "not", "dict"]')
        assert mock_urlopen.called
    print("  PASS")


if __name__ == "__main__":
    test_webhook_custom_headers()
    test_webhook_invalid_json_headers()
    test_webhook_non_dict_headers()
    print("\nAll webhook headers tests passed.")
