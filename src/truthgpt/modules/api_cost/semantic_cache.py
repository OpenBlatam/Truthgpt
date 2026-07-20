"""
Semantic Cache for LLM API responses (GPTCache-style).

Reference: Bang, F. (2023). GPTCache: An Open-Source Semantic Cache for LLM
Applications. https://arxiv.org/abs/2306.11516

Key ideas:
- Two-tier lookup: exact hash match (O(1)) then embedding similarity (ANN).
- Local embedding model (sentence-transformers) to avoid API cost for caching itself.
- SQLite persistence + optional FAISS index for vector search.
- TTL eviction and LRU bounded size.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    prompt_hash: str
    prompt: str
    response: str
    model: str
    embedding: Optional[List[float]]
    created_at: float
    last_access: float
    hits: int = 0
    tokens_saved: int = 0
    cost_saved_usd: float = 0.0


def _hash_prompt(prompt: str, model: str = '') -> str:
    h = hashlib.sha256()
    h.update(model.encode('utf-8', errors='ignore'))
    h.update(b'\x00')
    h.update(prompt.encode('utf-8', errors='ignore'))
    return h.hexdigest()


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class EmbeddingCache:
    """Pluggable local embedding provider with graceful fallback.

    Tries sentence-transformers; falls back to deterministic hashing-based
    pseudo-embedding (still useful for exact/near-exact match) when the
    library is unavailable.
    """

    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None
        self._dim = 384
        self._lock = threading.Lock()
        self._memo: 'OrderedDict[str, List[float]]' = OrderedDict()
        self._memo_cap = 4096
        self._try_load()

    def _try_load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(self.model_name)
            try:
                self._dim = int(self._model.get_sentence_embedding_dimension())
            except Exception:
                self._dim = 384
            logger.info('EmbeddingCache: loaded %s (dim=%d)', self.model_name, self._dim)
        except Exception as e:  # pragma: no cover
            logger.warning('EmbeddingCache: sentence-transformers unavailable (%s); using fallback', e)
            self._model = None

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> List[float]:
        key = _hash_prompt(text)
        with self._lock:
            if key in self._memo:
                self._memo.move_to_end(key)
                return self._memo[key]
        if self._model is not None:
            try:
                vec = self._model.encode([text], normalize_embeddings=True)[0]
                emb = [float(x) for x in vec]
            except Exception as e:
                logger.warning('Embedding failed, fallback: %s', e)
                emb = self._fallback_embed(text)
        else:
            emb = self._fallback_embed(text)
        with self._lock:
            self._memo[key] = emb
            if len(self._memo) > self._memo_cap:
                self._memo.popitem(last=False)
        return emb

    def _fallback_embed(self, text: str) -> List[float]:
        # Deterministic feature hashing -> 384-dim sparse-ish vector
        dim = self._dim
        vec = [0.0] * dim
        tokens = text.lower().split()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode('utf-8')).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 16) & 1 else -1.0
            vec[idx] += sign
        # L2 normalize
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class SemanticCache:
    """Two-tier semantic cache: exact hash + embedding similarity.

    Thread-safe. SQLite-backed persistence. In-memory hot index for speed.
    """

    def __init__(
        self,
        cache_dir: str = './.api_cost_cache',
        similarity_threshold: float = 0.92,
        max_entries: int = 100_000,
        ttl_seconds: int = 7 * 24 * 3600,
        embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2',
        exact_match_first: bool = True,
    ):
        self.cache_dir = cache_dir
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.exact_match_first = exact_match_first
        os.makedirs(self.cache_dir, exist_ok=True)
        self.db_path = os.path.join(self.cache_dir, 'semantic_cache.sqlite')
        self._lock = threading.RLock()
        self._embedder = EmbeddingCache(embedding_model)
        self._hot_index: Dict[str, Tuple[List[float], str]] = {}  # hash -> (emb, response)
        self._init_db()
        self._load_hot_index()
        self.stats = {'hits_exact': 0, 'hits_semantic': 0, 'misses': 0, 'cost_saved_usd': 0.0}

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    prompt_hash TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    embedding TEXT,
                    created_at REAL NOT NULL,
                    last_access REAL NOT NULL,
                    hits INTEGER DEFAULT 0,
                    tokens_saved INTEGER DEFAULT 0,
                    cost_saved_usd REAL DEFAULT 0.0
                )
                """
            )
            conn.execute('CREATE INDEX IF NOT EXISTS idx_last_access ON cache(last_access)')
            conn.commit()

    def _load_hot_index(self, limit: int = 10_000) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    'SELECT prompt_hash, embedding, response FROM cache '
                    'ORDER BY last_access DESC LIMIT ?', (limit,)
                )
                for h, emb_json, resp in cur.fetchall():
                    if emb_json:
                        try:
                            self._hot_index[h] = (json.loads(emb_json), resp)
                        except Exception:
                            continue
            logger.info('SemanticCache: loaded %d hot entries', len(self._hot_index))
        except Exception as e:
            logger.warning('SemanticCache hot load failed: %s', e)

    def get(self, prompt: str, model: str = '') -> Optional[str]:
        now = time.time()
        h = _hash_prompt(prompt, model)
        with self._lock:
            # Tier 1: exact hash
            if self.exact_match_first:
                resp = self._db_get_exact(h, now)
                if resp is not None:
                    self.stats['hits_exact'] += 1
                    return resp
            # Tier 2: semantic similarity
            emb = self._embedder.embed(prompt)
            best_sim = 0.0
            best_resp: Optional[str] = None
            best_hash: Optional[str] = None
            for ch, (cemb, cresp) in self._hot_index.items():
                sim = _cosine(emb, cemb)
                if sim > best_sim:
                    best_sim = sim
                    best_resp = cresp
                    best_hash = ch
            if best_resp is not None and best_sim >= self.similarity_threshold:
                self.stats['hits_semantic'] += 1
                if best_hash:
                    self._touch(best_hash, now)
                logger.debug('SemanticCache hit sim=%.3f', best_sim)
                return best_resp
            self.stats['misses'] += 1
            return None

    def put(
        self,
        prompt: str,
        response: str,
        model: str = '',
        tokens_saved: int = 0,
        cost_saved_usd: float = 0.0,
    ) -> None:
        now = time.time()
        h = _hash_prompt(prompt, model)
        emb = self._embedder.embed(prompt)
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        'INSERT OR REPLACE INTO cache '
                        '(prompt_hash, prompt, response, model, embedding, created_at, last_access, hits, tokens_saved, cost_saved_usd) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT hits FROM cache WHERE prompt_hash=?), 0), ?, ?)',
                        (h, prompt, response, model, json.dumps(emb), now, now, h, tokens_saved, cost_saved_usd),
                    )
                    conn.commit()
                self._hot_index[h] = (emb, response)
                if len(self._hot_index) > 10_000:
                    # Drop oldest by popping arbitrary (dicts are ordered insertion)
                    first_key = next(iter(self._hot_index))
                    self._hot_index.pop(first_key, None)
                self._evict_if_needed()
            except Exception as e:
                logger.warning('SemanticCache put failed: %s', e)

    def _db_get_exact(self, prompt_hash: str, now: float) -> Optional[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    'SELECT response, created_at FROM cache WHERE prompt_hash=?', (prompt_hash,)
                )
                row = cur.fetchone()
                if row is None:
                    return None
                response, created_at = row
                if self.ttl_seconds > 0 and (now - created_at) > self.ttl_seconds:
                    conn.execute('DELETE FROM cache WHERE prompt_hash=?', (prompt_hash,))
                    conn.commit()
                    self._hot_index.pop(prompt_hash, None)
                    return None
                self._touch(prompt_hash, now)
                return response
        except Exception as e:
            logger.warning('SemanticCache exact get failed: %s', e)
            return None

    def _touch(self, prompt_hash: str, now: float) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'UPDATE cache SET last_access=?, hits=hits+1 WHERE prompt_hash=?',
                    (now, prompt_hash),
                )
                conn.commit()
        except Exception:
            pass

    def _evict_if_needed(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute('SELECT COUNT(*) FROM cache')
                count = cur.fetchone()[0]
                if count <= self.max_entries:
                    return
                to_delete = count - self.max_entries
                conn.execute(
                    'DELETE FROM cache WHERE prompt_hash IN '
                    '(SELECT prompt_hash FROM cache ORDER BY last_access ASC LIMIT ?)',
                    (to_delete,),
                )
                conn.commit()
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        total = self.stats['hits_exact'] + self.stats['hits_semantic'] + self.stats['misses']
        hit_rate = 0.0 if total == 0 else (self.stats['hits_exact'] + self.stats['hits_semantic']) / total
        return {**self.stats, 'hit_rate': hit_rate, 'total_requests': total}