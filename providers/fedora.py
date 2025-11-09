
# providers/fedora.py
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
    """Fedora provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "dnf", "install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "dnf", "remove", "-y"] + packages)

    def update(self) -> bool:
        return run_cmd(["sudo", "dnf", "update", "-y"])

    def search(self, package: str) -> bool:
        return run_cmd(["dnf", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["rpm", "-qa", "--qf", "%{NAME}\n"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        return {
            "yq": "sudo dnf install yq",
            "timeshift": "sudo dnf install timeshift"
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
                "yq"
            ]
        }
