# VPC
resource "vkcs_networking_network" "main" {
  name = "${var.project_name}-vpc"
}

# Публичная подсеть
resource "vkcs_networking_subnet" "public" {
  name        = "${var.project_name}-public-subnet"
  network_id  = vkcs_networking_network.main.id
  cidr        = "10.0.10.0/24"        
  enable_dhcp = true
  allocation_pool {
    start = "10.0.10.10"
    end   = "10.0.10.200"
  }
}

# Приватная подсеть (опционально, для узлов кластера)
resource "vkcs_networking_subnet" "private" {
  name        = "${var.project_name}-private-subnet"
  network_id  = vkcs_networking_network.main.id
  cidr        = "10.0.20.0/24"
  enable_dhcp = true
}

# Роутер с выходом в интернет
resource "vkcs_networking_router" "router" {
  name                = "${var.project_name}-router"
  admin_state_up      = true
  external_network_id = data.vkcs_networking_network.external.id
}

data "vkcs_networking_network" "external" {
  name = "internet"
}

# Подключение публичной подсети к роутеру
resource "vkcs_networking_router_interface" "public" {
  router_id = vkcs_networking_router.router.id
  subnet_id = vkcs_networking_subnet.public.id
}

# Подключение приватной подсети к роутеру (чтобы узлы могли выходить в интернет)
resource "vkcs_networking_router_interface" "private" {
  router_id = vkcs_networking_router.router.id
  subnet_id = vkcs_networking_subnet.private.id
}
