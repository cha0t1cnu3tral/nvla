#!/usr/bin/env bash
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

set -euo pipefail

bin_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
systemd_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

if command -v systemctl >/dev/null 2>&1; then
	systemctl --user disable --now nvda-linux-preview.service >/dev/null 2>&1 || true
fi

launcher_path="$bin_dir/nvda-linux-preview"
if [[ -L "$launcher_path" ]]; then
	rm -f -- "$launcher_path"
fi

rm -f \
	"$applications_dir/nvda-linux-preview.desktop" \
	"$systemd_dir/nvda-linux-preview.service"

if command -v update-desktop-database >/dev/null 2>&1; then
	update-desktop-database "$applications_dir" >/dev/null 2>&1 || true
fi
if command -v systemctl >/dev/null 2>&1; then
	systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

printf 'Removed NVDA Linux preview user-level artifacts.\n'
