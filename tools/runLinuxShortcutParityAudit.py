# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.shortcut_parity import (  # noqa: E402
	auditShortcutParity,
	formatShortcutParityReport,
)


def main() -> int:
	parser = argparse.ArgumentParser(description="Audit Linux keyboard shortcut parity against shared NVDA commands.")
	parser.add_argument("--output", type=Path, help="Write the Markdown audit to this path.")
	args = parser.parse_args()
	report = formatShortcutParityReport(auditShortcutParity(SOURCE_DIR / "globalCommands.py"))
	print(report)
	if args.output is not None:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		args.output.write_text(report, encoding="utf-8")
		print(f"\nWrote Linux keyboard shortcut parity audit to {args.output}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
