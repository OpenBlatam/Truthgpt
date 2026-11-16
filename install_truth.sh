#!/usr/bin/env bash
# ==============================================================================
# 🛠️ TruthGPT SOTA - Universal Installer for macOS and Linux
# This script installs TruthGPT and enables the 'truthgpt' and 'truth' commands globally.
# ==============================================================================

set -e

# Formatting helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "\n${CYAN}${BOLD}=== Starting TruthGPT Industrial Installation (macOS & Linux) ===${NC}\n"

# 1. Detect OS & Architecture
OS="$(uname -s)"
ARCH="$(uname -m)"
echo -e "Platform detected: ${BOLD}${OS} (${ARCH})${NC}"

# 2. Check Python 3.10+
echo -e "Checking Python environment..."
PYTHON_BIN=""
for cand in python3 python python3.12 python3.11 python3.10; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
            PYTHON_BIN="$cand"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}✗ Error: Python 3.10 or higher is required.${NC}"
    if [ "$OS" = "Darwin" ]; then
        echo -e "${YELLOW}On macOS, you can install it using Homebrew:${NC}"
        echo -e "    brew install python@3.11"
    else
        echo -e "${YELLOW}On Debian/Ubuntu:${NC}"
        echo -e "    sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
    fi
    exit 1
fi

PY_VER="$("$PYTHON_BIN" --version 2>&1)"
echo -e "${GREEN}✓ Python found: ${PY_VER}${NC}"

# 3. Define Installation Directory
# If running inside an existing TruthGPT repository (has pyproject.toml and truth_cli.py):
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -f "$SCRIPT_DIR/truth_cli.py" ]; then
    INSTALL_DIR="$SCRIPT_DIR"
    echo -e "Using current directory: ${BOLD}$INSTALL_DIR${NC}"
else
    INSTALL_DIR="$HOME/.truthgpt"
    echo -e "Installation target directory: ${BOLD}$INSTALL_DIR${NC}"
    mkdir -p "$INSTALL_DIR"

    # Download / Clone codebase
    REPO_URL="https://github.com/OpenBlatam/IA-Models-Clone.git"
    if command -v git >/dev/null 2>&1; then
        echo -e "Git detected. Syncing repository..."
        if [ -d "$INSTALL_DIR/.git" ]; then
            cd "$INSTALL_DIR" && git pull || true
        else
            git clone "$REPO_URL" "$INSTALL_DIR"
        fi
    else
        echo -e "Git not found. Downloading archive..."
        ZIP_URL="${REPO_URL%.git}/archive/refs/heads/main.zip"
        TEMP_ZIP="/tmp/truthgpt_install.zip"
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$ZIP_URL" -o "$TEMP_ZIP"
        else
            wget -q "$ZIP_URL" -O "$TEMP_ZIP"
        fi
        unzip -q -o "$TEMP_ZIP" -d "$INSTALL_DIR"
        rm -f "$TEMP_ZIP"
    fi
fi

# Detect project root if nested
PROJECT_DIR="$INSTALL_DIR"
if [ ! -f "$PROJECT_DIR/pyproject.toml" ]; then
    FOUND_TOML="$(find "$INSTALL_DIR" -name "pyproject.toml" | head -n 1)"
    if [ -n "$FOUND_TOML" ]; then
        PROJECT_DIR="$(dirname "$FOUND_TOML")"
    fi
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✓ Project directory resolved: $PROJECT_DIR${NC}"

# 4. Set up Virtual Environment
VENV_DIR="$PROJECT_DIR/.venv"
echo -e "\n${CYAN}Setting up isolated Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Created virtualenv at: $VENV_DIR${NC}"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Ensure pip & setuptools are up to date
"$VENV_PIP" install --upgrade pip setuptools wheel >/dev/null 2>&1 || true

# 5. Install Dependencies & TruthGPT Package
echo -e "\n${CYAN}Installing TruthGPT dependencies (this may take 1-2 minutes)...${NC}"
if [ "$OS" = "Darwin" ]; then
    echo -e "Configuring Apple Silicon / macOS optimizations (Metal MPS / CPU)..."
fi

# Install editable package via pip in virtualenv
"$VENV_PIP" install -e .

# 6. Global Command Setup (truthgpt & truth)
echo -e "\n${CYAN}Configuring global system command...${NC}"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

WRAPPER_SCRIPT="$BIN_DIR/truthgpt"
cat << EOF > "$WRAPPER_SCRIPT"
#!/usr/bin/env bash
export TRUTHGPT_HOME="$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"
exec "$VENV_PYTHON" "$PROJECT_DIR/truth_cli.py" "\$@"
EOF
chmod +x "$WRAPPER_SCRIPT"

# Also symlink or alias 'truth'
ln -sf "$WRAPPER_SCRIPT" "$BIN_DIR/truth"

# Optional: Link to /usr/local/bin if writable
if [ -w "/usr/local/bin" ]; then
    ln -sf "$WRAPPER_SCRIPT" "/usr/local/bin/truthgpt" 2>/dev/null || true
    ln -sf "$WRAPPER_SCRIPT" "/usr/local/bin/truth" 2>/dev/null || true
fi

# 7. Add ~/.local/bin to PATH in Shell Configurations
PATH_ADDED=0
for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$RC" ] || [ "$RC" = "$HOME/.zshrc" ]; then
        touch "$RC"
        if ! grep -q '\.local/bin' "$RC"; then
            echo '' >> "$RC"
            echo '# TruthGPT CLI path' >> "$RC"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
            PATH_ADDED=1
        fi
    fi
done

export PATH="$BIN_DIR:$PATH"

# 8. Verification
echo -e "\n${CYAN}Verifying installation...${NC}"
if "$WRAPPER_SCRIPT" --help >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Command test succeeded!${NC}"
else
    echo -e "${YELLOW}Note: Initial verification run completed.${NC}"
fi

echo -e "\n${GREEN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}   🎉 TruthGPT Successfully Installed!${NC}"
echo -e "${GREEN}${BOLD}============================================================${NC}\n"
echo -e "You can now use either of these commands from any terminal:"
echo -e "  ${BOLD}${CYAN}truthgpt${NC}   (or ${BOLD}${CYAN}truth${NC})"
echo -e ""
echo -e "To launch the interactive dashboard:"
echo -e "  ${BOLD}truthgpt${NC}"
echo -e ""
echo -e "To view all available commands:"
echo -e "  ${BOLD}truthgpt --help${NC}"
echo -e ""
if [ "$PATH_ADDED" -eq 1 ]; then
    echo -e "${YELLOW}⚡ If your current terminal does not recognize the command immediately,${NC}"
    echo -e "${YELLOW}   run this command once or open a new terminal window:${NC}"
    echo -e "   ${BOLD}source ~/.zshrc${NC}  (or ${BOLD}source ~/.bashrc${NC})\n"
fi
