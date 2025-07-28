import os
import json
import torch
import numpy as np
from datetime import datetime
from src.embed import Embedder
from src.extract import extract_outline
from src.summarizer import Summarizer
import fitz  # PyMuPDF

def load_input(input_path):
    with open(input_path, 'r') as f:
        return json.load(f)

def extract_section_text(pdf_path, page_number, heading_text):
    doc = fitz.open(pdf_path)
    if page_number >= len(doc):
        return ""
    page = doc[page_number]
    text_instances = page.search_for(heading_text.strip(), quads=False)
    if not text_instances:
        return ""
    found = text_instances[0]
    text = page.get_textbox(found).strip()
    return text

def process_case(json_path, pdf_dir, output_path):
    input_data = load_input(json_path)
    persona = input_data['persona']['role']
    job = input_data['job_to_be_done']['task']
    documents = input_data['documents']

    embedder = Embedder()
    summarizer = Summarizer()

    query_string = f"Persona: {persona}. Job: {job}"
    query_embedding = embedder.embed_query(persona, job)

    section_records = []
    for doc in documents:
        filename = doc["filename"]
        filepath = os.path.join(pdf_dir, filename)
        if not os.path.exists(filepath):
            print(f"[!] File not found: {filepath}")
            continue

        outline_data = extract_outline(filepath)
        print(f"[DEBUG] Outline for {filename}:", json.dumps(outline_data, indent=2))

        for section in outline_data.get("outline", []):
            page_num = section["page"]
            heading_text = section["text"]
            section_text = section.get("section_text", "")

            if not section_text or len(section_text) < 50:
                continue

            section_records.append({
                "doc": filename,
                "page": page_num,
                "heading": heading_text,
                "text": section_text
            })

    print(f"[DEBUG] Extracted {len(section_records)} sections.")
    if not section_records:
        print("[!] No valid sections found.")
        return

    section_texts = [(s["text"] + s["doc"]) for s in section_records]
    section_embeddings = embedder.embed_sections(section_texts)
    ranked_sections = embedder.rank_sections_by_query(query_embedding, query_string, section_records, section_embeddings)

    top_k = min(7, len(ranked_sections))
    top_sections = []
    for rank, section in enumerate(ranked_sections[:top_k], 1):
        summary = summarizer.summarize(section["text"])
        top_sections.append({
            "document": section["doc"],
            "page_number": section["page"],
            "section_title": section["heading"],
            "importance_rank": rank,
            "refined_text": summary
        })
        print(f"[RANK {rank}] Section: {section['heading']}")

    output = {
        "metadata": {
            "documents": [d["filename"] for d in documents],
            "persona": persona,
            "job_to_be_done": job,
            "processed_at": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": [
            {
                "document": s["document"],
                "page_number": s["page_number"],
                "section_title": s["section_title"],
                "importance_rank": s["importance_rank"]
            } for s in top_sections
        ],
        "subsection_analysis": [
            {
                "document": s["document"],
                "page_number": s["page_number"],
                "refined_text": s["refined_text"]
            } for s in top_sections
        ]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"[✓] Done. Output saved to {output_path}")

def main():
    input_base = "input"
    output_base = "output"

    for testcase in os.listdir(input_base):
        testcase_path = os.path.join(input_base, testcase)
        if not os.path.isdir(testcase_path):
            continue

        
        json_files = [f for f in os.listdir(testcase_path) if f.endswith(".json")]
        if not json_files:
            print(f"[!] No JSON found in {testcase_path}")
            continue
        json_path = os.path.join(testcase_path, json_files[0])

       
        pdf_dir = os.path.join(testcase_path, "pdf")
        if not os.path.exists(pdf_dir):
            print(f"[!] No PDF folder found in {testcase_path}")
            continue

        output_path = os.path.join(output_base, f"{testcase}.json")
        print(f"\n[★] Processing {testcase}...")
        process_case(json_path, pdf_dir, output_path)

if __name__ == "__main__":
    main()
