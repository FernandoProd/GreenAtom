terraform {
  required_providers {
    vkcs = {
      source  = "vk-cs/vkcs"
      version = "< 1.0.0"
    }
  }
  backend "local" {}
}

provider "vkcs" {
  username   = "EMAIL"
  password   = "PASSWORD"
  project_id = "PROJECT ID"
  region     = "RegionOne"
  auth_url   = "https://msk.cloud.vk.com/infra/identity/v3/"
}
