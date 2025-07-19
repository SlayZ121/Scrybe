from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os

class Summarizer:
    
    def __init__(self, model_dir="models/summary_model", device="cpu"):
        assert os.path.exists(model_dir), f"Local model dir '{model_dir}' not found"
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, local_files_only=True)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)


    def summarize(self, text: str, max_length=120, min_length=30) -> str:
        if not text or len(text.strip()) < 50:
            return text.strip()

        
        input_text = "summarize: " + text.strip()
        inputs = self.tokenizer.encode(
            input_text, return_tensors="pt", truncation=True, max_length=1000
        ).to(self.device)

        summary_ids = self.model.generate(
            inputs,
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True,
        )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary.strip()


# Example usage
if __name__ == "__main__":
    sample=""" The rise of social media platforms has transformed the way people communicate, share information, and form communities. Platforms like Facebook, Twitter, Instagram, and TikTok have enabled users to create and disseminate content instantly to global audiences. This shift has democratized content creation, allowing anyone with internet access to become a publisher, influencer, or activist. However, it has also led to the spread of misinformation, cyberbullying, and the erosion of privacy. The algorithms that govern content visibility often prioritize sensationalism over accuracy, leading to echo chambers and polarization. Governments and tech companies continue to debate over the ethical responsibilities of these platforms, especially regarding content moderation, data protection, and freedom of expression. As digital engagement becomes more deeply embedded in daily life, the need for digital literacy and regulatory frameworks becomes increasingly critical to ensure a healthy, informed, and respectful online environment."""
    s = Summarizer()
    print(s.summarize(sample))
