import json
from src.extract import extract_outline

INPUT_FILE = "input/sample.pdf"
OUTPUT_FILE = "output/sample.json"

def main():
    result = extract_outline(INPUT_FILE)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✅ Output written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
