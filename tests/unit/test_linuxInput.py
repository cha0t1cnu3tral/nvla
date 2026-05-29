# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.input import LinuxInputAdapter, makeKeyboardGesture, translateRawKeyEvent


class TestLinuxInputAdapter(unittest.TestCase):
	def test_translates_raw_key_event(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="a",
				pressed=True,
				modifiers=("Control_L", "shift", "control"),
				scanCode=30,
			),
		)

		self.assertEqual("A", event.keyName)
		self.assertTrue(event.isPressed)
		self.assertEqual(frozenset(("control", "shift")), event.modifiers)
		self.assertEqual("control+shift+A", event.gestureName)
		self.assertEqual(30, event.scanCode)

	def test_translates_key_release(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				keyName="space",
				isPressed=False,
				modifiers=("alt-r",),
			),
		)

		self.assertEqual("Space", event.keyName)
		self.assertFalse(event.isPressed)
		self.assertEqual(frozenset(("alt",)), event.modifiers)
		self.assertEqual("alt+Space", event.gestureName)

	def test_dispatches_fed_keyboard_events_to_listeners_and_observer(self):
		adapter = LinuxInputAdapter()
		received = []
		observerEvents = []
		observer = SimpleNamespace(handleKeyEvent=observerEvents.append)

		adapter.initialize_keyboard(observer)
		adapter.registerKeyboardListener(received.append)
		event = adapter.feedRawKeyboardEvent(
			SimpleNamespace(
				key="enter",
				modifiers=("super",),
			),
		)

		self.assertEqual("super+Enter", event.gestureName)
		self.assertEqual([event], received)
		self.assertEqual([event], observerEvents)

	def test_creates_keyboard_gesture_from_key_event(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="f1",
				modifiers=("control", "NVDA"),
			),
		)

		gesture = makeKeyboardGesture(event)

		self.assertEqual(("kb(linux):NVDA+control+F1",), gesture.identifiers)
		self.assertEqual(("kb(linux):nvda+control+f1",), gesture.normalizedIdentifiers)
		self.assertEqual("NVDA+control+F1", gesture.displayName)
		self.assertFalse(gesture.isCharacter)

	def test_unmodified_single_character_gesture_is_character(self):
		event = translateRawKeyEvent(SimpleNamespace(key="x"))

		gesture = makeKeyboardGesture(event)

		self.assertTrue(gesture.isCharacter)
		self.assertEqual(("kb(linux):X",), gesture.identifiers)

	def test_dispatches_pressed_key_to_gesture_executor(self):
		adapter = LinuxInputAdapter()
		executed = []

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.setKeyboardGestureExecutor(executed.append)
		event = adapter.feedRawKeyboardEvent(
			SimpleNamespace(
				key="n",
				modifiers=("NVDA",),
				pressed=True,
			),
		)

		self.assertEqual(1, len(executed))
		self.assertEqual(event, executed[0].event)
		self.assertEqual(("kb(linux):NVDA+N",), executed[0].identifiers)

	def test_does_not_dispatch_released_key_to_gesture_executor(self):
		adapter = LinuxInputAdapter()
		executed = []

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.setKeyboardGestureExecutor(executed.append)
		adapter.feedRawKeyboardEvent(
			SimpleNamespace(
				key="n",
				modifiers=("NVDA",),
				pressed=False,
			),
		)

		self.assertEqual([], executed)

	def test_terminate_keyboard_clears_runtime_state(self):
		adapter = LinuxInputAdapter()
		received = []
		executed = []

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.registerKeyboardListener(received.append)
		adapter.setKeyboardGestureExecutor(executed.append)
		adapter.terminate_keyboard()
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="a"))

		self.assertEqual([], received)
		self.assertEqual([], executed)
