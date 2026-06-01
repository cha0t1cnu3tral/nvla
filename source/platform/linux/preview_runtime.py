# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from .speech import SpeechOutput, createSpeechOutput


def runNativePreview(
	*,
	durationSeconds: float | None = None,
	pollIntervalSeconds: float = 0.05,
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

	def handleDispatch(eventName: str, obj: Any, **kwargs: Any) -> None:
		if eventName != "gainFocus":
			return
		announcement = _formatObjectAnnouncement(obj)
		if announcement:
			announce(announcement)

	accessibility.registerDispatchListener(handleDispatch)
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
		write(f"Mouse capture mode: {inputAdapter.mouseCaptureMode.value}")
		write("Linux native preview started. Press Ctrl+C to stop.")
		output.speak("NVDA Linux preview started")
		endTime = None if durationSeconds is None else monotonic() + max(0, durationSeconds)
		while True:
			accessibility.pump_all()
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
		if mouseInitialized:
			inputAdapter.terminate_mouse()
		if keyboardInitialized:
			inputAdapter.terminate_keyboard()
		if accessibilityInitialized:
			accessibility.terminate()
		output.terminate()
	return 0


def _formatObjectAnnouncement(obj: Any) -> str:
	parts = []
	for value in (getattr(obj, "name", None), getattr(obj, "description", None)):
		if value and value not in parts:
			parts.append(str(value))
	role = getattr(obj, "role", None)
	roleLabel = getattr(role, "displayString", None) or getattr(role, "name", None)
	if roleLabel:
		roleLabel = str(roleLabel).lower()
		if roleLabel not in parts:
			parts.append(roleLabel)
	return ", ".join(parts)
