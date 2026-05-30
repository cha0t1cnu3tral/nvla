# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest
from unittest import mock

from platform.linux.input import (
	KeyboardCaptureMode,
	LinuxInputAdapter,
	ManualKeyboardEventSource,
	X11KeyboardEventSource,
	WaylandKeyboardEventSource,
	createKeyboardEventSource,
	executeKeyboardGesture,
	makeKeyboardGesture,
	translateRawKeyEvent,
)


class _CountingKeyboardEventSource:
	def __init__(self):
		self.startCount = 0
		self.stopCount = 0

	def start(self, emit):
		self.startCount += 1

	def stop(self):
		self.stopCount += 1


class _FailingKeyboardEventSource(_CountingKeyboardEventSource):
	def start(self, emit):
		super().start(emit)
		raise RuntimeError("Capture unavailable")


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

	def test_translates_configured_insert_modifier_to_nvda_modifier(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="n",
				modifiers=("insert",),
				nvdaModifierKeys=4,
			),
		)

		self.assertEqual(frozenset(("NVDA",)), event.modifiers)
		self.assertEqual("NVDA+N", event.gestureName)

	def test_translates_configured_numpad_insert_modifier_to_nvda_modifier(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="f1",
				modifiers=("KP_Insert",),
				nvdaModifierKeys=2,
			),
		)

		self.assertEqual(frozenset(("NVDA",)), event.modifiers)
		self.assertEqual("NVDA+F1", event.gestureName)

	def test_translates_configured_caps_lock_modifier_to_nvda_modifier(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="t",
				modifiers=("Caps_Lock",),
				nvdaModifierKeys=1,
			),
		)

		self.assertEqual(frozenset(("NVDA",)), event.modifiers)
		self.assertEqual("NVDA+T", event.gestureName)

	def test_leaves_unconfigured_nvda_modifier_keys_as_regular_keys(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="n",
				modifiers=("capslock",),
				nvdaModifierKeys=4,
			),
		)

		self.assertEqual(frozenset(("capslock",)), event.modifiers)
		self.assertEqual("capslock+N", event.gestureName)

	def test_nvda_modifier_key_press_is_modifier_gesture(self):
		event = translateRawKeyEvent(SimpleNamespace(key="insert", nvdaModifierKeys=4))

		gesture = makeKeyboardGesture(event)

		self.assertEqual("NVDA", event.keyName)
		self.assertTrue(gesture.isModifier)
		self.assertEqual(("kb(desktop):NVDA", "kb(laptop):NVDA", "kb:NVDA"), gesture.identifiers)

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

	def test_manual_keyboard_event_source_feeds_adapter(self):
		source = ManualKeyboardEventSource()
		adapter = LinuxInputAdapter(keyboardEventSource=source)
		received = []

		adapter.registerKeyboardListener(received.append)
		adapter.initialize_keyboard(SimpleNamespace())
		event = source.emit(SimpleNamespace(key="f2", modifiers=("NVDA",)))

		self.assertTrue(source.isStarted)
		self.assertEqual(KeyboardCaptureMode.GLOBAL, adapter.keyboardCaptureMode)
		self.assertEqual("NVDA+F2", received[0].gestureName)
		self.assertEqual(event, received[0])

	def test_terminate_keyboard_stops_event_source(self):
		source = ManualKeyboardEventSource()
		adapter = LinuxInputAdapter(keyboardEventSource=source)

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.terminate_keyboard()

		self.assertFalse(source.isStarted)
		self.assertEqual(KeyboardCaptureMode.DISABLED, adapter.keyboardCaptureMode)
		with self.assertRaises(RuntimeError):
			source.emit(SimpleNamespace(key="a"))

	def test_selects_keyboard_event_source_from_session_environment(self):
		self.assertIsInstance(createKeyboardEventSource({"DISPLAY": ":1"}), X11KeyboardEventSource)
		self.assertIsInstance(createKeyboardEventSource({"WAYLAND_DISPLAY": "wayland-0"}), WaylandKeyboardEventSource)
		self.assertIsInstance(
			createKeyboardEventSource({"DISPLAY": ":1", "WAYLAND_DISPLAY": "wayland-0"}),
			WaylandKeyboardEventSource,
		)
		self.assertIsNone(createKeyboardEventSource({}))

	def test_unsupported_keyboard_event_source_does_not_abort_initialization(self):
		adapter = LinuxInputAdapter(keyboardEventSource=X11KeyboardEventSource())

		adapter.initialize_keyboard(SimpleNamespace())

		self.assertIsNotNone(adapter.keyboardEventSourceStartError)
		self.assertEqual(KeyboardCaptureMode.LOCAL_ONLY, adapter.keyboardCaptureMode)

	def test_keyboard_event_source_failure_uses_local_only_fallback(self):
		source = _FailingKeyboardEventSource()
		adapter = LinuxInputAdapter(keyboardEventSource=source)

		adapter.initialize_keyboard(SimpleNamespace())

		self.assertIsInstance(adapter.keyboardEventSourceStartError, RuntimeError)
		self.assertEqual(KeyboardCaptureMode.LOCAL_ONLY, adapter.keyboardCaptureMode)
		self.assertEqual(1, source.stopCount)

	def test_keyboard_initialize_and_terminate_are_idempotent(self):
		source = _CountingKeyboardEventSource()
		adapter = LinuxInputAdapter(keyboardEventSource=source)

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.initialize_keyboard(SimpleNamespace())
		adapter.terminate_keyboard()
		adapter.terminate_keyboard()

		self.assertEqual(1, source.startCount)
		self.assertEqual(1, source.stopCount)

	def test_uses_local_only_fallback_without_session_keyboard_source(self):
		adapter = LinuxInputAdapter()

		with mock.patch("platform.linux.input.createKeyboardEventSource", return_value=None):
			adapter.initialize_keyboard(SimpleNamespace())

		self.assertEqual(KeyboardCaptureMode.LOCAL_ONLY, adapter.keyboardCaptureMode)

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

	def test_unhandled_gesture_requests_pass_through_before_observer_dispatch(self):
		adapter = LinuxInputAdapter()
		received = []
		observerEvents = []

		adapter.initialize_keyboard(SimpleNamespace(handleKeyEvent=observerEvents.append))
		adapter.registerKeyboardListener(received.append)
		adapter.setKeyboardGestureExecutor(lambda gesture: False)
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a", pressed=True))

		self.assertTrue(event.shouldPassThrough)
		self.assertEqual([event], received)
		self.assertEqual([event], observerEvents)

	def test_tracks_pressed_nvda_modifier_for_following_key_events(self):
		adapter = LinuxInputAdapter()
		executed = []

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.setKeyboardGestureExecutor(executed.append)
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="n", pressed=True, nvdaModifierKeys=4))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=False, nvdaModifierKeys=4))
		unmodifiedEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="n", pressed=True, nvdaModifierKeys=4))

		self.assertEqual("NVDA+N", event.gestureName)
		self.assertEqual("N", unmodifiedEvent.gestureName)
		self.assertEqual("kb(desktop):NVDA+N", executed[0].identifiers[0])
		self.assertEqual("kb(desktop):N", executed[1].identifiers[0])

	def test_does_not_dispatch_modifier_only_key_to_gesture_executor(self):
		adapter = LinuxInputAdapter()
		executed = []

		adapter.initialize_keyboard(SimpleNamespace())
		adapter.setKeyboardGestureExecutor(executed.append)
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))

		self.assertEqual("NVDA", event.gestureName)
		self.assertEqual([], executed)

	def test_keeps_nvda_modifier_pressed_until_all_configured_keys_are_released(self):
		adapter = LinuxInputAdapter()

		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=6))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="KP_Insert", pressed=True, nvdaModifierKeys=6))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=False, nvdaModifierKeys=6))
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="t", pressed=True, nvdaModifierKeys=6))

		self.assertEqual("NVDA+T", event.gestureName)

	def test_second_nvda_modifier_press_within_timeout_requests_pass_through(self):
		now = 10.0
		adapter = LinuxInputAdapter(clock=lambda: now, multiPressTimeoutSeconds=0.5)
		executed = []
		adapter.setKeyboardGestureExecutor(executed.append)

		adapter.feedRawKeyboardEvent(SimpleNamespace(key="capslock", pressed=True, nvdaModifierKeys=1))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="capslock", pressed=False, nvdaModifierKeys=1))
		now += 0.25
		pressedEvent = adapter.feedRawKeyboardEvent(
			SimpleNamespace(key="capslock", pressed=True, nvdaModifierKeys=1),
		)
		releasedEvent = adapter.feedRawKeyboardEvent(
			SimpleNamespace(key="capslock", pressed=False, nvdaModifierKeys=1),
		)

		self.assertEqual("capslock", pressedEvent.keyName)
		self.assertTrue(pressedEvent.shouldPassThrough)
		self.assertTrue(releasedEvent.shouldPassThrough)
		self.assertEqual([], executed)

	def test_nvda_modifier_press_after_timeout_remains_nvda_modifier(self):
		now = 10.0
		adapter = LinuxInputAdapter(clock=lambda: now, multiPressTimeoutSeconds=0.5)

		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=False, nvdaModifierKeys=4))
		now += 0.75
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))

		self.assertEqual("NVDA", event.keyName)
		self.assertFalse(event.shouldPassThrough)

	def test_non_modifier_press_clears_nvda_modifier_pass_through_candidate(self):
		now = 10.0
		adapter = LinuxInputAdapter(clock=lambda: now, multiPressTimeoutSeconds=0.5)

		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="n", pressed=True, nvdaModifierKeys=4))
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=False, nvdaModifierKeys=4))
		now += 0.25
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))

		self.assertEqual("NVDA", event.keyName)
		self.assertFalse(event.shouldPassThrough)

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
		adapter.feedRawKeyboardEvent(SimpleNamespace(key="insert", pressed=True, nvdaModifierKeys=4))
		received.clear()
		executed.clear()
		adapter.terminate_keyboard()
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a"))

		self.assertEqual([], received)
		self.assertEqual([], executed)
		self.assertEqual("A", event.gestureName)
