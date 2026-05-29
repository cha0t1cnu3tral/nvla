# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.input import (
	LinuxInputAdapter,
	executeKeyboardGesture,
	makeKeyboardGesture,
	translateRawKeyEvent,
)


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

		self.assertEqual(
			(
				"kb(desktop):NVDA+control+F1",
				"kb(laptop):NVDA+control+F1",
				"kb:NVDA+control+F1",
			),
			gesture.identifiers,
		)
		self.assertEqual(
			(
				"kb(desktop):nvda+control+f1",
				"kb(laptop):nvda+control+f1",
				"kb:nvda+control+f1",
			),
			gesture.normalizedIdentifiers,
		)
		self.assertEqual("NVDA+control+F1", gesture.displayName)
		self.assertFalse(gesture.isCharacter)

	def test_keyboard_gesture_exposes_input_core_shape(self):
		event = translateRawKeyEvent(SimpleNamespace(key="shift", modifiers=()))

		gesture = makeKeyboardGesture(event)

		self.assertEqual(("kb(desktop):shift", "kb(laptop):shift", "kb:shift"), gesture.identifiers)
		self.assertTrue(gesture.isModifier)
		self.assertEqual(("desktop keyboard", "shift"), gesture.getDisplayTextForIdentifier("kb(desktop):shift"))
		with self.assertRaises(NotImplementedError):
			gesture.send()

	def test_unmodified_single_character_gesture_is_character(self):
		event = translateRawKeyEvent(SimpleNamespace(key="x"))

		gesture = makeKeyboardGesture(event)

		self.assertTrue(gesture.isCharacter)
		self.assertEqual(
			(
				"kb(desktop):X",
				"kb(laptop):X",
				"kb:X",
			),
			gesture.identifiers,
		)

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
		self.assertEqual("kb(desktop):NVDA+N", executed[0].identifiers[0])

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

	def test_executes_keyboard_gesture_through_input_core_manager(self):
		event = translateRawKeyEvent(SimpleNamespace(key="n", modifiers=("NVDA",)))
		gesture = makeKeyboardGesture(event)
		executed = []
		manager = SimpleNamespace(executeGesture=executed.append)

		self.assertTrue(executeKeyboardGesture(gesture, manager=manager))

		self.assertEqual([gesture], executed)

	def test_enable_input_core_execution_dispatches_pressed_key_to_manager(self):
		adapter = LinuxInputAdapter()
		executed = []
		manager = SimpleNamespace(executeGesture=executed.append)

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.enableInputCoreGestureExecution(manager=manager)
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="n", modifiers=("NVDA",), pressed=True))

		self.assertEqual(1, len(executed))
		self.assertEqual(("kb(desktop):NVDA+N", "kb(laptop):NVDA+N", "kb:NVDA+N"), executed[0].identifiers)

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
