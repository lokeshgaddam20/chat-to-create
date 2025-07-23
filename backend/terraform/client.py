"""
Terraform Cloud Client for executing terraform operations
"""
import os
import json
import subprocess
from typing import Dict, Any, Optional

class TerraformCloudClient:
    def __init__(self, organization: str, token: Optional[str] = None):
        """
        Initialize Terraform Cloud client
        
        Args:
            organization: Terraform Cloud organization name
            token: Terraform Cloud API token. If not provided, will try to get from env var TF_TOKEN_app_terraform_io
        """
        self.terraform_path = "terraform"  # Assumes terraform is in PATH
        self.workspace_dir = None
        self.organization = organization
        self.token = token or os.getenv("TF_TOKEN_app_terraform_io")
        
        if not self.token:
            raise ValueError("Terraform Cloud token must be provided or set in TF_TOKEN_app_terraform_io environment variable")
            
        # Create terraform CLI config file with token
        self._setup_terraform_credentials()

    def _setup_terraform_credentials(self) -> None:
        """Setup Terraform Cloud credentials"""
        cli_config = {
            "credentials": {
                "app.terraform.io": {
                    "token": self.token
                }
            }
        }
        
        # Create .terraform.d directory in user's home
        terraform_d = os.path.expanduser("~/.terraform.d")
        os.makedirs(terraform_d, exist_ok=True)
        
        # Write credentials file
        credentials_path = os.path.join(terraform_d, "credentials.tfrc.json")
        with open(credentials_path, "w") as f:
            json.dump(cli_config, f, indent=2)

    def execute_template(self, template_path: str, variables: Dict[str, Any], workspace_name: str) -> Dict[str, Any]:
        """
        Executes a terraform template with the given variables
        
        Args:
            template_path: Path to the terraform template directory
            variables: Dictionary of variables to pass to terraform
            workspace_name: Name of the Terraform Cloud workspace
            
        Returns:
            Dict containing the execution results
        """
        self.workspace_dir = os.path.abspath(template_path)
        
        # Create/update backend configuration for Terraform Cloud
        self._setup_cloud_backend(workspace_name)
        
        # Create terraform.tfvars file
        self._create_tfvars(variables)
        
        # Initialize Terraform
        init_result = self._run_terraform_command("init")
        if init_result.get("error"):
            return init_result
            
        # Run terraform plan
        plan_result = self._run_terraform_command("plan")
        if plan_result.get("error"):
            return plan_result
            
        # Run terraform apply
        apply_result = self._run_terraform_command("apply", "-auto-approve")
        
        return {
            "status": "success" if not apply_result.get("error") else "error",
            "details": apply_result
        }
    
    def _setup_cloud_backend(self, workspace_name: str) -> None:
        """Setup Terraform Cloud backend configuration"""
        backend_config = {
            "terraform": {
                "backend": {
                    "remote": {
                        "hostname": "app.terraform.io",
                        "organization": self.organization,
                        "workspaces": {
                            "name": workspace_name
                        }
                    }
                }
            }
        }
        
        # Write backend config
        backend_path = os.path.join(self.workspace_dir, "backend.tf.json")
        with open(backend_path, "w") as f:
            json.dump(backend_config, f, indent=2)

    def _create_tfvars(self, variables: Dict[str, Any]) -> None:
        """Creates terraform.tfvars file from variables"""
        tfvars_content = []
        for key, value in variables.items():
            if isinstance(value, str):
                tfvars_content.append(f'{key} = "{value}"')
            else:
                tfvars_content.append(f'{key} = {value}')
                
        tfvars_path = os.path.join(self.workspace_dir, "terraform.tfvars")
        with open(tfvars_path, "w") as f:
            f.write("\n".join(tfvars_content))
    
    def _run_terraform_command(self, command: str, *args) -> Dict[str, Any]:
        """Executes a terraform command"""
        try:
            cmd = [self.terraform_path, command, *args]
            result = subprocess.run(
                cmd,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "output": result.stdout,
                "command": " ".join(cmd)
            }
        except subprocess.CalledProcessError as e:
            return {
                "error": str(e),
                "output": e.stdout,
                "stderr": e.stderr,
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "error": str(e),
                "command": " ".join(cmd)
            }
