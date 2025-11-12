# providers/gentoo.py
import subprocess
import shutil
import re
from .base_provider import BaseProvider

YELLOW = '\033[1;33m'
NC = '\033[0m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
GREEN = '\033[0;32m'

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
    """Gentoo provider implementation."""

    def __init__(self):
        if not shutil.which("eselect"):
            print(f"{YELLOW}Warning: 'eselect' not found. Overlays will not work.{NC}")
            print("Please install 'app-eselect/eselect-repository'.")
            self.can_add_overlay = False
        else:
            self.can_add_overlay = True
        
        if not shutil.which("qlist"):
            print(f"{RED}Error: 'qlist' not found. This provider cannot function.{NC}")
            print("Please install 'app-portage/portage-utils'.")
            self.can_list = False
        else:
            self.can_list = True

    def install(self, packages: list) -> bool:
        """Installs packages one-by-one to show progress."""
        all_ok = True
        total = len(packages)
        for i, pkg in enumerate(packages):
            # Emerge can take version strings like '=app-misc/yq-4.0'
            pkg_name = pkg.replace("=", "==") if "=" in pkg else pkg
            print(f"\n--- Installing {pkg_name} ({i+1}/{total}) ---")
            if not run_cmd(["sudo", "emerge", "--noreplace", "--verbose", f"={pkg_name}" if "==" in pkg_name else pkg_name]):
                print(f"{YELLOW}Warning: Failed to install {pkg_name}{NC}")
                all_ok = False
        return all_ok

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "emerge", "-C", "--verbose"] + packages)

    def update(self, ignore_list: list) -> bool:
        # This is complex. We'd have to add to /etc/portage/package.mask
        if ignore_list:
            print(f"{YELLOW}Ignoring packages in emerge is manual.{NC}")
            print(f"Please add the following to /etc/portage/package.mask to prevent updates:")
            for pkg in ignore_list:
                print(f"  >={pkg}")
        
        run_cmd(["sudo", "emerge", "--sync"])
        return run_cmd(["sudo", "emerge", "-auDN", "@world"])

    def search(self, package: str) -> bool:
        return run_cmd(["emerge", "-s", package])

    def get_installed_packages(self) -> set:
        if not self.can_list: return set()
        try:
            result = run_cmd_capture(["qlist", "-I"])
            packages = set()
            for line in result.stdout.strip().split('\n'):
                if '/' in line:
                    packages.add(line.split('/')[-1])
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # --- NEW: Version Pinning Methods ---
    
    def get_package_version(self, package: str) -> str:
        if not self.can_list: return ""
        try:
            # qlist -I <pkg> | awk '{print $1}' | cut -d'/' -f2
            result = run_cmd_capture(["qlist", "-I", package])
            # First line is what we want
            first_line = result.stdout.strip().split('\n')[0]
            return first_line.split('/')[-1].split('-')[-1] # Simplistic
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            return ""

    def get_installed_packages_with_versions(self) -> dict:
        if not self.can_list: return {}
        pkg_map = {}
        try:
            result = run_cmd_capture(["qlist", "-I"])
            for line in result.stdout.strip().split('\n'):
                if '/' in line:
                    try:
                        full_name = line.split(' ')[0]
                        name = full_name.split('/')[-1]
                        version = name.split('-')[-1]
                        name_no_ver = name.rsplit('-', 1)[0]
                        pkg_map[name_no_ver] = version
                    except ValueError:
                        pass
            return pkg_map
        except (subprocess.CalledProcessError, FileNotFoundError):
            return pkg_map
            
    def compare_versions(self, v1: str, v2: str) -> int:
        # Use Python's packaging library if available, otherwise string compare
        try:
            from packaging import version
            v1_p = version.parse(v1)
            v2_p = version.parse(v2)
            if v1_p > v2_p: return 1
            if v1_p < v2_p: return 2
            return 0
        except ImportError:
            if v1 > v2: return 1
            if v1 < v2: return 2
            return 0
            
    def downgrade(self, package: str, version: str) -> bool:
        """Downgrading on Gentoo is not simple."""
        print(f"  {YELLOW}Downgrading on Gentoo is a manual process.{NC}")
        print(f"  Please unmerge '{package}' and emerge '={package}-{version}'")
        return False

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            result = run_cmd_capture(["emerge", "-s", package])
            # Emerge search is very verbose... find first match
            for line in result.stdout.split('\n'):
                if package in line:
                    print(f"  {BLUE}Available:{NC} {line.strip()}")
                    break
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
        
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo emerge app-misc/yq",
            "timeshift": "sudo emerge app-backup/timeshift",
            "snapper": "sudo emerge sys-fs/snapper",
            "flatpak": "sudo emerge sys-apps/flatpak",
            "portage-utils": "sudo emerge app-portage/portage-utils",
            "eselect-repository": "sudo emerge app-eselect/eselect-repository"
        }

    def get_base_packages(self) -> dict:
        return {
            "description": "Base packages for all Gentoo machines",
            "packages": [
                "app-portage/portage-utils", 
                "app-eselect/eselect-repository", 
                "app-misc/yq",
                "net-misc/networkmanager",
                "app-editors/vim",
                "dev-vcs/git",
                "sys-fs/snapper",
                "sys-apps/flatpak"
            ],
            "gentoo_overlay": {
                "guru": []
            }
        }

    def install_overlay(self, overlay_map: dict) -> bool:
        if not self.can_add_overlay:
            print("Error: 'eselect repository' is not available. Cannot add overlays.")
            return False

        all_ok = True
        all_packages = []
        needs_sync = False
        
        try:
            result = run_cmd_capture(["eselect", "repository", "list", "-i"])
            enabled_repos = result.stdout
        except Exception:
            enabled_repos = ""

        for overlay, packages in overlay_map.items():
            if overlay not in enabled_repos:
                print(f"Adding Gentoo overlay: {overlay}")
                if not run_cmd(["sudo", "eselect", "repository", "add", overlay, "git"]):
                    print(f"Warning: Failed to add overlay: {overlay}")
                    all_ok = False
                else:
                    needs_sync = True
            
            all_packages.extend(packages)
        
        if needs_sync:
            print("Running 'emerge --sync' after adding overlays...")
            if not run_cmd(["sudo", "emerge", "--sync"]):
                print("Error: 'emerge --sync' failed.")
                return False
        
        if all_packages:
            if not self.install(all_packages):
                all_ok = False
        return all_ok
