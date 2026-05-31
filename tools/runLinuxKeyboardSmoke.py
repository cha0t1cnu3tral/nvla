# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.keyboard_smoke import runKeyboardSmoke  # noqa: E402


def main() -> int:
	parser = argparse.ArgumentParser(description="Observe NVDA Linux preview X11 keyboard gestures.")
	parser.add_argument("--duration", type=float, default=15, help="Observation duration in seconds.")
	args = parser.parse_args()
	return runKeyboardSmoke(durationSeconds=args.duration)


if __name__ == "__main__":
	raise SystemExit(main())
