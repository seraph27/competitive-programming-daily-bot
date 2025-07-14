import json
import random
from urllib import request

from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("atcoder")

class AtCoderClient:
    PROBLEMS_URL = "https://kenkoooo.com/atcoder/resources/problems.json"

    def __init__(self):
        self._cache = []

    def fetch_all_problems(self):
        if self._cache:
            return self._cache
        with request.urlopen(self.PROBLEMS_URL, timeout=10) as resp:
            data = json.load(resp)
        probs = []
        for p in data:
            probs.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "contest_id": p.get("contest_id"),
                "link": f"https://atcoder.jp/contests/{p.get('contest_id')}/tasks/{p.get('id')}"
            })
        self._cache = probs
        return self._cache

    def get_random_problem(self):
        self.fetch_all_problems()
        return random.choice(self._cache) if self._cache else None
