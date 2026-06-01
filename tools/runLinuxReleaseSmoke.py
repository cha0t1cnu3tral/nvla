# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.release_smoke import runReleaseSmoke  # noqa: E402


def main() -> int:
	parser = argparse.ArgumentParser(description="Run the NVDA Linux preview release smoke workflow.")
	parser.add_argument("--duration", type=float, default=30, help="Native preview duration in seconds.")
	parser.add_argument(
		"--strict-capture",
		action="store_true",
		help="Fail before runtime when global keyboard or mouse capture is unavailable.",
	)
	args = parser.parse_args()
	return runReleaseSmoke(durationSeconds=args.duration, strictCapture=args.strict_capture)


if __name__ == "__main__":
	raise SystemExit(main())
