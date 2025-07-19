import os
import re
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

GENERIC_HEADINGS = {"introduction", "overview", "summary", "conclusion", "disclaimer", "preface", "foreword"}


class Embedder:
    def __init__(self, model_path="models/embedding_model", device="cpu"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please download it first.")
        self.device = device
        self.model = SentenceTransformer(model_path, device=self.device)

    def embed_query(self, persona: str, job: str) -> np.ndarray:
        query = f"{persona}. {job}"
        return self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)

    def embed_sections(self, sections: list[str]) -> np.ndarray:
        return self.model.encode(sections, convert_to_numpy=True, normalize_embeddings=True)

    @staticmethod
    def tokenize(text):
        return set(re.findall(r"\w+", text.lower()))

    def rank_sections_by_query(self, query_embedding: np.ndarray, query: str, sections: list[dict], embeddings: np.ndarray, top_k=5):
        query_tokens = self.tokenize(query)
        ranked = []

        for section, section_embedding in zip(sections, embeddings):
            heading = section.get("heading", "")
            body = section.get("text", "")
            title= section.get("doc","")
            
            emb_sim = cosine_similarity([query_embedding], [section_embedding])[0][0]
            text_tokens = self.tokenize(title +" "+ heading)
            
            keyword_overlap = len(query_tokens & text_tokens) / max(1, len(query_tokens))
            heading_tokens = self.tokenize(heading)
            heading_overlap = len(query_tokens & heading_tokens) / max(1, len(query_tokens))
            heading_boost = 0.1 if heading_overlap > 0 else 0.0
            generic_penalty = -0.2 if heading.lower().strip() in GENERIC_HEADINGS else 0.0

            score = (
                0.8 * emb_sim +
                0.1 * keyword_overlap +
                generic_penalty
            )

            ranked.append((score, section))

        ranked.sort(reverse=True, key=lambda x: x[0])
        return [s for _, s in ranked[:top_k]]



