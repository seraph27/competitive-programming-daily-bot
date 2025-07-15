import json
import random
from urllib import request

from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("codeforces")

class CodeforcesClient:
    PROBLEMS_URL = "https://codeforces.com/api/problemset.problems"

    def __init__(self):
        self._cache = []

    def fetch_all_problems(self):
        if self._cache:
            return self._cache
        with request.urlopen(self.PROBLEMS_URL, timeout=10) as resp:
            data = json.load(resp)
        if data.get("status") != "OK":
            logger.error(f"Failed to fetch problems: {data}")
            return []
        probs = []
        for p, stat in zip(data["result"]["problems"], data["result"]["problemStatistics"]):
            probs.append({
                "contestid": p.get('contestId'),
                "id": p.get('index'),
                "title": p.get("name"),
                "link": f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}",
                "rating": p.get("rating"),
                "tags": p.get("tags", []),
                "solved_count": stat.get("solvedCount")
            })
        self._cache = probs
        return self._cache

    def get_random_problem(self, min_rating=None, max_rating=None):
        """Return a random problem optionally filtered by a rating range."""
        self.fetch_all_problems()
        choices = self._cache
        if min_rating is not None:
            choices = [p for p in choices if p.get("rating") and p["rating"] >= min_rating]
        if max_rating is not None:
            choices = [p for p in choices if p.get("rating") and p["rating"] <= max_rating]
        return random.choice(choices) if choices else None
