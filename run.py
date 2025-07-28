from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# Create base model directory
os.makedirs("models/embedding_model", exist_ok=True)
os.makedirs("models/summary_model", exist_ok=True)

# Download and save SentenceTransformer model
print("Downloading SentenceTransformer model...")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
sbert_model.save("models/embedding_model")

# Download and save T5-small model
print("Downloading T5-small model...")
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
t5_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

tokenizer.save_pretrained("models/summary_model")
t5_model.save_pretrained("models/summary_model")

print("All models downloaded and saved.")
