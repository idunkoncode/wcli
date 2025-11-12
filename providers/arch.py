# providers/arch.py
import subprocess
import shutil
import re
from pathlib import Path
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
    """Arch Linux provider implementation."""

    def __init__(self):
        self.helper_cmd = None
        if shutil.which("paru"):
            self.helper_cmd = "paru"
        elif shutil.which("yay"):
            self.helper_cmd = "yay"
        else:
            print(f"{YELLOW}Warning: No AUR helper (paru, yay) found. 'arch_aur' packages will be skipped.{NC}")
        
        # Check for vercmp
        if not shutil.which("vercmp"):
             print(f"{RED}Error: 'vercmp' (from pacman-contrib) is required for version comparison.{NC}")
             print("Please install 'pacman-contrib'")
             # This is a critical error, but we'll let it fail later
             self.can_compare = False
        else:
             self.can_compare = True

    def install(self, packages: list) -> bool:
        """
        Installs packages one-by-one to show progress.
        Uses helper if any package contains a version string.
        """
        total = len(packages)
        all_ok = True
        
        # Packages with '=' need an AUR helper
        aur_pkgs = [p for p in packages if "=" in p]
        pacman_pkgs = [p for p in packages if "=" not in p]

        if pacman_pkgs:
            print(f"{BLUE}Installing {len(pacman_pkgs)} official packages...{NC}")
            if not run_cmd(["sudo", "pacman", "-S", "--noconfirm", "--needed"] + pacman_pkgs):
                all_ok = False # Don't stop, just report

        if aur_pkgs:
            if not self.helper_cmd:
                print(f"{RED}Error: Cannot install versioned packages '{', '.join(aur_pkgs)}' without an AUR helper.{NC}")
                return False
                
            print(f"{BLUE}Installing {len(aur_pkgs)} versioned packages using {self.helper_cmd}...{NC}")
            if not run_cmd([self.helper_cmd, "-S", "--noconfirm", "--needed"] + aur_pkgs):
                all_ok = False

        return all_ok

    def remove(self, packages: list) -> bool:
        return run_cmd(["sudo", "pacman", "-Rs", "--noconfirm"] + packages)

    def update(self, ignore_list: list) -> bool:
        if not self.helper_cmd:
            print(f"{RED}Error: No AUR helper found. Cannot update.{NC}")
            return False
            
        cmd = [self.helper_cmd, "-Syu", "--noconfirm"]
        if ignore_list:
            print(f"{YELLOW}Ignoring {len(ignore_list)} packages: {', '.join(ignore_list)}{NC}")
            for pkg in ignore_list:
                cmd.extend(["--ignore", pkg])
        
        return run_cmd(cmd)

    def search(self, package: str) -> bool:
        if self.helper_cmd:
            return run_cmd([self.helper_cmd, "-Ss", package])
        else:
            return run_cmd(["pacman", "-Ss", package])

    def get_installed_packages(self) -> set:
        try:
            result = run_cmd_capture(["pacman", "-Qq"])
            return set(result.stdout.strip().split('\n'))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    # --- NEW: Version Pinning Methods ---
    
    def get_package_version(self, package: str) -> str:
        try:
            result = run_cmd_capture(["pacman", "-Q", package])
            return result.stdout.strip().split(' ')[1]
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            return ""
            
    def get_installed_packages_with_versions(self) -> dict:
        pkg_map = {}
        try:
            result = run_cmd_capture(["pacman", "-Q"])
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        name, version = line.split(' ')
                        pkg_map[name] = version
                    except ValueError:
                        pass # Ignore malformed lines
            return pkg_map
        except (subprocess.CalledProcessError, FileNotFoundError):
            return pkg_map

    def compare_versions(self, v1: str, v2: str) -> int:
        if not self.can_compare: return 0 # Failsafe
        try:
            proc = subprocess.run(["vercmp", v1, v2], capture_output=True, text=True)
            result = proc.returncode
            if result == 1: return 1 # v1 > v2
            if result == 2: return 2 # v1 < v2
            return 0 # v1 == v2
        except FileNotFoundError:
            return 0 # Should not happen if __init__ check passed

    def _find_pkg_file(self, package: str, version: str) -> str:
        """Finds a package file in cache or Arch Linux Archive."""
        arch = os.uname().m_machine
        pkg_file_name = f"{package}-{version}-{arch}.pkg.tar.zst"
        
        # 1. Check local cache
        cache_path = Path(f"/var/cache/pacman/pkg/{pkg_file_name}")
        if cache_path.exists():
            print(f"  {GREEN}✓ Found in pacman cache{NC}")
            return str(cache_path)
            
        # 2. Check Arch Linux Archive
        print(f"  {BLUE}Checking Arch Linux Archive (ALA)...{NC}")
        archive_url = f"https://archive.archlinux.org/packages/{package[0]}/{package}/{pkg_file_name}"
        
        try:
            # Use curl -sfI to check if header is valid (file exists)
            run_cmd_capture(["curl", "-sfI", archive_url])
            print(f"  {GREEN}✓ Found in ALA. Will download from URL.{NC}")
            return archive_url
        except subprocess.CalledProcessError:
            print(f"  {RED}✗ Not found in ALA.{NC}")
            return ""

    def downgrade(self, package: str, version: str) -> bool:
        pkg_file = self._find_pkg_file(package, version)
        if not pkg_file:
            print(f"  {RED}Error: Cannot find package file for {package}-{version}.{NC}")
            return False
        
        # Use pacman -U to install the specific file
        return run_cmd(["sudo", "pacman", "-U", "--noconfirm", pkg_file])

    def show_package_versions(self, package: str):
        # 2. Repo version
        try:
            helper = self.helper_cmd or "pacman"
            result = run_cmd_capture([helper, "-Si", package])
            repo_ver = re.search(r"Version\s*:\s*(.*)", result.stdout).group(1)
            print(f"  {BLUE}Available:{NC} {repo_ver.strip()}")
        except (subprocess.CalledProcessError, AttributeError):
            print(f"  {YELLOW}Not found in repositories{NC}")
            
        # 3. Cached versions
        print(f"  {BLUE}In Cache:{NC}")
        found = False
        cache_dir = Path("/var/cache/pacman/pkg")
        if cache_dir.exists():
            for f in cache_dir.glob(f"{package}-*.pkg.tar.zst"):
                print(f"    - {f.name}")
                found = True
        if not found:
            print("    (none)")
            
    # --- End of Versioning Methods ---

    def get_deps(self) -> dict:
        return {
            "yq": "sudo pacman -S go-yq",
            "timeshift": "sudo pacman -S timeshift",
            "snapper": "sudo pacman -S snapper",
            "flatpak": "sudo pacman -S flatpak",
            "pacman-contrib": "sudo pacman -S pacman-contrib", # For vercmp
            "paru": "(Install 'paru' or 'yay' from the AUR)"
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
                "go-yq",
                "timeshift",
                "flatpak",
                "pacman-contrib" # For vercmp
            ],
            "arch_aur": [
                "paru" 
            ]
        }

    def install_aur(self, packages: list) -> bool:
        if not self.helper_cmd:
            print(f"{RED}Error: No AUR helper found. Cannot install packages.{NC}")
            return False
        
        print(f"{BLUE}Using '{self.helper_cmd}' to install {len(packages)} AUR packages...{NC}")
        # Install one by one to show progress
        all_ok = True
        for i, pkg in enumerate(packages):
            print(f"\n--- Installing AUR Pkg {pkg} ({i+1}/{len(packages)}) ---")
            if not run_cmd([self.helper_cmd, "-S", "--noconfirm", "--needed", pkg]):
                print(f"{YELLOW}Warning: Failed to install {pkg}{NC}")
                all_ok = False
        return all_ok
