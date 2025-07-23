# functions/terraform_functions.py
import os
from backend.terraform.client import TerraformCloudClient

# Get Terraform Cloud settings from environment variables
TF_ORGANIZATION = os.getenv("TF_ORGANIZATION")
TF_TOKEN = os.getenv("TF_TOKEN_app_terraform_io")

def create_gcs_bucket(bucket_name: str, project_id: str, location: str = "US", **kwargs):
    """Creates GCS bucket using Terraform Cloud API"""
    template_path = "templates/gcp/gcs-bucket"
    variables = {
        "bucket_name": bucket_name,
        "project_id": project_id,
        "location": location,
        **kwargs
    }
    
    # Create workspace name based on bucket name
    workspace_name = f"gcs-{bucket_name}"
    
    terraform_client = TerraformCloudClient(
        organization=TF_ORGANIZATION,
        token=TF_TOKEN
    )
    return terraform_client.execute_template(
        template_path=template_path,
        variables=variables,
        workspace_name=workspace_name
    )

# Function registry - maps template names to actual functions
FUNCTION_REGISTRY = {
    "gcs-bucket": create_gcs_bucket
}