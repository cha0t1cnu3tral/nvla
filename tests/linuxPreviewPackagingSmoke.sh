#!/usr/bin/env bash
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

set -euo pipefail

root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/nvda-linux-preview-packaging.XXXXXX")"

cleanup() {
	case "$temp_dir" in
		"${TMPDIR:-/tmp}"/nvda-linux-preview-packaging.*)
			rm -rf -- "$temp_dir"
			;;
		*)
			printf 'Refusing to remove unexpected temporary directory: %s\n' "$temp_dir" >&2
			exit 1
			;;
	esac
}
trap cleanup EXIT

export XDG_BIN_HOME="$temp_dir/bin dir % & |"
export XDG_DATA_HOME="$temp_dir/data"
export XDG_CONFIG_HOME="$temp_dir/config"

bash "$root_dir/packaging/linux/installPreview.sh"

launcher_path="$XDG_BIN_HOME/nvda-linux-preview"
rendered_launcher_path="${launcher_path//%/%%}"
test -L "$launcher_path"
grep -Fx -- "Exec=\"$rendered_launcher_path\"" \
	"$XDG_DATA_HOME/applications/nvda-linux-preview.desktop"
grep -Fx -- "ExecStart=\"$rendered_launcher_path\"" \
	"$XDG_CONFIG_HOME/systemd/user/nvda-linux-preview.service"

bash "$root_dir/packaging/linux/uninstallPreview.sh"

test ! -e "$launcher_path"
test ! -e "$XDG_DATA_HOME/applications/nvda-linux-preview.desktop"
test ! -e "$XDG_CONFIG_HOME/systemd/user/nvda-linux-preview.service"

printf 'Linux preview packaging smoke passed.\n'
