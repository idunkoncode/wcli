# providers/fedora.py
import subprocess
import re
from .base_provider import BaseProvider

# --- Add colors ---
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'

def run_cmd(cmd: list) -> bool:
    """Helper to run an interactive command."""
    try:
        # Use subprocess.run directly for output streaming
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
        
def run_cmd_capture(cmd: list) -> subprocess.CompletedProcess:
    """Helper to run a non-interactive command and capture output."""
    return subprocess.run(cmd, check=True, text=True, capture_output=True, errors='ignore')

class Provider(BaseProvider):
    """Fedora provider implementation."""

    def install(self, packages: list) -> bool:
        """Installs packages one-by-one to show progress."""
        all_ok = True
        total = len(packages)
        for i, pkg in enumerate(packages):
            # dnf install <pkg-version>
            pkg_name = pkg.replace("==", "-").replace("=", "-")
            print(f"\n--- Installing {pkg_name} ({i+1}/{total}) ---")
            if not run_cmd(["sudo", "dnf", "install", "-y", pkg_name]):
                print(f"{YELLOW}Warning: Failed to install {pkg_name}{NC}")
                all_ok = False
        return all_ok

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "dnf", "remove", "-y"] + packages)

    def update(self, ignore_list: list) -> bool:
        cmd = ["sudo", "dnf", "update", "-y"]
        if ignore_list:
            print(f"{YELLOW}Ignoring {len(ignore_list)} packages: {', '.join(ignore_list)}{NC}")
            for pkg in ignore_list:
                cmd.append(f"--exclude={pkg}")
        return run_cmd(cmd)

    def search(self, package: str) -> bool:
        return run_cmd(["dnf", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = run_cmd_capture(["rpm", "-qa", "--qf", "%{NAME}\n"])
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # --- Version Pinning Methods ---
    
    def get_package_version(self, package: str) -> str:
        try:
            # rpm -q <pkg> --qf '%{VERSION}-%{RELEASE}'
            result = run_cmd_capture(["rpm", "-q", package, "--qf", "%{VERSION}-%{RELEASE}"])
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def get_installed_packages_with_versions(self) -> dict:
        pkg_map = {}
        try:
            # rpm -qa --qf '%{NAME}\t%{VERSION}-%{RELEASE}\n'
            result = run_cmd_capture(["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"])
            for line in result.stdout.strip().split('\n'):
                if line and '\t' in line:
                    try:
                        name, version = line.split('\t')
                        pkg_map[name] = version
                    except ValueError:
                        pass
            return pkg_map
        except (subprocess.CalledProcessError, FileNotFoundError):
            return pkg_map
            
    def compare_versions(self, v1: str, v2: str) -> int:
        try:
            # Use rpmdev-vercmp if available (from rpmdevtools)
            proc = subprocess.run(["rpmdev-vercmp", v1, v2], capture_output=True, text=True)
            if proc.returncode == 11: return 1 # v1 > v2
            if proc.returncode == 12: return 2 # v1 < v2
            return 0 # v1 == v2
        except FileNotFoundError:
            # Fallback for simple string compare
            if v1 > v2: return 1
            if v1 < v2: return 2
            return 0
            
    def downgrade(self, package: str, version: str) -> bool:
        """Downgrades a package to a specific version."""
        print(f"  {BLUE}Attempting to downgrade {package} to {version}...{NC}")
        # dnf downgrade <pkg-version>
        if not run_cmd(["sudo", "dnf", "downgrade", "-y", f"{package}-{version}"]):
            print(f"  {YELLOW}Could not downgrade {package}. It may not be available in your repos.{NC}")
            print(f"  {YELLOW}Try running: sudo dnf --showduplicates list {package}{NC}")
            return False
        return True

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            result = run_cmd_capture(["dnf", "info", package])
            repo_ver = re.search(r"Version\s*:\s*(.*)", result.stdout).group(1)
            print(f"  {BLUE}Available:{NC} {repo_ver.strip()}")
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
        # 3. All versions
        print(f"  {BLUE}All available versions (run 'dnf --showduplicates list {package}'):{NC}")
        
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo dnf install yq",
            "timeshift": "sudo dnf install timeshift",
            "snapper": "sudo dnf install snapper",
            "flatpak": "sudo dnf install flatpak",
            "rpmdevtools": "sudo dnf install rpmdevtools" # For rpmdev-vercmp
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
                "flatpak",
                "rpmdevtools"
            ],
            "fedora_copr": {
                "atim/heroic-games-launcher": ["heroic-games-launcher"]
            }
        }

    def install_copr(self, copr_map: dict) -> bool:
        all_ok = True
        all_packages = []
        for repo, packages in copr_map.items():
            # Check if repo is already enabled
            repo_name = repo.replace('/', '-')
            if not Path(f"/etc/yum.repos.d/_copr_copr.fedorainfracloud.org_{repo_name}.repo").exists():
                print(f"Enabling COPR repo: {repo}")
                if not run_cmd(["sudo", "dnf", "copr", "enable", "-y", repo]):
                    print(f"{YELLOW}Warning: Failed to enable COPR repo: {repo}{NC}")
                    all_ok = False
                    continue # Skip packages from this repo
            
            all_packages.extend(packages)
        
        if all_packages:
            if not self.install(all_packages):
                all_ok = False
        return all_ok
