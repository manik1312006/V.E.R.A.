#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  V.E.R.A. Installer (Linux/macOS) — Run this once after cloning
# ═══════════════════════════════════════════════════════════════════════════

set -e

VERA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo " ╔══════════════════════════════════════════════╗"
echo " ║   V.E.R.A. Installer                        ║"
echo " ║   Virtual Entity for Real-time Assistance   ║"
echo " ╚══════════════════════════════════════════════╝"
echo ""
echo " Installing from: $VERA_DIR"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────────────
echo "[1/4] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo " ERROR: Python3 not found. Please install Python 3.10+."
    exit 1
fi
PYVER=$(python3 --version 2>&1)
echo " Found $PYVER"
echo ""

# ── Step 2: Install dependencies ─────────────────────────────────────────
echo "[2/4] Installing Python dependencies..."
python3 -m pip install -r "$VERA_DIR/requirements.txt" --quiet
echo " Dependencies installed successfully."
echo ""

# ── Step 3: Set up config ────────────────────────────────────────────────
echo "[3/4] Setting up config..."
if [ ! -f "$VERA_DIR/config.yaml" ]; then
    cp "$VERA_DIR/config.template.yaml" "$VERA_DIR/config.yaml"
    echo " Created config.yaml from template."
    echo " V.E.R.A. will ask for your API key on first run."
else
    echo " config.yaml already exists, skipping."
fi
echo ""

# ── Step 4: Create launcher ────────────────────────────────────────────────
echo "[4/4] Creating launcher (vera)..."
cat > "$VERA_DIR/vera" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
python3 vera.py "$@"
EOF
chmod +x "$VERA_DIR/vera"

# Add to PATH if not already there
SHELL_RC="$HOME/.bashrc"
if [[ "$OSTYPE" == "darwin"* ]]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "$VERA_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "export PATH=\"\$PATH:$VERA_DIR\"" >> "$SHELL_RC"
    echo " Added $VERA_DIR to your PATH in $SHELL_RC"
else
    echo " $VERA_DIR is already in your PATH."
fi
echo ""

# ── Done! ─────────────────────────────────────────────────────────────────
echo " ═══════════════════════════════════════════════════"
echo "  Installation complete!"
echo ""
echo "  Open a NEW terminal window (or run 'source $SHELL_RC') and type:"
echo ""
echo "      vera"
echo ""
echo "  to launch V.E.R.A. from anywhere on your machine."
echo " ═══════════════════════════════════════════════════"
echo ""
