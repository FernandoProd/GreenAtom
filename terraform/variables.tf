variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "microservices"
}

variable "my_ip" {
  description = "Your public IP for SSH access"
  type        = string
  sensitive   = true
  default     = "0.0.0.0/0"          
}
