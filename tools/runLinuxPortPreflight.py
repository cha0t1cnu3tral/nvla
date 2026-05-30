# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "source"))

from platform.linux.preflight import formatPreflightReport, isReadyForPreview, runPreflightChecks  # noqa: E402


def main() -> int:
	checks = runPreflightChecks()
	print(formatPreflightReport(checks))
	if isReadyForPreview(checks):
		print("\nLinux preview dependencies are present.")
		return 0
	print("\nLinux preview dependencies are incomplete.")
	return 1


if __name__ == "__main__":
	raise SystemExit(main())
