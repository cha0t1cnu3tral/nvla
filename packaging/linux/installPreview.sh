#!/usr/bin/env bash
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
bin_dir="${XDG_BIN_HOME:-$HOME/.local/bin}"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
systemd_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

escape_systemd_argument() {
	local value="$1"
	value="${value//\\/\\\\}"
	value="${value//\"/\\\"}"
	value="${value//%/%%}"
	printf '"%s"' "$value"
}

mkdir -p "$bin_dir" "$applications_dir" "$systemd_dir"
launcher_path="$bin_dir/nvda-linux-preview"
if [[ -e "$launcher_path" && ! -L "$launcher_path" ]]; then
	printf 'Refusing to replace non-symbolic launcher at %s\n' "$launcher_path" >&2
	exit 1
fi
ln -sfn "$root_dir/tools/runLinuxPort.sh" "$launcher_path"
launcher_exec="$(escape_systemd_argument "$launcher_path")"
escaped_launcher_exec="${launcher_exec//\\/\\\\}"
escaped_launcher_exec="${escaped_launcher_exec//&/\\&}"
escaped_launcher_exec="${escaped_launcher_exec//|/\\|}"
sed "s|@NVDA_LINUX_PREVIEW_LAUNCHER@|$escaped_launcher_exec|" \
	"$root_dir/packaging/linux/nvda-linux-preview.desktop" \
	> "$applications_dir/nvda-linux-preview.desktop"
sed "s|@NVDA_LINUX_PREVIEW_LAUNCHER@|$escaped_launcher_exec|" \
	"$root_dir/packaging/linux/nvda-linux-preview.service" \
	> "$systemd_dir/nvda-linux-preview.service"

if command -v update-desktop-database >/dev/null 2>&1; then
	update-desktop-database "$applications_dir" >/dev/null 2>&1 || true
fi
if command -v systemctl >/dev/null 2>&1; then
	systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

printf 'Installed NVDA Linux preview launcher at %s\n' "$launcher_path"
printf 'Run nvda-linux-preview manually before enabling the user service.\n'
