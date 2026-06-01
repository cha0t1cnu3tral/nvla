# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.release_smoke import (  # noqa: E402
	formatReleaseSmokeReport,
	runReleaseSmoke,
)


def main() -> int:
	parser = argparse.ArgumentParser(description="Run the NVDA Linux preview release smoke workflow.")
	parser.add_argument("--duration", type=float, default=30, help="Native preview duration in seconds.")
	parser.add_argument(
		"--strict-capture",
		action="store_true",
		help="Fail before runtime when global keyboard or mouse capture is unavailable.",
	)
	parser.add_argument(
		"--report",
		type=Path,
		help="Write a Markdown validation report with the transcript and manual checklist.",
	)
	args = parser.parse_args()
	output: list[str] = []

	def write(message: str) -> None:
		print(message)
		output.append(message)

	result = runReleaseSmoke(durationSeconds=args.duration, strictCapture=args.strict_capture, write=write)
	if args.report is not None:
		args.report.parent.mkdir(parents=True, exist_ok=True)
		args.report.write_text(
			formatReleaseSmokeReport(
				output=output,
				exitStatus=result,
				durationSeconds=args.duration,
				strictCapture=args.strict_capture,
			),
			encoding="utf-8",
		)
		print(f"\nWrote Linux preview release smoke report to {args.report}")
	return result


if __name__ == "__main__":
	raise SystemExit(main())
