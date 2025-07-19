import os
import json
from src.extract import extract_outline

INPUT_DIR = "input"
OUTPUT_DIR = "output"

for filename in os.listdir(INPUT_DIR):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(INPUT_DIR, filename)
        try:
            result = extract_outline(pdf_path)
            output_filename = filename.replace(".pdf", ".json")
            with open(os.path.join(OUTPUT_DIR, output_filename), "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
