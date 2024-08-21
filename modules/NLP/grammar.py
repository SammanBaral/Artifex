from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class GrammarCorrector:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("grammarly/coedit-large")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("grammarly/coedit-large").to(self.device)

    def correct(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
        outputs = self.model.generate(**inputs, max_length=512)
        corrected_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected_text

# Initialize the grammar corrector
grammar_corrector = GrammarCorrector()