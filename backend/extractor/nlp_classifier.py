from transformers import pipeline
from typing import Tuple

class NLPTemplateClassifier:
    def __init__(self):
        # Load pre-trained classification model or train custom one
        self.classifier = pipeline(
            "zero-shot-classification", 
            model="facebook/bart-large-mnli"
        )
        
        # Define possible intents/templates
        self.candidate_labels = [
            "create gcs bucket",
            "create cloud storage bucket",
            "create google storage"
        ]
        
        # Map labels to template names
        self.label_to_template = {
            "create gcs bucket": "gcs-bucket",
            "create cloud storage bucket": "gcs-bucket",
            "create google storage": "gcs-bucket"
        }
    
    def classify_intent(self, user_input: str) -> Tuple[str, float]:
        result = self.classifier(user_input, self.candidate_labels)
        
        best_label = result['labels'][0]
        confidence = result['scores'][0]
        
        template_name = self.label_to_template.get(best_label)
        return template_name, confidence