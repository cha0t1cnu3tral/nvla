# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from platform.common.errors import NotSupportedYetError
from platform.linux.process_focus import LinuxProcessFocusAdapter


class _FakeX11Display:
	def __init__(self, properties):
		self.id = 100
		self.properties = properties
		self.isClosed = False

	def screen(self):
		return SimpleNamespace(root=self)

	def intern_atom(self, name, only_if_exists):
		self.assertOnlyIfExists = only_if_exists
		return name if name in self.properties else 0

	def get_full_property(self, atom, _propertyType):
		value = self.properties.get(atom)
		return None if value is None else SimpleNamespace(value=value)

	def close(self):
		self.isClosed = True


def _makeFakeX11Modules(properties):
	displays = []

	def makeDisplay():
		display = _FakeX11Display(properties)
		displays.append(display)
		return display

	return (
		SimpleNamespace(
			X=SimpleNamespace(AnyPropertyType=0),
			display=SimpleNamespace(Display=makeDisplay),
		),
		displays,
	)


class TestLinuxProcessFocusAdapter(unittest.TestCase):
	def test_gets_x11_desktop_and_active_window(self):
		modules, displays = _makeFakeX11Modules({"_NET_ACTIVE_WINDOW": [200]})
		adapter = LinuxProcessFocusAdapter(
			environ={"DISPLAY": ":1"},
			loadXlibModules=lambda: modules,
		)

		self.assertEqual(100, adapter.get_desktop_window())
		self.assertEqual(200, adapter.get_foreground_window())
		self.assertTrue(all(display.isClosed for display in displays))

	def test_returns_zero_when_x11_has_no_active_window(self):
		modules, _displays = _makeFakeX11Modules({"_NET_ACTIVE_WINDOW": []})
		adapter = LinuxProcessFocusAdapter(
			environ={"DISPLAY": ":1"},
			loadXlibModules=lambda: modules,
		)

		self.assertEqual(0, adapter.get_foreground_window())

	def test_prefers_stacking_order_for_x11_window_enumeration(self):
		modules, _displays = _makeFakeX11Modules(
			{
				"_NET_CLIENT_LIST_STACKING": [300, 200],
				"_NET_CLIENT_LIST": [200, 300],
			},
		)
		adapter = LinuxProcessFocusAdapter(
			environ={"DISPLAY": ":1"},
			loadXlibModules=lambda: modules,
		)

		self.assertEqual([300, 200], adapter.list_window_handles())

	def test_falls_back_to_x11_client_list_for_window_enumeration(self):
		modules, _displays = _makeFakeX11Modules({"_NET_CLIENT_LIST": [200, 300]})
		adapter = LinuxProcessFocusAdapter(
			environ={"DISPLAY": ":1"},
			loadXlibModules=lambda: modules,
		)

		self.assertEqual([200, 300], adapter.list_window_handles())

	def test_lists_numeric_proc_directories_as_process_ids(self):
		with tempfile.TemporaryDirectory() as directory:
			procDir = Path(directory)
			for name in ("20", "3", "self", "cpuinfo"):
				(procDir / name).mkdir()

			self.assertEqual(
				[3, 20],
				LinuxProcessFocusAdapter(procDir=procDir).list_process_ids(),
			)

	def test_x11_window_discovery_requires_display(self):
		adapter = LinuxProcessFocusAdapter(environ={})

		with self.assertRaises(NotSupportedYetError):
			adapter.get_desktop_window()

	def test_x11_window_enumeration_requires_ewmh_client_list(self):
		modules, _displays = _makeFakeX11Modules({})
		adapter = LinuxProcessFocusAdapter(
			environ={"DISPLAY": ":1"},
			loadXlibModules=lambda: modules,
		)

		with self.assertRaises(NotSupportedYetError):
			adapter.list_window_handles()


if __name__ == "__main__":
	unittest.main()
