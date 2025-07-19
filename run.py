from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Download and save to a local folder
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

tokenizer.save_pretrained("./bart_model")
model.save_pretrained("./bart_model")
