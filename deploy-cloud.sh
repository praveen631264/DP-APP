#!/bin/bash
# This script initiates the production deployment to Google Cloud using Terraform.

echo "Starting Google Cloud deployment with Terraform..."

# Navigate to the deployment directory
cd gcp_deployment

# Check if the terraform.tfvars file exists
if [ ! -f "terraform.tfvars" ]; then
  echo "ERROR: The 'terraform.tfvars' file does not exist."
  echo "Please follow the instructions in gcp_deployment/README.md to create it before deploying."
  exit 1
fi

echo "Initializing Terraform..."
terraform init

echo "Applying Terraform configuration..."
terraform apply
