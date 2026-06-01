# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.input import LinuxInputAdapter
from platform.linux.mouse import (
	ManualMouseEventSource,
	MouseCaptureMode,
	WaylandMouseEventSource,
	X11MouseEventSource,
	createMouseEventSource,
	translateRawMouseEvent,
)


class _FakeX11Display:
	def __init__(self, *, hasRecordExtension=True):
		self.display = self
		self.hasRecordExtension = hasRecordExtension
		self.disabledContexts = []
		self.freedContexts = []
		self.isClosed = False

	def has_extension(self, name):
		return name == "RECORD" and self.hasRecordExtension

	def record_create_context(self, *args):
		self.createdContextArgs = args
		return 42

	def record_enable_context(self, context, callback):
		self.enabledContext = context
		self.callback = callback

	def record_disable_context(self, context):
		self.disabledContexts.append(context)

	def record_free_context(self, context):
		self.freedContexts.append(context)

	def flush(self):
		return None

	def close(self):
		self.isClosed = True


def _makeFakeX11Modules(*, hasRecordExtension=True):
	displays = []

	def makeDisplay():
		display = _FakeX11Display(hasRecordExtension=hasRecordExtension)
		displays.append(display)
		return display

	class EventField:
		def __init__(self, *args):
			pass

		def parse_binary_value(self, data, *args):
			return data[0], data[1:]

	modules = SimpleNamespace(
		X=SimpleNamespace(ButtonPress=4, ButtonRelease=5, MotionNotify=6),
		display=SimpleNamespace(Display=makeDisplay),
		record=SimpleNamespace(AllClients="all", FromServer="server"),
		rq=SimpleNamespace(EventField=EventField),
	)
	return modules, displays


class TestLinuxMouse(unittest.TestCase):
	def test_translates_raw_mouse_event(self):
		event = translateRawMouseEvent(SimpleNamespace(kind="buttonDown", x=10, y=20, button=1))

		self.assertEqual("buttonDown", event.kind)
		self.assertEqual((10, 20), (event.x, event.y))
		self.assertEqual(1, event.button)

	def test_manual_mouse_source_feeds_adapter(self):
		source = ManualMouseEventSource()
		adapter = LinuxInputAdapter()
		received = []
		adapter.registerMouseListener(received.append)

		adapter.initialize_mouse(eventSource=source)
		event = source.emit(SimpleNamespace(kind="move", x=10, y=20))

		self.assertEqual(MouseCaptureMode.GLOBAL_OBSERVE_ONLY, adapter.mouseCaptureMode)
		self.assertEqual([event], received)
		adapter.terminate_mouse()
		self.assertFalse(source.isStarted)

	def test_selects_mouse_event_source_from_session_environment(self):
		self.assertIsInstance(createMouseEventSource({"DISPLAY": ":1"}), X11MouseEventSource)
		self.assertIsInstance(createMouseEventSource({"WAYLAND_DISPLAY": "wayland-0"}), WaylandMouseEventSource)
		self.assertIsNone(createMouseEventSource({}))

	def test_x11_record_source_observes_global_pointer_events(self):
		modules, displays = _makeFakeX11Modules()
		source = X11MouseEventSource(loadXlibModules=lambda: modules)
		received = []
		source.start(received.append)

		source._handleRecordReply(
			SimpleNamespace(
				category="server",
				client_swapped=False,
				data=[
					SimpleNamespace(type=6, root_x=10, root_y=20, detail=0),
					SimpleNamespace(type=4, root_x=10, root_y=20, detail=1),
					SimpleNamespace(type=5, root_x=10, root_y=20, detail=1),
				],
			),
		)
		source.stop()

		self.assertEqual(["move", "buttonDown", "buttonUp"], [event.kind for event in received])
		self.assertEqual([None, 1, 1], [event.button for event in received])
		self.assertEqual([42], displays[0].disabledContexts)
		self.assertEqual([42], displays[0].freedContexts)
		self.assertTrue(all(display.isClosed for display in displays))

	def test_x11_record_failure_uses_local_only_fallback(self):
		modules, _displays = _makeFakeX11Modules(hasRecordExtension=False)
		source = X11MouseEventSource(loadXlibModules=lambda: modules)
		adapter = LinuxInputAdapter()

		adapter.initialize_mouse(eventSource=source)

		self.assertEqual(MouseCaptureMode.LOCAL_ONLY, adapter.mouseCaptureMode)
		self.assertIsNotNone(adapter.mouseEventSourceStartError)
		adapter.terminate_mouse()


if __name__ == "__main__":
	unittest.main()
