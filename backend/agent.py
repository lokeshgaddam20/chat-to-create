from typing import Dict
import json
from backend.extractor.template_identifier import TemplateIdentifier
from backend.extractor.nlp_classifier import NLPTemplateClassifier
from backend.extractor.variable_extractor import VariableExtractor
from functions.terraform_functions import FUNCTION_REGISTRY

class InfrastructureAgent:
    def __init__(self):
        # Load all components
        self.template_identifier = TemplateIdentifier()
        self.nlp_classifier = NLPTemplateClassifier()
        self.variable_extractor = VariableExtractor(self.template_identifier.registry)
        self.function_registry = FUNCTION_REGISTRY
        
        # Load template registry
        with open('backend/templates/registry.json', 'r') as f:
            self.template_registry = json.load(f)
    
    def process_request(self, user_input: str) -> Dict:
        """Main processing pipeline for GCP infrastructure requests"""
        
        # Step 1: Identify template
        template_name, confidence = self.template_identifier.identify_template(user_input)
        
        if confidence < 0.4:  # Adjusted threshold for GCP-specific matching
            template_name, confidence = self.nlp_classifier.classify_intent(user_input)
        
        if not template_name or confidence < 0.2:  # Lower threshold since we have fewer templates
            return {"error": "Could not identify GCP infrastructure request"}
        
        # Step 2: Extract variables
        variables = self.variable_extractor.extract_variables(user_input, template_name)
        
        # Step 3: Validate required variables
        template_config = self.template_registry["templates"][template_name]
        missing_vars = []
        for required_var in template_config["required_vars"]:
            if not variables.get(required_var):
                missing_vars.append(required_var)
        
        if missing_vars:
            return {
                "status": "missing_variables",
                "template": template_name,
                "missing": missing_vars,
                "extracted": variables
            }
        
        # Step 4: Get and call the function
        function = self.function_registry.get(template_name)
        if not function:
            return {"error": f"No function found for template {template_name}"}
        
        # Step 5: Execute the function
        try:
            result = function(**variables)
            return {
                "status": "success",
                "template": template_name,
                "variables": variables,
                "result": result
            }
        except Exception as e:
            return {
                "status": "error", 
                "template": template_name,
                "error": str(e)
            }

# Usage example
if __name__ == "__main__":
    agent = InfrastructureAgent()
    result = agent.process_request('Create a GCS bucket called "my-data" in project "my-gcp-project"')
    print(result)