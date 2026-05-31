#!/usr/bin/env bash
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
bin_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
systemd_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$bin_dir" "$applications_dir" "$systemd_dir"
ln -sfn "$root_dir/tools/runLinuxPort.sh" "$bin_dir/nvda-linux-preview"
cp "$root_dir/packaging/linux/nvda-linux-preview.desktop" "$applications_dir/"
cp "$root_dir/packaging/linux/nvda-linux-preview.service" "$systemd_dir/"

printf 'Installed NVDA Linux preview launcher at %s\n' "$bin_dir/nvda-linux-preview"
printf 'Run nvda-linux-preview manually before enabling the user service.\n'
