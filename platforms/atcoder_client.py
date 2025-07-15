import json
import random
import time
import gzip
import math
from urllib import request
from urllib.error import HTTPError
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("atcoder")

class AtCoderClient:
    PROBLEMS_URL = "https://kenkoooo.com/atcoder/resources/problems.json"
    MODELS_URL   = "https://kenkoooo.com/atcoder/resources/problem-models.json"

    def __init__(self):
        self._cache = []

    def _fetch_json(self, url: str):
        try:
            req = request.Request(
                url,
                headers={
                    "User-Agent":      "Mozilla/5.0",
                    "Accept-Encoding": "gzip, deflate"
                }
            )
            with request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                headers = getattr(resp, "headers", {})
                if getattr(headers, "get", lambda x: None)("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except HTTPError as e:
            logger.error(f"[AtCoderClient] {url} → HTTP {e.code}: {e.reason}")
            return None

    def fetch_all_problems(self):
        if self._cache:
            return self._cache

        data = self._fetch_json(self.PROBLEMS_URL) or []
        time.sleep(1.1)  # API policy: ≥1s between calls

        models_json = self._fetch_json(self.MODELS_URL)
        # problem-models.json is actually a JSON *object* mapping problem IDs →
        # { difficulty, solved_count, … } :contentReference[oaicite:0]{index=0}
        if isinstance(models_json, dict):
            models = models_json
        elif isinstance(models_json, list):
            # (just in case it ever switches back to an array)
            models = {m.get("id"): m for m in models_json if isinstance(m, dict)}
        else:
            models = {}

        probs = []
        for p in data:
            pid = p.get("id")
            raw = None
            if pid in models:
                raw = models[pid].get("difficulty")

            if raw is None:
                disp_diff = None
            elif raw >= 400:
                disp_diff = round(raw)
            else:
                disp_diff = round(400 / math.exp(1.0 - raw / 400))

            probs.append({
                "id":         pid,
                "title":      p.get("title"),
                "contest_id": p.get("contest_id"),
                "difficulty": disp_diff,
                "link":       f"https://atcoder.jp/contests/{p.get('contest_id')}/tasks/{pid}"
            })

        self._cache = probs
        return probs

    def get_random_problem(self, min_rating=None, max_rating=None):
        choices = self.fetch_all_problems()
        if min_rating is not None:
            choices = [p for p in choices if p.get("difficulty") and p["difficulty"] >= min_rating]
        if max_rating is not None:
            choices = [p for p in choices if p.get("difficulty") and p["difficulty"] <= max_rating]
        return random.choice(choices) if choices else None
