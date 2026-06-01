# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from .preview_commands import LinuxPreviewCommandController, formatObjectAnnouncement
from .speech import SpeechOutput, createSpeechOutput


def runNativePreview(
	*,
	durationSeconds: float | None = None,
	pollIntervalSeconds: float = 0.05,
	requireGlobalCapture: bool = False,
	services: Any | None = None,
	speechOutput: SpeechOutput | None = None,
	createOutput: Callable[[], SpeechOutput | None] = createSpeechOutput,
	createServices: Callable[[Callable[[str], None]], Any] | None = None,
	monotonic: Callable[[], float] = time.monotonic,
	wait: Callable[[float], Any] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Run the dependency-light Linux preview without loading the shared NVDA core."""

	if wait is None:
		wait = threading.Event().wait
	stopRequested = threading.Event()
	output = speechOutput if speechOutput is not None else createOutput()
	if output is None:
		write("Install Speech Dispatcher or espeak-ng before running the Linux preview.")
		return 1

	def announce(text: str) -> None:
		output.cancel()
		output.speak(text)
		write(f"speech: {text}")

	if services is None:
		if createServices is None:
			from .factory import create_platform_services

			createServices = lambda announce: create_platform_services(announce=announce)
		services = createServices(announce)
	accessibility = services.accessibility
	inputAdapter = services.input
	commandController = LinuxPreviewCommandController(
		dispatcher=accessibility.dispatcher,
		announce=announce,
		requestStop=stopRequested.set,
		passNextKeyThrough=inputAdapter.passNextKeyThrough,
		getClipboardText=getattr(getattr(services, "clipboard", None), "get_text", None),
		getBatteryStatus=getattr(getattr(services, "system", None), "get_battery_status", None),
	)

	def handleDispatch(eventName: str, obj: Any, **kwargs: Any) -> None:
		if eventName != "gainFocus":
			return
		announcement = formatObjectAnnouncement(obj)
		if announcement:
			announce(announcement)

	accessibility.registerDispatchListener(handleDispatch)
	inputAdapter.registerKeyboardGestureHandler(commandController.handleGesture)
	accessibilityInitialized = False
	keyboardInitialized = False
	mouseInitialized = False
	try:
		accessibility.initialize()
		accessibilityInitialized = True
		inputAdapter.initialize_keyboard(observer=None)
		keyboardInitialized = True
		inputAdapter.initialize_mouse()
		mouseInitialized = True
		write(f"Speech output: {output.name}")
		write(f"Keyboard capture mode: {inputAdapter.keyboardCaptureMode.value}")
		if inputAdapter.keyboardEventSourceStartError is not None:
			write(f"Keyboard capture fallback reason: {inputAdapter.keyboardEventSourceStartError}")
		write(f"Mouse capture mode: {inputAdapter.mouseCaptureMode.value}")
		if inputAdapter.mouseEventSourceStartError is not None:
			write(f"Mouse capture fallback reason: {inputAdapter.mouseEventSourceStartError}")
		if requireGlobalCapture and not _hasRequiredGlobalCapture(inputAdapter):
			write("Required global keyboard or mouse capture is unavailable.")
			return 3
		write("Linux native preview started. Press Ctrl+C to stop.")
		output.speak("NVDA Linux preview started")
		endTime = None if durationSeconds is None else monotonic() + max(0, durationSeconds)
		while True:
			accessibility.pump_all()
			if stopRequested.is_set():
				break
			if endTime is not None:
				remaining = endTime - monotonic()
				if remaining <= 0:
					break
				wait(min(pollIntervalSeconds, remaining))
			else:
				wait(pollIntervalSeconds)
	except KeyboardInterrupt:
		write("Linux native preview interrupted.")
	except Exception as error:
		write(f"Linux native preview failed: {error}")
		return 2
	finally:
		accessibility.unregisterDispatchListener(handleDispatch)
		inputAdapter.unregisterKeyboardGestureHandler(commandController.handleGesture)
		if mouseInitialized:
			inputAdapter.terminate_mouse()
		if keyboardInitialized:
			inputAdapter.terminate_keyboard()
		if accessibilityInitialized:
			accessibility.terminate()
		output.terminate()
	return 0


def _hasRequiredGlobalCapture(inputAdapter: Any) -> bool:
	return (
		inputAdapter.keyboardCaptureMode.value in ("global", "globalCommands")
		and inputAdapter.mouseCaptureMode.value in ("global", "globalObserveOnly")
	)
