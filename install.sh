Here is the `install.sh` script, converted to install `fcli` on Fedora.

All references to `dcli` have been changed to `fcli`, and the dependency checks now point to `dnf` instead of `pacman`. The `paru` dependency, which is not relevant to Fedora, has been removed.

-----

### `install.sh` (for Fedora/fcli)

```bash
#!/usr/bin/env bash
# fcli installation script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="fcli"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  fcli Installation Script              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Error: Do not run this script as root${NC}" >&2
  echo "Run as a regular user. The script will use sudo when needed." >&2
  exit 1
fi

# Check if fcli script exists
if [ ! -f "$SCRIPT_DIR/$SCRIPT_NAME" ]; then
  echo -e "${RED}Error: fcli script not found in $SCRIPT_DIR${NC}" >&2
  exit 1
fi

# Check if fcli is already installed
if [ -f "$INSTALL_DIR/$SCRIPT_NAME" ]; then
  echo -e "${YELLOW}Warning: fcli is already installed at $INSTALL_DIR/$SCRIPT_NAME${NC}"
  read -p "Do you want to reinstall? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled${NC}"
    exit 0
  fi
fi

# Install fcli
echo -e "${BLUE}Installing fcli to $INSTALL_DIR...${NC}"
if sudo cp "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"; then
  echo -e "${GREEN}✓${NC} Copied fcli to $INSTALL_DIR"
else
  echo -e "${RED}Error: Failed to copy fcli${NC}" >&2
  exit 1
fi

# Make executable
if sudo chmod +x "$INSTALL_DIR/$SCRIPT_NAME"; then
  echo -e "${GREEN}✓${NC} Set executable permissions"
else
  echo -e "${RED}Error: Failed to set permissions${NC}" >&2
  exit 1
fi

# Verify installation
if command -v fcli &> /dev/null; then
  echo -e "${GREEN}✓${NC} fcli is now available in PATH"
else
  echo -e "${RED}Error: fcli not found in PATH after installation${NC}" >&2
  echo "You may need to restart your terminal or run: hash -r" >&2
  exit 1
fi

# Check for dependencies
echo ""
echo -e "${BLUE}Checking dependencies...${NC}"

dependencies=("yq" "timeshift")
missing_deps=()

for dep in "${dependencies[@]}"; do
  if command -v "$dep" &> /dev/null; then
    echo -e "${GREEN}✓${NC} $dep installed"
  else
    echo -e "${YELLOW}⚠${NC} $dep not installed (required for some features)"
    missing_deps+=("$dep")
  fi
done

if [ ${#missing_deps[@]} -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}Missing dependencies:${NC}"
  for dep in "${missing_deps[@]}"; do
    case $dep in
      yq)
        echo "  • yq - Required for YAML parsing"
        echo "    Install with: sudo dnf install yq"
        ;;
      timeshift)
        echo "  • timeshift - System backup (optional, for fcli backup commands)"
        echo "    Install with: sudo dnf install timeshift"
        ;;
    esac
  done
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  First computer?"
echo "    1. Run: fcli init"
echo "    2. Run: fcli repo init (to set up git)"
echo ""
echo "  Additional computer?"
echo "    • Run: fcli repo clone"
echo ""
echo "Run 'fcli help' to see all available commands"
```
