# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.focus_speech_smoke import runFocusSpeechSmoke  # noqa: E402


def main() -> int:
	parser = argparse.ArgumentParser(description="Speak live NVDA Linux preview AT-SPI focus events.")
	parser.add_argument("--duration", type=float, default=30, help="Observation duration in seconds.")
	args = parser.parse_args()
	return runFocusSpeechSmoke(durationSeconds=args.duration)


if __name__ == "__main__":
	raise SystemExit(main())
