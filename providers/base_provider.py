# providers/base_provider.py
from abc import ABC, abstractmethod

# <-- NEW: Add colors for warnings -->
YELLOW = '\033[1;33m'
NC = '\033[0m'

class BaseProvider(ABC):
    """
    Abstract base class defining the interface for all distro providers.
    """

    @abstractmethod
    def install(self, packages: list) -> bool:
        """Install a list of packages."""
        pass

    @abstractmethod
    def remove(self, packages: list) -> bool:
        """Remove a list of packages."""
        pass

    @abstractmethod
    def update(self) -> bool:
        """Update all system packages."""
        pass

    @abstractmethod
    def search(self, package: str) -> bool:
        """Search for a package."""
        pass

    @abstractmethod
    def get_installed_packages(self) -> set:
        """Return a set of all installed package names."""
        pass

    @abstractmethod
    def get_deps(self) -> dict:
        """Return a dict of dependencies { 'yq': 'install_cmd', ... }."""
        pass

    @abstractmethod
    def get_base_packages(self) -> dict:
        """Return a dict of base packages for the 'init' command."""
        pass

    # --- NEW: Optional Helper Methods ---
    # These are not abstract. Providers can override them if they support them.
    
    def _unsupported(self, feature_name: str) -> bool:
        """Default function for unsupported features."""
        print(f"{YELLOW}Warning: {feature_name} packages are declared, but this system's provider ({self.__class__.__name__}) does not support them. Skipping.{NC}")
        return False

    def install_aur(self, packages: list) -> bool: return self._unsupported("AUR")
    def install_copr(self, copr_map: dict) -> bool: return self._unsupported("COPR")
    def install_ppa(self, ppa_map: dict) -> bool: return self._unsupported("PPA")
    def install_obs(self, obs_map: dict) -> bool: return self._unsupported("OBS")
    def install_overlay(self, overlay_map: dict) -> bool: return self._unsupported("Gentoo Overlay")
    def install_src(self, packages: list) -> bool: return self._unsupported("Void Src")
