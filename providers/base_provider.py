
# providers/base_provider.py
from abc import ABC, abstractmethod

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
