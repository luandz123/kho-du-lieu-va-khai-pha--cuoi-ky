"""Gợi ý hybrid = lọc cộng tác (item-based CF, đã có ở bản cũ) + gợi ý theo nội dung (embedding).

  điểm(i) = α · CF(i) + (1 − α) · NộiDung(i)

  CF(i)       tổng độ tương đồng cosine giữa phim i và các phim user đã thích (≥ 4 sao),
              chỉ tính trong 40 hàng xóm gần nhất của mỗi phim (giống bản cũ), chia cho max -> [0, 1].
  NộiDung(i)  cosine giữa vector mô tả phim i và "vector sở thích" của user
              (trung bình vector các phim user đã thích), chia cho max -> [0, 1].
  α = 1       đúng bằng CF của bản cũ;  α = 0  chỉ dùng nội dung.

Vì sao cần hybrid: CF chỉ học từ hành vi chấm điểm. Người dùng mới (ít rating) hoặc phim ít người
chấm thì CF yếu (cold-start); phần nội dung vẫn hoạt động vì chỉ cần mô tả phim.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from mining.cf import build_sparse_ratings_matrix, compute_item_cosine_similarities_top_k

SEED_THRESHOLD = 4
NEIGHBOR_K = 40


@dataclass
class Recommendation:
    movie_id: int
    score: float
    cf: float
    content: float
    because: int | None      # phim user đã thích giống phim này nhất (để giải thích)


class HybridRecommender:
    def __init__(self, embeddings: dict[int, np.ndarray], popularity_prior: bool = True):
        self.popularity_prior = popularity_prior
        self.emb_ids = np.array(sorted(embeddings))
        self.emb_index = {m: i for i, m in enumerate(self.emb_ids)}
        self.E = np.vstack([embeddings[m] for m in self.emb_ids]).astype(np.float32)

    def fit(self, train: pd.DataFrame) -> "HybridRecommender":
        """train: các cột user_id, movie_id, rating."""
        R, _, idx_to_movie, _, _ = build_sparse_ratings_matrix(train)
        self.neighbors = compute_item_cosine_similarities_top_k(R, idx_to_movie, max_k=NEIGHBOR_K)
        self.popularity = train.groupby("movie_id").size().to_dict()
        self.catalog = set(self.popularity)
        return self

    def recommend(self, ratings: dict[int, int], alpha: float = 0.7, top_n: int = 5,
                  candidates: set[int] | None = None) -> list[Recommendation]:
        """ratings: {movie_id: số sao} mà user đã chấm. Không gợi ý lại phim đã chấm."""
        seeds = [m for m, r in ratings.items() if r >= SEED_THRESHOLD]
        pool = (candidates if candidates is not None else self.catalog) - set(ratings)
        if not pool:
            return []
        pool = np.array(sorted(pool))

        # --- CF
        cf = {}
        for s in seeds:
            for m, sim in self.neighbors.get(s, []):
                cf[m] = cf.get(m, 0.0) + sim
        cf_vec = np.array([cf.get(m, 0.0) for m in pool])
        if cf_vec.max() > 0:
            cf_vec = cf_vec / cf_vec.max()

        # --- Nội dung
        seed_rows = [self.emb_index[s] for s in seeds if s in self.emb_index]
        content_vec = np.zeros(len(pool))
        has_emb = np.array([m in self.emb_index for m in pool])
        if seed_rows and has_emb.any():
            profile = self.E[seed_rows].mean(axis=0)
            profile /= np.linalg.norm(profile) or 1.0
            rows = [self.emb_index[m] for m in pool[has_emb]]
            content_vec[has_emb] = np.clip(self.E[rows] @ profile, 0, None)

        pop = np.array([self.popularity.get(m, 0) for m in pool])
        if self.popularity_prior and content_vec.max() > 0:
            # Nội dung giống nhưng gần như không ai xem thì ít khả năng user thích:
            # nhân với độ phổ biến theo thang log (phim 1 rating ~0, phim nhiều rating nhất = 1).
            content_vec = content_vec * np.log1p(pop) / np.log1p(max(self.popularity.values()))
        if content_vec.max() > 0:
            content_vec = content_vec / content_vec.max()

        score = alpha * cf_vec + (1 - alpha) * content_vec
        # Xếp hạng: điểm giảm dần, hòa thì phim phổ biến hơn, rồi movie_id tăng dần (giống bản cũ).
        order = np.lexsort((pool, -pop, -score))[:top_n]

        out = []
        for i in order:
            m = int(pool[i])
            out.append(Recommendation(m, float(score[i]), float(cf_vec[i]), float(content_vec[i]),
                                      self._because(m, seeds)))
        return out

    def _because(self, movie_id: int, seeds: list[int]) -> int | None:
        if not seeds:
            return None
        sims = {m: s for m, s in self.neighbors.get(movie_id, [])}
        best = max(seeds, key=lambda s: sims.get(s, 0.0))
        if sims.get(best, 0.0) > 0:
            return best
        if movie_id in self.emb_index:
            seed_rows = [s for s in seeds if s in self.emb_index]
            if seed_rows:
                v = self.E[self.emb_index[movie_id]]
                return max(seed_rows, key=lambda s: float(self.E[self.emb_index[s]] @ v))
        return None
