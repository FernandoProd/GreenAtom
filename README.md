# GreenAtom — Microservices Ticketing App on Kubernetes (VK Cloud)

A simple microservices-based application for **IT Summer Festival 2026** registration and ticket management, deployed on a managed Kubernetes cluster in VK Cloud.

## Overview

The project demonstrates a cloud‑native microservice architecture:
- **User Service** (FastAPI) – user registration and authentication.
- **Ticket Service** (FastAPI) – ticket creation, revocation, and status checks.
- **Redis** – used as a shared cache / data store.
- **Frontend** – static HTML/CSS/JS served by a lightweight web server.

All components are containerised, pushed to Docker Hub, and orchestrated by Kubernetes.  
Infrastructure (network, subnets, security groups) is provisioned with **Terraform**.  
Horizontal Pod Autoscaler (HPA) automatically scales backend services under load.

## Architecture

![Current Architecture](docs/architecture.png)  
*(Replace with actual diagram if available)*

- **VPC:** `microservices-vpc`  
  - Public subnet `10.0.10.0/24`  
  - Private subnet `10.0.20.0/24` (optional, for further expansion)  
- **Ingress Controller (nginx)** exposed via a public IP.  
- Two Ingress resources separate API and frontend traffic.  
- Kubernetes namespace `microservices` contains all workloads.

## Prerequisites

- [Terraform](https://www.terraform.io/) ≥ 1.0
- [kubectl](https://kubernetes.io/docs/tasks/tools/) configured for the VK Cloud cluster
- [Docker](https://docs.docker.com/get-docker/) (if you want to build images yourself)
- [Docker Hub](https://hub.docker.com/) account (or any container registry)
- VK Cloud account with API access

## Infrastructure Setup (Terraform)

1. **Clone the repository**
   ```bash
   git clone https://github.com/fernandoprod/GreenAtom.git
   cd GreenAtom/terraform
2. **Configure credentials**
Edit main.tf and replace the placeholder values with your VK Cloud credentials, or set environment variables:

    ```hcl
    provider "vkcs" {
      username   = "your-email@example.com"
      password   = "your-password"
      project_id = "your-project-id"
      region     = "RegionOne"
      auth_url   = "https://msk.cloud.vk.com/infra/identity/v3/"
    }

Alternatively, use environment variables OS_USERNAME, OS_PASSWORD, OS_PROJECT_ID, OS_AUTH_URL.

3. **Initialize and apply Terraform**

    ```bash
    terraform init
    terraform apply -auto-approve
    ```
    This will create:
    - VPC microservices-vpc 
    - Public and private subnets 
    - Router and network interfaces 
    - Security group microservices-k8s-sg with required rules

## Kubernetes Cluster Setup
1. **Create a Managed Kubernetes Cluster** in VK Cloud panel:
   - Name: prod-k8s
   - Version: 1.34.2 (or latest)
   - Master node: 1 × STD3-2-8 
   - Worker group: 2 nodes × Standard-2-4, 50 GB disk 
   - Network: microservices-vpc, subnet microservices-public-subnet 
   - Enable Ingress Controller (ingress-nginx)
   - Security group: microservices-k8s-sg 
   - Assign external IP to the API server 
2. **Download kubeconfig** from the cluster page and place it at ~/.kube/config.
3. **Set up kubectl**
    ```bash
    export OS_PASSWORD='your-password'
    kubectl config use-context default/prod-k8s
    kubectl config set-cluster prod-k8s --insecure-skip-tls-verify=true
    kubectl get nodes   # both should be Ready
## Building and Pushing Docker Images (optional)
Pre‑built images are available on Docker Hub:
- `fernandoprod/user-service:latest`
- `fernandoprod/ticket-service:latest`
- `fernandoprod/frontend:latest`

If you want to build them yourself:

    ```bash
    cd GreenAtom/user_service
    docker build -t <your-repo>/user-service:latest .
    docker push <your-repo>/user-service:latest

    cd ../ticket_service
    docker build -t <your-repo>/ticket-service:latest .
    docker push <your-repo>/ticket-service:latest

    cd ../frontend_ga
    docker build -t <your-repo>/frontend:latest .
    docker push <your-repo>/frontend:latest
  
Then update the image names in k8s/*-deployment.yaml files accordingly.

## Deploying to Kubernetes
1. Apply all Kubernetes manifests

    ```bash
    cd GreenAtom/k8s
    kubectl apply -f .
   
This creates namespace microservices and all resources (Deployments, Services, Ingress, HPA).

2. Check that pods are running

    ```bash
    kubectl get pods -n microservices
    Wait until all pods are in Running state.

3. Check Ingress and external IP
    ```bash
    kubectl get ingress -n microservices
   
You will see an address like 89.208.208.36.nip.io.

## Accessing the Application
Open your browser and navigate to http://<INGRESS-ADDRESS> (e.g., `http://89.208.208.36.nip.io`).

- Frontend will load – you can register, login, obtain and revoke tickets.
- API health checks:
    ```bash
    curl http://<INGRESS-ADDRESS>/api/users/health
    curl http://<INGRESS-ADDRESS>/api/tickets/health
  
## Horizontal Pod Autoscaling (HPA)
The project includes HPA for both backend services. To see it in action:

1. Install hey (load generator)
    ```bash
    sudo apt install hey   # or download from https://github.com/rakyll/hey

2. Generate load
    ```bash
    hey -z 60s -c 20 http://<INGRESS-ADDRESS>/api/users/health
3. Watch scaling
    ```bash
    kubectl get pods -n microservices -w
    # Or monitor HPA directly
    kubectl get hpa -n microservices -w
   
You should see the number of user-service pods increase (from 2 up to 5) during the test, then scale back down after a few minutes.

### Cleanup
To avoid unnecessary charges, delete all resources:

    ```bash
    # Delete Kubernetes resources
    kubectl delete namespace microservices
    kubectl delete namespace kubernetes-dashboard   # if installed
    
    # Destroy Terraform-managed infrastructure
    cd GreenAtom/terraform
    terraform destroy -auto-approve
    
    # Delete the Kubernetes cluster via VK Cloud panel (optional)```
## Project Structure
    ```text
    GreenAtom/
    ├── terraform/                 # Infrastructure as Code
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── network.tf
    │   ├── security.tf
    │   └── outputs.tf
    ├── k8s/                       # Kubernetes manifests
    │   ├── namespace.yaml
    │   ├── redis-deployment.yaml
    │   ├── redis-service.yaml
    │   ├── user-service-deployment.yaml
    │   ├── user-service-service.yaml
    │   ├── ticket-service-deployment.yaml
    │   ├── ticket-service-service.yaml
    │   ├── frontend-deployment.yaml
    │   ├── frontend-service.yaml
    │   ├── api-ingress.yaml
    │   ├── frontend-ingress.yaml
    │   └── hpa.yaml
    ├── user_service/              # User Service (FastAPI)
    │   ├── main.py
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── ...
    ├── ticket_service/            # Ticket Service (FastAPI)
    │   ├── main.py
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── ...
    ├── frontend_ga/               # Static Frontend
    │   ├── index.html
    │   ├── style.css
    │   ├── script.js
    │   ├── Dockerfile
    │   └── ...
    └── .gitignore

## Technologies Used
- Cloud: VK Cloud (OpenStack‑based)
- Infrastructure as Code: Terraform (VK Cloud provider)
- Containerisation: Docker, Docker Hub
- Orchestration: Kubernetes (Managed K8s)
- Backend: Python, FastAPI, Redis
- Frontend: HTML5, CSS3, JavaScript (vanilla)
- Scaling: Kubernetes HPA (CPU‑based)
- Ingress: NGINX Ingress Controller

## License
This project is created for educational purposes as part of the VK Cloud administration course.