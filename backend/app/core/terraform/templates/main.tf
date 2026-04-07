terraform {
    required_providers {
        yandex = {
            source = "yandex-cloud/yandex"
        }
    }
}

provider "yandex" {
    zone = var.zone
}

data "yandex_vpc_subnet" "existing" {
    subnet_id = var.subnet_id
}

data "yandex_compute_image" "os" {
    family = var.os_family
}

resource "yandex_compute_instance" "vm" {
    name        = var.server_name
    zone        = var.zone
    platform_id = "standard-v3"

    resources {
        cores         = var.cores                       # 2
        memory        = var.memory                      # 4
        core_fraction = var.core_fraction               # 50
    }

    boot_disk {
        initialize_params {
            image_id = data.yandex_compute_image.os.id
            size     = var.disk_size
            type     = "network-ssd"
        }
    }

    network_interface {
        subnet_id = data.yandex_vpc_subnet.existing.id
        nat       = true                                # turn on public IP
    }

    metadate {
        ssh-keys = "ubuntu:${var.ssh_public_key}"
    }
}