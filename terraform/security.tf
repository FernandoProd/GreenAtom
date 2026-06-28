# Группа безопасности для узлов кластера
resource "vkcs_networking_secgroup" "k8s" {
  name        = "${var.project_name}-k8s-sg"
  description = "Security group for Kubernetes cluster nodes"
}

# SSH доступ (по вашему IP, но для учёбы разрешим всем)
resource "vkcs_networking_secgroup_rule" "ssh_external" {
  direction         = "ingress"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.my_ip
  security_group_id = vkcs_networking_secgroup.k8s.id
}

# Порт для Kubernetes API (6443)
resource "vkcs_networking_secgroup_rule" "k8s_api" {
  direction         = "ingress"
  protocol          = "tcp"
  port_range_min    = 6443
  port_range_max    = 6443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = vkcs_networking_secgroup.k8s.id
}

# Порт для Ingress (HTTP/HTTPS)
resource "vkcs_networking_secgroup_rule" "http_https" {
  direction         = "ingress"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = vkcs_networking_secgroup.k8s.id
}

resource "vkcs_networking_secgroup_rule" "https" {
  direction         = "ingress"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = vkcs_networking_secgroup.k8s.id
}

# Внутреннее взаимодействие: TCP (все порты)
resource "vkcs_networking_secgroup_rule" "internal_tcp" {
  direction         = "ingress"
  protocol          = "tcp"
  port_range_min    = 1
  port_range_max    = 65535
  remote_ip_prefix  = "10.0.0.0/16"
  security_group_id = vkcs_networking_secgroup.k8s.id
}

# Внутреннее взаимодействие: UDP (все порты)
resource "vkcs_networking_secgroup_rule" "internal_udp" {
  direction         = "ingress"
  protocol          = "udp"
  port_range_min    = 1
  port_range_max    = 65535
  remote_ip_prefix  = "10.0.0.0/16"
  security_group_id = vkcs_networking_secgroup.k8s.id
}
