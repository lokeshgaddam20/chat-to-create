#!/usr/bin/env python
"""
Test script for the entire infrastructure request pipeline
"""
import os
import sys
import argparse
from backend.extractor.nlp_classifier import NLPTemplateClassifier
from backend.extractor.template_identifier import TemplateIdentifier
from backend.extractor.variable_extractor import VariableExtractor
from functions.terraform_functions import create_gcs_bucket

def test_nlp_pipeline(user_input: str, project_id: str):
    """Test the entire NLP to infrastructure pipeline"""
    
    print("\n🔍 Testing NLP Pipeline")
    print("═" * 50)
    print(f"Input: '{user_input}'")
    print("═" * 50)

    # Step 1: Template Identification
    print("\n1️⃣ Template Identification")
    print("-------------------------")
    identifier = TemplateIdentifier()
    template_name, confidence = identifier.identify_template(user_input)
    
    print(f"Template Matcher Result:")
    print(f"- Template: {template_name}")
    print(f"- Confidence: {confidence:.2f}")
    
    # If confidence is low, try NLP classifier
    if confidence < 0.4:
        print("\nLow confidence, trying NLP classifier...")
        classifier = NLPTemplateClassifier()
        template_name, confidence = classifier.classify_intent(user_input)
        print(f"NLP Classifier Result:")
        print(f"- Template: {template_name}")
        print(f"- Confidence: {confidence:.2f}")
    
    if not template_name or confidence < 0.2:
        print("\n❌ Failed to identify template with sufficient confidence")
        sys.exit(1)
        
    # Step 2: Variable Extraction
    print("\n2️⃣ Variable Extraction")
    print("--------------------")
    extractor = VariableExtractor(identifier.registry)
    variables = extractor.extract_variables(user_input, template_name)
    
    print("Extracted Variables:")
    for key, value in variables.items():
        print(f"- {key}: {value}")
        
    # Add required project_id if not extracted
    if 'project_id' not in variables:
        variables['project_id'] = project_id
        print(f"- project_id: {project_id} (from arguments)")
    
    # Step 3: Infrastructure Creation
    print("\n3️⃣ Infrastructure Creation")
    print("-----------------------")
    try:
        print("Executing terraform template...")
        result = create_gcs_bucket(**variables)
        
        if result.get("status") == "success":
            print("\n✅ Pipeline test successful!")
            print("\nDetails:")
            print(f"- Bucket Name: {variables.get('bucket_name', 'N/A')}")
            print(f"- Location: {variables.get('location', 'US')}")
            print(f"- Project ID: {variables.get('project_id', 'N/A')}")
            
            print("\nYou can verify the resources in:")
            print(f"1. GCP Console: https://console.cloud.google.com/storage/browser/{variables.get('bucket_name')}")
            if 'workspace_name' in result:
                print(f"2. Terraform Cloud: https://app.terraform.io/app/{os.getenv('TF_ORGANIZATION')}/workspaces/{result['workspace_name']}")
        else:
            print("\n❌ Infrastructure creation failed!")
            print("\nError details:")
            print(result.get("details", {}).get("error", "Unknown error"))
            print("\nCommand output:")
            print(result.get("details", {}).get("output", "No output"))
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Pipeline test failed with error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Test the entire NLP to Infrastructure pipeline")
    parser.add_argument("--project-id", required=True, help="GCP Project ID")
    parser.add_argument("prompt", nargs="*", help="The infrastructure request prompt")
    args = parser.parse_args()

    # Check for required environment variables
    if not os.getenv("TF_TOKEN_app_terraform_io"):
        print("Error: TF_TOKEN_app_terraform_io environment variable is not set")
        sys.exit(1)
    
    if not os.getenv("TF_ORGANIZATION"):
        print("Error: TF_ORGANIZATION environment variable is not set")
        sys.exit(1)

    # Get the prompt from arguments or ask for it
    if not args.prompt:
        print("Enter your infrastructure request prompt:")
        prompt = input("> ")
    else:
        prompt = " ".join(args.prompt)

    test_nlp_pipeline(prompt, args.project_id)

if __name__ == "__main__":
    main()
