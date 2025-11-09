def get_deps(self) -> dict:
        return {
            "yq": "sudo dnf install yq",
            "timeshift": "sudo dnf install timeshift",
            "snapper": "sudo dnf install snapper",
            "flatpak": "sudo dnf install flatpak"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Fedora machines",
            "packages": [
                "@core",
                "kernel",
                "linux-firmware",
                "NetworkManager",
                "vim-enhanced",
                "git",
                "yq",
                "snapper",
                "flatpak"
            ],
            "fedora_copr": {
                "atim/heroic-games-launcher": ["heroic-games-launcher"]
            }
        }
