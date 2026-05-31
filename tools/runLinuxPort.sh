#!/usr/bin/env bash
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${PYTHON:-python3}" "$root_dir/tools/runLinuxPort.py" "$@"
