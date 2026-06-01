# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
import unittest


class TestLinuxPreviewPackaging(unittest.TestCase):
	def setUp(self):
		self.root = Path(__file__).resolve().parents[2]

	def testShellLauncherUsesLinuxPythonEntryPoint(self):
		launcher = (self.root / "tools" / "runLinuxPort.sh").read_text(encoding="utf-8")
		self.assertIn('exec "${PYTHON:-python3}" "$root_dir/tools/runLinuxPort.py" "$@"', launcher)

	def testInstallerLinksLauncherAndInstallsDesktopArtifacts(self):
		installer = (self.root / "packaging" / "linux" / "installPreview.sh").read_text(encoding="utf-8")
		self.assertIn('ln -sfn "$root_dir/tools/runLinuxPort.sh" "$bin_dir/nvda-linux-preview"', installer)
		self.assertIn("nvda-linux-preview.desktop", installer)
		self.assertIn("nvda-linux-preview.service", installer)
		self.assertIn("systemctl --user daemon-reload", installer)

	def testUninstallerRemovesUserLevelPreviewArtifacts(self):
		uninstaller = (
			self.root / "packaging" / "linux" / "uninstallPreview.sh"
		).read_text(encoding="utf-8")
		self.assertIn("systemctl --user disable --now nvda-linux-preview.service", uninstaller)
		self.assertIn('"$bin_dir/nvda-linux-preview"', uninstaller)
		self.assertIn('"$applications_dir/nvda-linux-preview.desktop"', uninstaller)
		self.assertIn('"$systemd_dir/nvda-linux-preview.service"', uninstaller)
		self.assertIn("systemctl --user daemon-reload", uninstaller)

	def testDesktopEntryUsesInstalledPreviewCommand(self):
		desktopEntry = (
			self.root / "packaging" / "linux" / "nvda-linux-preview.desktop"
		).read_text(encoding="utf-8")
		self.assertIn("Exec=nvda-linux-preview", desktopEntry)

	def testSystemdServiceUsesInstalledPreviewCommand(self):
		service = (
			self.root / "packaging" / "linux" / "nvda-linux-preview.service"
		).read_text(encoding="utf-8")
		self.assertIn("ExecStart=%h/.local/bin/nvda-linux-preview", service)

	def testPackagingReadmeLinksUserFacingLinuxPreviewGuide(self):
		readme = (self.root / "packaging" / "linux" / "README.md").read_text(encoding="utf-8")
		self.assertIn("documentation/nvda linux documentation/user/linux-preview.md", readme)

	def testLinuxPreviewGuideDocumentsNativeCommandsAndStrictSmoke(self):
		guide = (
			self.root / "documentation" / "nvda linux documentation" / "user" / "linux-preview.md"
		).read_text(encoding="utf-8")
		for command in ("NVDA+T", "NVDA+Tab", "NVDA+B", "NVDA+H", "NVDA+Q"):
			with self.subTest(command=command):
				self.assertIn(command, guide)
		self.assertIn("--strict-capture", guide)


if __name__ == "__main__":
	unittest.main()
