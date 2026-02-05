#!/usr/bin/env bash
set -euo pipefail

# Export the enterprise staging folder into a separate repo directory.
# Usage:
#   ./scripts/export_enterprise_repo.sh /path/to/genxai-enterprise

TARGET_DIR="${1:-}"

if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: $0 /path/to/genxai-enterprise"
  exit 1
fi

if [[ ! -d "enterprise" ]]; then
  echo "Error: enterprise/ folder not found. Nothing to export."
  exit 1
fi

mkdir -p "$TARGET_DIR"

echo "Exporting enterprise/ to $TARGET_DIR..."
rsync -av --delete enterprise/ "$TARGET_DIR/"

echo "Done. Next steps:"
echo "1) cd $TARGET_DIR"
echo "2) Move studio folder to repo root: mv studio ./"
echo "3) Add your commercial LICENSE/EULA"
echo "4) Initialize git and push to private repo"