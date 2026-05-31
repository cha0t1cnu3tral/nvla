# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "source"
sys.path.insert(0, str(SOURCE_DIR))

from platform.linux.launcher import runLinuxPreview  # noqa: E402


if __name__ == "__main__":
	raise SystemExit(
		runLinuxPreview(
			sourceDir=SOURCE_DIR,
			args=sys.argv[1:],
		),
	)
