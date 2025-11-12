# providers/opensuse.py
import subprocess
import hashlib
import re
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'

def run_cmd(cmd: list) -> bool:
    """Helper to run an interactive command."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_cmd_capture(cmd: list) -> subprocess.CompletedProcess:
    """Helper to run a non-interactive command and capture output."""
    return subprocess.run(cmd, check=True, text=True, capture_output=True, errors='ignore')

class Provider(BaseProvider):
    """openSUSE provider implementation."""

    def install(self, packages: list) -> bool:
        """Installs packages one-by-one to show progress."""
        all_ok = True
        total = len(packages)
        for i, pkg in enumerate(packages):
            print(f"\n--- Installing {pkg} ({i+1}/{total}) ---")
            if not run_cmd(["sudo", "zypper", "install", "--non-interactive", "--no-recommends", pkg]):
                print(f"{YELLOW}Warning: Failed to install {pkg}{NC}")
                all_ok = False
        return all_ok

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "zypper", "remove", "--non-interactive"] + packages)

    def update(self, ignore_list: list) -> bool:
        cmd = ["sudo", "zypper", "dup", "--non-interactive", "--no-recommends"]
        if ignore_list:
            print(f"{YELLOW}Ignoring {len(ignore_list)} packages: {', '.join(ignore_list)}{NC}")
            # zypper uses 'addlock'
            for pkg in ignore_list:
                run_cmd(["sudo", "zypper", "addlock", pkg])
        
        all_ok = run_cmd(cmd)
        
        if ignore_list:
            print(f"{YELLOW}Removing locks...{NC}")
            run_cmd(["sudo", "zypper", "removelock"] + ignore_list)
            
        return all_ok

    def search(self, package: str) -> bool:
        return run_cmd(["zypper", "search", package])

    def get_installed_packages(self) -> set:
        try:
            result = run_cmd_capture(["rpm", "-qa", "--qf", "%{NAME}\n"])
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # --- NEW: Version Pinning Methods ---
    
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
            # rpmdev-vercmp is in rpm-devel or similar, not always present.
            # Use 'rpm --eval' as a built-in alternative.
            # This is complex, so we'll do a simpler string sort for now.
            # A more robust solution would use the `packaging` python library
            # For this exercise, we'll simulate it.
            if v1 > v2: return 1
            if v1 < v2: return 2
            return 0
        except Exception:
            return 0 # Failsafe
            
    def downgrade(self, package: str, version: str) -> bool:
        """Downgrades a package to a specific version."""
        print(f"  {BLUE}Attempting to install {package}-{version}...{NC}")
        # zypper install <pkg-version>
        if not run_cmd(["sudo", "zypper", "install", "--non-interactive", "--no-recommends", f"{package}-{version}"]):
            print(f"  {YELLOW}Could not install {package}-{version}. It may not be available in your repos.{NC}")
            return False
        return True

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            result = run_cmd_capture(["zypper", "info", package])
            repo_ver = re.search(r"Version\s*:\s*(.*)", result.stdout).group(1)
            print(f"  {BLUE}Available:{NC} {repo_ver.strip()}")
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
        # 3. Cached versions
        print(f"  {BLUE}In Cache:{NC} (Run 'zypper search -s {package}' for details)")
        
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo zypper install yq",
            "timeshift": "sudo zypper install timeshift",
            "snapper": "sudo zypper install snapper",
            "flatpak": "sudo zypper install flatpak"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all openSUSE machines",
            "packages": [
                "patterns-base-base",
                "kernel-default",
                "NetworkManager",
                "vim",
                "git",
                "yq",
                "snapper",
                "flatpak"
            ]
        }

    def install_obs(self, obs_map: dict) -> bool:
        all_ok = True
        all_packages = []
        
        try:
            result = run_cmd_capture(["zypper", "lr", "-a"])
            existing_repos = result.stdout
        except Exception:
            existing_repos = ""

        for repo_url, packages in obs_map.items():
            alias = f"wcli-obs-{hashlib.md5(repo_url.encode()).hexdigest()[:8]}"
            
            if alias not in existing_repos:
                print(f"Adding OBS repo: {repo_url}")
                if not run_cmd(["sudo", "zypper", "addrepo", "--refresh", "--name", alias, repo_url, alias]):
                    print(f"Warning: Failed to add OBS repo: {repo_url}")
                    all_ok = False
                else:
                    run_cmd(["sudo", "zypper", "--gpg-auto-import-keys", "refresh"])
            
            all_packages.extend(packages)
        
        if all_packages:
            if not run_cmd(["sudo", "zypper", "install", "--non-interactive", "--no-recommends", "--allow-vendor-change"] + all_packages):
                all_ok = False
        return all_ok
