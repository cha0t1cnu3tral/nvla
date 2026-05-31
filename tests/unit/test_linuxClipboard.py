# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest
from unittest import mock

from platform.common.errors import NotSupportedYetError
from platform.linux.clipboard import LinuxClipboardAdapter


class TestLinuxClipboardAdapter(unittest.TestCase):
	def test_prefers_wayland_clipboard_client_in_wayland_session(self):
		adapter = LinuxClipboardAdapter(
			environ={"WAYLAND_DISPLAY": "wayland-0"},
			which=lambda executable: f"/usr/bin/{executable}",
		)

		self.assertTrue(adapter.available)
		self.assertEqual("wayland", adapter._command.name)

	def test_prefers_xclip_outside_wayland(self):
		adapter = LinuxClipboardAdapter(
			environ={"DISPLAY": ":1"},
			which=lambda executable: f"/usr/bin/{executable}",
		)

		self.assertEqual("xclip", adapter._command.name)

	def test_falls_back_to_xsel(self):
		adapter = LinuxClipboardAdapter(
			environ={"DISPLAY": ":1"},
			which=lambda executable: f"/usr/bin/{executable}" if executable == "xsel" else None,
		)

		self.assertEqual("xsel", adapter._command.name)

	def test_reads_text_from_selected_client(self):
		run = mock.Mock(return_value=SimpleNamespace(stdout="clipboard text"))
		adapter = LinuxClipboardAdapter(
			environ={"WAYLAND_DISPLAY": "wayland-0"},
			which=lambda executable: f"/usr/bin/{executable}",
			run=run,
		)

		self.assertEqual("clipboard text", adapter.get_text())
		self.assertEqual(["wl-paste", "--no-newline"], run.call_args.args[0])

	def test_writes_text_to_selected_client(self):
		run = mock.Mock()
		adapter = LinuxClipboardAdapter(
			environ={"DISPLAY": ":1"},
			which=lambda executable: f"/usr/bin/{executable}",
			run=run,
		)

		adapter.set_text("ready")

		self.assertEqual(["xclip", "-selection", "clipboard", "-in"], run.call_args.args[0])
		self.assertEqual("ready", run.call_args.kwargs["input"])

	def test_missing_client_is_explicitly_unsupported(self):
		adapter = LinuxClipboardAdapter(environ={}, which=lambda executable: None)

		self.assertFalse(adapter.available)
		with self.assertRaises(NotSupportedYetError):
			adapter.get_text()
		with self.assertRaises(NotSupportedYetError):
			adapter.set_text("ready")


if __name__ == "__main__":
	unittest.main()
