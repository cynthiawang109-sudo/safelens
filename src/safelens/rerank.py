"""Optional pinned local cross-encoder over at most fifty fused report candidates."""

import math
import threading
from copy import deepcopy

_MODELS = {}
_LOCK = threading.Lock()


class LocalReranker:
    def __init__(self, settings):
        self.settings = settings

    def rerank(self, question, reports):
        if not reports:
            return []
        with _LOCK:
            key = (self.settings.rerank_model, self.settings.rerank_revision)
            if key not in _MODELS:
                from sentence_transformers import CrossEncoder
                _MODELS[key] = CrossEncoder(key[0], revision=key[1], device="cpu", trust_remote_code=False,
                                           cache_folder="data/models", max_length=512)
            hits = deepcopy(reports[:50])
            scores = _MODELS[key].predict([(question, h["text"]) for h in hits], batch_size=16, show_progress_bar=False)
        for hit, score in zip(hits, scores):
            if not math.isfinite(float(score)):
                raise ValueError("Invalid cross-encoder score")
            hit["fusion_score"] = hit["score"]
            hit["score"] = float(score)
        return sorted(hits, key=lambda h: (-h["score"], h["acn"]))
