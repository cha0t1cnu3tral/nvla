# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from io import StringIO
import unittest
from unittest.mock import patch

import argsParsing
import NVDAState


class TestNVDAStateWithoutWindowsRegistry(unittest.TestCase):
	def testOptionalInstalledStateDefaultsAreUnavailable(self):
		with patch.object(NVDAState, "winreg", None):
			self.assertIsNone(NVDAState.WritePaths.startMenuFolder)
			self.assertIsNone(NVDAState.WritePaths._startMenuFolderX86)
			self.assertIsNone(NVDAState.WritePaths.installDir)
			self.assertIsNone(NVDAState.WritePaths._installDirX86)

	def testInstallPathCalculationFailsExplicitly(self):
		with patch.object(NVDAState, "winreg", None):
			with self.assertRaisesRegex(RuntimeError, "Windows registry"):
				_ = NVDAState.WritePaths.defaultInstallDir

	def testRegistryFeatureFlagsDefaultToDisabled(self):
		with patch.object(NVDAState, "winreg", None):
			self.assertFalse(NVDAState._forceSecureModeEnabled())
			self.assertFalse(NVDAState._serviceDebugEnabled())
			self.assertFalse(NVDAState._configInLocalAppDataEnabled())


class TestArgsParsingWithoutWindowsDialogs(unittest.TestCase):
	def testHelpUsesProvidedConsoleStream(self):
		stream = StringIO()
		parser = argsParsing.NoConsoleOptionParser(prog="nvda-linux")
		with patch.object(argsParsing, "winUser", None):
			parser.print_help(stream)
		self.assertIn("usage: nvda-linux", stream.getvalue())

	def testErrorUsesConsoleParserExit(self):
		stream = StringIO()
		parser = argsParsing.NoConsoleOptionParser(prog="nvda-linux")
		with (
			patch.object(argsParsing, "winUser", None),
			patch("sys.stderr", stream),
			self.assertRaises(SystemExit) as exitContext,
		):
			parser.error("bad option")
		self.assertEqual(2, exitContext.exception.code)
		self.assertIn("bad option", stream.getvalue())


if __name__ == "__main__":
	unittest.main()
