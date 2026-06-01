# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from platform.linux.input import (
	KeyboardCaptureMode,
	LinuxInputAdapter,
	ManualKeyboardEventSource,
	X11KeyboardEventSource,
	X11NVDAModifierKeyboardEventSource,
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


class _FakeX11Display:
	def __init__(self, *, hasRecordExtension=True):
		self.display = self
		self.hasRecordExtension = hasRecordExtension
		self.disabledContexts = []
		self.freedContexts = []
		self.grabbedKeys = []
		self.ungrabbedKeys = []
		self.allowedEvents = []
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

	def keycode_to_keysym(self, keyCode, column):
		return keyCode

	def keysym_to_keycode(self, keysym):
		return keysym

	def screen(self):
		return SimpleNamespace(root=self)

	def grab_key(self, *args):
		self.grabbedKeys.append(args)

	def ungrab_key(self, *args):
		self.ungrabbedKeys.append(args)

	def allow_events(self, *args):
		self.allowedEvents.append(args)

	def pending_events(self):
		return 0

	def flush(self):
		return None

	def sync(self):
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
		X=SimpleNamespace(
			AnyModifier=32768,
			ControlMask=4,
			CurrentTime=0,
			GrabModeAsync=1,
			GrabModeSync=0,
			KeyPress=2,
			KeyRelease=3,
			Mod1Mask=8,
			Mod4Mask=64,
			ReplayKeyboard=5,
			ShiftMask=1,
			SyncKeyboard=3,
		),
		XK=SimpleNamespace(
			keysym_to_string=lambda keysym: {
				38: "a",
				50: "Shift_L",
				57: "n",
				90: "KP_Insert",
				91: "KP_0",
				118: "Insert",
			}[keysym],
			string_to_keysym=lambda name: {
				"Caps_Lock": 66,
				"Insert": 118,
				"KP_0": 91,
				"KP_Insert": 90,
			}[name],
		),
		display=SimpleNamespace(Display=makeDisplay),
		record=SimpleNamespace(AllClients="all", FromServer="server"),
		rq=SimpleNamespace(EventField=EventField),
	)
	return modules, displays


def _normalizeIdentifier(identifier):
	prefix, chord = identifier.lower().split(":", 1)
	return f"{prefix}:{'+'.join(sorted(chord.split('+')))}"


class TestLinuxInputAdapter(unittest.TestCase):
	def test_translates_all_global_keyboard_commands_to_shared_identifiers(self):
		globalCommandsPath = Path(__file__).resolve().parents[2] / "source" / "globalCommands.py"
		tree = ast.parse(globalCommandsPath.read_text(encoding="utf-8"))
		keyboardIdentifiers = {
			node.value
			for node in ast.walk(tree)
			if isinstance(node, ast.Constant)
			and isinstance(node.value, str)
			and node.value.startswith("kb")
			and ":" in node.value
		}

		self.assertGreater(len(keyboardIdentifiers), 100)
		for identifier in keyboardIdentifiers:
			with self.subTest(identifier=identifier):
				_, chord = identifier.split(":", 1)
				*modifiers, keyName = chord.split("+")
				event = translateRawKeyEvent(
					SimpleNamespace(
						key=keyName,
						modifiers=modifiers,
						nvdaModifierKeys=0,
					),
				)
				gesture = makeKeyboardGesture(event)
				self.assertIn(
					_normalizeIdentifier(identifier),
					gesture.normalizedIdentifiers,
				)

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

	def test_translates_title_shortcut_to_shared_nvda_identifier(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="t",
				modifiers=("Caps_Lock",),
				nvdaModifierKeys=1,
			),
		)

		gesture = makeKeyboardGesture(event)

		self.assertIn("kb:nvda+t", gesture.normalizedIdentifiers)

	def test_translates_linux_super_modifier_to_windows_compatible_identifier(self):
		event = translateRawKeyEvent(
			SimpleNamespace(
				key="d",
				modifiers=("Super_L",),
			),
		)

		self.assertEqual(frozenset(("windows",)), event.modifiers)
		self.assertEqual("windows+D", event.gestureName)

	def test_translates_linux_named_keys_to_existing_nvda_key_names(self):
		expectedKeyNames = {
			"Back_Space": "backspace",
			"Down": "downArrow",
			"KP_1": "numpad1",
			"KP_Add": "numpadPlus",
			"KP_Decimal": "numpadDelete",
			"KP_Divide": "numpadDivide",
			"KP_Enter": "numpadEnter",
			"KP_Multiply": "numpadMultiply",
			"KP_Subtract": "numpadMinus",
			"Left": "leftArrow",
			"Page_Down": "pageDown",
			"Page_Up": "pageUp",
			"Right": "rightArrow",
			"Up": "upArrow",
		}

		for linuxKeyName, nvdaKeyName in expectedKeyNames.items():
			with self.subTest(linuxKeyName=linuxKeyName):
				event = translateRawKeyEvent(SimpleNamespace(key=linuxKeyName))
				self.assertEqual(nvdaKeyName, event.keyName)
				self.assertEqual(nvdaKeyName, event.gestureName)

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

		self.assertEqual("windows+Enter", event.gestureName)
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
		self.assertIsInstance(createKeyboardEventSource({"DISPLAY": ":1"}), X11NVDAModifierKeyboardEventSource)
		self.assertIsInstance(createKeyboardEventSource({"WAYLAND_DISPLAY": "wayland-0"}), WaylandKeyboardEventSource)
		self.assertIsInstance(
			createKeyboardEventSource({"DISPLAY": ":1", "WAYLAND_DISPLAY": "wayland-0"}),
			WaylandKeyboardEventSource,
		)
		self.assertIsNone(createKeyboardEventSource({}))

	def test_unsupported_keyboard_event_source_does_not_abort_initialization(self):
		modules, _displays = _makeFakeX11Modules(hasRecordExtension=False)
		adapter = LinuxInputAdapter(
			keyboardEventSource=X11KeyboardEventSource(loadXlibModules=lambda: modules),
		)

		adapter.initialize_keyboard(SimpleNamespace())

		self.assertIsNotNone(adapter.keyboardEventSourceStartError)
		self.assertEqual(KeyboardCaptureMode.LOCAL_ONLY, adapter.keyboardCaptureMode)

	def test_x11_record_source_observes_global_key_events(self):
		modules, displays = _makeFakeX11Modules()
		source = X11KeyboardEventSource(loadXlibModules=lambda: modules)
		received = []
		source.start(received.append)

		source._handleRecordReply(
			SimpleNamespace(
				category="server",
				client_swapped=False,
				data=[
					SimpleNamespace(type=2, detail=50),
					SimpleNamespace(type=2, detail=38),
					SimpleNamespace(type=3, detail=38),
					SimpleNamespace(type=3, detail=50),
				],
			),
		)
		source.stop()

		self.assertEqual(["Shift_L", "a", "a", "Shift_L"], [event.key for event in received])
		self.assertEqual([True, True, False, False], [event.pressed for event in received])
		self.assertEqual({"Shift_L"}, received[1].modifiers)
		self.assertEqual(42, displays[1].enabledContext)
		self.assertEqual([42], displays[0].disabledContexts)
		self.assertEqual([42], displays[0].freedContexts)
		self.assertTrue(all(display.isClosed for display in displays))

	def test_x11_record_source_uses_observe_only_capture_mode(self):
		modules, _displays = _makeFakeX11Modules()
		adapter = LinuxInputAdapter(
			keyboardEventSource=X11KeyboardEventSource(loadXlibModules=lambda: modules),
		)

		adapter.initialize_keyboard(SimpleNamespace())

		self.assertEqual(KeyboardCaptureMode.GLOBAL_OBSERVE_ONLY, adapter.keyboardCaptureMode)
		adapter.terminate_keyboard()

	def test_x11_nvda_modifier_source_grabs_and_suppresses_handled_chord(self):
		modules, displays = _makeFakeX11Modules()
		source = X11NVDAModifierKeyboardEventSource(
			loadXlibModules=lambda: modules,
			nvdaModifierKeys=4,
		)
		adapter = LinuxInputAdapter(keyboardEventSource=source)
		adapter.setKeyboardGestureExecutor(lambda gesture: True)
		adapter.initialize_keyboard(SimpleNamespace())

		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=118, state=0, time=10))
		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=57, state=0, time=11))
		source._handleGrabbedEvent(SimpleNamespace(type=3, detail=57, state=0, time=12))
		source._handleGrabbedEvent(SimpleNamespace(type=3, detail=118, state=0, time=13))
		self.assertEqual(KeyboardCaptureMode.GLOBAL_COMMANDS, adapter.keyboardCaptureMode)
		adapter.terminate_keyboard()

		self.assertIn((118, modules.X.AnyModifier, False, modules.X.GrabModeAsync, modules.X.GrabModeSync), displays[0].grabbedKeys)
		self.assertEqual(
			[(modules.X.SyncKeyboard, time) for time in (10, 11, 12, 13)],
			displays[0].allowedEvents,
		)
		self.assertIn((118, modules.X.AnyModifier), displays[0].ungrabbedKeys)

	def test_x11_nvda_modifier_source_replays_unhandled_chord_event(self):
		modules, displays = _makeFakeX11Modules()
		source = X11NVDAModifierKeyboardEventSource(
			loadXlibModules=lambda: modules,
			nvdaModifierKeys=4,
		)
		adapter = LinuxInputAdapter(keyboardEventSource=source)
		adapter.setKeyboardGestureExecutor(lambda gesture: False)
		adapter.initialize_keyboard(SimpleNamespace())

		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=118, state=0, time=10))
		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=57, state=0, time=11))
		self.assertEqual(set(), adapter._pressedNVDAModifierKeys)
		adapter.terminate_keyboard()

		self.assertEqual((modules.X.ReplayKeyboard, 11), displays[0].allowedEvents[-1])

	def test_x11_nvda_modifier_source_replays_chord_before_executor_is_attached(self):
		modules, displays = _makeFakeX11Modules()
		source = X11NVDAModifierKeyboardEventSource(
			loadXlibModules=lambda: modules,
			nvdaModifierKeys=4,
		)
		adapter = LinuxInputAdapter(keyboardEventSource=source)
		adapter.initialize_keyboard(SimpleNamespace())

		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=118, state=0, time=10))
		source._handleGrabbedEvent(SimpleNamespace(type=2, detail=57, state=0, time=11))
		adapter.terminate_keyboard()

		self.assertEqual((modules.X.ReplayKeyboard, 11), displays[0].allowedEvents[-1])

	def test_keyboard_event_source_failure_uses_local_only_fallback(self):
		source = _FailingKeyboardEventSource()
		adapter = LinuxInputAdapter(keyboardEventSource=source)

		adapter.initialize_keyboard(SimpleNamespace())
		startError = adapter.keyboardEventSourceStartError
		self.assertEqual(KeyboardCaptureMode.LOCAL_ONLY, adapter.keyboardCaptureMode)
		adapter.terminate_keyboard()

		self.assertIsInstance(startError, RuntimeError)
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
				"kb(desktop):control+f1+nvda",
				"kb(laptop):control+f1+nvda",
				"kb:control+f1+nvda",
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

	def test_document_navigation_handler_consumes_gesture_before_input_core(self):
		adapter = LinuxInputAdapter()
		executed = []
		handled = []

		adapter.registerKeyboardGestureHandler(lambda gesture: handled.append(gesture) or True)
		adapter.setKeyboardGestureExecutor(executed.append)
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="h", pressed=True))

		self.assertEqual(event, handled[0].event)
		self.assertEqual([], executed)
		self.assertFalse(event.shouldPassThrough)

	def test_unregisters_keyboard_gesture_handler(self):
		adapter = LinuxInputAdapter()
		handled = []

		def handler(gesture):
			handled.append(gesture)
			return True

		adapter.registerKeyboardGestureHandler(handler)
		adapter.unregisterKeyboardGestureHandler(handler)
		event = adapter.feedRawKeyboardEvent(SimpleNamespace(key="h", pressed=True))

		self.assertEqual([], handled)
		self.assertTrue(event.shouldPassThrough)

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

	def test_unhandled_key_repeat_and_release_remain_pass_through(self):
		adapter = LinuxInputAdapter()
		executed = []

		def execute(gesture):
			executed.append(gesture)
			return False

		adapter.setKeyboardGestureExecutor(execute)
		pressedEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a", pressed=True))
		repeatedEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a", pressed=True))
		releasedEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a", pressed=False))
		nextPressedEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="a", pressed=True))

		self.assertTrue(pressedEvent.shouldPassThrough)
		self.assertTrue(repeatedEvent.shouldPassThrough)
		self.assertTrue(releasedEvent.shouldPassThrough)
		self.assertTrue(nextPressedEvent.shouldPassThrough)
		self.assertEqual(2, len(executed))

	def test_pass_next_key_through_replays_complete_chord_without_handlers(self):
		adapter = LinuxInputAdapter()
		handled = []
		adapter.registerKeyboardGestureHandler(lambda gesture: handled.append(gesture) or True)
		adapter.passNextKeyThrough()

		controlDown = adapter.feedRawKeyboardEvent(SimpleNamespace(key="control", pressed=True))
		sDown = adapter.feedRawKeyboardEvent(SimpleNamespace(key="s", modifiers=("control",), pressed=True))
		sRepeat = adapter.feedRawKeyboardEvent(SimpleNamespace(key="s", modifiers=("control",), pressed=True))
		sUp = adapter.feedRawKeyboardEvent(SimpleNamespace(key="s", modifiers=("control",), pressed=False))
		controlUp = adapter.feedRawKeyboardEvent(SimpleNamespace(key="control", pressed=False))
		nextEvent = adapter.feedRawKeyboardEvent(SimpleNamespace(key="t", pressed=True))

		self.assertTrue(controlDown.shouldPassThrough)
		self.assertTrue(sDown.shouldPassThrough)
		self.assertTrue(sRepeat.shouldPassThrough)
		self.assertTrue(sUp.shouldPassThrough)
		self.assertTrue(controlUp.shouldPassThrough)
		self.assertFalse(nextEvent.shouldPassThrough)
		self.assertEqual(["T"], [gesture.event.gestureName for gesture in handled])

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
