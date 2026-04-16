from unittest.mock import patch, MagicMock
import pytest
from scripts.fetcher import fetch, FetchError

def test_fetch_returns_text_and_caches(tmp_path, fixtures_dir):
    html = (fixtures_dir / "sample_gov_page.html").read_text(encoding="utf-8")
    mock_resp = MagicMock(status_code=200, text=html, content=html.encode("utf-8"))
    mock_resp.raise_for_status = MagicMock()
    with patch("scripts.fetcher.requests.get", return_value=mock_resp) as mock_get:
        text1 = fetch("https://www.gov.cn/test", cache_dir=tmp_path)
        text2 = fetch("https://www.gov.cn/test", cache_dir=tmp_path)
    assert "国内生产总值增长 5%" in text1
    assert text1 == text2
    assert mock_get.call_count == 1  # second call hits cache

def test_fetch_rejects_non_whitelisted_url(tmp_path):
    with pytest.raises(FetchError, match="not on whitelist"):
        fetch("https://evil.example.com/policy", cache_dir=tmp_path)

def test_fetch_http_error_raises(tmp_path):
    mock_resp = MagicMock(status_code=404)
    mock_resp.raise_for_status = MagicMock(side_effect=Exception("404"))
    with patch("scripts.fetcher.requests.get", return_value=mock_resp):
        with pytest.raises(FetchError):
            fetch("https://www.gov.cn/missing", cache_dir=tmp_path)
