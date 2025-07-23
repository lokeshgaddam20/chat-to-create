#!/usr/bin/env python
"""
Test script for Terraform Cloud backend setup
"""
import os
import sys
import argparse
from backend.terraform.client import TerraformCloudClient

def setup_test_template(base_dir: str) -> str:
    """Creates a test Terraform template for GCS bucket"""
    template_dir = os.path.join(base_dir, "test-template")
    os.makedirs(template_dir, exist_ok=True)
    
    # Create main.tf
    main_tf = '''
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
}

resource "google_storage_bucket" "test_bucket" {
  name          = var.bucket_name
  location      = var.location
  force_destroy = true  # For easy cleanup in testing
}
'''
    
    # Create variables.tf
    variables_tf = '''
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "bucket_name" {
  description = "Name of the GCS bucket"
  type        = string
}

variable "location" {
  description = "Location for the bucket"
  type        = string
  default     = "US"
}
'''
    
    with open(os.path.join(template_dir, "main.tf"), "w") as f:
        f.write(main_tf)
    
    with open(os.path.join(template_dir, "variables.tf"), "w") as f:
        f.write(variables_tf)
        
    return template_dir

def main():
    parser = argparse.ArgumentParser(description="Test Terraform Cloud backend setup")
    parser.add_argument("--organization", required=True, help="Terraform Cloud organization name")
    parser.add_argument("--project-id", required=True, help="GCP Project ID")
    parser.add_argument("--bucket-prefix", default="test-bucket", help="Prefix for the test bucket name")
    args = parser.parse_args()

    # Check for Terraform Cloud token
    if not os.getenv("TF_TOKEN_app_terraform_io"):
        print("Error: TF_TOKEN_app_terraform_io environment variable is not set")
        sys.exit(1)

    try:
        # Create a unique bucket name
        import uuid
        bucket_name = f"{args.bucket_prefix}-{uuid.uuid4().hex[:8]}"
        
        # Create test template
        template_dir = setup_test_template(os.path.dirname(os.path.abspath(__file__)))
        
        print(f"Testing Terraform Cloud backend with organization: {args.organization}")
        print(f"Creating test bucket: {bucket_name}")
        
        # Initialize client
        client = TerraformCloudClient(organization=args.organization)
        
        # Execute template
        result = client.execute_template(
            template_path=template_dir,
            variables={
                "project_id": args.project_id,
                "bucket_name": bucket_name,
                "location": "US"
            },
            workspace_name=f"test-{bucket_name}"
        )
        
        if result.get("status") == "success":
            print("\n✅ Test successful!")
            print(f"Created bucket: {bucket_name}")
            print("\nDetails:")
            print(f"- Workspace: test-{bucket_name}")
            print(f"- Organization: {args.organization}")
            print("\nYou can verify the resources in:")
            print(f"1. GCP Console: https://console.cloud.google.com/storage/browser/{bucket_name}")
            print(f"2. Terraform Cloud: https://app.terraform.io/app/{args.organization}/workspaces/test-{bucket_name}")
        else:
            print("\n❌ Test failed!")
            print("\nError details:")
            print(result.get("details", {}).get("error", "Unknown error"))
            print("\nCommand output:")
            print(result.get("details", {}).get("output", "No output"))
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
