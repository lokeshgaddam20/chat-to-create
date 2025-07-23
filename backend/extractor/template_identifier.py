import json
import re
from typing import Dict, List, Tuple

class TemplateIdentifier:
    def __init__(self, registry_path="templates/registry.json"):
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)
        
        # Pre-compile regex patterns for faster matching
        self.keyword_patterns = {}
        for template_name, config in self.registry["templates"].items():
            pattern = r'\b(' + '|'.join(config["keywords"]) + r')\b'
            self.keyword_patterns[template_name] = re.compile(pattern, re.IGNORECASE)
    
    def identify_template(self, user_input: str) -> Tuple[str, float]:
        """
        Returns: (template_name, confidence_score)
        """
        scores = {}
        
        for template_name, pattern in self.keyword_patterns.items():
            matches = pattern.findall(user_input)
            # Simple scoring: number of keyword matches
            scores[template_name] = len(matches)
        
        # Get highest scoring template
        if not scores or max(scores.values()) == 0:
            return None, 0.0
            
        best_template = max(scores, key=scores.get)
        confidence = scores[best_template] / len(user_input.split())
        
        return best_template, confidence

# Usage
identifier = TemplateIdentifier()
template, confidence = identifier.identify_template("Create an S3 bucket for storing images")
# Returns: ("s3-bucket", 0.2)