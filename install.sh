#!/usr/bin/env bash
# sys-sync installation script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="sys-sync"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  sys-sync Installation Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}Error: Do not run this script as root${NC}" >&2
  echo "Run as a regular user. The script will use sudo when needed." >&2
  exit 1
fi

# Check if sys-sync script exists
if [ ! -f "$SCRIPT_DIR/$SCRIPT_NAME" ]; then
  echo -e "${RED}Error: ${SCRIPT_NAME} script not found in $SCRIPT_DIR${NC}" >&2
  echo "Make sure this installer is in the same directory as the 'sys-sync' script." >&2
  exit 1
fi

# Check if sys-sync is already installed
if [ -f "$INSTALL_DIR/$SCRIPT_NAME" ]; then
  echo -e "${YELLOW}Warning: ${SCRIPT_NAME} is already installed at $INSTALL_DIR/$SCRIPT_NAME${NC}"
  read -p "Do you want to reinstall? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled${NC}"
    exit 0
  fi
fi

# Install sys-sync
echo -e "${BLUE}Installing ${SCRIPT_NAME} to $INSTALL_DIR...${NC}"
if sudo cp "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"; then
  echo -e "${GREEN}✓${NC} Copied ${SCRIPT_NAME} to $INSTALL_DIR"
else
  echo -e "${RED}Error: Failed to copy ${SCRIPT_NAME}${NC}" >&2
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
if command -v $SCRIPT_NAME &> /dev/null; then
  echo -e "${GREEN}✓${NC} ${SCRIPT_NAME} is now available in PATH"
else
  echo -e "${RED}Error: ${SCRIPT_NAME} not found in PATH after installation${NC}" >&2
  echo "You may need to restart your terminal or run: hash -r" >&2
  exit 1
fi

# ============================================================================
# CHECK DEPENDENCIES
# ============================================================================

echo ""
echo -e "${BLUE}Checking dependencies...${NC}"

# Get distro-specific install commands
DEP_YQ_INSTALL=""
DEP_TS_INSTALL=""
DEP_PARU_NOTE=false

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID=$ID
    [ -z "$DISTRO_ID" ] && [ -n "$ID_LIKE" ] && DISTRO_ID=$ID_LIKE
fi

case $DISTRO_ID in
    fedora)
        DEP_YQ_INSTALL="sudo dnf install yq"
        DEP_TS_INSTALL="sudo dnf install timeshift"
        ;;
    arch)
        DEP_YQ_INSTALL="sudo pacman -S go-yq"
        DEP_TS_INSTALL="sudo pacman -S timeshift"
        DEP_PARU_NOTE=true
        ;;
    debian|ubuntu|pop)
        DEP_YQ_INSTALL="sudo apt install yq"
        DEP_TS_INSTALL="sudo apt install timeshift"
        ;;
    *)
        echo -e "${YELLOW}Warning: Could not detect distro for dependency check.${NC}"
        ;;
esac

# Check for dependencies
missing_deps=()
if ! command -v yq &> /dev/null; then
  missing_deps+=("yq")
fi
if ! command -v timeshift &> /dev/null; then
  missing_deps+=("timeshift")
fi

if [ ${#missing_deps[@]} -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}Missing dependencies:${NC}"
  for dep in "${missing_deps[@]}"; do
    case $dep in
      yq)
        echo "  • yq - (REQUIRED) Required for all operations"
        [ -n "$DEP_YQ_INSTALL" ] && echo "    Install with: ${DEP_YQ_INSTALL}"
        ;;
      timeshift)
        echo "  • timeshift - (Optional) Required for 'sys-sync backup' commands"
        [ -n "$DEP_TS_INSTALL" ] && echo "    Install with: ${DEP_TS_INSTALL}"
        ;;
    esac
  done
fi

if [ "$DEP_PARU_NOTE" = true ] && ! command -v paru &> /dev/null; then
  echo ""
  echo -e "${YELLOW}Optional recommendation for Arch:${NC}"
  echo "  • paru - (Optional) For 'sys-sync update' and search."
  echo "    Install from: https://github.com/morganamilo/paru"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  First computer?"
echo "    1. Run: sys-sync init"
echo "    2. Run: sys-sync repo init (to set up git)"
echo ""
echo "  Additional computer?"
echo "    • Run: sys-sync repo clone"
echo ""
echo "Run 'sys-sync help' to see all available commands"
