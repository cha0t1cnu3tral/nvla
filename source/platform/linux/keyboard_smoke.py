# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Mapping

from .input import (
	KeyboardCaptureMode,
	LinuxInputAdapter,
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
	"""Observe live X11 gestures through the preview keyboard backend."""

	if environ is None:
		environ = os.environ
	if environ.get("WAYLAND_DISPLAY"):
		write("Wayland global keyboard capture is not implemented yet.")
		return 1
	if not environ.get("DISPLAY"):
		write("Set DISPLAY and run this tool from an X11 desktop session.")
		return 1
	if wait is None:
		wait = threading.Event().wait
	if source is None:
		source = X11NVDAModifierKeyboardEventSource() if commandGrabs else X11KeyboardEventSource()
	adapter = LinuxInputAdapter(keyboardEventSource=source)
	if commandGrabs:
		adapter.setKeyboardGestureExecutor(
			lambda gesture: _handleSmokeCommand(gesture.displayName, handledGestureNames, write),
		)
	adapter.registerKeyboardListener(lambda event: write(_formatEvent(event)))
	try:
		adapter.initialize_keyboard(observer=None)
		mode = adapter.keyboardCaptureMode
		write(f"Keyboard capture mode: {mode.value}")
		if mode is KeyboardCaptureMode.LOCAL_ONLY:
			write(f"X11 keyboard observation failed: {adapter.keyboardEventSourceStartError}")
			return 2
		if commandGrabs:
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
