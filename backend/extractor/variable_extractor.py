import re
from typing import Dict, Any

class VariableExtractor:
    def __init__(self, template_registry):
        self.template_registry = template_registry
        
        # Pre-defined extraction patterns
        self.extraction_patterns = {
            'bucket_name': [
                r'bucket\s+(?:called|named)\s+"([^"]+)"',
                r'bucket\s+"([^"]+)"',
                r'gcs\s+bucket\s+([a-z0-9-]+)',
                r'storage\s+bucket\s+([a-z0-9-]+)'
            ],
            'project_id': [
                r'project\s+(?:id|ID)?\s+"([^"]+)"',
                r'project\s+([a-z][-a-z0-9]{4,28}[a-z0-9])'
            ],
            'location': [
                r'(?:location|region)\s+"([^"]+)"',
                r'in\s+(US(?:-[A-Z]+)?|EU|ASIA|[a-z]+-[a-z]+\d+)',
                r'region\s+(us-[a-z]+\d+|europe-[a-z]+\d+|asia-[a-z]+\d+)'
            ]
        }
    
    def extract_variables(self, user_input: str, template_name: str) -> Dict[str, Any]:
        template_config = self.template_registry["templates"][template_name]
        required_vars = template_config["required_vars"]
        optional_vars = template_config["optional_vars"]
        
        extracted = {}
        
        # Extract each required/optional variable
        for var_name in required_vars + optional_vars:
            if var_name in self.extraction_patterns:
                extracted[var_name] = self._extract_variable(user_input, var_name)
        
        # Handle special cases (like RAM -> instance_type conversion)
        if 'instance_type' in required_vars and not extracted.get('instance_type'):
            ram_match = re.search(r'(\d+)\s*gb\s*ram', user_input.lower())
            if ram_match:
                ram_size = ram_match.group(1)
                extracted['instance_type'] = self.ram_to_instance.get(ram_size, 't3.medium')
        
        return extracted
    
    def _extract_variable(self, text: str, var_name: str) -> Any:
        patterns = self.extraction_patterns.get(var_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None