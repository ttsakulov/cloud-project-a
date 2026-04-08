variable "server_name" {
  type = string
}

variable "zone" {
  type    = string
  default = "ru-central1-d"
}

variable "folder_id" {
  type = string
}

variable "token" {
  type = string
  sensitive = true
}

variable "subnet_id" {
  type = string
}

variable "os_family" {
  type    = string
  default = "ubuntu-2204-lts"
}

variable "cores" {
  type    = number
  default = 2
}

variable "memory" {
  type    = number
  default = 4
}

variable "core_fraction" {
  type    = number
  default = 50
}

variable "disk_size" {
  type    = number
  default = 20
}

variable "ssh_public_key" {
  type = string
}