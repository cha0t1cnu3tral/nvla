# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import ast
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

import argsParsing
import languageHandler
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


class TestLinuxSharedBootstrapFallbacks(unittest.TestCase):
	def testLogFormatterUsesStandardTimestampOutsideWindows(self):
		logHandlerPath = Path(__file__).resolve().parents[2] / "source" / "logHandler.py"
		source = logHandlerPath.read_text(encoding="utf-8")
		self.assertIn("if not _IS_WINDOWS:", source)
		self.assertIn("return super().formatTime(record, datefmt)", source)

	def testLanguageHandlerUsesProcessLocaleOutsideWindows(self):
		with (
			patch.object(languageHandler, "_IS_WINDOWS", False),
			patch.object(languageHandler.locale, "getlocale", return_value=("en_US", "UTF-8")),
		):
			self.assertEqual("en_US", languageHandler.getWindowsLanguage())
			self.assertEqual(languageHandler.LCID_NONE, languageHandler.localeNameToWindowsLCID("en_US"))

	def testQueueHandlerSelectsLinuxWatchdogOutsideWindows(self):
		queueHandlerPath = Path(__file__).resolve().parents[2] / "source" / "queueHandler.py"
		source = queueHandlerPath.read_text(encoding="utf-8")
		self.assertIn("if sys.platform.startswith(\"win\"):", source)
		self.assertIn("from platform.linux import watchdog", source)

	def testLinuxAccessibilityDefersHeavyEventDispatchImports(self):
		accessibilityPath = (
			Path(__file__).resolve().parents[2] / "source" / "platform" / "linux" / "accessibility.py"
		)
		tree = ast.parse(accessibilityPath.read_text(encoding="utf-8"))
		topLevelImports = {
			alias.name
			for node in tree.body
			if isinstance(node, ast.Import)
			for alias in node.names
		}
		self.assertNotIn("api", topLevelImports)
		self.assertNotIn("eventHandler", topLevelImports)


if __name__ == "__main__":
	unittest.main()
