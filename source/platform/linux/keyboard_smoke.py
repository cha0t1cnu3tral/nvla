# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Mapping

from .input import (
	KeyboardCaptureMode,
	LinuxInputAdapter,
	WaylandKeyboardEventSource,
	X11KeyboardEventSource,
	X11NVDAModifierKeyboardEventSource,
)


def runKeyboardSmoke(
	*,
	durationSeconds: float = 15,
	commandGrabs: bool = False,
	handledGestureNames: tuple[str, ...] = ("NVDA+T",),
	environ: Mapping[str, str] | None = None,
	source: Any | None = None,
	wait: Callable[[float], Any] | None = None,
	write: Callable[[str], None] = print,
) -> int:
	"""Observe live gestures through the preview keyboard backend."""

	if environ is None:
		environ = os.environ
	isWayland = bool(environ.get("WAYLAND_DISPLAY"))
	if not isWayland and not environ.get("DISPLAY"):
		write("Set WAYLAND_DISPLAY or DISPLAY and run this tool from a Linux desktop session.")
		return 1
	if wait is None:
		wait = threading.Event().wait
	if source is None:
		source = (
			WaylandKeyboardEventSource()
			if isWayland
			else X11NVDAModifierKeyboardEventSource()
			if commandGrabs
			else X11KeyboardEventSource()
		)
	adapter = LinuxInputAdapter(keyboardEventSource=source)
	if commandGrabs or isWayland:
		adapter.setKeyboardGestureExecutor(
			lambda gesture: _handleSmokeCommand(gesture.displayName, handledGestureNames, write),
		)
	adapter.registerKeyboardListener(lambda event: write(_formatEvent(event)))
	try:
		adapter.initialize_keyboard(observer=None)
		mode = adapter.keyboardCaptureMode
		write(f"Keyboard capture mode: {mode.value}")
		if mode is KeyboardCaptureMode.LOCAL_ONLY:
			write(f"Keyboard capture failed: {adapter.keyboardEventSourceStartError}")
			return 2
		if commandGrabs or isWayland:
			write("Press NVDA+T in another application; it should be logged as handled and suppressed.")
			write("Try another NVDA chord to exercise pass-through replay.")
		else:
			write("Press keys in other applications. Handled keys still reach the focused application.")
		wait(durationSeconds)
	except KeyboardInterrupt:
		write("Keyboard smoke observation interrupted.")
	finally:
		adapter.terminate_keyboard()
	return 0


def _formatEvent(event: Any) -> str:
	action = "down" if event.isPressed else "up"
	passThrough = " passThrough" if event.shouldPassThrough else ""
	return f"{action}: {event.gestureName}{passThrough}"


def _handleSmokeCommand(
	gestureName: str,
	handledGestureNames: tuple[str, ...],
	write: Callable[[str], None],
) -> bool:
	if gestureName not in handledGestureNames:
		return False
	write(f"handled: {gestureName}")
	return True
