
# providers/arch.py
import subprocess
from .base_provider import BaseProvider

def run_cmd(cmd: list) -> bool:
    """Helper to run a subprocess command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Provider(BaseProvider):
    """Arch Linux provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "pacman", "-S", "--noconfirm", "--needed"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "pacman", "-Rs", "--noconfirm"] + packages)

    def update(self) -> bool:
        print("Note: 'update' uses 'paru'. Ensure it's installed.")
        return run_cmd(["paru", "-Syu", "--noconfirm"])

    def search(self, package: str) -> bool:
        print("Note: 'search' uses 'paru'. Ensure it's installed.")
        return run_cmd(["paru", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["pacman", "-Qq"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        return {
            "yq": "sudo pacman -S go-yq",
            "timeshift": "sudo pacman -S timeshift",
            "paru": "(Install from AUR)"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Arch machines",
            "packages": [
                "base",
                "linux",
                "linux-firmware",
                "networkmanager",
                "vim",
                "git",
                "go-yq"
            ]
        }
