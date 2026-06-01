# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
import unittest

from platform.linux.shortcut_parity import (
	auditShortcutParity,
	collectKeyboardIdentifiers,
	formatShortcutParityReport,
)


class TestLinuxShortcutParity(unittest.TestCase):
	def setUp(self):
		self.globalCommandsPath = Path(__file__).resolve().parents[2] / "source" / "globalCommands.py"

	def test_collects_shared_global_keyboard_identifiers(self):
		identifiers = collectKeyboardIdentifiers(self.globalCommandsPath)

		self.assertGreater(len(identifiers), 100)
		self.assertIn("kb:NVDA+t", identifiers)
		self.assertIn("kb(laptop):NVDA+l", identifiers)
		self.assertNotIn("ts:double_tap", identifiers)

	def test_reports_native_preview_and_shared_runtime_pending_identifiers(self):
		report = auditShortcutParity(self.globalCommandsPath)

		self.assertIn("kb:NVDA+t", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+tab", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+b", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+1", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+f12", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+f2", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+c", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+shift+b", report.previewHandledIdentifiers)
		self.assertIn("kb:NVDA+2", report.sharedRuntimePendingIdentifiers)
		self.assertNotIn("kb:NVDA+t", report.sharedRuntimePendingIdentifiers)

	def test_formats_markdown_summary_and_identifier_lists(self):
		report = formatShortcutParityReport(auditShortcutParity(self.globalCommandsPath))

		self.assertIn("# NVDA Linux Keyboard Shortcut Parity Audit", report)
		self.assertIn("Identifier translation coverage:", report)
		self.assertIn("Native preview-handled shared identifiers:", report)
		self.assertIn("Shared-runtime integration pending:", report)
		self.assertIn("- `kb:NVDA+t`", report)


if __name__ == "__main__":
	unittest.main()
