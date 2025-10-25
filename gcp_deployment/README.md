# Google Cloud Deployment with Terraform

This folder contains the complete Terraform configuration to deploy the Intelli-Docs application to a scalable, production-ready environment on Google Cloud.

It provisions the entire cloud infrastructure, including application services, storage, and security, based on Google Cloud managed services.

## Prerequisites

1.  **Google Cloud Account & Project:** You must have a Google Cloud account with a project created and billing enabled.
2.  **Terraform CLI:** Install the Terraform CLI on your local machine. [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
3.  **Google Cloud SDK (`gcloud`):** Install the `gcloud` command-line tool. [Installation Guide](https://cloud.google.com/sdk/docs/install)
4.  **MongoDB Atlas Cluster:** Create a free-tier MongoDB Atlas cluster. [Get Started Guide](https://www.mongodb.com/docs/atlas/getting-started/)
    *   After creation, ensure you configure IP Access to allow connections from anywhere (`0.0.0.0/0`) for Cloud Run to connect. For production, you would lock this down further.
    *   Get your cluster's connection string.

## Deployment Steps

### 1. Authenticate to Google Cloud

Run the following command and follow the prompts to log in to your Google account. This gives Terraform the necessary permissions.

```bash
gcloud auth application-default login
```

### 2. Configure Your Environment

1.  **Create a `terraform.tfvars` file:** This file will contain all your project-specific variables. Create a new file named `terraform.tfvars` in this directory.

2.  **Populate the file:** Copy the content below into `terraform.tfvars` and replace the placeholder values with your own.

    ```hcl
    # terraform.tfvars

    gcp_project_id      = "your-gcp-project-id" # Replace with your GCP Project ID
    gcp_region          = "us-central1"         # You can change this to your preferred region
    mongo_db_connection = "mongodb+srv://..." # Replace with your full MongoDB Atlas connection string
    flask_secret_key    = "a-very-strong-and-random-secret-key" # Replace with a real secret
    ```

### 3. Initialize & Deploy

Navigate to this `gcp_deployment` directory in your terminal and run the following commands:

1.  **Initialize Terraform:** This downloads the necessary providers.

    ```bash
    terraform init
    ```

2.  **Plan the deployment:** This shows you all the resources that will be created.

    ```bash
    terraform plan
    ```

3.  **Apply the configuration:** This will build your Docker image, push it to the Artifact Registry, and deploy all the services. Type `yes` when prompted.

    ```bash
    terraform apply
    ```

### 4. Check the Output

Once the deployment is complete, Terraform will output the public URL of your deployed Flask application.

```
Outputs:

flask_app_url = "https://your-app-name-....a.run.app"
```

You can now access your application at this URL.

### 5. Cleaning Up

When you are finished, you can destroy all the created cloud resources to avoid incurring further costs. **This action is irreversible.**

```bash
terraform destroy
```
