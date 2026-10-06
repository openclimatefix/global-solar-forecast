"""get_forecast should survive API connection failures (issue #88)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

SRC = Path(__file__).resolve().parents[1] / "src" / "v1"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestForecastConnectionErrors(unittest.TestCase):
    def setUp(self) -> None:
        # Fresh import each test so patches apply cleanly.
        for name in list(sys.modules):
            if name == "forecast" or name.startswith("forecast."):
                del sys.modules[name]

    @patch("streamlit.cache_data", lambda **_kwargs: (lambda f: f))
    @patch("streamlit.error")
    @patch("requests.post")
    def test_connection_error_returns_none(
        self, mock_post: MagicMock, mock_error: MagicMock, *_args: object,
    ) -> None:
        mock_post.side_effect = requests.ConnectionError("Connection aborted")
        import forecast as forecast_mod

        result = forecast_mod.get_forecast("Testland", 1.0, 0.0, 0.0)
        self.assertIsNone(result)
        mock_error.assert_called()
        self.assertEqual(mock_post.call_args.kwargs.get("timeout"), 20)

    @patch("streamlit.cache_data", lambda **_kwargs: (lambda f: f))
    @patch("streamlit.error")
    @patch("requests.post")
    def test_timeout_returns_none(
        self, mock_post: MagicMock, mock_error: MagicMock, *_args: object,
    ) -> None:
        mock_post.side_effect = requests.Timeout("timed out")
        import forecast as forecast_mod

        result = forecast_mod.get_forecast("Testland", 1.0, 0.0, 0.0)
        self.assertIsNone(result)
        mock_error.assert_called()

    @patch("streamlit.cache_data", lambda **_kwargs: (lambda f: f))
    @patch("streamlit.error")
    @patch("requests.post")
    def test_http_error_status_returns_none(
        self, mock_post: MagicMock, mock_error: MagicMock, *_args: object,
    ) -> None:
        response = MagicMock()
        response.status_code = 503
        mock_post.return_value = response
        import forecast as forecast_mod

        result = forecast_mod.get_forecast("Testland", 1.0, 0.0, 0.0)
        self.assertIsNone(result)
        mock_error.assert_called()
