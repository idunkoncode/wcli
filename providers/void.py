
# providers/void.py
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
    """Void Linux provider implementation."""

    def install(self, packages: list) -> bool:
        return run_cmd(["sudo", "xbps-install", "-y"] + packages)

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "xbps-remove", "-y"] + packages)

    def update(self) -> bool:
        return run_cmd(["sudo", "xbps-install", "-Syu"])

    def search(self, package: str) -> bool:
        return run_cmd(["xbps-query", "-Rs", package])

    def get_installed_packages(self) -> set:
        try:
            result = subprocess.run(
                ["xbps-query", "-l"],
                capture_output=True, text=True, check=True, errors='ignore'
            )
            # output is 'name-version-revision'
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Split 'ii name-version-rev comment'
                    pkg_full = line.split(' ')[1]
                    # Get name from 'name-version-rev'
                    pkg_name = pkg_full.rsplit('-', 2)[0]
                    packages.add(pkg_name)
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def get_deps(self) -> dict:
        return {
            "yq": "sudo xbps-install -y yq",
            "timeshift": "sudo xbps-install -y timeshift"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Void machines",
            "packages": [
                "NetworkManager",
                "vim",
                "git",
                "yq"
            ]
        }
