import json
import random
from urllib import request

from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("atcoder")

class AtCoderClient:
    PROBLEMS_URL = "https://kenkoooo.com/atcoder/resources/problems.json"
    MODELS_URL = "https://kenkoooo.com/atcoder/resources/problem-models.json"

    def __init__(self):
        self._cache = []

    def fetch_all_problems(self):
        if self._cache:
            return self._cache
        req = request.Request(self.PROBLEMS_URL, headers={"User-Agent": "Mozilla/5.0"})
        with request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)

        req_models = request.Request(self.MODELS_URL, headers={"User-Agent": "Mozilla/5.0"})
        with request.urlopen(req_models, timeout=10) as resp:
            models = json.load(resp)

        probs = []
        for p in data:
            model = models.get(p.get("id"), {})
            probs.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "contest_id": p.get("contest_id"),
                "difficulty": model.get("difficulty"),
                "link": f"https://atcoder.jp/contests/{p.get('contest_id')}/tasks/{p.get('id')}"
            })
        self._cache = probs
        return self._cache

    def get_random_problem(self, min_rating=None, max_rating=None):
        """Return a random problem optionally filtered by difficulty range."""
        self.fetch_all_problems()
        choices = self._cache
        if min_rating is not None:
            choices = [p for p in choices if p.get("difficulty") and p["difficulty"] >= min_rating]
        if max_rating is not None:
            choices = [p for p in choices if p.get("difficulty") and p["difficulty"] <= max_rating]
        return random.choice(choices) if choices else None
