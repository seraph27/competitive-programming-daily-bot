import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import io, json
import pytest
from unittest.mock import patch, MagicMock
from platforms import CodeforcesClient, AtCoderClient

def test_codeforces_random_problem():
    client = CodeforcesClient()
    fake_response = {
        "status": "OK",
        "result": {
            "problems": [{"contestId": 1, "index": "A", "name": "Test", "rating": 800, "tags": []}],
            "problemStatistics": [{"contestId": 1, "index": "A", "solvedCount": 10}]
        }
    }
    fake_file = MagicMock()
    fake_file.__enter__.return_value = io.BytesIO(json.dumps(fake_response).encode())
    with patch("urllib.request.urlopen", return_value=fake_file):
        prob = client.get_random_problem()
    assert prob["title"] == "Test"
    assert "codeforces.com" in prob["link"]

def test_atcoder_random_problem():
    client = AtCoderClient()
    fake_data = [{"id": "abc100_a", "title": "A", "contest_id": "abc100"}]
    fake_file = MagicMock()
    fake_file.__enter__.return_value = io.BytesIO(json.dumps(fake_data).encode())
    with patch("urllib.request.urlopen", return_value=fake_file):
        prob = client.get_random_problem()
    assert prob["contest_id"] == "abc100"
    assert "atcoder.jp" in prob["link"]
