#!/usr/bin/env bash
# wcli Python version installation script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Install location
# We put the package in /usr/local/lib/ and symlink the executable
INSTALL_DIR="/usr/local/lib/wcli"
BIN_DIR="/usr/local/bin"
SCRIPT_NAME="wcli"
PACKAGE_NAME="providers"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  wcli (Python) Installation Script     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Error: Do not run this script as root${NC}" >&2
  echo "Run as a regular user. The script will use sudo when needed." >&2
  exit 1
fi

# Check if files exist
if [ ! -f "$SCRIPT_DIR/$SCRIPT_NAME" ]; then
  echo -e "${RED}Error: ${SCRIPT_NAME} script not found in $SCRIPT_DIR${NC}" >&2
  exit 1
fi
if [ ! -d "$SCRIPT_DIR/$PACKAGE_NAME" ]; then
  echo -e "${RED}Error: ${PACKAGE_NAME}/ directory not found in $SCRIPT_DIR${NC}" >&2
  exit 1
fi

# Check for Python 3 and PyYAML
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed. Please install it first.${NC}" >&2
    exit 1
fi
if ! python3 -c "import yaml" &> /dev/null; then
    echo -e "${YELLOW}Warning: PyYAML (python3-yaml) not found.${NC}"
    echo "This is required. Please install it."
    echo "e.g., sudo apt install python3-yaml OR sudo dnf install python3-pyyaml"
    read -p "Continue installation anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${YELLOW}Installation cancelled${NC}"
      exit 0
    fi
fi

# Install/reinstall
echo -e "${BLUE}Installing files to $INSTALL_DIR...${NC}"
sudo mkdir -p "$INSTALL_DIR"
sudo cp "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"
sudo cp -r "$SCRIPT_DIR/$PACKAGE_NAME" "$INSTALL_DIR/"

# Set permissions
sudo chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Create symlink
echo -e "${BLUE}Creating symlink in $BIN_DIR...${NC}"
sudo ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "$BIN_DIR/$SCRIPT_NAME"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Run 'wcli help' to see all available commands"
