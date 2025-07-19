import os
import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer, util

class SectionRanker:
    def __init__(self, model_path='models/all-MiniLM-L6-v2'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer(model_path, device=self.device)

    def embed_text(self, texts):
        return self.model.encode(texts, convert_to_tensor=True)

    def rank_sections(self, persona, job, sections):
        """
        sections: list of dicts with keys: {document, page_number, section_title, content}
        Returns the same list, ranked by importance.
        """
        # 1. Embed context (persona + job)
        query_text = f"Persona: {persona}\nTask: {job}"
        query_embedding = self.embed_text([query_text])[0]

        # 2. Embed all sections
        section_embeddings = self.embed_text([s['content'] for s in sections])

        # 3. Compute cosine similarities
        similarities = util.cos_sim(query_embedding, section_embeddings)[0].cpu().numpy()

        # 4. Rank sections
        ranked_sections = []
        for idx, sim in enumerate(similarities):
            ranked_sections.append({
                "document": sections[idx]["document"],
                "page_number": sections[idx]["page_number"],
                "section_title": sections[idx]["section_title"],
                "importance_rank": float(sim),
                "content": sections[idx]["content"]
            })

        # Sort by similarity descending
        ranked_sections = sorted(ranked_sections, key=lambda x: x["importance_rank"], reverse=True)

        return ranked_sections

    def rank_subsections(self, persona, job, ranked_sections, top_k=5):
        """
        Returns refined, ranked subsection analysis from top-ranked sections.
        """
        query_text = f"Persona: {persona}\nTask: {job}"
        query_embedding = self.embed_text([query_text])[0]

        subsection_analysis = []
        for section in ranked_sections[:top_k]:
            content = section['content']
            paragraphs = [p.strip() for p in content.split('\n') if len(p.strip()) > 50]

            if not paragraphs:
                continue

            para_embeddings = self.embed_text(paragraphs)
            sims = util.cos_sim(query_embedding, para_embeddings)[0].cpu().numpy()

            top_indices = np.argsort(sims)[::-1][:3]  # Top 3 relevant paragraphs

            for idx in top_indices:
                subsection_analysis.append({
                    "document": section['document'],
                    "page_number": section['page_number'],
                    "refined_text": paragraphs[idx],
                    "similarity_score": float(sims[idx])
                })

        return subsection_analysis


# Example usage
if __name__ == "__main__":
    ranker = SectionRanker()

    with open("intermediate/sections.json", "r") as f:
        data = json.load(f)

    persona = data["persona"]
    job = data["job"]
    sections = data["sections"]

    ranked = ranker.rank_sections(persona, job, sections)
    subsections = ranker.rank_subsections(persona, job, ranked)

    print("Top Sections:")
    for r in ranked[:3]:
        print(f"{r['section_title']} (Score: {r['importance_rank']:.4f})")

    print("\nSubsections:")
    for sub in subsections:
        print(f"{sub['refined_text'][:100]}... (Score: {sub['similarity_score']:.4f})")
