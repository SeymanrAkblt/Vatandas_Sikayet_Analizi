# models.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import List

class TextClassifier:
    def __init__(self, model_dir: str, max_len: int = 160):
        # models.py -> TextClassifier.__init__ içinde
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model     = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)

        self.model.eval()
        self.max_len = max_len
        self.id2label = self.model.config.id2label

    def predict(self, texts: List[str]) -> List[str]:
        if isinstance(texts, str): texts = [texts]
        inputs = self.tokenizer(texts, padding=True, truncation=True,
                                max_length=self.max_len, return_tensors="pt")
        with torch.no_grad():
            logits = self.model(**inputs).logits
            preds = torch.argmax(logits, dim=-1).cpu().numpy().tolist()
        return [self.id2label[int(p)] for p in preds]
