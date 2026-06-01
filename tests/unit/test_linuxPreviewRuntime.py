# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from types import SimpleNamespace
import unittest

from platform.linux.preview_runtime import runNativePreview


class _Adapter:
	def __init__(self, *, fail=False):
		self.fail = fail
		self.dispatcher = SimpleNamespace(focusObject=None)
		self.listener = None
		self.calls = []

	def registerDispatchListener(self, listener):
		self.listener = listener

	def unregisterDispatchListener(self, listener):
		self.calls.append("unregisterDispatchListener")
		self.listener = None

	def initialize(self):
		self.calls.append("initialize")
		if self.fail:
			raise RuntimeError("registry unavailable")

	def pump_all(self):
		self.calls.append("pump_all")
		if self.listener is not None:
			listener = self.listener
			self.listener = None
			listener(
				"gainFocus",
				SimpleNamespace(
					name="Save",
					description="Write changes",
					role=SimpleNamespace(name="BUTTON"),
				),
			)

	def terminate(self):
		self.calls.append("terminate")


class _Input:
	keyboardCaptureMode = SimpleNamespace(value="localOnly")
	mouseCaptureMode = SimpleNamespace(value="globalObserveOnly")
	keyboardEventSourceStartError = None
	mouseEventSourceStartError = None

	def __init__(self):
		self.calls = []
		self.handlers = []

	def registerKeyboardGestureHandler(self, handler, *, first=False):
		self.calls.append("registerKeyboardGestureHandler")
		if first:
			self.handlers.insert(0, handler)
		else:
			self.handlers.append(handler)

	def unregisterKeyboardGestureHandler(self, handler):
		self.calls.append("unregisterKeyboardGestureHandler")
		self.handlers.remove(handler)

	def initialize_keyboard(self, observer):
		self.calls.append("initialize_keyboard")

	def initialize_mouse(self):
		self.calls.append("initialize_mouse")

	def passNextKeyThrough(self):
		self.calls.append("passNextKeyThrough")

	def terminate_keyboard(self):
		self.calls.append("terminate_keyboard")

	def terminate_mouse(self):
		self.calls.append("terminate_mouse")


class _Speech:
	name = "testSpeech"

	def __init__(self):
		self.spoken = []
		self.cancelCount = 0
		self.isTerminated = False

	def speak(self, text):
		self.spoken.append(text)

	def cancel(self):
		self.cancelCount += 1

	def terminate(self):
		self.isTerminated = True


class TestLinuxPreviewRuntime(unittest.TestCase):
	def test_runs_native_preview_lifecycle_and_announces_focus(self):
		accessibility = _Adapter()
		inputAdapter = _Input()
		output = _Speech()
		writes = []

		result = runNativePreview(
			durationSeconds=0,
			services=SimpleNamespace(accessibility=accessibility, input=inputAdapter),
			speechOutput=output,
			write=writes.append,
		)

		self.assertEqual(0, result)
		self.assertEqual(["NVDA Linux preview started", "Save, Write changes, button"], output.spoken)
		self.assertEqual(1, output.cancelCount)
		self.assertTrue(output.isTerminated)
		self.assertEqual(
			["initialize", "pump_all", "unregisterDispatchListener", "terminate"],
			accessibility.calls,
		)
		self.assertEqual(
			["initialize_keyboard", "initialize_mouse", "terminate_mouse", "terminate_keyboard"],
			[
				call
				for call in inputAdapter.calls
				if call not in ("registerKeyboardGestureHandler", "unregisterKeyboardGestureHandler")
			],
		)
		self.assertEqual([], inputAdapter.handlers)
		self.assertIn("Keyboard capture mode: localOnly", writes)
		self.assertIn("Mouse capture mode: globalObserveOnly", writes)

	def test_reports_missing_speech_output(self):
		writes = []

		result = runNativePreview(createOutput=lambda: None, write=writes.append)

		self.assertEqual(1, result)
		self.assertIn("Speech Dispatcher", writes[0])

	def test_cleans_up_speech_and_listener_after_accessibility_failure(self):
		accessibility = _Adapter(fail=True)
		output = _Speech()
		writes = []

		result = runNativePreview(
			services=SimpleNamespace(accessibility=accessibility, input=_Input()),
			speechOutput=output,
			write=writes.append,
		)

		self.assertEqual(2, result)
		self.assertTrue(output.isTerminated)
		self.assertEqual(["initialize", "unregisterDispatchListener"], accessibility.calls)
		self.assertIn("registry unavailable", writes[-1])

	def test_nvda_q_stops_runtime_through_registered_command_handler(self):
		accessibility = _Adapter()
		inputAdapter = _Input()
		output = _Speech()
		originalPumpAll = accessibility.pump_all

		def pumpAll():
			originalPumpAll()
			inputAdapter.handlers[0](SimpleNamespace(event=SimpleNamespace(gestureName="NVDA+Q")))

		accessibility.pump_all = pumpAll

		result = runNativePreview(
			services=SimpleNamespace(accessibility=accessibility, input=inputAdapter),
			speechOutput=output,
			write=lambda text: None,
		)

		self.assertEqual(0, result)
		self.assertIn("Exiting NVDA Linux preview", output.spoken)
		self.assertEqual([], inputAdapter.handlers)

	def test_reports_keyboard_and_mouse_capture_fallback_reasons(self):
		accessibility = _Adapter()
		inputAdapter = _Input()
		inputAdapter.keyboardEventSourceStartError = RuntimeError("keyboard unavailable")
		inputAdapter.mouseEventSourceStartError = RuntimeError("mouse unavailable")
		writes = []

		result = runNativePreview(
			durationSeconds=0,
			services=SimpleNamespace(accessibility=accessibility, input=inputAdapter),
			speechOutput=_Speech(),
			write=writes.append,
		)

		self.assertEqual(0, result)
		self.assertIn("Keyboard capture fallback reason: keyboard unavailable", writes)
		self.assertIn("Mouse capture fallback reason: mouse unavailable", writes)

	def test_strict_capture_fails_after_local_only_runtime_fallback(self):
		accessibility = _Adapter()
		inputAdapter = _Input()
		output = _Speech()
		writes = []

		result = runNativePreview(
			requireGlobalCapture=True,
			services=SimpleNamespace(accessibility=accessibility, input=inputAdapter),
			speechOutput=output,
			write=writes.append,
		)

		self.assertEqual(3, result)
		self.assertTrue(output.isTerminated)
		self.assertEqual([], inputAdapter.handlers)
		self.assertIn("Required global keyboard or mouse capture is unavailable.", writes)


if __name__ == "__main__":
	unittest.main()
